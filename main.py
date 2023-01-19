# -*- coding: utf-8 -*-
import sys, re, os
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
import six

from six.moves import urllib

try:
    import cookielib
except ImportError:
    import http.cookiejar as cookielib

try:
    import json
except ImportError:
    import simplejson as json

BASE_URL = 'https://rumble.com'
PLUGIN_URL = sys.argv[0]
PLUGIN_ID = int(sys.argv[1])
PLUGIN_NAME = PLUGIN_URL.replace("plugin://","")

ADDON = xbmcaddon.Addon()
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')

HOME_DIR = 'special://home/addons/{0}'.format(PLUGIN_NAME)
RESOURCE_DIR = HOME_DIR + 'resources/'
MEDIA_DIR = RESOURCE_DIR + 'media/'

#language
__language__ = ADDON.getLocalizedString

try:
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo('profile').decode('utf-8'))
except:
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

lang = ADDON.getSetting('lang')
favorites = os.path.join(profile, 'favorites.dat')

if os.path.exists(favorites)==True:
    FAV = open(favorites).read()
else:
    FAV = []


def notify(message,name=False,iconimage=False,timeShown=5000):

    if not name:
        name = ADDON_NAME
    if not iconimage:
        iconimage = ADDON_ICON

    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (name, message, timeShown, iconimage))


def to_unicode(text, encoding='utf-8', errors='strict'):
    """Force text to unicode"""
    if isinstance(text, bytes):
        return text.decode(encoding, errors=errors)
    return text


def get_search_string(heading='', message=''):
    """Ask the user for a search string"""
    search_string = None
    keyboard = xbmc.Keyboard(message, heading)
    keyboard.doModal()
    if keyboard.isConfirmed():
        search_string = to_unicode(keyboard.getText())
    return search_string


def getRequest(url, ref=''):

    try:
        if ref == '':
            ref = url

        cj = cookielib.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        opener.addheaders=[('Accept-Language', 'en-gb,en;q=0.5'),('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'),('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'), ('Referer', ref)]
        data = opener.open(url).read()
        response = data.decode('utf-8')
    except:
        response = ''

    return response


# main menu
def home_menu():

    # Search
    addDir( xbmc.getLocalizedString(137), '', 1, MEDIA_DIR + 'search.png', '', '' ,'' )
    # Favorites
    addDir( xbmc.getLocalizedString(1036), '', 7, MEDIA_DIR + 'favorite.png', '', '', '' )
    # News
    addDir( xbmc.getLocalizedString(29916), BASE_URL + '/category/news', 3, MEDIA_DIR + 'news.png', '', '', 'other' )
    # Viral
    addDir( __language__(30050), BASE_URL + '/category/viral',3,MEDIA_DIR + 'viral.png','','','other' )
    # Podcasts
    addDir( __language__(30051), BASE_URL + '/category/podcasts',3,MEDIA_DIR +'podcast.png','','','other')
    # Battle Leaderboard
    addDir( __language__(30052), BASE_URL + '/battle-leaderboard',3,MEDIA_DIR + 'leader.png','','','top')
    # Entertainment
    addDir( __language__(30053), BASE_URL + '/category/entertainment',3,MEDIA_DIR + 'entertaiment.png','','','other')
    # Sports
    addDir( xbmc.getLocalizedString(19548), BASE_URL + '/category/sports',3,MEDIA_DIR + 'sports.png','','','other')
    # Science
    addDir( xbmc.getLocalizedString(29948), BASE_URL + '/category/science',3,MEDIA_DIR + 'science.png','','','other')
    # Technology
    addDir( __language__(30054), BASE_URL + '/category/technology', 3, MEDIA_DIR + 'technology.png', '', '', 'other' )
    # Vlogs
    addDir( __language__(30055), BASE_URL + '/category/vlogs', 3, MEDIA_DIR + 'vlog.png', '', '', 'other' )
    # Settings
    addDir( xbmc.getLocalizedString(5), '', 8, MEDIA_DIR + 'settings.png', '', '', '' )
    SetView('WideList')
    xbmcplugin.endOfDirectory(PLUGIN_ID, cacheToDisc=False)


# search menu
def search_menu():

    # Search Video
    addDir( __language__(30100), BASE_URL + '/search/video?q=',2,MEDIA_DIR + 'search.png','','','video')
    # Search Channel
    addDir( __language__(30101), BASE_URL + '/search/channel?q=',2,MEDIA_DIR + 'search.png','','','channel')
    # Search User
    addDir( __language__(30102), BASE_URL + '/search/channel?q=',2,MEDIA_DIR + 'search.png','','','user')
    SetView('WideList')
    xbmcplugin.endOfDirectory(PLUGIN_ID)


