# StreamDownloader
= Using =

GetStreamOrVideo1.2.py -v VOD_link | -c channelName | -p playlist_URL | -pf playlistFile [-o OutputFolder]  -- качает стрим или видео.
если указан ключ -v, качает видео VOD_link.
если указано ключ -c, качает стрим с канала channelName.
если указан ключ - p, качает сегменты с плейлиста playlist_URL.
-pf - тоже, что и ключ -p, но не URL, а путь к локальному файлу.

GetStreamReal.py <channel> -- качает текущий идущий стрим с канала channel, даже если текущая трансляция удалена.
