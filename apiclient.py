import json
import requests
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

    def __init__(self, code):
        self.get_token(code)

    def get_token(self, code=None):
        if code is None and self.refresh_token is None:
            raise Exception('The `code` argument is required on the first '
                            'call to get_token')

        # Assemble POST data

        post_data = {
            'client_id': client_id,
            'client_secret': client_secret,
        }
        if code is None:
            post_data['refresh_token'] = self.refresh_token
            post_data['grant_type'] = 'refresh_token'
        else:
            post_data['code'] = code
            post_data['redirect_uri'] = 'urn:ietf:wg:oauth:2.0:oob'
            post_data['grant_type'] = 'authorization_code'

        # Make token request

        response = requests.post(
            'https://accounts.google.com/o/oauth2/token', data=post_data)
        j = json.loads(response.text)
        if 'error' in j:
            raise Exception(
                '{}: {}'.format(j['error'], j['error_description']))

        # Extract token(s)

        self.access_token = j['access_token']
        if code is not None:
            self.refresh_token = j['refresh_token']
