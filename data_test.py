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
s = data.Session()
me = s.query(data.Channel).first()
del s

me.fetch_normal_playlists(c)
