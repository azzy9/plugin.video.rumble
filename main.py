# -*- coding: utf-8 -*-
import sys
import re
import os

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs

import six
from six.moves import urllib

from lib.general import *
from lib.rumble_user import RumbleUser
from lib.comments import CommentWindow

try:
    import json
except ImportError:
    import simplejson as json

BASE_URL = 'https://rumble.com'
PLUGIN_URL = sys.argv[0]
PLUGIN_ID = int(sys.argv[1])
PLUGIN_NAME = PLUGIN_URL.replace('plugin://','')

ADDON = xbmcaddon.Addon()
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')

HOME_DIR = 'special://home/addons/' + PLUGIN_NAME
RESOURCE_DIR = HOME_DIR + 'resources/'
MEDIA_DIR = RESOURCE_DIR + 'media/'

KODI_VERSION = float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4])
DATE_FORMAT = ADDON.getSetting('date_format')

RUMBLE_USER = RumbleUser()

if six.PY2:
    favorites = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'favorites.dat'))
else:
    favorites = xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'favorites.dat'))


def favorites_create():

    """ creates favorite directory if doesn't exist """

    if six.PY2:
        addon_data_path = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    else:
        addon_data_path = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

    if os.path.exists(addon_data_path) is False:
        os.mkdir(addon_data_path)

    xbmc.sleep(1)


def favorites_load( return_string = False ):

    """ load favourites from file into variable """

    if os.path.exists( favorites ):
        fav_str = open( favorites ).read()
        if return_string:
            return fav_str
        if fav_str:
            return json.loads( fav_str )
    else:
        favorites_create()

    # nothing to load, return type necessary
    if return_string:
        return ''

    return []


def to_unicode( text, encoding='utf-8', errors='strict' ):

    """ Forces text to unicode """

    if isinstance(text, bytes):
        return text.decode(encoding, errors=errors)

    return text


def get_search_string( heading='', message='' ):

    """ Ask the user for a search string """

    search_string = None

    keyboard = xbmc.Keyboard(message, heading)
    keyboard.doModal()

    if keyboard.isConfirmed():
        search_string = to_unicode(keyboard.getText())

    return search_string


def home_menu():

    """ Creates home menu """

    # Search
    add_dir( get_string(137), '', 1, MEDIA_DIR + 'search.png', '', '' ,'' )
    # Favorites
    add_dir( get_string(1036), '', 7, MEDIA_DIR + 'favorite.png', '', '', '' )

    if RUMBLE_USER.has_login_details():
        # subscriptions
        add_dir( 'Subscriptions', BASE_URL + '/subscriptions', 3, MEDIA_DIR + 'favorite.png', '', '', 'subscriptions' )
        # subscriptions
        add_dir( 'Following', BASE_URL + '/', 3, MEDIA_DIR + 'favorite.png', '', '', 'following' )

    # News
    add_dir( get_string(29916), BASE_URL + '/category/news/recorded', 3, MEDIA_DIR + 'news.png', '', '', 'cat_video' )
    # Viral
    add_dir( get_string(30050), BASE_URL + '/category/viral/recorded', 3, MEDIA_DIR + 'viral.png', '', '', 'cat_video' )
    # Podcasts
    add_dir( get_string(30051), BASE_URL + '/category/podcasts/recorded', 3, MEDIA_DIR +'podcast.png','','','cat_video')
    # Battle Leaderboard
    add_dir( get_string(30052), BASE_URL + '/battle-leaderboard/recorded', 3, MEDIA_DIR + 'leader.png', '', '', 'top' )
    # Entertainment
    add_dir( get_string(30053), BASE_URL + '/category/entertainment/recorded', 3, MEDIA_DIR + 'entertaiment.png', '', '', 'cat_video' )
    # Sports
    add_dir( get_string(19548), BASE_URL + '/category/sports/recorded', 3, MEDIA_DIR + 'sports.png', '', '', 'cat_video' )
    # Science
    add_dir( get_string(29948), BASE_URL + '/category/science/recorded', 3, MEDIA_DIR + 'science.png', '', '', 'cat_video' )
    # Technology
    add_dir( get_string(30054), BASE_URL + '/category/technology/recorded', 3, MEDIA_DIR + 'technology.png', '', '', 'cat_video' )
    # Vlogs
    add_dir( get_string(30055), BASE_URL + '/category/vlogs/recorded', 3, MEDIA_DIR + 'vlog.png', '', '', 'cat_video' )
    # Settings
    add_dir( get_string(5), '', 8, MEDIA_DIR + 'settings.png', '', '', '' )

    view_set('WideList')
    xbmcplugin.endOfDirectory(PLUGIN_ID, cacheToDisc=False)

