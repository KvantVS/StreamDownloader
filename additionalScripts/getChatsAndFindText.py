from urllib.request import urlopen
import requests, random
import m3u8
import os
import subprocess
import sys
import time, datetime
import logging
import re

client_id = CID_twitchPlayer
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
debug = True  # отвечает за вывод доп.инфы
channel = 'artgameslp'

l_findedComments = []

def GetChat(videoId):
    canProduce = True;
    #print('Защли в GetChat')
    url = 'https://api.twitch.tv/v5/videos/' + videoId + '/comments?content_offset_seconds=0'
    h = {'Accept': 'application/vnd.twitchtv.v5+json',
         'Client-ID': client_id}
    r = requests.get(url, headers=h)
    j = r.json()
    while canProduce:
        FindTextInChat(j['comments'], '(?<!skalik)92', videoId, '') #corbannndallas '^\d+' лет 92  ^\d+$  (?<!skalik)92  ?<! - негативное заглядывание назад (проверяет есть ли перед словом условие, если есть то не считает этот экземпляр найденным)

        if '_next' in j:
            #print('переходим на next: ' , j['next'])
            url = 'https://api.twitch.tv/v5/videos/' + videoId + '/comments?cursor=' + j['_next']
            r = requests.get(url, headers=h)
            j = r.json()
        else:
            canProduce = False
    #print('Выходим из GetChat')


def FindTextInChat(messages, whatToFind, videoId, byWhom=''):
    global l_findedComments
    #c=0
    #print('ищем:', whatToFind, byWhom)
    for msg in messages:
        #c+=1
        if (byWhom == '') or (msg['commenter']['name'] == byWhom):
            srch = re.search(whatToFind, msg['message']['body'], re.IGNORECASE)
            if srch:
                s = 'НАЙДЕН! комментарий: (' + str(msg['content_offset_seconds']) + ') ' + msg['commenter']['name'] + ': ' + msg['message']['body'] + '\r\n Видео: ' + str(videoId) + '\r\n'
                l_findedComments.append(s)
                print(s)
        #if (c == 1) or (c==2) or (c==3):
            #s = 'комментарий: ' + msg['commenter']['name'] + ': ' + msg['message']['body'] + '\r\n Видео: ' + str(videoId) + '\r\n'
            #print(s)
        

# --- 3. Получаем access_token через открытое апи
url = 'http://api.twitch.tv/api/channels/{0}/access_token?client_id={1}'.format(channel, client_id)
r = requests.get(url)
j = r.json()
token = j['token']
sig = j['sig']
if debug:
    print('token = ', token)
    print('sig = ', sig)
    
# --- 4. получаем ID канала
url = 'https://api.twitch.tv/kraken/users?login=' + channel
h = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID':client_id}  # m..
r = requests.get(url, headers=h)
channelId = r.json()['users'][0]['_id']
if debug:
    print('channeld ID = ',channelId)

# --- 5. получаем список видосов
url = f'https://api.twitch.tv/kraken/channels/{channelId}/videos?client_id={client_id}&offset=29&limit=15&sort=time'  #j..
h = {'Accept': 'application/vnd.twitchtv.v5+json'}
r = requests.get(url, headers=h)
#print(r.status_code, r.text)
videoList = r.json()['videos']


for video in videoList:
    videoId = video['_id'][1:]
    print(str(videoId) + ' - получаем чат видео (' + str(video['created_at']))
    GetChat(videoId)
    #FindTextInChat(msgs, '^\d+', videoId, '') #corbannndallas
   
    
