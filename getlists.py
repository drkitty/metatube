#!/usr/bin/env python

from sys import stdout

import data
from client import authentication_request_url, GoogleAPIClient


c = GoogleAPIClient()

if c.access_token is None:
    print 'Open the following URL in your Web browser and grant access'
    print authentication_request_url
    print
    print 'Enter the authorization code here:'

    code = raw_input('> ')

    c.get_token_pair(code)


data.Channel.fetch_user_channel(c)
data.Channel.fetch_user_channel(c, username='retsupurae')

s = data.Session()
me = s.query(data.Channel).filter(
    data.Channel.title == 'electricmuffin11').first()
rp = s.query(data.Channel).filter(
    data.Channel.title == 'retsupurae').first()
del s

me.list_normal_playlists(c)
me.list_special_playlists(c)

rp.list_normal_playlists(c)
rp.list_special_playlists(c)

while True:
    playlist_ids = raw_input('> ')
    playlist_ids = playlist_ids.split(',')
    data.Playlist.fetch_playlists(c, playlist_ids)

#me.fetch_normal_playlists(c)
#me.fetch_special_playlists(c, names=('favorites',))

#s = data.Session()
#for playlist in s.query(data.Playlist):
    #playlist.fetch_playlist_videos(c)
#del s
