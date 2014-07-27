from __future__ import unicode_literals

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
from client import authentication_request_url, GoogleAPIClient


CHUNK_SIZE = 100000


def utf8mb4_connect(**kwargs):
    connection = oursql.Connection(
        host=settings.database['host'], user=settings.database['user'],
        db=settings.database['db'], **kwargs)
    cursor = connection.cursor()
    cursor.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_bin'")
    return connection


engine = create_engine('mysql+oursql://metatube@localhost/metatubedb',
                       echo=settings.debug, encoding=b'utf_8',
                       creator=utf8mb4_connect)

Base = declarative_base()

Session = sessionmaker(bind=engine)


class EverythingManager(object):
    def __init__(self):
        self.api_client = GoogleAPIClient()
        if self.api_client.access_token is None:
            print ('Open the following URL in your Web browser and grant '
                   'metatube read-only access to your account.')
            print authentication_request_url
            print
            print 'Then enter the authorization code here:'
            code = raw_input('> ')
            self.api_client.get_token_pair(code)
            print

        self.session = Session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()


class Video(Base):
    __tablename__ = 'video'

    id = Column(String(16), primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    date_published = Column(DateTime)
    channel_id = Column(String(40), ForeignKey('channel.id'))
    playlist_videos = relationship('PlaylistVideo', backref='video')
    downloaded = Column(Boolean)
    skip = Column(Boolean)

    def __repr__(self):
        return '<Video: "{}">'.format(self.title.encode('ascii', 'replace'))

    def download(self, mgr):
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
        mgr.session.merge(self)


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
    def fetch_playlists(cls, mgr, ids):
        def process_playlist(item):
            snippet = item['snippet']

            Channel.fetch_channels(mgr, ids=(snippet['channelId'],))

            mgr.session.merge(Playlist(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
                channel_id=snippet['channelId'],
            ))

        mgr.api_client.get('/playlists', {
            'part': 'snippet',
            'id': ','.join(ids),
        }, process_playlist)


    def fetch_playlist_videos(self, mgr):
        video_ids = []
        playlist_videos = []

        def process_playlist_item(item):
            snippet = item['snippet']
            video_id = snippet['resourceId']['videoId']

            video_ids.append(video_id)
            playlist_videos.append(PlaylistVideo(
                video_id=video_id,
                playlist_id=self.id,
                position=snippet['position'],
            ))

        mgr.api_client.get('/playlistItems', {
            'part': 'snippet',
            'fields': 'items/snippet(position,resourceId)',
            'playlistId': self.id,
        }, process_playlist_item)

        fetched_video_ids = []

        def process_video(item):
            snippet = item['snippet']

            Channel.fetch_channels(mgr, ids=(snippet['channelId'],))
            v = Video(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
                date_published=dateutil.parser.parse(
                    snippet['publishedAt'].rstrip('Z')),
                channel_id=snippet['channelId'],
            )
            mgr.session.merge(v)
            fetched_video_ids.append(item['id'])

        mgr.api_client.get('/videos', {
            'part': 'id,snippet',
            'id': ','.join(video_ids),
            'fields': 'items(id,snippet)',
        }, process_video)

        for playlist_video in playlist_videos:
            # If a video is removed, sometimes its information can be accessed
            # via the /playlistItems endpoint even if it's not accessible via
            # the /videos endpoint.
            if playlist_video.video_id in fetched_video_ids:
                mgr.session.merge(playlist_video)


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
    def fetch_channels(cls, mgr, ids=(), username=None, track=None):
        get_mine = bool(not ids and not username)

        ids = filter(lambda id: id not in cls.fetched, ids)
        if not ids and not username and not get_mine:
            return
        if ids and username:
            raise Exception(
                'You cannot call this method with both `ids` and `username`')

        def process_channel(item):
            snippet = item['snippet']

            cls.fetched.add(item['id'])

            old = mgr.session.query(Channel).get(item['id'])
            if old is not None:
                tracked = old.tracked if track is None else track
                new_mine = old.mine
            else:
                tracked = False if track is None else track
                new_mine = get_mine

            mgr.session.merge(Channel(
                id=item['id'],
                title=snippet['title'],
                description=snippet['description'],
                mine=new_mine,
                tracked=tracked,
            ))

        params = {'part': 'id,snippet'}
        if get_mine:
            params['mine'] = 'true'
        elif ids:
            params['id'] = ','.join(ids)
        elif username:
            params['forUsername'] = username
        else:
            raise Exception('This should never happen')
        mgr.api_client.get('/channels', params, process_channel)

    def find_playlists(self, mgr):
        playlists = []

        def process_playlist(item):
            snippet = item['snippet']

            playlists.append({
                'id': item['id'],
                'title': item['snippet']['title'],
            })

        def process_channel(item):
            special_playlists = item['contentDetails']['relatedPlaylists']
            playlist_ids = special_playlists.itervalues()

            mgr.api_client.get('/playlists', {
                'part': 'id,snippet',
                'id': ','.join(playlist_ids),
            }, process_playlist)

        # Find normal playlists.
        mgr.api_client.get('/playlists', {
            'part': 'snippet',
            'channelId': self.id,
        }, process_playlist)

        # Find special playlists.
        mgr.api_client.get('/channels', {
            'part': 'contentDetails',
            'id': self.id,
        }, process_channel)

        return playlists