def search_menu():

    """ Creates search menu """

    # Search Video
    add_dir( get_string(30100), BASE_URL + '/search/video?q=', 2, MEDIA_DIR + 'search.png', '', '', 'video' )
    # Search Channel
    add_dir( get_string(30101), BASE_URL + '/search/channel?q=', 2, MEDIA_DIR + 'search.png', '', '', 'channel' )
    # Search User
    add_dir( get_string(30102), BASE_URL + '/search/channel?q=', 2, MEDIA_DIR + 'search.png', '', '', 'user' )
    view_set('WideList')
    xbmcplugin.endOfDirectory(PLUGIN_ID)


def pagination( url, page, cat, search=False ):

    """ list directory items then show pagination """

    if url > '':

        page = int(page)
        page_url = url
        paginated = True

        if page == 1:
            if search:
                page_url = url + search
        elif search and cat == 'video':
            page_url = url + search + "&page=" + str( page )
        elif cat in {'channel', 'cat_video', 'user', 'other', 'subscriptions' }:
            page_url = url + "?page=" + str( page )

        if cat == 'following':
            paginated = False

        amount = list_rumble( page_url, cat )

        if paginated and amount > 15 and page < 10:

            # for next page
            page = page + 1

            name = get_string(30150) + " " + str( page )
            list_item = xbmcgui.ListItem(name)

            link_params = {
                'url': url,
                'mode': '3',
                'name': name,
                'page': str( page ),
                'cat': cat,
            }

            link = build_url( link_params )

            if search and cat == 'video':
                link = link + "&search=" + urllib.parse.quote_plus(search)

            xbmcplugin.addDirectoryItem(PLUGIN_ID, link, list_item, True)

    view_set('WideList')
    xbmcplugin.endOfDirectory(PLUGIN_ID)


def get_image( data, image_id ):

    """ method to get an image from scraped page's CSS from the image ID """

    image_re = re.compile(
        "i.user-image--img--id-" + str( image_id ) + ".+?{\s*background-image: url(.+?);",
        re.MULTILINE|re.DOTALL|re.IGNORECASE
    ).findall(data)

    if image_re != []:
        image = str(image_re[0]).replace('(', '').replace(')', '')
    else:
        image = ''

    return image


def list_rumble( url, cat ):

    """ Method to get and display items from Rumble """

    amount = 0
    headers = None

    if 'subscriptions' in url or cat == 'following':
        # make sure there is a session
        # result is stored in a cookie
        RUMBLE_USER.has_session()

    data = request_get(url, None, headers)

    if 'search' in url:
        if cat == 'video':
            amount = dir_list_create( data, cat, 'video', True, 1 )
        else:
            amount = dir_list_create( data, cat, 'channel', True )
    elif cat in { 'subscriptions', 'cat_video' }:
        amount = dir_list_create( data, cat, 'cat_video', False, 2 )
    elif cat in { 'channel', 'user', 'top', 'other' }:
        amount = dir_list_create( data, cat, 'video', False, 2 )
    elif cat == 'following':
        amount = dir_list_create( data, cat, 'following', False, 2 )

    return amount


