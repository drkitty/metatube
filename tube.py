#!/usr/bin/env python2

import argparse

from client import authentication_request_url, GoogleAPIClient
from data import Channel, Playlist, Session, Video


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--update', action='store_true')
    parser.add_argument('-d', '--download', action='store_true')
    parser.add_argument('--list-channels', action='store_true')
    parser.add_argument('--list-playlists', action='store_true')
    parser.add_argument('-p', '--add-playlists')
    parser.add_argument('-c', '--add-channels')
    args = parser.parse_args()

    c = GoogleAPIClient()

    if c.access_token is None:
        print 'Open the following URL in your Web browser and grant access'
        print authentication_request_url
        print
        print 'Enter the authorization code here:'

        code = raw_input('> ')

        c.get_token_pair(code)

    try:
        s = Session()

        if s.query(Channel).filter(Channel.mine == True).count() == 0:
            Channel.fetch_channels(c, track=True)

        if args.list_channels:
            for channel in s.query(Channel).filter(Channel.tracked == True):
                print '{:>35}  {}'.format(channel.id, channel.title)
        if args.list_playlists:
            s = Session()
            for channel in s.query(Channel).filter(Channel.tracked == True):
                channel.list_normal_playlists(c)
                channel.list_special_playlists(c)
            #for playlist in s.query(Playlist):
                #print '{:>35}  {} (~{})'.format(playlist.id, playlist.title)
        if args.add_channels:
            for username in args.add_channels.split(','):
                fetched = Channel.fetch_channels(c, username=username,
                                                 track=True)
        if args.add_playlists:
            Playlist.fetch_playlists(c, args.add_playlists.split(','))
        if args.update:
            for playlist in s.query(Playlist):
                playlist.fetch_playlist_videos(c)
        if args.download:
            for video in s.query(Video):
                print '{} (~{})'.format(video.title, video.channel.title)
                video.download()
    except:
        s.rollback()
        raise
    finally:
        s.close()




if __name__ == '__main__':
    main()
