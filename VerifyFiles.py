import os
import sys
import m3u8
import time
import subprocess
from os.path import join, getsize

logfile = 'verifyedLog.txt'
inputstxt = 'inputs.txt'
l_logFolderNotFound = []
l_logInputsNotFound = []
l_logInputsNotOrder = []
l_logZeroSize = []

# sTemplate = 'file {0}\n'
sTemplate = "file '{0}'\n"
folder = r'E:\Vadim\Coding\StreamDownloader\Streams\welovegames\2018-09-08_17-20'

if len(sys.argv) > 1:
    folder = sys.argv[1]

# - удаляем кавычки
print('folder === ', folder)
if folder[0] == '"':
    folder = folder[1:]
if folder[-1] == '"':
    folder = folder[0:-1]

# --- сбор данных --------------------------------------------------------------
# файлы по плейлисту
pl = m3u8.load(join(folder, 'playlist.m3u8'))

# файлы в папке
files = os.listdir(folder)
# если не обозначить как list(... , то проверка работает жутко некорректно:
ts_files = list(filter(lambda x: x.endswith('.ts'), files))

# --- 1. берем файлы из плейлиста и проверяем есть ли они в файлах папки -------
for p in pl.files:
    if p not in ts_files:
        l_logFolderNotFound.append(p)

# --- 2.  проверяем наличие файлов в inputs.txt (по плейлисту) -----------------
# --- 2.1 и проверяем порядок файлов в inputs.txt

# считываем inputs.txt в список
l_inputsFiles = []
l_inputsFiles.clear()
with open(join(folder, inputstxt), 'r') as inputstxtFile:
    for line in inputstxtFile:
        l_inputsFiles.append(line)

# --- для первого файла
# если [0] файл из плейлиста не найден на [0] месте в inputs.txt, то он либо
# не на своем месте, либо вообще отсутствует в inputs.txt
p = pl.files[0]
if sTemplate.format(p) != l_inputsFiles[0]:
    if (not sTemplate.format(p) in l_inputsFiles):
        l_logInputsNotFound.append(p)  # файл не найден в inputs.txt
    else:
        l_logInputsNotOrder.append(p)  # файл идёт не по порядку в inputs.txt

# --- для остальных файлов
ip = 1
for i in range(len(pl.files)-1):
    p = pl.files[ip]
    if not sTemplate.format(p) in l_inputsFiles:
        l_logInputsNotFound.append(p)
    else:
        try:
            # ищем файл из плейлиста в inputs.txt
            il = l_inputsFiles.index(sTemplate.format(p))
            # если пред ним идет не тот же файл, что идет перед файлом из плейлиста, то ошибка
            if l_inputsFiles[il - 1] != sTemplate.format(pl.files[ip - 1]):
                l_logInputsNotOrder.append(p)
        #except ValueError as e:
        #    print(e)
        #except IndexError as e:
        #    print(e)
        except Exception as e:
            print(e)
    ip += 1

# --- 3 Проверка на 0-й размер
for f in ts_files:
    size = getsize(join(folder, f))
    if size == 0:
        l_logZeroSize.append(f)

# - пишем всё в logfile.txt
with open(join(folder, logfile), 'w') as log:
    for s in l_logFolderNotFound:
        log.write(f'не найден файл {s} в папке\n')

    for s in l_logInputsNotFound:
        log.write(f'в {inputstxt} не найден файл {s}\n')

    for s in l_logInputsNotOrder:
        log.write(f'файл {s} не по порядку в {inputstxt} (согласно плейлисту, проверьте заодно плейлист)\n')

    for s in l_logZeroSize:
        log.write(f'файл {s} нулевого размера')

    if (not l_logFolderNotFound and
    not l_logInputsNotFound and
    not l_logInputsNotOrder and
    not l_logZeroSize):
        log.write('Кажется, всё норм. Можно запускать второй батник.')
        print(f'Кажется, всё норм. Можно запускать второй батник. (Проверьте в файле {logfile}')

print('Готово')

time.sleep(1)
cmdline = '"' + folder + r'\verifyedLog.txt"'
proc = subprocess.Popen(cmdline, shell=True, stdout=subprocess.PIPE)
out = proc.stdout.readlines()
