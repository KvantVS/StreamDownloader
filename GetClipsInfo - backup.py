'''
Скачиваем инфу по клипам
'''

import requests
import time
from datetime import datetime, timezone
import os
from os.path import realpath, dirname, exists, join

from twitch_basic import *

client_id = CID_streamDownloader
#non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
channel = 'welovegames'  # 'blackufa_twitch' # 'sholidays' #'artgameslp' #https://www.twitch.tv/sholidays
games = {'493057': "PLAYERUNKNOWN'S BATTLEGROUNDS",
         '494683': 'theHunter: Call of the Wild',
         '459064': 'Cuphead',
         '492504': 'Human: Fall Flat',
         '16256': 'Vietcong',
         '2684': 'Spider-Man',
         '29433': 'Dark Souls',
         '503762': 'Super Seducer',
         '66082': 'Games + Demos',
         '458912': 'Kingdom Come: Deliverance',
         '497078': 'Far Cry 5',
         '460090': 'Subnautica',
         '33214': 'Fortnite',
         '6369': 'God of War',
         '500188': 'Hunt: Showdown',
         '417919': 'PULSAR: Lost Colony',
         '506343': 'E3 2018',
         '488500': 'Battlefield 1',
         '458857': 'OMSI 2',
         '118198': "Assassin's Creed IV: Black Flag",
         '23979': 'Aliens vs. Predator',
         '33862': 'Bloody Trapland',
         '490377': 'Sea of Thieves',
         '28394': 'Total War: Shogun 2',
         '488552': 'Overwatch',
         '17329': 'The Operative: No One Lives Forever',
         '498459': 'Jurassic World Evolution',
         '502502': 'Desolate',
         '503159': 'Dead Dozen',
         '497480': 'Detroit: Become Human',
         '500196': 'Hand Simulator',
         '33437': 'Resident Evil 6',
         '5975': 'Shadow of the Colossus',
         '26559': 'Batman: Arkham City',
         '490378': 'South Park: The Fractured But Whole',
         '490201': 'Crossing Souls',
         '313445': 'Tropico 5',
         '493551': 'Conan Exiles',
         '494839': 'Deep Rock Galactic',
         '22851': 'Battlefield: Bad Company 2',
         '488974': 'Devil May Cry 4: Special Edition',
         '494925': 'Raft',
         '14304': 'Diablo II: Lord of Destruction',
         '495122': 'State of Decay 2',
         '497388': 'A Way Out',
         '12001': 'SOS',
         '19009': 'Dead Space',
         '497467': 'Monster Hunter World',
         '488518': 'Friday the 13th: The Game',
         '73586': 'Outlast',
         '12004': 'DmC Devil May Cry',
         '18763': 'Fallout 3',
         '68000': 'The Evil Within',
         '313553': 'XCOM: Enemy Within',
         '23017': 'Dead Space 2',
         '498668': 'Warhammer: Vermintide 2',
         '502557': 'Sexy Serial Killer',
         '502223': 'Total War Saga: Thrones of Britannia',
         '11210': 'Sega Classics Collection',
         '491487': 'Dead by Daylight',
         '5126': 'Resident Evil 3: Nemesis',
         '492546': 'Star Wars Battlefront II',
         '495764': 'Golf It!',
         '493036': 'Worms W.M.D',
         '493125': 'My Summer Car',
         '501930': 'Surviving Mars',
         '488758': 'Vampyr',
         '496712': 'Call of Duty: WWII',
         '8645': 'Resident Evil 2',
         '14805': 'Metal Gear Solid',
         '489776': 'Fallout 4',
         '13793': 'SimCity',
         '497435': 'XCOM 2: War of the Chosen',
         '497110': 'Ben and Ed: Blood Party',
         '10384': 'God of War II',
         '506344': 'Totally Accurate Battlegrounds',
         '10775': 'S.T.A.L.K.E.R.: Shadow of Chernobyl',
         '494162': 'NieR Automata',
         '493909': 'Witchkin',
         '15631': 'Grand Theft Auto: Vice City',
         '17729': 'Battletoads & Double Dragon: The Ultimate Team',
         '369285': 'Road Redemption',
         '6715': 'Doom',
         '1468': 'Resident Evil 4',
         '18924': 'Brütal Legend',
         '18892': 'Rage',
         '822': "Devil May Cry 3: Dante's Awakening",
         '494591': 'Absolver',
         '18864': 'Silent Hill: Homecoming',
         '490644': 'Divinity: Original Sin II',
         '489093': 'Terminator',
         '17179': 'Star Wars: Knights of the Old Republic',
         '9348': "Resident Evil: Director's Cut",
         '490744': 'Stardew Valley',
         '33385': 'Depth',
         '497057': 'Destiny 2'}


''' === old - V5 API ===
url = 'https://api.twitch.tv/kraken/clips/top/?channel='+channel+'&trending=false&period=all'
h = {'Accept': 'application/vnd.twitchtv.v5+json',
    'Client-ID':client_id,
     'limit':'10'}
'''