def dir_list_create( data, cat, video_type='video', search = False, play=0 ):

    """ create and display dir list based upon type """

    amount = 0

    if video_type == 'video':
        videos = re.compile(r'a href=([^\>]+)><div class=\"(?:[^\"]+)\"><img class=\"video-item--img\" src=(https:\/\/.+?) alt=(?:[^\>]+)>(?:<span class=\"video-item--watching\">[^\<]+</span>)?(?:<div class=video-item--overlay-rank>(?:[0-9]+)</div>)?</div><(?:[^\>]+)></span></a><div class=\"video-item--info\"><time class=\"video-item--meta video-item--time\" datetime=(.+?)-(.+?)-(.+?)T(?:.+?) title\=\"(?:[^\"]+)\">(?:[^\<]+)</time><h3 class=video-item--title>(.+?)</h3><address(?:[^\>]+)><a rel=author class=\"(?:[^\=]+)=(.+?)><div class=ellipsis-1>(.+?)</div>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
        if videos:
            amount = len(videos)
            for link, img, year, month, day, title, channel_link, channel_name in videos:
                if '<svg' in channel_name:
                    channel_name = channel_name.split('<svg')[0] + " (Verified)"

                video_title = '[B]' + clean_text( title ) + '[/B]\n[COLOR gold]' + channel_name + '[/COLOR] - [COLOR lime]' + get_date_formatted( DATE_FORMAT, year, month, day ) + '[/COLOR]'
                #open get url and open player
                add_dir( video_title, BASE_URL + link, 4, str(img), str(img), '', cat, False, True, play, { 'name' : channel_link, 'subscribe': True }  )

    elif video_type == 'cat_video':
        videos = re.compile(r'<img\s*class=\"videostream__image\"\s*src=(.+?)alt=(?:\"[^\"]+\"|[^\"\s]+)\s*(?:[^\>]+)>\s*<div class=\"videostream__info\">\s*<div class=\"videostream__badge videostream__status videostream__status--duration\">\s*(.+?)\s*</div>\s*</div>\s*</div>\s*</a>\s*<div class=\"videostream__footer\">\s*<a\s*class=\"link\"\s*href=([^\>]+)>\s*<h3 class=\"videostream__title clamp-2\">\s*([^\<]+)</h3>\s*</a>\s*<address class=\"channel\">\s*<a\s*rel=\"author\"\s*class=\"channel__link link ([^\"]+)\"\s*href=([^\>]+)>\s*(?:<span class=\"channel__avatar channel__letter\">\s*[a-z]\s*</span>|<div class=\"channel__avatar channel__border\">\s*<div\s*(?:[^>]+)>\s*</div>\s*</div>)\s*<div>\s*<div class=\"channel__data\">\s*<span class=\"channel__name clamp-1\">\s*([^\<]+)</span>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
        if videos:
            amount = len(videos)
            for img, video_length, link, title, img_id, channel_link, channel_name in videos:
                if '<svg' in channel_name:
                    channel_name = channel_name.split('<svg')[0] + " (Verified)"

                video_title = '[B]' + clean_text( title.strip() ) + '[/B]\n[COLOR gold]' + channel_name.strip().strip('"') + '[/COLOR]'
                #open get url and open player
                add_dir( video_title, BASE_URL + link.strip(), 4, str(img.strip()), str(img.strip()), '', cat, False, True, play, { 'name' : channel_link.strip(), 'subscribe': True }  )

    elif video_type == 'following':
        following = re.compile(r'<a\s*class=\"main-menu-item-channel\s*(?:main-menu-item-channel-is-live)?\"\s*title=\"?(?:[^\"]+)\"?\s*href=([^>\s]+)(?:\s*data-js=\"main_menu_live_channel\")?\s*>\s*<div class=\"main-menu-item-channel-label-wrapper\">\s*<i class=\'user-image (?:user-image--img user-image--img--id-([^\s\']+)\s*(?:channel-live)?\')?(?:user-image--letter\s*(?:channel-live)\' data-letter=([a-zA-Z]))? data-js=user-image>\s*</i>\s*<span class=\"main-menu-item-label main-menu-item-channel-label\">([^<]+)</span>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
        if following:
            amount = len(following)
            for link, img_id, img_letter, channel_name in following:

                if img_id:
                    img = str( get_image( data, img_id ) )
                else:
                    img = MEDIA_DIR + 'letters/' + img_letter + '.png'
                video_title = '[B]' + channel_name.strip() + '[/B]'
                #open get url and open player
                add_dir( video_title, BASE_URL + link.strip(), 3, img, img, '', 'other', True, True, play, { 'name' : link.strip(), 'subscribe': False } )

    else:
        channels = re.compile(r'a href=(.+?)>\s*<div class=\"channel-item--img\">\s*<i class=\'user-image (?:user-image--img user-image--img--id-([^\']+)\')?(?:user-image--letter\' data-letter=([a-zA-Z]))? data-js=user-image>\s*</i>\s*</div>\s*<h3 class=channel-item--title>(.+?)</h3>\s*<span class=channel-item--subscribers>(.+?) followers</span>',re.DOTALL).findall(data)
        if channels:
            amount = len(channels)
            for link, img_id, img_letter, channel_name, subscribers in channels:

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
                if img_id:
                    img = str( get_image( data, img_id ) )
                else:
                    img = MEDIA_DIR + 'letters/' + img_letter + '.png'
                video_title = '[B]' + channel_name + '[/B]\n[COLOR palegreen]' + subscribers + '[/COLOR] [COLOR yellow]' + get_string(30156) + '[/COLOR]'
                #open get url and open player
                add_dir( video_title, BASE_URL + link, 3, img, img, '', cat, True, True, play, { 'name' : link, 'subscribe': True } )

    return amount

def get_video_id( url ):

    """ gets a video id from a URL, helps in resolving """

    data = request_get(url)

    # gets embed id from embed url
    video_id = re.compile(
        ',\"embedUrl\":\"' + BASE_URL + '/embed/(.*?)\/\",',
        re.MULTILINE|re.DOTALL|re.IGNORECASE
    ).findall(data)

    if video_id:
        return video_id[0]
    return False

def resolver( url ):

    """ Resolves a URL for rumble & returns resolved link to video """

    # playback options - 0: large to small, 1: small to large, 2: quality select
    playback_method = ADDON.getSetting('playbackMethod')

    media_url = False

    if playback_method == '2':
        urls = []

    video_id = get_video_id( url )

    if video_id:

        # use site api to get video urls
        # TODO: use as dict / array instead of using regex to get URLs
        data = request_get(BASE_URL + '/embedJS/u3/?request=video&ver=2&v=' + video_id)
        sizes = [ '1080', '720', '480', '360', 'hls' ]

        # reverses array - small to large
        if playback_method == '1':
            sizes = sizes[::-1]

        for quality in sizes:

            # get urls for quality
            matches = re.compile(
                '"' + quality + '".+?url.+?:"(.*?)"',
                re.MULTILINE|re.DOTALL|re.IGNORECASE
            ).findall(data)

            if matches:
                if playback_method == '2':
                    urls.append(( quality, matches[0] ))
                else:
                    media_url = matches[0]
                    break

        # quality select
        if playback_method == '2':
            if len(urls) > 0:
                selected_index = xbmcgui.Dialog().select(
                    'Select Quality', [(sourceItem[0] or '?') for sourceItem in urls]
                )
                if selected_index != -1:
                    media_url = urls[selected_index][1]

    if media_url:
        media_url = media_url.replace('\/', '/')

    return media_url


def play_video( name, url, iconimage, play=2 ):

    """ method to play video """

    # get video link
    url = resolver(url)

    if url:

        # Use HTTP
        if ADDON.getSetting('useHTTP') == 'true':
            url = url.replace('https://', 'http://', 1)

        list_item = xbmcgui.ListItem(name, path=url)
        list_item.setArt({'icon': iconimage, 'thumb': iconimage})

        if KODI_VERSION > 19.8:
            vidtag = list_item.getVideoInfoTag()
            vidtag.setTitle(name)
        else:
            list_item.setInfo(type='video', infoLabels={'Title': name, 'plot': ''})

        if play == 1:
            xbmc.Player().play(item=url, listitem=list_item)
        elif play == 2:
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)

    else:
        xbmcgui.Dialog().ok( 'Error', 'Video not found' )


def search_items( url, cat ):

    """ Searches rumble  """

    search_str = get_search_string(heading="Search")

    if not search_str:
        return False, 0

    title = urllib.parse.quote_plus(search_str)

    pagination( url, 1, cat, title )


def favorites_show():

    """  Displays favorites """

    data = favorites_load()

    try:

        amount = len(data)
        if amount > 0:
            for i in data:
                name = i[0]
                url = i[1]
                mode = i[2]
                iconimage = i[3]
                fan_art = i[4]
                description = i[5]
                cat = i[6]
                folder = ( i[7] == 'True' )
                play = i[8]

                add_dir( name, url, mode, str(iconimage), str(fan_art), str(description), cat, folder, True, int(play) )
            view_set('WideList')
            xbmcplugin.endOfDirectory(PLUGIN_ID)
        else:
            xbmcgui.Dialog().ok( get_string(14117), get_string(30155) )

    except Exception:
        view_set('WideList')
        xbmcplugin.endOfDirectory(PLUGIN_ID)


def favorite_add(name, url, fav_mode, iconimage, fanart, description, cat, folder, play):

    """ add favorite from name """

    data = favorites_load()
    data.append((name, url, fav_mode, iconimage, fanart, description, cat, folder, play))
    fav_file = open( favorites, 'w' )
    fav_file.write(json.dumps(data))
    fav_file.close()

    notify( get_string(30152), name, iconimage )


def favorite_remove( name ):

    """ remove favorite from name """

    # TODO: remove via something more unique instead
    # TODO: remove via a method that doesn't require to loop through all favorites

    data = favorites_load()

    if data:
        for index in range(len(data)):
            if data[index][0] == name:
                del data[index]
                fav_file = open( favorites, 'w' )
                fav_file.write(json.dumps(data))
                fav_file.close()
                break

    notify( get_string(30154), name )



def favorites_import():

    """ Due to plugin name change from original fork, the favorites will need to be imported """

    if not xbmcgui.Dialog().yesno(
        'Import Favorites',
        'This will replace the favorites with the plugin.video.rumble.matrix version.\nProceed?',
        nolabel = 'Cancel',
        yeslabel = 'Ok'
    ):
        return

    # no point trying to run this as it didn't exist for python 2
    if six.PY2:
        notify( 'Favorites Not Found' )
        return

    # make sure path exists
    favorites_create()

    #load matrix favourites
    rumble_matrix_dir = xbmcvfs.translatePath(os.path.join('special://home/userdata/addon_data/plugin.video.rumble.matrix', 'favorites.dat'))

    if os.path.exists(rumble_matrix_dir):
        rumble_matrix = open( rumble_matrix_dir ).read()

        if rumble_matrix:
            fav_file = open( favorites, 'w' )
            fav_file.write(rumble_matrix)
            fav_file.close()
            notify( 'Imported Favorites' )
            return

    notify( 'Favorites Not Found' )


def login_session_reset():

    """ Forces a rumble session reset """

    RUMBLE_USER.reset_session_details()
    notify( 'Session has been reset' )


def subscribe( name, action ):

    """ Attempts to (un)subscribe to rumble channel """

    # make sure we have a session
    if RUMBLE_USER.has_session():

        action_type = False
        if '/user/' in name:
            name = name.replace( '/user/', '' )
            action_type = 'user'
        elif '/c/' in name:
            name = name.replace( '/c/', '' )
            action_type = 'channel'

        if action_type:

            # subscribe to action
            data = RUMBLE_USER.subscribe( action, action_type, name )

            if data:

                # Load data from JSON
                data = json.loads(data)

                # make sure everything looks fine
                if data.get( 'user', False ) and data.get( 'data', False ) \
                    and data[ 'user' ][ 'logged_in' ] and data[ 'data' ][ 'thumb' ]:

                    if action == 'subscribe':
                        notify( 'Subscribed to ' + name, None, data[ 'data' ][ 'thumb' ] )
                    else:
                        notify( 'Unubscribed to ' + name, None, data[ 'data' ][ 'thumb' ] )

                    return True

    notify( 'Unable to to perform action' )

    return False


def add_dir(name, url, mode, iconimage, fanart, description, cat, folder=True, fav_context=False, play=0, subscribe_context=False):

    """ Adds directory items """

    link_params = {
        'url': url,
        'mode': str( mode ),
        'name': name,
        'fanart': fanart,
        'iconimage': iconimage,
        'description': description,
        'cat': cat,
    }

    context_menu = []

    if play:
        link_params['play'] = str( play )

    link = build_url( link_params )

    list_item = xbmcgui.ListItem( name )
    if folder:
        list_item.setArt({'icon': 'DefaultFolder.png', 'thumb': iconimage})
    else:
        list_item.setArt({'icon': 'DefaultVideo.png', 'thumb': iconimage})

    if play == 2 and mode == 4:
        list_item.setProperty('IsPlayable', 'true')
        context_menu.append((get_string(30158), 'Action(Queue)'))

    if KODI_VERSION > 19.8:
        vidtag = list_item.getVideoInfoTag()
        vidtag.setMediaType('video')
        vidtag.setTitle(name)
        vidtag.setPlot(description)
    else:
        list_item.setInfo(type='Video', infoLabels={'Title': name, 'Plot': description})

    if fanart > '':
        list_item.setProperty('fanart_image', fanart)
    else:
        list_item.setProperty('fanart_image', HOME_DIR + 'fanart.jpg')

    if RUMBLE_USER.has_login_details():

        if subscribe_context:
            if subscribe_context['subscribe']:
                context_menu.append(('Subscribe to ' + subscribe_context['name'],'RunPlugin(%s)' % build_url( {'mode': '11','name': subscribe_context['name'], 'cat': 'subscribe'} )))
            else:
                context_menu.append(('Unsubscribe to ' + subscribe_context['name'],'RunPlugin(%s)' % build_url( {'mode': '11','name': subscribe_context['name'], 'cat': 'unsubscribe'} )))

        if play == 2 and mode == 4:
            context_menu.append(('Comments','RunPlugin(%s)' % build_url( {'mode': '12','url': url} )))

    if fav_context:

        favorite_str = favorites_load( True )

        try:
            name_fav = json.dumps(name)
        except Exception:
            name_fav = name

        try:

            # checks fav name via string (I do not like how this is done, so will redo in future)
            if name_fav in favorite_str:
                context_menu.append((get_string(30153),'RunPlugin(%s)' % build_url( {'mode': '6','name': name} )))
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

                context_menu.append((get_string(30151),'RunPlugin(%s)' %build_url( fav_params )))
        except Exception:
            pass

    if context_menu:
        list_item.addContextMenuItems(context_menu)

    xbmcplugin.addDirectoryItem(handle=PLUGIN_ID, url=link, listitem=list_item, isFolder=folder)

def comments_show( url ):

    """ Retrieves and shows video's comments in a modal """

    video_id = get_video_id( url )

    if video_id:
        win = CommentWindow(
            'addon-rumble-comments.xml',
            ADDON.getAddonInfo('path'),
            'default',
            video_id=video_id
        )
        win.doModal()
        del win
    else:
        notify( "Cannot find comments", "Comments" )

def main():

    """ main method to start plugin """

    params=get_params()

    mode=int(params.get( 'mode', 0 ))
    page=int(params.get( 'page', 1 ))
    play=int(params.get( 'play', 0 ))
    fav_mode=int(params.get( 'fav_mode', 0 ))

    url = params.get( 'url', None )
    if url:
        url=urllib.parse.unquote_plus(url)

    name = params.get( 'name', None )
    if name:
        name = urllib.parse.unquote_plus(name)

    iconimage=params.get( 'iconimage', None )
    if iconimage:
        iconimage=urllib.parse.unquote_plus(iconimage)

    fanart=params.get( 'fanart', None )
    if fanart:
        fanart=urllib.parse.unquote_plus(fanart)

    description=params.get( 'description', None )
    if description:
        description=urllib.parse.unquote_plus(description)

    subtitle=params.get( 'subtitle', None )
    if subtitle:
        subtitle=urllib.parse.unquote_plus(subtitle)

    cat=params.get( 'cat', None )
    if cat:
        cat=urllib.parse.unquote_plus(cat)

    search=params.get( 'search', None )
    if search:
        search=urllib.parse.unquote_plus(search)

    folder=params.get( 'folder', None )
    if folder:
        folder=urllib.parse.unquote_plus(folder)

    folder=params.get( 'folder', None )
    if folder:
        folder=urllib.parse.unquote_plus(folder)


    if mode==0:
        home_menu()
    elif mode==1:
        search_menu()
    elif mode==2:
        search_items(url,cat)
    elif mode==3:
        if search and search is not None:
            pagination(url, page, cat, search)
        else:
            pagination(url, page, cat)
    elif mode==4:
        play_video(name, url, iconimage, play)
    elif mode in [5,6]:
        if '\\ ' in name:
            name = name.split('\\ ')[1]
        if '  - ' in name:
            name = name.split('  - ')[0]
        if mode == 5:
            favorite_add( name, url, fav_mode, iconimage, fanart, description, cat, str(folder), str(play) )
        else:
            favorite_remove( name )
    elif mode==7:
        favorites_show()
    elif mode==8:
        ADDON.openSettings()
    elif mode==9:
        favorites_import()
    elif mode==10:
        login_session_reset()
    elif mode==11:
        subscribe(name, cat)
    elif mode==12:
        comments_show(url)

if __name__ == "__main__":
    main()
