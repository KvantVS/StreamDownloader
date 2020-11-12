import sys
import datetime
import logging
from os.path import dirname, realpath

non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)

# oauth:wqan18jxu2s2y5or2nwogi9iqfi9mr
# my_userid = 156900010
# user_id na_podhvate - 41580942

# Client-ID и всякие ключи
CID_streamDownloader = ''  # (мой (whatisplayingbot)
CID_chatWriter = ''  # (мой (chatWriter))
CID_twitchPlayer = 'jzkbprff40iqj646a697cyrvl0zt2m6'  # (твича)
CID_NewApp = ''

my_client_secret = ''  # (мой)
newApp_secret = ''

streamDownloaderToken = ''

API = 'https://api.twitch.tv/'
API_KRAKEN = f'{API}kraken/'
API_TWITCH = f'{API}api/'
API_HELIX = f'{API}helix/'
API_V5CLOSED = f'{API}v5/'
API_USHER = 'https://usher.ttvnw.net/'

HEADER_AcceptV5 = 'application/vnd.twitchtv.v5+json'
STR_ACCEPT = 'Accept'
STR_CLIENT = 'Client-ID'

# RE_MOMENTS_writechatmodule = '^([^\S]?(LUL|PogChamp|МЛЖ|DansGame|SeemsGood|CurseLit|GTChimp|SwiftRage|CarlSmile|CoolStoryBob|blackufaCoolstory)[\s]*)+$|^([\S]+LUL[\s]?)+$|^[ах]+\)*[\s]*$|^[X:;]D*\)*[\s]*$|^хд*\)*[\s]*$'
# RE_MOMENTS_chatfromvideo = '^([^\S]?(LUL|PogChamp|МЛЖ|МЛГ|млг|ЭмЭлДжи|DansGame|SeemsGood|CurseLit|GTChimp|SwiftRage|CarlSmile|CoolStoryBob|blackufaCoolstory)[\s]*)+$|^([\S]+LUL[\s]?)+$|^[ах]+\)*[\s]*$|^[X:;]D*\)*[\s]*$|^хд*\)*[\s]*$'
# RE_mlg = '^([^\S]?MLG[\s]*)+$|^([\S]+MLG[\s]?)+$'
# re_links = '\S*\.com|\S*\.ru'

baseFolder = dirname(realpath(__file__))


