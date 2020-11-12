'''
Создать inputs.txt из .ts-файлов. ts-файлы должны быть вида 1.ts, 2.ts, 3.ts...
'''
import sys, os, datetime

#path = r"E:\Vadim\Coding\StreamDownloader\Streams\sholidays\2018-09-08_02-48"
path = os.path.dirname(os.path.realpath(__file__))
files = os.listdir(path)
ts_files = list(filter(lambda x: x.endswith('.ts'), files))
ts_files2 = []

# if ints:
for f in ts_files:
    #s = f[:-3] #убираем разрешение
    #i = int(s)
    ts_files2.append(f)
ts_files2.sort()

with open(os.path.join(path, 'inputs_sorted.txt'), 'w') as inputtxt:
    for f in ts_files2:
        s = ("file '" + str(f) + "'\n")
        inputtxt.write(s)

print('Готово')
input()

# if datetimes:
'''
for f in ts_files:
    s = f[:-3] #разрешение
    s = s[:-6]
    dt = datetime.datetime.strptime(s, '%Y-%m-%d %H-%M-%S.%f')   #2018-09-08 06-52-03.847000+00-00.ts.ts
    ts_files2.append(dt)
ts_files2.sort()

with open(os.path.join(path, 'inputs_sorted.txt'), 'w') as inputtxt:
    for f in ts_files2:
        s = f.strftime("file '%Y-%m-%d %H-%M-%S.%f+00-00.ts'\n")
        inputtxt.write(s)
'''
