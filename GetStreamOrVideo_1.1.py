#
# Записываем live-стрим по VOD`у
#
import argparse
import random
import m3u8
import os
import sys
import time
import logging
import re
from urllib.request import urlopen
from os.path import dirname, realpath, exists, basename, join

from twitch_basic import CID_streamDownloader, HEADER_AcceptV5, STR_ACCEPT,\
    STR_CLIENT, API_KRAKEN, API_TWITCH, API_USHER, API_HELIX, sendRequest,\
    GetInfoAboutVideo, GetPlaylistUrl, DownloadFile


logging.basicConfig(filename='StreamDownloading.log', level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

client_id = CID_streamDownloader
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)

debug = True  # отвечает за вывод доп.инфы

curdir = dirname(realpath(__file__))
folderTemplate = "\\Streams\\{0}\\{1}\\"
inputsTxt = 'inputs.txt'
streamsTxt = 'stream.txt'
batFile2 = '2. runFFMPEG.bat'
batFile1 = '1. VerifyFiles.bat'
playlistFile = 'playlist.m3u8'
ffmpegCmd = 'ffmpeg -f concat -safe 0 -i {0} -c copy "{1}"\npause'
urlPlaylistRequestVod = API_USHER +\
    'vod/{0}.m3u8?nauth={1}&nauthsig={2}&p={3}&allow_source=true'


def CheckWhetherStreamOnline(ch):
    """
    Проверка онлайн ли стрим
    """
    url = API_HELIX + 'streams?user_login=' + ch
    h = {STR_CLIENT: client_id}

    j = sendRequest(url, h)
    #print(j)

    if ('data' in j and
        j['data'] and
        len(j['data']) > 0 and
        j['data'][0]['type'] == 'live'):
            print("Есть стрим!")
            return (True, j)
    else:
        print('Нету стрима')
        return (False, None)

    if 'error' in j:
        print(j['error'])
        logging.info(j['error'])
        return(False, None)


def WriteStreamTxtFile(filepathname, whatToWrite, openmode='ab'):
    with open(filepathname, openmode) as streamfile:
            streamfile.write(whatToWrite.encode('utf8'))


# def GetStreamInfoFromPlaylist(searching_broadcast_id, channel):
#     '''
#     ищем id трансляции в url эскиза...
#     '''
#     # https://vod-secure.twitch.tv/383a97e559f7227ca73f_tanya_monster_games_35229643168_1270525534/chunked/index-dvr.m3u8
#     global client_id
#     user_id = APInew_GetChannelID(channel, client_id)
#     url = f'{API_HELIX}/videos?user_id={user_id}&first=100'  # + '&type=archive'
#     h = {STR_CLIENT: client_id}
#     try:
#         j = sendRequest(url, h)
#     except Exception as e:
#         print('Не могу найти видео по плейлисту', e)
#         return (None, None)
#     if j:
#         if 'data' in j:
#             for video in j['data']:
#                 thumbnail_url = video['thumbnail_url']      # https://static-cdn.jtvnw.net/s3_vods/85cb5acc9e3c62890cb1_liz0n_35215301792_1269629042/thumb/thumb0-%{width}x%{height}.jpg
#                 ll = thumbnail_url.split('/')[4].split('_')  # 85cb5acc9e3c62890cb1_liz0n_35215301792_1269629042
#                 broad_id = ll[-2]
#                 if broad_id == searching_broadcast_id:
#                     return (video['created_at'], video['streamName']
#     else:
#         return (None, None)


# ==============================================================================

# 0. Вторым аргументом идет канал или id видео
#outFolder = r'E:\Vadim\Coding\StreamDownloader\Streams\snailkicktm\2018-10-06_16-04'
outFolder = ''

if len(sys.argv) == 1:
    print('Не указан канал')
    print('Using: ' + sys.argv[0] + ' -c <channel_url> OR')
    print('Using: ' + sys.argv[0] + ' -v <video_url>\n')
    # arg = 'https://www.twitch.tv/vika_karter'
    # arg = 'https://www.twitch.tv/videos/311651965'

parser = argparse.ArgumentParser()
parser.add_argument('-v', default='')  # video     https://www.twitch.tv/videos/311651965
parser.add_argument('-c', default='')  # channel   https://www.twitch.tv/vika_karter
parser.add_argument('-p', default='')  # playlist
# https://vod137-ttvnw.akamaized.net/0b26d0808e1f5ab30159_snailkicktm_30660760768_984922979/chunked/index-dvr.m3u8
# https://vod-secure.twitch.tv/daa0f22bddf88598523c_welovegames_32800722784_1118671499/chunked/index-dvr.m3u8
parser.add_argument('-o', default='')  # output

args = parser.parse_args()
args = vars(args)

v = args['v']
c = args['c']  # c = 'https://www.twitch.tv/liz0n'
p = args['p']
o = args['o']

selfcmd = ' '.join(sys.argv)

