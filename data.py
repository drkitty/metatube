import dateutil.parser
from sqlalchemy import (
    create_engine, Boolean, Column, DateTime, ForeignKey, Integer, String,
    Text
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import settings


engine = create_engine('mysql+oursql://metatube@localhost/metatubedb',
                       echo=settings.debug)

Base = declarative_base()

Session = sessionmaker(bind=engine)


class Video(Base):
    __tablename__ = 'video'

    id = Column(String(16), primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    date_published = Column(DateTime)
    channel_id = Column(String(40), ForeignKey('channel.id'))

    def __repr__(self):
        return '<Video "{}">'.format(self.title)


class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(String(40), primary_key=True)
    title = Column(String(60))
    description = Column(Text)
    channel_id = Column(String(40), ForeignKey('channel.id'))

    def __repr__(self):
        return '<Playlist "{}">'.format(self.title)

    def get_playlist_videos(self, client):
        videos = []
        playlist_videos = []
        channels = []

        def process(item):
            snippet = item['snippet']

            v = Video(
                id=snippet['resourceId']['videoId'],
                title=snippet['title'],
                description=snippet['description'],
                date_published=dateutil.parser.parse(snippet['publishedAt']),
                channel_id=snippet['channelId'],
            )
            videos.append(v)
            playlist_videos.append(PlaylistVideo(
                video=v,
                playlist=self,
                position=snippet['position'],
            ))



        params = {
            'part': 'id,snippet',
            'playlistId': self.id,
        }

        client.get('/playlistItems', params, process)

        return channels, videos, playlist_videos


class PlaylistVideo(Base):
    __tablename__ = 'playlistvideo'

    video = Column(String(16), ForeignKey('video.id'), primary_key=True)
    playlist = Column(String(40), ForeignKey('playlist.id'), primary_key=True)
    position = Column(Integer)


class Channel(Base):
    __tablename__ = 'channel'

    id = Column(String(40), primary_key=True)
    title = Column(String(200))
    description = Column(Text)
    playlists = relationship('Playlist', backref='channel')

    def __repr__(self):
        return '<Channel "{}">'.format(self.title)

    @classmethod
    def get_user_channels(cls, client, username=None):
        channels = []

        def process_channel(item):
            snippet = item['snippet']

            channels.append(Channel(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
            ))

        params = {'part': 'id,snippet'}
        if username is None:
            params['mine'] = 'true'
        else:
            params['forUsername'] = username

        client.get('/channels', params, process_channel)

        return channels

    def get_normal_playlists(self, client):
        playlists = []

        def process_playlist(item):
            snippet = item['snippet']
            playlists.append(Playlist(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
                channel=self,
            ))

        params = {'part': 'snippet'}

        params['channelId'] = self.id

        client.get('/playlists', {
            'part': 'snippet',
            'channelId': self.id,
        }, process_playlist)

        return playlists

    def get_special_playlists(self, client, names=()):
        playlists = []

        def process_playlist(item):
            snippet = item['snippet']
            playlists.append(Playlist(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
                channel=self,
            ))

        def process_channel(item):
            special_playlists = item['contentDetails']['relatedPlaylists']
            selected_playlist_ids = [special_playlists[name] for name in names
                                     if name in special_playlists]

            client.get('/playlists', {
                'part': 'id,snippet',
                'id': ','.join(selected_playlist_ids),
            }, process_playlist)

        client.get('/channels', {
            'part': 'contentDetails',
            'id': self.id,
        }, process_channel)

        return playlists
