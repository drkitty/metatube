from __future__ import unicode_literals

import dateutil.parser


def get_normal_playlists(client, channel_id=None):
    playlists = []

    def process_playlist(item):
        snippet = item['snippet']
        playlists.append({
            'id': item['id'],
            'title': snippet['title'],
            'description': snippet['description'],
        })

    client.get('/playlists', {
        'part': 'snippet',
        'mine': 'true',
    }, process_playlist)

    return playlists

def get_special_playlists(client, channel_id=None, names=()):
    playlists = []

    def process_playlist(item):
        snippet = item['snippet']
        playlists.append({
            'id': item['id'],
            'title': snippet['title'],
            'description': snippet['description'],
        })

    def process_channel(item):
        special_playlists = item['contentDetails']['relatedPlaylists']
        selected_playlist_ids = []

        print special_playlists
        for name in names:
            if name in special_playlists:
                selected_playlist_ids.append(special_playlists[name])

        client.get('/playlists', {
            'part': 'snippet',
            'id': ','.join(selected_playlist_ids),
        }, process_playlist)

    params = {
        'part': 'contentDetails',
    }
    if channel_id is None:
        params['mine'] = 'true'
    else:
        params['id'] = channel_id

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