if (v != '' and p != '') or (c != '' and p != '') or (c != '' and v != ''):
    print('Нужен только один параметр: -c, -v или -p\nКоманда запуска:', selfcmd)
    input()
    sys.exit(1)

isStreamMode = False
videoMode = False
playlistMode = False

if c:
    isStreamMode = True
    srch = re.search('(twitch.tv\/)(.+)', c, re.IGNORECASE)
    srch2 = re.search('^[a-zA-Z\d]+$', c, re.IGNORECASE)
    if srch:
        channel = srch.group(2)
        print('Канал: ' + channel + '\n')
    elif srch2:
        channel = srch2.group(0)
        print('Канал: ' + channel + '\n')
    else:
        print('Не могу распарсить аргумент')

if v:
    videoMode = True
    srch = re.search('(twitch.tv\/videos\/)(\d+)', v, re.IGNORECASE)
    if srch:
        video_id = srch.group(2)
        print('Качаем видео ' + video_id + '\n')
    else:
        print('не могу распарсить аргумент')

if p:
    playlistMode = True
    isStreamMode = True
    pll = p
    print('playlist =', pll)
    # stream - https://vod-secure.twitch.tv/75f38e1c2c3f00214f1b_liz0n_35228636272_1270462591/chunked/index-dvr.m3u8
    # ? ------ https://vod137-ttvnw.akamaized.net/0b26d0808e1f5ab30159_snailkicktm_30660760768_984922979/chunked/index-dvr.m3u8
    # video -- https://vod-secure.twitch.tv/daa0f22bddf88598523c_welovegames_32800722784_1118671499/chunked/index-dvr.m3u8
    # video -- https://vod-secure.twitch.tv/383a97e559f7227ca73f_tanya_monster_games_35229643168_1270525534/chunked/index-dvr.m3u8
    # ptemp = p.split('/')  # daa0f22bddf88598523c_welovegames_32800722784_1118671499
    # ptemp2 = ptemp[3].split('_')
    ptemp = p.split('/')[3].split('_')
    channel = '_'.join(ptemp[1:-2])
    broadcast_id = ptemp[2]
    # video_date, stream_name = GetStreamInfoFromPlaylist(broadcast_id, channel)
    # print('ch = ' + ch)
    # print('broadcast_id = ' + broadcast_id)

if o:
    outFolder = o
    print(o)
    input()

# input()
# sys.exit()

# включить и указать пл, если надо качать с плейлиста
# pll = 'https://vod137-ttvnw.akamaized.net/0b26d0808e1f5ab30159_snailkicktm_30660760768_984922979/chunked/index-dvr.m3u8'
# channel = 'welovegames'
# videoDate='0_0_0'
# video_id = 0
# strr='000'

