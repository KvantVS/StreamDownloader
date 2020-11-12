'''
1. GET-запрос к 'https://api.twitch.tv/v5/videos/' + videoId + '/comments'
   в заголовке: content_offset_seconds=0 и client_id
   Получаем json-список сообщений чата на 6 минут
2. В конце объекта будет объект "_next": с длиииииинным длинным ID.
   Берем этот ID
3. Для следующих сообщений делаем GET-Запрос к https://api.twitch.tv/v5/videos/205529476/comments?cursor=<ID который взяли в п.2>
(например: https://api.twitch.tv/v5/videos/205529476/comments?cursor=eyJpZCI6ImIzMWZiOWVlLWEwMDItNGY1My1iYWNiLTYzMThkZGQxZTAzNCIsImhrIjoiYnJvYWRjYXN0OjI2ODU5MTYyNzg0Iiwic2siOiJBQUFBV0E2SlNFQVUtLWFNTU1XYlFBIn0f)
'''

import time, datetime
import sys
import requests
import re
import os

import twitch_basic

def ConvertTime(t):
    if t >= 60:
        x = t % 60
        t = int(t / 60)
        return (x, t)
    else:
        return (t, 0)
##################################

def GetVideoChat(videoId, needToGetVideoInfo=True, sChannel='', sVideoCreated='', sVideoName='', sGame=''):
    l_wowmoments = []
    l_clips = []
    l_serials = []
    l_links = []
    messageFormat = '%s (%s) (%s)  %s: %s\n'  #время_системы (время_относительно_начала_ролика)  ник: сообщение
    videoTimeFormat ='%d:%02d:%02d'
    non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
    clientId = 'm195drduyerw4kt1ahc0iul8gc2i34'

    ttt1 = time.time()
    
    url = 'https://api.twitch.tv/v5/videos/' + videoId + '/comments?content_offset_seconds=0'
    h = {'Accept': 'application/vnd.twitchtv.v5+json',
         'Client-ID': clientId}
    r = requests.get(url, headers=h)
    j = r.json()

    # - убираем запрещенные в проводнике символы (составляем таблицу трансляции, потом её применяем)
    symbols = '/:*?"<>|'
    sblank = ''
    trans = sblank.maketrans(symbols, symbols, symbols)

    if needToGetVideoInfo:
        sChannel, sVideoCreated, sVideoName, sGame = twitch_basic.GetInfoAboutVideo(videoId, True)
    sChannel = sChannel.translate(trans)
    sGame = sGame.translate(trans)
    folderTemplate = os.path.dirname(os.path.realpath(__file__)) + "\\Chats\\{channel}\\".format(channel=sChannel)
    outputFilename = folderTemplate + '{0}_{1}_{2}_{3}'.format(sChannel, sVideoCreated, videoId, sGame)
    

    if not os.path.exists(folderTemplate):
        os.makedirs(folderTemplate)
    # ===============================

    print('Получаем чат...')
    canProduce = True;
    with open(outputFilename + '.txt', 'wb') as chatfile:
        while canProduce:
            if 'comments' in j:
                for msg in j['comments']:
                    s_msgTime = msg['created_at']
                    i_timeRelative = msg['content_offset_seconds']
                    s_msgText = msg['message']['body']
                    s_msgNickname = msg['commenter']['display_name']
                    s_msgType = msg['source']

                    #2017-11-13T13:00:17.710599Z
                    #2017-11-13T13:00:17Z
                    s_msgTime = s_msgTime[:-1].split('.')[0]

                    dt_msgTime = datetime.datetime.strptime(s_msgTime, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
                    s_msgTime = dt_msgTime.strftime("%H:%M:%S").translate(non_bmp_map)

                    i_timeRelativeSecs, i_timeRelative = ConvertTime(i_timeRelative)
                    i_timeRelativeMinutes, i_timeRelative = ConvertTime(i_timeRelative)
                    i_timeRelativeHours, i_timeRelative = ConvertTime(i_timeRelative)
                    s_timeRelative = videoTimeFormat % (i_timeRelativeHours,i_timeRelativeMinutes,i_timeRelativeSecs)  #время относительно начала ролика
                    s_msgType = s_msgType[:4]
                    
                    message = messageFormat % (s_msgTime, s_timeRelative, s_msgType, s_msgNickname, s_msgText)
                    # 04:43:15 (3:38:43) (chat)  JIucToyxuu: мне показалось или там был проигнорен глушак на пп?
                    # 04:43:15 (3:38:43) (comm)  JIucToyxuu: мне показалось или там был проигнорен глушак на пп? # комментарий добавленный ВНЕ стрима

                    chatfile.write(message.encode('utf-8'))

                    ######################################################
                    # ^([^\S]*LUL[\s]*)+$ --- for LUL LUL LUL
                    # ^([\S]+LUL[\s]*)+$ ---- blackufaLUL blackufaLUL
                    # ^[ах]+\)*[\s]*$ ---------- for ахах
                    # ^[X:;]D*\)*[\s]*$ - XD, xDDDD, :DD, ;DDDD
                    srch = re.search('^([^\S]?(LUL|PogChamp|МЛЖ|DansGame|SeemsGood|CurseLit|GTChimp|SwiftRage|CarlSmile|CoolStoryBob|blackufaCoolstory)[\s]*)+$|^([\S]+LUL[\s]?)+$|^[ах]+\)*[\s]*$|^[X:;]D*\)*[\s]*$|^хд*\)*[\s]*$', s_msgText, re.IGNORECASE)
                    srch2 = re.search('^([^\S]?MLG[\s]*)+$|^([\S]+MLG[\s]?)+$', s_msgText, re.IGNORECASE)
                    srch3 = re.search('^клип', s_msgText, re.IGNORECASE)
                    srch_clips = re.search('^.*clips', s_msgText, re.IGNORECASE)
                    srch_links = re.search('\S*\.com|\S*\.ru', s_msgText, re.IGNORECASE)
                    srch_serials = re.search('сериал', s_msgText, re.IGNORECASE)
                    
                    
                    if (srch or srch2 or srch3 or srch_clips):
                        s = s_timeRelative + ": " + s_msgText
                        l_wowmoments.append(s)

                    if (srch_clips or srch3):
                        s = s_timeRelative + ": " + s_msgText
                        l_clips.append(s)

                    if srch_serials:
                        s = s_timeRelative + ": " + s_msgText
                        l_serials.append(s)

                    if srch_links:
                        s = s_timeRelative + ": " + s_msgText
                        l_links.append(s)

            if '_next' in j:
                url = 'https://api.twitch.tv/v5/videos/' + videoId + '/comments?cursor=' + j['_next']
                r = requests.get(url, headers=h)
                j = r.json()
            else:
                canProduce = False

    with open(outputFilename + '_moments.txt', 'wb') as wowFile:
        for s in l_wowmoments:
            ws = s + '\n'
            wowFile.write(ws.encode('utf-8'))

        if l_clips:
            wowFile.write('\n = КЛИПЫ = \n'.encode('utf-8'))
        for s in l_clips:
            ws = s + '\n'
            wowFile.write(ws.encode('utf-8'))

        if l_serials:
            wowFile.write('\r\n = СЕРИАЛЫ = \r\n'.encode('utf-8'))
        for s in l_serials:
            ws = s + '\n'
            wowFile.write(ws.encode('utf-8'))

        if l_links:
            wowFile.write('\r\n = ССЫЛКИ = \r\n'.encode('utf-8'))
        for s in l_links:
            ws = s + '\r\n'
            wowFile.write(ws.encode('utf-8'))

    ttt2 = time.time()
    print('Готово! Скачан чат для видео {0} за {1} секунд'.format(videoId, ttt2-ttt1))

##########