logging.basicConfig(filename='TwitchBasic.log', level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Получение токена --------------------------------
# url = 'https://id.twitch.tv/oauth2/token'
# data = {'client_id': CID_NewApp,
#         'client_secret': newApp_secret,
#         'grant_type': 'client_credentials',
#         'scope': 'clips:edit user:read:email'
#         }
# print(SendPost(url, data))
'''
{'access_token': 'ulf9so5hv5u5wi2wka3buc97uvt4wq', 
'expires_in': 5632720, 
'scope': ['clips:edit', 'user:read:email'], 
'token_type': 'bearer'}
'''


def SendPost(url, params={}, headers=None):
    import requests
    try:
        if headers:
            r = requests.post(url, data=params, headers=headers)
        else:
            r = requests.post(url, data=params)
        j = r.json()
    except Exception as e:
        j = "{'error': '" + str(e) + "'}"
        print('error:', j['error'])
        print(j['status'])
        print(j['message'])
    #raise Exception('asdf')
    return j


    '''https://id.twitch.tv/oauth2/revoke
    ?client_id=<your client ID>
    &token=<your OAuth token>
'''


def sendRequest(url, headers=None):
    print('sending GET to ', url)
    import requests
    try:
        if headers:
            r = requests.get(url, headers=headers)
        else:
            r = requests.get(url)
        j = r.json()
        # print(j)
    except Exception as e:
        j = "{'error': '" + str(e) + "'}"
        print('error:', j['error'])
        print(j['status'])
        print(j['message'])
    #raise Exception('asdf')
    return j

# def sendRequest2(url, headers=None):
#     import requests
#     if headers:
#         r = requests.get(url, headers=headers)
#     else:
#         r = requests.get(url)
#     j = r.json()
#     return j


def GetInfoAboutVideo(videoId, bProcessDate=False):
    """
    Получаем инфу о видео по ID через API v5
    bProcessDate - преобразовать дату в %Y-%m-%d_%H-%M из %Y-%m-%dT%H_%M_%SZ
    """

    print(f"получаем инфу о видео {videoId}")
    #j = sendRequest(API_KRAKEN + f'videos/{videoId}?client_id={CID_twitchPlayer}')
    url = API_KRAKEN + f'videos/{videoId}'
    print(url)
    j = sendRequest(url, {STR_CLIENT: CID_streamDownloader, STR_ACCEPT: HEADER_AcceptV5})

    if 'error' in j:
        print('error', j['error'])
        return(0, 0, 0, 0, 0, 0)
    # try:
    #     print(j['error'] + '\n' + j['message'])
    #     return (0, 0, 0, 0, 0)
    # except:
    else:
        videoTitle = j['title'].translate(non_bmp_map)
        videoDate = j['recorded_at'].replace(":", "_")
        channel = j['channel']['name']
        user_id = j['channel']['_id']
        game = j['game']
        if bProcessDate:
            dtVideoCreated = datetime.datetime.strptime(videoDate, "%Y-%m-%dT%H_%M_%SZ")  #.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
            videoDate = dtVideoCreated.strftime("%Y-%m-%d_%H-%M").translate(non_bmp_map)
        return (channel, user_id, videoDate, videoTitle, game, j)


def GetInfoAboutVideoV5(videoId, bProcessDate=False):
    """
    Получаем инфу о видео по ID через API v5
    bProcessDate - преобразовать дату в %Y-%m-%d_%H-%M из %Y-%m-%dT%H_%M_%SZ
    """
    return GetInfoAboutVideo(videoId, bProcessDate)


def GetInfoAboutVideoVNew(videoId, clientID=CID_twitchPlayer, bProcessDate=False):
    j = sendRequest(API_HELIX + f'videos?id={videoId}',
        {STR_CLIENT: clientID})
    return j


def GetVideosFromChannelVNew(channelID, type='archive', clientID=CID_twitchPlayer):
    '''
    type: archive, upload, highlight, all
    '''
    h = {STR_CLIENT: CID_twitchPlayer}
    j = sendRequest(API_HELIX + f'videos?user_id=channelID&type={type}', h)
    return j




# def GetInfoAboutStream():


def ConvertTime(t, scale=60):
    if t >= scale:
        x = t % scale
        t = int(t / scale)
        return (x, t)
    else:
        return (t, 0)

# def ConvertTime2(s, scale=60):
#     if s >= scale:
#         m = s % scale  #  _минуты_. Или часы. Или дни и т.д.
#         s = int(s / scale)  # оставшиеся секунды
#         if s >= scale:
#             h = s % scale  #  минуты. Или _часы_. Или дни и т.д.
#             s = int(s / scale)  # оставшиеся секунды
#         else:
#             h = 0
#     else:
#         h = 0
#         m = 0
#     return (h, m, s)


def ConvertTime2(t, scale=60):
    if t >= scale:
        s = t % scale  # оставшиеся секунды
        m = t / scale  #  _минуты_. Или часы. Или дни и т.д.
        if m >= scale:
            h = m / scale  # оставшиеся секунды
            m = m % scale  #  минуты. Или _часы_. Или дни и т.д.
        else:
            h = 0
    else:
        h = 0
        m = 0
        s = t
    return (int(h), int(m), s)


def GetPlaylistUrl(variative_url, needToDownload=False):
    import m3u8
    v_pl = m3u8.load(variative_url)
    if not v_pl.is_variant:
        print("Не вариативный плейлист")
        return ''
    # --- выбираем плейлист с лучшим качеством
    maxband = 0
    for p in v_pl.playlists:
        if p.stream_info.bandwidth > maxband:
            maxband = p.stream_info.bandwidth
            playlistUrl = p.uri
    print('плейлист с лучшим качеством: ' + playlistUrl + '\n')

    if needToDownload:
        pass

    return playlistUrl


def DownloadFile(url, filename, replaceIfExists=True):
    '''Качаем url и сохраняем в filename'''

    import urllib, http
    from urllib.request import urlopen
    from os import makedirs
    from os.path import exists, dirname, basename
    import time

    # print(url)
    # print(filename)
    # print(' ========')
    try:
        logging.info(f'Downloading {url}  .. to file: {filename}')
        if (not replaceIfExists) and (exists(filename)):
            # print(f'Файл уже есть, {filename}')
            #pass
            return True
        else:
            u = urlopen(url)
            if not exists(dirname(filename)):
                makedirs(dirname(filename))
            with open(filename, 'wb') as f:
                f.write(u.read())
            print(f'{basename(filename)} downloaded.')
        return True
    except urllib.error.HTTPError as e:
        print(e)
        logging.error(str(e))
        time.sleep(1)
        return False
    except http.client.IncompleteRead:
        time.sleep(5)
        return DownloadFile(url, filename)
    except ConnectionResetError as e:
        print(e)
        logging.error(str(e))
        time.sleep(5)
        return DownloadFile(url, filename)
    except urllib.error.URLError as e:
        print(e)
        logging.error(str(e))
        time.sleep(5)
        return DownloadFile(url, filename)


def GetStream(channel):
    url = f'{API_HELIX}streams?user_login={channel}'
    h = {STR_CLIENT: CID_streamDownloader}
    j = sendRequest(url, h)
    if ('data' in j and
        j['data'] and
        j['data'][0]['type'] == 'live'):
        return j['data'][0]
    else:
        return None


def getChannelID(channel, clientId):
    # Узнаём id канала
    try:
        j = sendRequest(f'{API_KRAKEN}users?login={channel}',
            {STR_ACCEPT: HEADER_AcceptV5, STR_CLIENT: clientId})
        channelId = j['users'][0]['_id']
    except Exception as e:
        print('Не удалось получить ID канала.', e)
        channelId = 0
    return channelId


def APInew_GetChannelID(login, clientId):
    try:
        j = sendRequest(f'{API_HELIX}users?login={login}',
            {STR_CLIENT: clientId})
        return j['data'][0]['id']
    except Exception as e:
        print('Не удалось получить ID канала.', e)
        return None


def APInew_GetChannelManyIDs(logins_list, clientId):
    s = 'login=' + '&login='.join(logins_list)
    try:
        j = sendRequest(f'{API_HELIX}users?{s}',
            {STR_CLIENT: clientId})
        #return [item['id'] for item in j['data']]
        return j
    except Exception as e:
        print('Не удалось получить ID канала.', e)
        return None


def TimeProcess(inTime):
    # 2017:07:25T18_57_43Z
    t = inTime.replace('_', '-')   # 2017:07:25T18-57-43Z
    t = t.replace(":", "-")   # 2017-07-25T18-57-43Z
    t = t.replace('T', '_')   # 2017-07-25_18-57-43Z
    t = t.replace('Z', '')    # 2017-07-25_18-57-43
    t = t[:-3]  # опускаем секунды  2017-07-25_18-57
    return t


# def getClipsByChannel(channelId, clientId, start='', end='', first='100'):
#     import time
#     cursor = ''
#     passedCursors = []
#     url = f'{API_HELIX}clips?broadcaster_id={channelId}&first={first}'
#     if cursor:
#         passedCursors.append(cursor)
#         url += f'&after={cursor}'
#     print(f'requesting... {url}')
#     h = {STR_CLIENT: clientId}
#     j = sendRequest(url, h)
#     if 'error' in j:
#         if 'status' in j:
#             if j['status'] == '429':  # много запросов на API-ресурс
#                 time.sleep(60)
#                 continue
#         else:
#             break
#     if 'data' in j:
#         return j['data']
#     else:
#         return ''