while 1:
    if isStreamMode:
        if not playlistMode:
            # --- 1. Проверка, онлайн ли стрим
            while 1:
                isOnline, stream = CheckWhetherStreamOnline(channel)
                if isOnline:
                    strr = stream['data'][0]
                    user_id = strr['user_id']
                    broadcast_id_prime = strr['id']
                    streamName = strr['title'].translate(non_bmp_map)
                    videoDate = strr['started_at'].replace(":", "-")   #2017-07-25T18_57_43Z
                    videoDate = videoDate.replace('T', '_').replace('Z', '')
                    videoDate = videoDate[:-3]  # опускаем секунды
                    if debug:
                        print('streamName: ', streamName)
                        print('videoDate: ', videoDate)
                        print('user_id: ', user_id, '\n')
                    break
                else:
                    time.sleep(30)
    else:
        channel, user_id, videoDate, streamName, game, vidjson = GetInfoAboutVideo(video_id, True)
        if channel == 0:
            print('channel == 0')
            sys.exit()

    # --------------------------------------------------------------------------
    # --- 2. Создадим директории
    if not outFolder:
        folderTemplate = curdir + folderTemplate.format(channel, videoDate)
    else:
        folderTemplate = outFolder + folderTemplate.format(channel, videoDate)
    print('Папка: ' + folderTemplate + '\n')

    if not exists(folderTemplate):
        os.makedirs(folderTemplate)

    # сохраним stream-объект в файл для отладки
    if isStreamMode:
        WriteStreamTxtFile(join(folderTemplate, streamsTxt), str(strr), 'wb')

    else:
        with open(join(folderTemplate, 'video.txt'), 'wb') as streamfile:
            streamfile.write(str(vidjson).encode('utf8'))

    # --------------------------------------------------------------------------
    if isStreamMode and not playlistMode:
        # 5. Получаем список видосов
        while 1:
            j = sendRequest(
                API_KRAKEN + 'channels/' + user_id + '/videos?limit=1&sort=time',
                {STR_ACCEPT: HEADER_AcceptV5, STR_CLIENT: client_id})
            videoList = j['videos']

            if videoList:
                # 6. Ищем видео со статусом "recording"
                video = videoList[0]
                ce = 0

                if video['status'].lower() == 'recording':
                    print(video['status'], 'видео найдено\n')
                    video_id = video['_id'][1:]  # v123456789
                    break
                else:
                    print("Видос пока не найден")
                    ce += 1
                    time.sleep(30)

                    if ce > 16:  # 8 минут
                        print('(!) прошло 8 минут, видео так и не было найдено\n')
                        break
        if ce > 16:
            continue

    # --------------------------------------------------------------------------
    # подготовим имя файла
    if playlistMode:
        playlistBaseUrl = dirname(pll) + '/'
    if not playlistMode:
        outputFilename = f'{channel}_{videoDate}_{video_id}.mp4'

        # - Получаем access token для доступа к недокументированному API
        #   чтобы получить плейлист
        j = sendRequest(
            f'{API_TWITCH}vods/{video_id}/access_token',
            {STR_ACCEPT: HEADER_AcceptV5, STR_CLIENT: client_id})
        token = j['token']
        sig = j['sig']

        # --------------------------------------------------------------------------
        # - 8. Получаем вариативный плейлист с плейлистами на каждое качество видео
        playlistUrl = GetPlaylistUrl(urlPlaylistRequestVod.format(
            video_id, token, sig, random.randint(1000000, 999999999)))
        s = '\n\nplaylist: ' + playlistUrl + '\n'
        WriteStreamTxtFile(join(folderTemplate, streamsTxt), s)

        DownloadFile(playlistUrl, join(folderTemplate, playlistFile))
        playlistBaseUrl = dirname(playlistUrl) + '/'

        # --------------------------------------------------------------------------
        # - Создаем батник для проверки файлов
        with open(join(folderTemplate, batFile1), 'w') as bat:
            s = join(curdir, 'VerifyFiles.py')
            bat.write(f'@"{s}" "{folderTemplate}"\n@pause')

        # - Создаем батник для склеивания сегментов с помощью ffmpeg
        with open(join(folderTemplate, batFile2), 'w') as bat:
            bat.write(ffmpegCmd.format(inputsTxt, outputFilename))

    # --------------------------------------------------------------------------
    # - Качаем .ts-сегменты
    c = 0
    c_error = 0
    while 1:
        tsFilename = str(c) + '.ts'
        tsFull = join(folderTemplate, tsFilename)
        if (exists(tsFull)):
            c += 1
            continue

        isDownloaded = DownloadFile(playlistBaseUrl + tsFilename, join(folderTemplate, tsFilename))

        if isDownloaded:
            # --- Обновляем файл-список для ffmpeg
            with open(join(folderTemplate, inputsTxt), "a") as f:
                f.write(f"file '{tsFilename}'\n")
            c += 1
            continue
            # ------------------------------------------------------------------

        else:
            # --- если не найден, то ищем заглушенный файл
            print(tsFilename, 'не найден. Trying to find muted-file')
            tsFilename = str(c) + '-muted.ts'
            url = playlistBaseUrl + tsFilename

            isDownloaded = DownloadFile(playlistBaseUrl + tsFilename, folderTemplate + tsFilename)

            if isDownloaded:
                with open(join(folderTemplate, inputsTxt), "a") as f:
                    f.write(f"file '{tsFilename}'\n")
                c += 1
                continue
                # --------------------------------------------------------------

            else:
                if isStreamMode:
                    #  Проверка, онлайн ли стрим
                    online, stream = CheckWhetherStreamOnline(channel)
                    if online:
                        broad_id = stream['data'][0]['id']
                        if broad_id != broadcast_id_prime:
                            streamHasEnd = True
                        else:
                            streamHasEnd = False
                    else:
                        streamHasEnd = True
                else:
                    streamHasEnd = True

                # - если стрим закончен, проверяем последний файл скачан или нет
                if streamHasEnd:
                    playlistUrl = GetPlaylistUrl(urlPlaylistRequestVod.format(
                        video_id, token, sig, random.randint(1000000, 999999999)))

                    pl = m3u8.load(playlistUrl)
                    if exists(join(folderTemplate, pl.files[-1])):
                        break
                    else:
                        c_error += 1
                        print(f'(!) файл .ts не найден, файл -muted.ts не найден, и последний файл не загружен - ждём 30 секунд ({c_error})')
                        time.sleep(30)
                    if debug:
                        print('playlistURL = ', playlistUrl)
                    if c_error > 16:
                        print(f'(!!) Файл не найден спустя {c_error*30/60} минут. Останавливаем загрузку.')
                        break
                else:
                    time.sleep(60)

    print(f'Загрузка завершена. Запустите файл {batFile1} для проверки файлов, затем {batFile2} в папке со стримом.')
    import subprocess
    cmdline = 'explorer "' + folderTemplate + '"'
    proc = subprocess.Popen(cmdline, shell=True, stdout=subprocess.PIPE)
    out = proc.stdout.readlines()

    if isStreamMode:
        time.sleep(60)
    else:
        break

input()
