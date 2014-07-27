#!/usr/bin/env python2

from __future__ import unicode_literals

import argparse

from data import Channel, EverythingManager, Playlist, Session, Video


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--update', action='store_true')
    group.add_argument('-d', '--download', action='store_true')
    group.add_argument('--list-channels', action='store_true')
    group.add_argument('-l', '--list-playlists', action='store_true')
    group.add_argument('-f', '--find-playlists', action='store_true')
    group.add_argument('-p', '--add-playlists')
    group.add_argument('-a', '--add-my-playlists', action='store_true')
    group.add_argument('-c', '--add-channels')
    args = parser.parse_args()

    with EverythingManager() as mgr:
        if mgr.session.query(Channel).filter(
                Channel.mine == True).count() == 0:
            print 'Fetching your channel...'
            Channel.fetch_channels(mgr, track=True)

        if args.list_channels:
            for channel in mgr.session.query(Channel).filter(
                    Channel.tracked == True):
                print '{:>35}  {}'.format(channel.id, channel.title)
        if args.list_playlists:
            for playlist in mgr.session.query(Playlist):
                print '{:>35}  {} (~{})'.format(
                    playlist.id, playlist.title, playlist.channel.title)
        if args.find_playlists:
            for channel in mgr.session.query(Channel).filter(
                    Channel.tracked == True):
                playlists = channel.find_playlists(mgr)
                for playlist in playlists:
                    print '{:>35}  {} (~{})'.format(
                        playlist['id'], playlist['title'], channel.title)
        if args.add_channels:
            for username in args.add_channels.split(','):
                Channel.fetch_channels(mgr, username=username,
                                       track=True)
        if args.add_playlists:
            Playlist.fetch_playlists(mgr, args.add_playlists.split(','))
        if args.add_my_playlists:
            channel = mgr.session.query(Channel).filter(
                Channel.tracked == True).first()
            playlists = channel.find_playlists(mgr)
            playlist_ids = [playlist['id'] for playlist in playlists]
            Playlist.fetch_playlists(mgr, playlist_ids)
        if args.update:
            for playlist in mgr.session.query(Playlist):
                print '{} (~{})'.format(playlist.title, playlist.channel.title)
                playlist.fetch_playlist_videos(mgr)
        if args.download:
            for video in mgr.session.query(Video):
                print '{} (~{})'.format(video.title, video.channel.title)
                video.download(mgr)


if __name__ == '__main__':
    main()
