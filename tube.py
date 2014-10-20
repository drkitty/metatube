#!/usr/bin/env python2

from __future__ import unicode_literals

import argparse

from data import Channel, EverythingManager, Playlist, Session, Video


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list-channels', action='store_true')
    group.add_argument('-l', '--list-playlists', action='store_true')
    group.add_argument('-i', '--list-videos')
    group.add_argument('-f', '--find-playlists', action='store_true')
    group.add_argument('-p', '--add-playlists')
    group.add_argument('-a', '--add-my-playlists', action='store_true')
    group.add_argument('-c', '--add-channels')
    group.add_argument('-u', '--update', action='store_true')
    group.add_argument('-d', '--download', action='store_true')
    args = parser.parse_args()

    with EverythingManager() as mgr:
        if mgr.session.query(Channel).filter(
                Channel.mine == True).count() == 0:
            print 'Fetching your channel...'
            Channel.fetch_channels(mgr, track=True)

        if args.list_channels:
            for channel in mgr.session.query(Channel).filter(
                    Channel.tracked == True):
                print '{:>34}  {}'.format(channel.id, channel.title)
        elif args.list_playlists:
            for playlist in mgr.session.query(Playlist):
                print '{:>34}  {} (~{})'.format(
                    playlist.id, playlist.title, playlist.channel.title)
        elif args.list_videos:
            playlist = mgr.session.query(Playlist).get(args.list_videos)
            for playlist_video in playlist.playlist_videos:
                video = playlist_video.video
                print '{:>16}  {} (~{})'.format(
                        video.id, video.title, video.channel.title)
        elif args.find_playlists:
            for channel in mgr.session.query(Channel).filter(
                    Channel.tracked == True):
                playlists = channel.find_playlists(mgr)
                for playlist in playlists:
                    print '{:>35}  {} (~{})'.format(
                        playlist['id'], playlist['title'], channel.title)
        elif args.add_channels:
            for username in args.add_channels.split(','):
                Channel.fetch_channels(mgr, username=username,
                                       track=True)
        elif args.add_playlists:
            Playlist.fetch_playlists(mgr, args.add_playlists.split(','))
        elif args.add_my_playlists:
            channel = mgr.session.query(Channel).filter(
                Channel.tracked == True).first()
            playlists = channel.find_playlists(mgr)
            playlist_ids = [playlist['id'] for playlist in playlists]
            Playlist.fetch_playlists(mgr, playlist_ids)
        elif args.update:
            for playlist in mgr.session.query(Playlist):
                print '{} (~{})'.format(playlist.title, playlist.channel.title)
                playlist.fetch_playlist_videos(mgr)
        elif args.download:
            videos = mgr.session.query(Video).filter(Video.skip == False)
            print '#################################'
            print '### Downloading thumbnails... ###'
            print '#################################'
            print
            for video in videos.filter(Video.thumbnail_downloaded == False):
                print 'thumbnail "{}" (~{})'.format(
                    video.title, video.channel.title)
                video.download_thumbnail(mgr)
            print
            print '#############################'
            print '### Downloading videos... ###'
            print '#############################'
            print
            for video in videos.filter(Video.video_downloaded == False):
                print 'video "{}" (~{})'.format(
                    video.title, video.channel.title)
                video.download_video(mgr)


if __name__ == '__main__':
    main()
