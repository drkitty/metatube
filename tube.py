from __future__ import unicode_literals

import dateutil.parser


def get_my_playlists(client):
    playlists = []

    # normal playlists

    def process_playlist(item):
        snippet = item['snippet']
        p = {
            'id': item['id'],
            'title': snippet['title'],
            'description': snippet['description'],
        }
        playlists.append(p)

    client.get('/playlists', {
        'part': 'snippet',
        'mine': 'true',
    }, process_playlist)

    # special playlists

    def process_channel(item):
        special_playlists = item['contentDetails']['relatedPlaylists']

        client.get('/playlists', {
            'part': 'snippet',
            'id': ','.join(special_playlists[title]
                           for title in ('favorites', 'likes')),
        }, process_playlist)

    client.get('/channels', {
        'part': 'contentDetails',
        'mine': 'true',
    }, process_channel)

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
