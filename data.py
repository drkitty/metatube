import dateutil.parser
import os
import os.path
import subprocess
from sys import stderr

import oursql
import requests
from sqlalchemy import (
    create_engine, Boolean, Column, DateTime, ForeignKey, Integer, String,
    Text
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import settings


CHUNK_SIZE = 100000


def utf8mb4_connect(**kwargs):
    connection = oursql.Connection(
        host=settings.database['host'], user=settings.database['user'],
        db=settings.database['db'], **kwargs)
    cursor = connection.cursor()
    cursor.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_bin'")
    return connection


engine = create_engine('mysql+oursql://metatube@localhost/metatubedb',
                       echo=settings.debug, encoding='utf_8',
                       creator=utf8mb4_connect)

Base = declarative_base()

Session = sessionmaker(bind=engine)


def format_playlist(playlist_id, playlist_title, channel_title):
    return '{:>35}  {} (~{})'.format(
        playlist_id, playlist_title, channel_title)


class Video(Base):
    __tablename__ = 'video'

    id = Column(String(16), primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    date_published = Column(DateTime)
    channel_id = Column(String(40), ForeignKey('channel.id'))
    playlist_videos = relationship('PlaylistVideo', backref='video')
    downloaded = Column(Boolean)

    def __repr__(self):
        return '<Video: "{}">'.format(self.title.encode('ascii', 'replace'))

    def download(self):
        try:
            if os.path.getsize('dl/' + self.id) != 0:
                return
        except OSError as e:
            if e.errno != 2:  # 'No such file or directory'
                raise

        p = subprocess.Popen(
            ('youtube-dl', '-g', 'https://www.youtube.com/watch?v=' + self.id),
            stdout=subprocess.PIPE)
        url, _ = p.communicate()
        url = url.strip()
        if p.returncode != 0:
            stderr.write('youtube-dl failed with error code {}\n'.format(
                p.returncode))
            return
        with open('temp', 'w') as f:
            for chunk in requests.get(url, stream=True).iter_content(
                    CHUNK_SIZE):
                f.write(chunk)

        try:
            os.mkdir('dl')
        except OSError as e:
            if e.errno != 17:  # 'File exists'
                raise
        os.rename('temp', 'dl/' + self.id)
        self.downloaded = True
        session = Session()
        session.merge(self)
        session.commit()


class Playlist(Base):
    __tablename__ = 'playlist'

    id = Column(String(40), primary_key=True)
    title = Column(String(60))
    description = Column(Text)
    channel_id = Column(String(40), ForeignKey('channel.id'))
    playlist_videos = relationship('PlaylistVideo', backref='playlist')

    def __repr__(self):
        return '<Playlist: "{}">'.format(self.title.encode('ascii', 'replace'))

    @classmethod
    def fetch_playlists(cls, client, ids):
        session = Session()

        def process_playlist(item):
            snippet = item['snippet']

            Channel.fetch_channels(client, ids=(snippet['channelId'],))

            session.merge(Playlist(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
                channel_id=snippet['channelId'],
            ))

        client.get('/playlists', {
            'part': 'snippet',
            'id': ','.join(ids),
        }, process_playlist)

        session.commit()


    def fetch_playlist_videos(self, client):
        session = Session()

        def process_video(item):
            snippet = item['snippet']

            print snippet['channelId']
            Channel.fetch_channels(client, ids=(snippet['channelId'],))

            v = Video(
                id=snippet['resourceId']['videoId'],
                title=snippet['title'],
                description=snippet['description'],
                date_published=dateutil.parser.parse(
                    snippet['publishedAt'].rstrip('Z')),
                channel_id=snippet['channelId'],
            )
            session.merge(v)
            session.merge(PlaylistVideo(
                video_id=v.id,
                playlist_id=self.id,
                position=snippet['position'],
            ))

        client.get('/playlistItems', {
            'part': 'id,snippet',
            'playlistId': self.id,
        }, process_video)

        session.commit()


class PlaylistVideo(Base):
    __tablename__ = 'playlistvideo'

    video_id = Column(String(16), ForeignKey('video.id'), primary_key=True)
    playlist_id = Column(String(40), ForeignKey('playlist.id'),
                         primary_key=True)
    position = Column(Integer, autoincrement=False, primary_key=True)


class Channel(Base):
    __tablename__ = 'channel'

    id = Column(String(40), primary_key=True)
    title = Column(String(200))
    description = Column(Text)
    mine = Column(Boolean)
    tracked = Column(Boolean)
    playlists = relationship('Playlist', backref='channel')
    videos = relationship('Video', backref='channel')

    fetched = set()

    def __repr__(self):
        return '<Channel: "{}">'.format(self.title.encode('ascii', 'replace'))

    @classmethod
    def fetch_channels(cls, client, ids=(), username=None, track=False):
        get_mine = bool(not ids and not username)

        ids = filter(lambda id: id not in cls.fetched, ids)
        if not ids and not username and not get_mine:
            return
        if ids and username:
            raise Exception(
                'You cannot call this method with both `ids` and `username`')

        fetched = set()
        session = Session()

        def process_channel(item):
            snippet = item['snippet']

            fetched.add(item['id'])

            session.merge(Channel(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
                mine=get_mine,
                tracked=track,
            ))

        params = {'part': 'id,snippet'}
        if get_mine:
            params['mine'] = 'true'
        elif ids:
            params['id'] = ','.join(ids)
        elif username:
            params['forUsername'] = ','.join(ids)
        else:
            return
        client.get('/channels', params, process_channel)

        session.commit()
        cls.fetched.update(fetched)

    def list_normal_playlists(self, client):
        def process_playlist(item):
            snippet = item['snippet']

            print format_playlist(
                item['id'], item['snippet']['title'], self.title)

        client.get('/playlists', {
            'part': 'snippet',
            'channelId': self.id,
        }, process_playlist)

    def fetch_playlists(self, client, ids=()):
        session = Session()

        def process_playlist(item):
            snippet = item['snippet']

            session.merge(Playlist(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
                channel_id=self.id,
            ))

        client.get('/playlists', {
            'part': 'snippet',
            'id': ','.join(ids),
        }, process_playlist)

        session.commit()

    def list_special_playlists(self, client):
        def process_playlist(item):
            snippet = item['snippet']

            print format_playlist(
                item['id'], item['snippet']['title'], self.title)

        def process_channel(item):
            special_playlists = item['contentDetails']['relatedPlaylists']
            playlist_ids = special_playlists.itervalues()

            client.get('/playlists', {
                'part': 'id,snippet',
                'id': ','.join(playlist_ids),
            }, process_playlist)


        client.get('/channels', {
            'part': 'contentDetails',
            'id': self.id,
        }, process_channel)
