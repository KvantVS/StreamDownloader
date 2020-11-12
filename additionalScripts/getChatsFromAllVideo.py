from urllib.request import urlopen
import requests
import sys
import datetime

import WriteChat_Module

client_id = CID_streamDownloader  #m..
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
debug = False  # отвечает за вывод доп.инфы
channel = 'BlackUFA'  # 'artgameslp'  BlackUFA_Twitch
urlApi = 'http://api.twitch.tv/api/'
urlKraken = 'https://api.twitch.tv/kraken'

# --- 3. Получаем access_token через открытое апи
url = '{0}channels/{1}/access_token?client_id={2}'.format(urlApi, channel, client_id)
'''
ответ:
{
"token":"{
    \"adblock\":false,
    \"player_type\":null,
    \"platform\":null,
    \"user_id\":null,
    \"channel\":\"artgameslp\",
    \"channel_id\":55926254,
    \"expires\":1519143416,
    \"chansub\":{
        \"view_until\":1924905600,
        \"restricted_bitrates\":[]},
    \"private\":{\"allowed_to_view\":true},
    \"privileged\":false,
    \"https_required\":false,
    \"show_ads\":true,
    \"device_id\":null,
    \"turbo\":false,
    \"subscriber\":false
    ,\"hide_ads\":false
    ,\"partner\":true
    ,\"game\":\"kingdom_come_deliverance\"
    ,\"mature\":false
    ,\"ci_gb\":false
    }"
,"sig":"c0bd7f0a0c08b2560bb118cb010d722f585002e1"
,"mobile_restricted":false
}
'''
r = requests.get(url)
j = r.json()

token = j['token']
sig = j['sig']
if debug:
    print('token = ', token)
    print('sig = ', sig)

# --- 4. получаем ID канала
url = '{0}users?login={1}'.format(urlKraken, channel)
h = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': client_id}
r = requests.get(url, headers=h)
channelId = r.json()['users'][0]['_id']
if debug:
    print('channeld ID = ', channelId)

# --- 5. получаем список видосов
canGo = True
offsetVideos = 0
limit = 5
i = offsetVideos + 1
while canGo:
    url = '{0}channels/{1}/videos?broadcast=false&client_id={2}&offset={3}&limit={4}&sort=time'.format(
        urlKraken, channelId, client_id, offsetVideos, limit)
    h = {'Accept': 'application/vnd.twitchtv.v5+json'}
    r = requests.get(url, headers=h)
    if debug:
        print('url: ', url)
    j = r.json()
    
    if 'videos' in j:
        videoList = j['videos']
        for video in videoList:
            if video['status'] == 'recording':
                i += 1
                continue
            videoId = video['_id'][1:]
            print('{0} - видео ({1} из {2}) - {3}'.format(videoId, i, j['_total'], video['recorded_at']))
            videoDate = video['recorded_at'].replace(":", "_")
            dtVideoCreated = datetime.datetime.strptime(videoDate, "%Y-%m-%dT%H_%M_%SZ")  # .replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
            videoDate = dtVideoCreated.strftime("%Y-%m-%d_%H-%M-%S").translate(non_bmp_map)
            videoTitle = video['title'].translate(non_bmp_map)
            sGame = video['game']
            WriteChat_Module.GetVideoChat(videoId, False, channel, videoDate, videoTitle, sGame)
            print('-------')
            i += 1
        offsetVideos += limit
        if not videoList:
            canGo = False
    else:
        canGo = False
       
        
