# -*- coding: utf-8 -*-
import sys, re, os
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs
import six

from six.moves import urllib

from resources.general import *
from resources.md5ex import *


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

lang = ADDON.getSetting('lang')
r_username = ADDON.getSetting('username')
r_password = ADDON.getSetting('password')

if six.PY2:
    favorites = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'favorites.dat'))
else:
    favorites = xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'favorites.dat'))


def createFavorites():
    addonID = ADDON.getAddonInfo('id')
    if six.PY2:
        addon_data_path = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    else:
        addon_data_path = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    if os.path.exists(addon_data_path)==False:
        os.mkdir(addon_data_path)
    xbmc.sleep(1)


def loadFavorites( return_string = False ):

    if os.path.exists(favorites):
        fav_str = open(favorites).read()
        if return_string:
            return fav_str
        if fav_str:
            return json.loads( fav_str )
    else:
        createFavorites()

    if return_string:
            return ''
    else:
        return []


def to_unicode(text, encoding='utf-8', errors='strict'):
    # Force text to unicode
    if isinstance(text, bytes):
        return text.decode(encoding, errors=errors)
    return text


def get_search_string(heading='', message=''):
    # Ask the user for a search string
    search_string = None
    keyboard = xbmc.Keyboard(message, heading)
    keyboard.doModal()
    if keyboard.isConfirmed():
        search_string = to_unicode(keyboard.getText())
    return search_string


# main menu
def home_menu():

    # Search
    addDir( xbmc.getLocalizedString(137), '', 1, MEDIA_DIR + 'search.png', '', '' ,'' )
    # Favorites
    addDir( xbmc.getLocalizedString(1036), '', 7, MEDIA_DIR + 'favorite.png', '', '', '' )

    if r_username and r_password:
        # subscriptions
        addDir( 'Subscriptions', BASE_URL + '/subscriptions', 3, MEDIA_DIR + 'favorite.png', '', '', 'other' )
        # subscriptions
        addDir( 'Following', BASE_URL + '/', 3, MEDIA_DIR + 'favorite.png', '', '', 'following' )

    # News
    addDir( xbmc.getLocalizedString(29916), BASE_URL + '/category/news', 3, MEDIA_DIR + 'news.png', '', '', 'other' )
    # Viral
    addDir( __language__(30050), BASE_URL + '/category/viral', 3, MEDIA_DIR + 'viral.png', '', '', 'other' )
    # Podcasts
    addDir( __language__(30051), BASE_URL + '/category/podcasts', 3, MEDIA_DIR +'podcast.png','','','other')
    # Battle Leaderboard
    addDir( __language__(30052), BASE_URL + '/battle-leaderboard', 3, MEDIA_DIR + 'leader.png', '', '', 'top' )
    # Entertainment
    addDir( __language__(30053), BASE_URL + '/category/entertainment', 3, MEDIA_DIR + 'entertaiment.png', '', '', 'other' )
    # Sports
    addDir( xbmc.getLocalizedString(19548), BASE_URL + '/category/sports', 3, MEDIA_DIR + 'sports.png', '', '', 'other' )
    # Science
    addDir( xbmc.getLocalizedString(29948), BASE_URL + '/category/science', 3, MEDIA_DIR + 'science.png', '', '', 'other' )
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
    addDir( __language__(30100), BASE_URL + '/search/video?q=', 2, MEDIA_DIR + 'search.png', '', '', 'video' )
    # Search Channel
    addDir( __language__(30101), BASE_URL + '/search/channel?q=',2,MEDIA_DIR + 'search.png', '', '', 'channel' )
    # Search User
    addDir( __language__(30102), BASE_URL + '/search/channel?q=',2,MEDIA_DIR + 'search.png', '', '', 'user' )
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

            name = __language__(30150) + " " + str( page )
            li=xbmcgui.ListItem(name)

            linkParams = {
                'url': url,
                'mode': '3',
                'name': name,
                'page': str( page ),
                'cat': cat,
            }

            link = buildURL( linkParams )

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
    headers = None

    if 'subscriptions' in url or cat == 'following':
        if not ADDON.getSetting('session'):
            login()
        headers = { 'cookie': 'u_s=' + ADDON.getSetting('session')}

    data = getRequest(url, None, headers)

    if 'search' in url:
        if cat == 'video':
            amount = create_dir_list( data, cat, 'video', True, 1 )
        else:
            amount = create_dir_list( data, cat, 'channel', True )
    elif cat in { 'channel', 'user', 'top', 'other' }:
        amount = create_dir_list( data, cat, 'video', False, 2 )
    elif cat == 'following':
        amount = create_dir_list( data, cat, 'following', False, 2 )

    return amount


