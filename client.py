import json
import requests
from copy import copy
from urllib import urlencode

from settings import client_id, client_secret


def build_authentication_request_url():
    url = 'https://accounts.google.com/o/oauth2/auth'
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': 'https://www.googleapis.com/auth/youtube.readonly',
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
    }
    return url + '?' + urlencode(params)


authentication_request_url = build_authentication_request_url()


class APIClient(object):
    access_token = None
    refresh_token = None

    def __init__(self):
        self.retrieve_stored_tokens()

    def retrieve_stored_tokens(self):
        try:
            with open('tokens.txt', 'r') as token_file:
                tokens = json.load(token_file)

            self.access_token = tokens['access']
            self.refresh_token = tokens['refresh']
        except IOError as e:
            if e.errno != 2:  # 'No such file or directory'
                raise()

    def store_tokens(self):
        with open('tokens.txt', 'w') as token_file:
            json.dump({
                'access': self.access_token,
                'refresh': self.refresh_token,
            }, token_file)

    def get_token_pair(self, code=None):
        # Assemble POST data

        post_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'grant_type': 'authorization_code',
        }

        # Make token request

        response = requests.post(
            'https://accounts.google.com/o/oauth2/token', data=post_data)
        j = json.loads(response.text)
        if 'error' in j:
            raise Exception(
                '{}: {}'.format(j['error'], j['error_description']))

        # Extract token(s)

        self.access_token = j['access_token']
        self.refresh_token = j['refresh_token']

        self.store_tokens()

    def refresh(self):
        if self.refresh_token is None:
            raise Exception('You must call get_token_pair first.')

        # Assemble POST data

        post_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token',
        }

        # Make token request

        response = requests.post(
            'https://accounts.google.com/o/oauth2/token', data=post_data)
        j = json.loads(response.text)
        if 'error' in j:
            raise Exception(
                '{}: {}'.format(j['error'], j['error_description']))

        # Extract token(s)

        self.access_token = j['access_token']

        self.store_tokens()

    def get(self, path, params, process):
        url = 'https://www.googleapis.com/youtube/v3' + path

        nextPageToken = True
        while nextPageToken is not None:
            page_params = copy(params)

            if isinstance(nextPageToken, basestring):
                page_params['pageToken'] = nextPageToken

            refresh_tries = 0
            while True:
                headers = {'Authorization': 'Bearer ' + self.access_token}
                response = requests.get(url, params=page_params,
                                        headers=headers)
                if response.status_code == 401:
                    if refresh_tries < 2:
                        self.refresh()
                        refresh_tries += 1
                    else:
                        raise Exception('Refresh failed')
                else:
                    break

            j = json.loads(response.text)

            if 'error' in j:
                raise Exception(j['error'])
            for item in j['items']:
                process(item)

            nextPageToken = j.get('nextPageToken', None)
