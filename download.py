#!/usr/bin/env python

import data
from client import authentication_request_url, GoogleAPIClient


c = GoogleAPIClient()

s = data.Session()
for playlist in s.query(data.Playlist):
    playlist.fetch_playlist_videos(c)
for video in s.query(data.Video):
    print u'+++ Downloading "{}" +++'.format(video.title)
    video.download()
del s