def create_dir_list( data, cat, type='video', search = False, play=False ):

    amount = 0

    if type == 'video':
        videos = re.compile('a href=([^\>]+)><div class=\"(?:[^\"]+)\"><img class=\"video-item--img\" src=(https:\/\/.+?) alt=(?:[^\>]+)>(?:<span class=\"video-item--watching\">[^\<]+</span>)?(?:<div class=video-item--overlay-rank>(?:[0-9]+)</div>)?</div><(?:[^\>]+)></span></a><div class=\"video-item--info\"><time class=\"video-item--meta video-item--time\" datetime=(.+?)-(.+?)-(.+?)T(?:.+?) title\=\"(?:[^\"]+)\">(?:[^\<]+)</time><h3 class=video-item--title>(.+?)</h3><address(?:[^\>]+)><a rel=author class=\"(?:[^\=]+)=(.+?)><div class=ellipsis-1>(.+?)</div>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
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

    elif type == 'following':
        following = re.compile('<a class=\"main-menu-item main-menu-item-channel\" title=\"?(?:[^\"]+)\"? href=([^>]+)>\s*<i class=\'user-image user-image--img user-image--img--id-([^\']+)\'></i>\s*<span class=\"main-menu-item-label main-menu-item-channel-label\">([^<]+)</span>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
        if following:
            amount = len(following)
            for link, img_id, channel_name in following:

                img = str( get_image( data, img_id ) )
                video_title = '[B]' + channel_name + '[/B]'
                #open get url and open player
                addDir( video_title, BASE_URL + link, 3, img, img, '', 'other', True, True, play )
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

    data = loadFavorites()

    try:

        amount = len(data)
        if amount > 0:
            for i in data:
                name = i[0]
                url = i[1]
                mode = i[2]
                iconimage = i[3]
                fanArt = i[4]
                description = i[5]
                cat = i[6]
                folder = ( i[7] == 'True' )
                play = i[8]

                addDir( name, url, mode, str(iconimage), str(fanArt), str(description), cat, folder, True, int(play) )
            SetView('WideList')
            xbmcplugin.endOfDirectory(PLUGIN_ID)
        else:
            xbmcgui.Dialog().ok( xbmc.getLocalizedString(14117), __language__(30155) )

    except:
        SetView('WideList')
        xbmcplugin.endOfDirectory(PLUGIN_ID)


def addFavorite(name, url, fav_mode, iconimage, fanart, description, cat, folder, play):

    data = loadFavorites()
    data.append((name, url, fav_mode, iconimage, fanart, description, cat, folder, play))
    b = open(favorites, 'w')
    b.write(json.dumps(data))
    b.close()
    notify( __language__(30152), name, iconimage )


def rmFavorite(name):
    data = loadFavorites()
    for index in range(len(data)):
        if data[index][0]==name:
            del data[index]
            b = open(favorites, 'w')
            b.write(json.dumps(data))
            b.close()
            break
    notify( __language__(30154), name )


def importFavorites():

    if not xbmcgui.Dialog().yesno(
        'Import Favorites',
        'This will replace the favorites with the plugin.video.rumble.matrix version.\nProceed?',
        nolabel = 'Cancel',
        yeslabel = 'Ok'
    ):
        return

    # no point trying to run this as it didn't exist for python 2
    if six.PY2:
        return

    # make sure path exists
    createFavorites()
    #load matrix favourites
    rumble_matrix_dir = xbmcvfs.translatePath(os.path.join('special://home/userdata/addon_data/plugin.video.rumble.matrix', 'favorites.dat'))
    if os.path.exists(rumble_matrix_dir):
        rumble_matrix = open(rumble_matrix_dir).read()
        if rumble_matrix:
            b = open(favorites, 'w')
            b.write(rumble_matrix)
            b.close()
            notify( 'Imported Favorites' )
            return
    notify( 'Favorites Not Found' )


def login():

    login_hash = MD5Ex()

    # gets salts
    data = getRequest( BASE_URL + '/service.php?name=user.get_salts', {'username': r_username}, [ ( 'Referer', BASE_URL ), ( 'Content-type', 'application/x-www-form-urlencoded' ) ] )
    salt = json.loads(data)['data']['salts']
    # generate hashes
    hashes = login_hash.hash(login_hash.hashStretch(r_password, salt[0], 128) + salt[1]) + ',' + login_hash.hashStretch(r_password, salt[2], 128) + ',' + salt[1]

    # login
    data = getRequest( BASE_URL + '/service.php?name=user.login', {'username': r_username, 'password_hashes':hashes}, [ ( 'Referer', BASE_URL ), ( 'Content-type', 'application/x-www-form-urlencoded' ) ] )

    if data:
        session = json.loads(data)['data']['session']
        if session:
            ADDON.setSetting('session', session)

def resetLoginSession():

    ADDON.setSetting('session', '')
    notify( 'Session has been reset' )

def addDir(name, url, mode, iconimage, fanart, description, cat, folder=True, fav_context=False, play=False):

    linkParams = {
        'url': url,
        'mode': str( mode ),
        'name': name,
        'fanart': fanart,
        'iconimage': iconimage,
        'description': description,
        'cat': cat,
    }

    if play:
        linkParams['play'] = str( play )

    link = buildURL( linkParams )

    li=xbmcgui.ListItem( name )
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
        li.setProperty('fanart_image', HOME_DIR + 'fanart.jpg')

    if fav_context:

        favorite_str = loadFavorites( True )

        try:
            name_fav = json.dumps(name)
        except:
            name_fav = name

        try:
            contextMenu = []

            # checks fave name via string ( I do not like how this is done )
            if name_fav in favorite_str:
                contextMenu.append((__language__(30153),'RunPlugin(%s)' %buildURL( {'mode': '6','name': name} )))
            else:
                fav_params = {
                    'url': url,
                    'mode': '5',
                    'name': name,
                    'fanart': fanart,
                    'iconimage': iconimage,
                    'description': description,
                    'cat': cat,
                    'folder': str(folder),
                    'fav_mode': str(mode),
                    'play': str(play),
                }

                contextMenu.append((__language__(30151),'RunPlugin(%s)' %buildURL( fav_params )))
            li.addContextMenuItems(contextMenu)
        except:
            pass

    xbmcplugin.addDirectoryItem(handle=PLUGIN_ID, url=link, listitem=li, isFolder=folder)


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
            pagination(url, page, cat, search)
        else:
            pagination(url, page, cat)
    elif mode==4:
        play_video(name, url, iconimage, play)
    elif mode==5:
        if '\\ ' in name:
            name = name.split('\\ ')[1]
        if '  - ' in name:
            name = name.split('  - ')[0]
        addFavorite( name, url, fav_mode, iconimage, fanart, description, cat, str(folder), str(play) )
    elif mode==6:
        if '\\ ' in name:
            name = name.split('\\ ')[1]
        if '  - ' in name:
            name = name.split('  - ')[0]
        rmFavorite( name )
    elif mode==7:
        getFavorites()
    elif mode==8:
        ADDON.openSettings()
    elif mode==9:
        importFavorites()
    elif mode==10:
        resetLoginSession()

if __name__ == "__main__":
	main()
