#
# Записываем live-стрим
#

from urllib.request import urlopen
import requests
import m3u8
import os
from os.path import dirname, realpath, exists, basename
import sys
import time
import logging

client_id = ''  #m..
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
debug = True  # отвечает за вывод доп.инфы
urlKraken = 'https://api.twitch.tv/kraken/'
urlApi = 'https://api.twitch.tv/api/'
urlUsher = 'https://usher.ttvnw.net/api/'
AcceptHeaderV5 = 'application/vnd.twitchtv.v5+json'

inputsTxt = 'inputs_rt.txt'
streamsTxt = 'streams_rt.txt'
batFile = 'runFFMPEG_rt.bat'
c = 0

logging.basicConfig(filename='StreamDownloading.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def CheckWhetherStreamOnline(ch):
    ''' Проверка онлайн ли стрим '''
    url = urlKraken + 'streams/' + channel
    h = {'Client-ID': client_id, 'stream-type': 'live'}
    try:
        r = requests.get(url, headers=h)
    except Exception as e:
        logging.info(e)
        print(e)
        return False
    stream = r.json()
    with open('stream.txt', 'a', encoding='utf8') as streamfile:
            streamfile.write(str(stream))
    if (stream['stream'] == None):
        print("Нету стрима")
        return (False, None)
    else:
        # if stream['stream']['stream_type'] != 'live':
        #     print('Кажется, это повтор')
        #     return (False, None)
        # else:
        print("Есть стрим!")
        return (True, stream)


if not client_id:
    print('Укажеите client-id')
    sys.exit()

# --- 0. Вторым аргументом идет название канала. Если не указан выбираем автоматически в блоке else
if len(sys.argv) > 1:
    channel = sys.argv[1]
else:
    print('Не указан канал. \nUsing: ' + sys.argv[0] + ' <channel_name>')
    print('Тогда сам выберу :P')
    channel = 'welovegames'  # 'sholidays' #na_podhvate #lily_mint #blackufa_twitch #artgameslp
print('Канал:', channel)

while 1:
    # --- 1. Проверка, онлайн ли стрим
    while 1:
        isOnline, stream = CheckWhetherStreamOnline(channel)
        if isOnline:
            streamName = stream['stream']['channel']['status'].translate(non_bmp_map)
            videoDate = stream['stream']['created_at'].replace(":", "-")   #2017-07-25T18_57_43Z
            videoDate = videoDate.replace('T', '_').replace('Z', '')
            videoDate = videoDate[:-3]  # опускаем секунды
            if debug:
                print('streamName: ', streamName)
                print('videoDate: ', videoDate)
            break
        else:
            time.sleep(30)

    # --- 2. Создадим директории, подготовим имя файла
    nowstr = videoDate
    # folderTemplate = dirname(realpath(__file__)) + "\\Streams\\{0}\\{1}_RT\\".format(channel, nowstr)
    folderTemplate = "E:\\Streams\\{0}\\{1}_RT\\".format(channel, nowstr)
    outputFilename = nowstr + '.mp4'
    if debug:
        print('folderTemplate: ', folderTemplate)
        print('outputFilename: ', outputFilename)

    if not exists(folderTemplate):
        os.makedirs(folderTemplate)

    # пишем название стрима в Streams.txt
    with open(folderTemplate + streamsTxt, 'ab') as infofile:
        infofile.write('{0} -- {1}\n'.format(nowstr, streamName).encode('utf8'))

    # Создаем батник для склеивания сегментов с помощью ffmpeg
    with open(folderTemplate + batFile, 'w') as bat:
        bat.write('ffmpeg -f concat -safe 0 -i {0} -c copy "{1}"\npause'.format(inputsTxt, outputFilename))

    # --- 3. Получаем access_token через открытое апи
    print('Получаем access_token через открытое апи')
    url = urlApi + 'channels/{0}/access_token?client_id={1}'.format(channel, client_id)
    r = requests.get(url)
    j = r.json()
    token = j['token']
    sig = j['sig']
    if debug:
        print('token = ', token)
        print('sig = ', sig)

    # --- 4. получаем ID канала
    print('Получаем ID канала')
    url = urlKraken + 'users?login=' + channel
    h = {'Accept': AcceptHeaderV5, 'Client-ID': client_id}
    r = requests.get(url, headers=h)
    channelId = r.json()['users'][0]['_id']
    if debug:
        print('channel ID: ', channelId)

    # плейлист
    url = urlUsher + 'channel/hls/{0}.m3u8?allow_source=true'\
    '&sig={1}&token={2}'.format(channel, sig, token)
    print('Пробуем получить крутой плейлист :')
    try:
        r = requests.get(url)
        v_pl = m3u8.load(url)
    except Exception as e:
        print(e)
        print('спим')
        time.sleep(30)
        print('продолжаем')
        continue
    if not v_pl.is_variant:
        print("Не вариативный плейлист")
        logging.info("Не вариативный плейлист")
        continue

    maxband = 0
    for p in v_pl.playlists:
        print(p.stream_info.bandwidth)
        if p.stream_info.bandwidth > maxband:
            maxband = p.stream_info.bandwidth
            plUrl = p.uri
    print('плейлист с лучшим качеством:', plUrl)

    # Скачиваем плейлист
    try:
        u = urlopen(plUrl)
        with open(os.path.join(folderTemplate, 'playlist_rt.m3u8'), 'wb') as plfile:
            plfile.write(u.read())
    except Exception as e:
        print(e)
        logging.info(e)
        continue
    print('playlist downloaded')

    # Подгружаем плейлист, качаем сегменты, снова подгружаем плейлист... пока не будет оффлайн и последний файл в плейлисте не скачан
    doLastIteration = False
    while 1:
        print('Загружаем плейлист...')
        try:
            pl = m3u8.load(plUrl)
        except Exception as e:
            print(e)
            break

        # --- Качаем .ts-сегменты
        doCheckOnline = True  # если ни один файл не был скачан за прогон плейлиста, то надо проверить стрим на онлайн
        for f in pl.segments:
            try:
                segmentDatetime = str(f.program_date_time)  ##EXT-X-PROGRAM-DATE-TIME:2018-09-06T21:28:01.42Z  # перед каждым файлов в плейлисте идёт
                segmentDatetime_name = segmentDatetime.replace(':', '-').replace('T', '_').replace('Z', '')
                chunkFilename = segmentDatetime_name + '.ts'
                if exists(folderTemplate + chunkFilename):
                    print('PASS')
                    continue
                else:
                    # по сути можно else: опустить, так как continue возвращает в начало цикла
                    doCheckOnline = False
                    doLastIteration = False

                filebasename = basename(f.uri)
                # --- файл соответствия (т.к. в таких плейлистах названия сегментов дичовые (600+ символов))
                with open(folderTemplate + 'conformityFile.txt', 'a') as confFile:
                    confFile.write('{0} = {1} = {2}\n'.format(c, segmentDatetime_name, filebasename))

                # --- тут непосредственно скачивается .ts-файл
                url = f.uri
                uo = urlopen(url)
                with open(folderTemplate + chunkFilename, "wb") as chunk:
                    chunk.write(uo.read())
                print(chunkFilename, 'chunk is downloaded')

                # --- Обновляем файл-список для ffmpeg
                with open(folderTemplate + inputsTxt, "a") as f:
                    f.write("file '" + chunkFilename + "'\n")
                c += 1
                errorCounter = 0
            except Exception as e:
                logging.info(e)
                print(e)

        if doLastIteration:
            break  # :)

        if doCheckOnline:
            isOnline, stream = CheckWhetherStreamOnline(channel)
            # Если Стрим закончился:
            if not isOnline:
                doLastIteration = True

    print('Загрузка завершена. Запустите файл runFFMPEG.bat в папке со стримом.')
    time.sleep(60)

input()
