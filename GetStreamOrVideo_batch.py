#
# Записываем live-стрим по VOD`у
#
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
folderTemplate = curdir + "\\Streams\\{0}\\{1}\\"
inputsTxt = 'inputs.txt'
streamsTxt = 'streams.txt'
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
    print(j)

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

# ==============================================================================

# включить и указать пл, если надо качать с плейлиста
# pll = 'https://vod137-ttvnw.akamaized.net/0b26d0808e1f5ab30159_snailkicktm_30660760768_984922979/chunked/index-dvr.m3u8'
pll = ''

# разбор аргумента sys.argv[1]
# ^\d+$               -- for video (old)
# ^[a-zA-Z\d]+$ (old) -- for channel (old)
# (twitch.tv\/videos\/)(\d+) -- (group(2)) for video
# (twitch.tv\/)(.+)          -- (group(2)) for channel

# 0. Вторым аргументом идет канал или id видео
#outFolder = r'E:\Vadim\Coding\StreamDownloader\Streams\snailkicktm\2018-10-06_16-04'
outFolder = ''

if len(sys.argv) > 1:
    arg = sys.argv[1]
    if len(sys.argv) > 2:
        outFolder = sys.argv[2]
else:
    print('Не указан канал')
    print('Using: ' + sys.argv[0] + ' <channel_url> or')
    print('Using: ' + sys.argv[0] + ' <video_url>\n')
    arg = 'https://www.twitch.tv/artgameslp'  # sholidays #na_podhvate #blackufa #artgameslp
    #arg = 'https://www.twitch.tv/videos/311651965'

srch = re.search('(twitch.tv\/videos\/)(\d+)', arg, re.IGNORECASE)
if srch:
    video_id = srch.group(2)
    isStreamMode = False
    print('Качаем видео ' + video_id + '\n')
else:
    srch = re.search('(twitch.tv\/)(.+)', arg, re.IGNORECASE)
    if srch:
        channel = srch.group(2)
        isStreamMode = True
        print('Качаем стрим с канала ' + channel + '\n')

if pll:
    isStreamMode = True

while 1:
    if isStreamMode:
        if not pll:
            # --- 1. Проверка, онлайн ли стрим
            while 1:
                isOnline, stream = CheckWhetherStreamOnline(channel)
                if isOnline:
                    strr = stream['data'][0]
                    user_id = strr['user_id']
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
        folderTemplate = folderTemplate.format(channel, videoDate)
    else:
        folderTemplate = outFolder
    print('Папка: ' + folderTemplate + '\n')

    if not exists(folderTemplate):
        os.makedirs(folderTemplate)

    # сохраним stream-объект в файл для отладки
    if isStreamMode:
        with open(join(folderTemplate, 'stream.txt'), 'wb') as streamfile:
            streamfile.write(str(strr).encode('utf8'))
    else:
        with open(join(folderTemplate, 'video.txt'), 'wb') as streamfile:
            streamfile.write(str(vidjson).encode('utf8'))

    # --------------------------------------------------------------------------
    if isStreamMode and not pll:
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
    if pll:
        playlistBaseUrl = dirname(pll) + '/'
    if not pll:
        outputFilename = f'{channel}_{videoDate}_{video_id}.mp4'

        # - Получаем access token для доступа к недокументированному API
        #   (чтобы получить плейлист)
        j = sendRequest(
            f'{API_TWITCH}vods/{video_id}/access_token',
            {STR_ACCEPT: HEADER_AcceptV5, STR_CLIENT: client_id})
        token = j['token']
        sig = j['sig']

        # --------------------------------------------------------------------------
        # - 8. Получаем вариативный плейлист с плейлистами на каждое качество видео
        playlistUrl = GetPlaylistUrl(urlPlaylistRequestVod.format(
            video_id, token, sig, random.randint(1000000, 999999999)))

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
            # если не найден, то ищем заглушенный файл
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
                #  Проверка, онлайн ли стрим
                online, stream = CheckWhetherStreamOnline(channel)
                if online:
                    streamHasEnd = False
                else:
                    streamHasEnd = True

                #  если стрим закончен, проверяем последний файл скачан или нет
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

time.sleep(2)
# input()
