import requests

urlKraken = 'https://api.twitch.tv/kraken/'
urlApi = 'https://api.twitch.tv/api/'
#urlUsher = 'https://usher.ttvnw.net/api/'
urlUsher = 'https://usher.ttvnw.net/'
AcceptHeaderV5 = 'application/vnd.twitchtv.v5+json'


def sendRequestF(url, headers):
    if headers:
        r = requests.get(url, headers=headers)
    else:
        r = requests.get(url)
    return r.json()

'''
url = urlKraken + 'streams/' + channel
    h = {'Client-ID': client_id, 'stream-type': 'live'}
    r = requests.get(url, headers=h)
'''
