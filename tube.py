from __future__ import unicode_literals

import dateutil.parser


def get_playlists(client):
    playlists = []

    def process(item):
        snippet = item['snippet']
        p = {
            'id': item['id'],
            'title': snippet['title'],
            'description': snippet['description'],
        }
        playlists.append(p)

    params = {
        'part': 'snippet',
        'mine': 'true',
    }

    client.get('/playlists', params, process)

    return playlists

def get_playlist_videos(client, playlist_id):
    videos = []

    def process(item):
        snippet = item['snippet']
        v = {
            'watch_id': snippet['resourceId']['videoId'],
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