#un_games = []  
un_games_set = set()  # список id неизвестных игр (которых нет в словаре games)
ls = []               # список подготовленных строк для записи в файл clips.txt.
                      # Сразу не пишу в файл потому, что нужно одним запросом сначала узнать неизвестные игры

# Узнаём id канала
# url = f'{API_KRAKEN}users?login={channel}'
# h = {STR_ACCEPT: HEADER_AcceptV5,
#      STR_CLIENT: client_id}
# r = requests.get(url, headers=h)
# channelId = r.json()['users'][0]['_id']

channelId = getChannelID(channel, client_id)

cursor = ''
first = '100'
c = 0

# Подготавливаем пути
folder = join(baseFolder, 'clips', channel)
if not exists(folder):
    os.makedirs(folder)

h = {STR_CLIENT: client_id}
passedCursors = []

while True:
    url = f'{API_HELIX}clips?broadcaster_id={channelId}&first={first}'
    if cursor:
        passedCursors.append(cursor)
        url += f'&after={cursor}'
    print(f'requesting... {url}')
    # r = requests.get(url, headers=h)
    # j = r.json()
    j = sendRequest(url, h)

    # if 'pagination' in j:
    #     print(j['pagination'])
    if 'error' in j:
        if 'status' in j:
            if j['status'] == '429':  # много запросов на API-ресурс
                time.sleep(60)
                continue
        else:
            break
    clips = j['data']

    for clip in clips:
        clip_url = clip['url']
        thumbnail_url = clip['thumbnail_url']
        title = clip['title'].replace('\n', '')
        view_count = clip['view_count']
        game_id = clip['game_id']
        try:
            game = games[game_id]  # берем название игры из словаря известных игр
        except KeyError:   # если игры нет в словаре, то сохраняем в список айдишников неизвестных игр (un_games)
            try:
                un_games_set.add(game_id)
                # un_games.index(game_id)  # проверка на наличие уже такого айдишника в списке
            except ValueError as e:
                # un_games.append(game_id)
                print(e)

        # --- дату переворачиваем так, чтобы Excel понимал при импорте данных из текст.файла (ДД.ММ.ГГГГ чч:мм)
        created_at = clip['created_at']
        dt = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")  # парсим строку, превращаем в datetime
        created_at = dt.strftime('%d.%m.%Y %H:%M:%S')             # из даты делаем строку нужного формата

        # --- раньше сразу писал в файл, но т.к. игр очень много, пришлось отложить запись на конец скрипта
        ls.append('{0}\t{{<{1}>}}\t{2}\t{3}\t{4}\t{5}\n'.format(
            created_at, game_id, view_count, clip_url, title, thumbnail_url))
        # ^^^ тут формат строк такой: Дата     {<id-Игры>}     кол-во просмотров   и т.д.
        #     Потом вместо {<ID-игры>} вставляется название игры по словарю games
    if 'cursor' in j['pagination']:
        cursor = j['pagination']['cursor']
        if cursor in passedCursors:
            print(f'Курсор {cursor} уже был (кол-во пройденных курсоров: {len(passedCursors)})')
            break
    else:
        print('все, курсора нет в pagination')
        print(j)
        break

# по списку id неизвестных игр идём, и по 100 штук выполняем запрос
# (т.к. "At most 100 id values can be specified")
# игры заносим в словарь известных игр - games
c = 0
un_games = list(un_games_set)
print(f'Получаем названия игр... (кол-во: {len(un_games)})')
while True:
    start = c * 100
    diff = len(un_games) - start
    d = 100 if diff > 100 else diff
    end = start + d
    newlist = un_games[start:end]

    u = API_HELIX + 'games?id=' + '&id='.join(newlist)
    print(f'requesting games... {u}')
    r = requests.get(u, headers=h)
    j = r.json()

    try:
        for game in j['data']:
            g_id = game['id']
            g_name = game['name']
            games[g_id] = g_name  # <-----------
    except:
        print(j)
        print(c)
        print(start)
        if 'status' in j:
            if j['status'] == '429':
                time.sleep(60)
                continue
        else:
            break
    c += 1
    if diff < 100:
        break

# Пишем наконец в файл clips.txt
with open(join(folder, 'clips.txt'), 'wb') as clipsfile:
    clipsfile.write('Дата\tИгра\tПросм\tURL\tНазвание\tPreview\n'.encode('utf8'))  # заголовки столбцов (для Excel)

    # ищем отметку с айди игры в каджой строке и заменяем её из списка "games"
    for s in ls:
        i1 = s.find('{<')
        i2 = s.find('>}')
        g_id = s[i1 + 2: i2]
        try:
            s2 = s.replace(s[i1: i2 + 2], games[g_id])
        except KeyError:
            s2 = s.replace(s[i1: i2 + 2], '')
        clipsfile.write(s2.encode('utf8'))