def pagination(url,page,cat,search=False):

    if url > '':

        page = int(page)
        pageUrl = url

        if page == 1:
            if search:
                pageUrl = url + search
        elif search and cat == 'video':
            pageUrl = url + search + "&page=" + str( page )
        elif cat in {'channel', 'user', 'other' }:
            pageUrl = url + "?page=" + str( page )

        amount = list_rumble( pageUrl, cat )

        if amount > 15 and page < 10:

            # for next page
            page = page + 1

            name = "[B]"+__language__(30150) + " " + str( page ) + "[/B]"
            li=xbmcgui.ListItem(name)
            link = PLUGIN_URL + "?mode=3&name=" + urllib.parse.quote_plus(name)+"&url=" + urllib.parse.quote_plus(url) + "&page=" + str( page ) + "&cat=" + urllib.parse.quote_plus(cat)

            if search and cat == 'video':
                link = link + "&search=" + urllib.parse.quote_plus(search)

            xbmcplugin.addDirectoryItem(PLUGIN_ID, link, li, True)

    SetView('WideList')
    xbmcplugin.endOfDirectory(PLUGIN_ID)


def get_image(data,id):
    image_re = re.compile("i.user-image--img--id-"+str(id)+".+?{ background-image: url(.+?);", re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    if image_re !=[]:
        image = str(image_re[0]).replace('(', '').replace(')', '')
    else:
        image = ''
    return image


def list_rumble(url, cat):

    amount = 0
    data = getRequest(url)

    if 'search' in url:
        if cat == 'video':
            amount = create_dir_list( data, cat, 'video', True, 1 )
        else:
            amount = create_dir_list( data, cat, 'channel', True )
    elif cat in { 'channel', 'user', 'top', 'other' }:
            amount = create_dir_list( data, cat, 'video', False, 2 )

    return amount


def create_dir_list( data, cat, type='video', search = False, play=False ):

    amount = 0

    if type == 'video':
        videos = re.compile('a href=([^\>]+)><div class=\"(?:[^\"]+)\"><img class=\"video-item--img\" src=(https:\/\/.+?) alt=(?:[^\>]+)>(?:<span class=\"video-item--watching\">[^\<]+</span>)?</div><(?:[^\>]+)></span></a><div class=\"video-item--info\"><time class=\"video-item--meta video-item--time\" datetime=(.+?)-(.+?)-(.+?)T(?:.+?) title\=\"(?:[^\"]+)\">(?:[^\<]+)</time><h3 class=video-item--title>(.+?)</h3><address(?:[^\>]+)><a rel=author class=\"(?:[^\=]+)=(.+?)><div class=ellipsis-1>(.+?)</div>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
        if videos:
            amount = len(videos)
            for link, img, year, month, day, title, channel_link, channel_name in videos:
                if '<svg' in channel_name:
                    channel_name = channel_name.split('<svg')[0] + " (Verified)"

                if int(lang) == 0:
                    video_date = month+'/'+day+'/'+year
                else:
                    video_date = day+'/'+month+'/'+year

                video_title = '[B]' + title + '[/B]\n[COLOR gold]' + channel_name + ' - [COLOR lime]' + video_date + '[/COLOR]'
                #open get url and open player
                addDir( video_title, BASE_URL + link, 4, str(img), str(img), '', cat, False, True, play )

    else:
        channels = re.compile('a href=(.+?)>\s*<div class=\"channel-item--img\">\s*<i class=\'user-image user-image--img user-image--img--id-(.+?)\'></i>\s*</div>\s*<h3 class=channel-item--title>(.+?)</h3>\s*<span class=channel-item--subscribers>(.+?) subscribers</span>',re.DOTALL).findall(data)
        if channels:
            amount = len(channels)
            for link, img_id, channel_name, subscribers in channels:

                # split channel and user
                if search:
                    if cat == 'channel':
                        if '/c/' not in link:
                            continue
                    else:
                        if '/user/' not in link:
                            continue

                if '<svg' in channel_name:
                    channel_name = channel_name.split('<svg')[0] + " (Verified)"
                img = str( get_image( data, img_id ) )
                video_title = '[B]' + channel_name + '[/B]\n[COLOR palegreen]' + subscribers + ' [COLOR yellow]' + __language__(30155) + '[/COLOR]'
                #open get url and open player
                addDir( video_title, BASE_URL + link, 3, img, img, '', cat, True, True, play )

    return amount


def resolver(url):

    # playback options - 0: large to small, 1: small to large, 2: quality select
    playbackMethod = ADDON.getSetting('playbackMethod')

    mediaURL = False

    if playbackMethod == '2':
       urls = []

    data = getRequest(url)

    # gets embed id from embed url
    embed_id = re.compile(',\"embedUrl\":\"' + BASE_URL + '/embed/(.*?)\/\",', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    if embed_id:
        # use site api to get video urls
        data = getRequest(BASE_URL + '/embedJS/u3/?request=video&ver=2&v=' + embed_id[0])
        sizes = [ '1080', '720', '480', '360', 'hls' ]

        # reverses array - small to large
        if playbackMethod == '1':
            sizes = sizes[::-1]

        for quality in sizes:

            matches = re.compile( '"' + quality + '".+?url.+?:"(.*?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)

            if matches:
                if playbackMethod == '2':
                    urls.append(( quality, matches[0] ))
                else:
                    mediaURL = matches[0]
                    break

        # quality select
        if playbackMethod == '2':
            if len(urls) > 0:
                selectedIndex = xbmcgui.Dialog().select(
                    'Select Quality', [(sourceItem[0] or '?') for sourceItem in urls]
                )
                if selectedIndex != -1:
                    mediaURL = urls[selectedIndex][1]

    if mediaURL:
        mediaURL = mediaURL.replace('\/', '/')

    return mediaURL


def play_video(name, url, iconimage, play=2):

    url = resolver(url)

    if url:

        li = xbmcgui.ListItem(name, path=url)
        li.setArt({"icon": iconimage, "thumb": iconimage})
        li.setInfo(type='video', infoLabels={'Title': name, 'plot': ''})

        if play == 1:
            xbmc.Player().play(item=url, listitem=li)
        elif play == 2:
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)

    else:
        xbmcgui.Dialog().ok( 'Error', 'Video not found' )


def search_items(url,cat):
    vq = get_search_string(heading="Search")
    if ( not vq ): return False, 0
    title = urllib.parse.quote_plus(vq)
    pagination(url,1,cat,title)


def getFavorites():

    try:
        items = json.loads(open(favorites).read())
    except:
        items = ''

    try:
        total = len(items)
        if int(total) > 0:
            for i in items:
                name = i[0]
                url = i[1]
                mode = i[2]
                iconimage = i[3]
                fanArt = i[4]
                description = i[5]
                cat = i[6]
                folder = i[7]
                if folder == 'True':
                    folder = True
                else:
                    folder = False
                play = i[8]

                addDir(name.encode('utf-8', 'ignore'),url.encode('utf-8'),mode,str(iconimage),str(fanArt),str(description).encode('utf-8', 'ignore'),cat.encode('utf-8'),folder,True,int(play))
            SetView('WideList')
            xbmcplugin.endOfDirectory(PLUGIN_ID)
        else:
            xbmcgui.Dialog().ok('[B]'+xbmc.getLocalizedString(14117)+'[/B]',__language__(30155))
    except:
        SetView('WideList')
        xbmcplugin.endOfDirectory(PLUGIN_ID)


def addFavorite(name,url,fav_mode,iconimage,fanart,description,cat,folder,play):

    if os.path.exists(favorites)==False:
        addonID = xbmcaddon.Addon().getAddonInfo('id')
        addon_data_path = xbmcvfs.translatePath(os.path.join('special://home/userdata/addon_data', addonID))
        if os.path.exists(addon_data_path)==False:
            os.mkdir(addon_data_path)
        xbmc.sleep(7)
        favList = []
    else:
        saved = open(favorites).read()
        favList = json.loads(saved)

    favList.append((name,url,fav_mode,iconimage,fanart,description,cat,folder,play))
    a = open(favorites, "w")
    a.write(json.dumps(favList))
    a.close()
    notify(__language__(30152),name,iconimage)


def rmFavorite(name):
    data = json.loads(open(favorites).read())
    for index in range(len(data)):
        if data[index][0]==name:
            del data[index]
            b = open(favorites, "w")
            b.write(json.dumps(data))
            b.close()
            break
    notify(__language__(30154), name)


def addDir(name,url,mode,iconimage,fanart,description,cat,folder=True,favorite=False,play=False):

    link = PLUGIN_URL + "?url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)+"&fanart="+urllib.parse.quote_plus(fanart)+"&iconimage="+urllib.parse.quote_plus(iconimage)+"&description="+urllib.parse.quote_plus(description)+"&cat="+urllib.parse.quote_plus(cat)
    if play:
        link = link + "&play="+str(play)
        
    li=xbmcgui.ListItem(name)
    if folder:
        li.setArt({'icon': 'DefaultFolder.png', 'thumb': iconimage})
    else:
        li.setArt({'icon': 'DefaultVideo.png', 'thumb': iconimage})
    if play == 2 and mode == 4:
        li.setProperty('IsPlayable', 'true')
    li.setInfo(type='Video', infoLabels={'Title': name, 'Plot': description})
    if fanart > '':
        li.setProperty('fanart_image', fanart)
    else:
        li.setProperty('fanart_image', HOME_DIR+'fanart.jpg')

    if favorite:
        try:
            name_fav = json.dumps(name)
        except:
            name_fav = name
        try:
            contextMenu = []
            if name_fav in FAV:
                contextMenu.append((__language__(30153),'RunPlugin(%s?mode=6&name=%s)'%(sys.argv[0], urllib.parse.quote_plus(name))))
            else:
                fav_params = ('%s?mode=5&name=%s&url=%s&iconimage=%s&fanart=%s&description=%s&cat=%s&folder=%s&play=%s&fav_mode=%s'%(sys.argv[0], urllib.parse.quote_plus(name), urllib.parse.quote_plus(url), urllib.parse.quote_plus(iconimage), urllib.parse.quote_plus(fanart), urllib.parse.quote_plus(description), urllib.parse.quote_plus(cat), urllib.parse.quote_plus(str(folder)), urllib.parse.quote_plus(str(play)), str(mode)))
                contextMenu.append((__language__(30151),'RunPlugin(%s)' %fav_params))
            li.addContextMenuItems(contextMenu)
        except:
            pass
    xbmcplugin.addDirectoryItem(handle=PLUGIN_ID, url=link, listitem=li, isFolder=folder)


def SetView(name):

    if name == 'Fanart':
        view_num = 502
    elif name == 'Wall':
        view_num = 500
    elif name == 'WideList':
        view_num = 55
    elif name == 'InfoWall':
        view_num = 54
    elif name == 'Shift':
        view_num = 53
    elif name == 'Poster':
        view_num = 51
    elif name == 'List':
        view_num = 50
    else:
        view_num = 0

    if view_num > 0:
        try:
            xbmc.executebuiltin('Container.SetViewMode(' + str( view_num ) + ')')
        except:
            pass


def get_params():
    return dict(urllib.parse.parse_qsl(sys.argv[2][1:], keep_blank_values=True))


def main():

    params=get_params()

    try:
        url=urllib.parse.unquote_plus(params["url"])
    except:
        url=None
    try:
        name=urllib.parse.unquote_plus(params["name"])
    except:
        name=None
    try:
        iconimage=urllib.parse.unquote_plus(params["iconimage"])
    except:
        iconimage=None
    try:
        mode=int(params["mode"])
    except:
        mode=None
    try:
        fanart=urllib.parse.unquote_plus(params["fanart"])
    except:
        fanart=None
    try:
        description=urllib.parse.unquote_plus(params["description"])
    except:
        description=None

    try:
        subtitle=urllib.parse.unquote_plus(params["subtitle"])
    except:
        subtitle=None
    try:
        cat=urllib.parse.unquote_plus(params["cat"])
    except:
        cat=None
    try:
        search=urllib.parse.unquote_plus(params["search"])
    except:
        search=None
    try:
        page=int(params["page"])
    except:
        page=1
    try:
        folder=urllib.parse.unquote_plus(params["folder"])
    except:
        folder=None
    try:
        fav_mode=int(params["fav_mode"])
    except:
        fav_mode=None
    try:
        play=int(params["play"])
    except:
        play=1

    if mode==None:
        home_menu()
    elif mode==1:
        search_menu()
    elif mode==2:
        search_items(url,cat)
    elif mode==3:
        if search and search !=None:
            pagination(url,page,cat,search)
        else:
            pagination(url,page,cat)
    elif mode==4:
        play_video(name, url, iconimage, play)
    elif mode==5:
        try:
            name = name.split('\\ ')[1]
        except:
            pass
        try:
            name = name.split('  - ')[0]
        except:
            pass
        addFavorite(name,url,fav_mode,iconimage,fanart,description,cat,str(folder),str(play))
    elif mode==6:
        try:
            name = name.split('\\ ')[1]
        except:
            pass
        try:
            name = name.split('  - ')[0]
        except:
            pass
        rmFavorite(name)
    elif mode==7:
        getFavorites()
    elif mode==8:
        xbmcaddon.Addon().openSettings()


if __name__ == "__main__":
	main()
