'''
Качаем плейлист отдельно

TODO:
добавить возможность передавать аргументом playlist_url
парсинг sys.argv[1]
'''

from urllib.request import urlopen
import requests
import random
import m3u8
import os
from os.path import dirname, realpath, exists, basename, join
import sys

from twitch_basic import *

# включить для дебага.....
debug = True

client_id = CID_chatWriter
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)

playlist_url = ''

print(sys.argv)
if not playlist_url:
    video_id = '505944491'  # https://www.twitch.tv/videos/
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        if sys.argv[1] == '-i':  # дичь из-за АНАКОНДЫ
            video_id = '505944491'
        print('VOD id:', video_id)
    else:
        print('Не указан video id.\nUsing: ' + sys.argv[0] + ' <video_id>')
    print('video_id:', video_id)

    channel, user_id, videoDate, videoTitle, game, jjj = GetInfoAboutVideo(video_id, True)
    if channel == 0:
        sys.exit()

    folderTemplate = dirname(realpath(__file__)) + "\\Streams\\{0}\\{1}\\".format(
        channel, videoDate)
    inputsTxt = 'inputs.txt'

    if not exists(folderTemplate):
        os.makedirs(folderTemplate)

    # --- 1. Получаем access_token через открытое апи
    # url = f'{API_TWITCH}vods/{video_id}/access_token?client_id={1}'.format(
    #     video_id, client_id)
    # r = requests.get(url)
    # j = r.json()
    # token = j['token']
    # sig = j['sig']

    print('получаем плейлист...')
    j = sendRequest(
        f'{API_TWITCH}vods/{video_id}/access_token',
        {STR_ACCEPT: HEADER_AcceptV5, STR_CLIENT: client_id})
    print(j)
    token = j['token']
    sig = j['sig']
    print('token =', token, 'sig =', sig)

    # --- 2. m3u8
    url = 'https://usher.ttvnw.net/vod/{0}.m3u8?nauth={1}&nauthsig={2}&p={3}&allow_source=true'.format(
        video_id, token, sig, str(random.randint(1000000, 999999999)))

    if debug:
        r = requests.get(url)
        print(r.text)

    vpl = m3u8.load(url)
    if debug:
        print('Вариативный m3u8 ? = ', vpl.is_variant)
    if not vpl.is_variant:
        print("Не вариативный плейлист")
        sys.exit()

    # --- выбираем плейлист с лучшим качеством
    maxband = 0
    for p in vpl.playlists:
        if p.stream_info.bandwidth > maxband:
            maxband = p.stream_info.bandwidth
            playlist_url = p.uri
    if debug:
        print(maxband)
        print('bestPlaylist = ' + playlist_url)
else:
    folderTemplate = dirname(realpath(__file__))

# качаем плейлист
u = urlopen(playlist_url)
with open(join(folderTemplate, 'playlist.m3u8'), 'wb') as plfile:
    plfile.write(u.read())

print('playlist downloaded')

input()
