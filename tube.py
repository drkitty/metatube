from __future__ import unicode_literals

import dateutil.parser


def get_user_playlists(client, username=None, likes=False, favorites=False,
                       uploads=False):
    playlists = []

    def process_playlist(item):
        snippet = item['snippet']
        p = {
            'id': item['id'],
            'title': snippet['title'],
            'description': snippet['description'],
        }
        playlists.append(p)

    if username is None:
        # normal playlists

        client.get('/playlists', {
            'part': 'snippet',
            'mine': 'true',
        }, process_playlist)

    if likes or favorites or uploads:
        # special playlists

        def process_channel(item):
            special_playlists = item['contentDetails']['relatedPlaylists']

            title_list = []
            if likes:
                title_list.append('likes')
            if favorites:
                title_list.append('favorites')
            if uploads:
                title_list.append('uploads')

            client.get('/playlists', {
                'part': 'snippet',
                'id': ','.join(special_playlists[title]
                               for title in title_list),
            }, process_playlist)

        params = {
            'part': 'contentDetails',
        }

        if username is None:
            params['mine'] = 'true'
        else:
            params['forUsername'] = username

        client.get('/channels', params, process_channel)

    return playlists


def get_playlist_videos(client, playlist_id):
    videos = []

    def process(item):
        snippet = item['snippet']
        v = {
            'id': snippet['resourceId']['videoId'],
            'title': snippet['title'],
            'description': snippet['description'],
            'position': snippet['position'],
            'date_published': dateutil.parser.parse(snippet['publishedAt']),
        }
        videos.append(v)

    params = {
        'part': 'snippet',
        'playlistId': playlist_id,
    }

    client.get('/playlistItems', params, process)

    return videos
