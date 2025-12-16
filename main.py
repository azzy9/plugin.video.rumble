# -*- coding: utf-8 -*-
import html
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

from datetime import datetime

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

DATE_FORMAT = ADDON.getSetting('date_format')
PLAYBACK_CAP = ADDON.getSetting('playback_cap')

RUMBLE_USER = RumbleUser()

if six.PY2:
    favorites = xbmc.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'favorites.dat'))
else:
    favorites = xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'favorites.dat'))

TEMPLATE_TYPES = {
    'channel': 'video',
    'top': 'video',
    'subscriptions': 'grid',
    'cat_video': 'grid',
    'live_stream': 'grid',
    'playlist': 'grid',
    'channel_video': 'grid',
    'user': 'grid',
    'following': 'following',
}

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
    add_dir( get_string(137), '', 1, { 'thumb': 'search.png' } )
    # Favorites
    add_dir( get_string(1036), '', 7, { 'thumb': 'favorite.png' } )

    if RUMBLE_USER.has_login_details():
        # Subscriptions
        add_dir( 'Subscriptions', BASE_URL + '/subscriptions', 3, { 'thumb': 'favorite.png' }, {}, 'subscriptions' )
        # Following
        add_dir( 'Following', BASE_URL + '/followed-channels', 3, { 'thumb': 'favorite.png' }, {}, 'following' )
        # Watch Later
        add_dir( 'Watch Later', BASE_URL + '/playlists/watch-later', 3, { 'thumb': 'favorite.png' }, {}, 'playlist' )

    # Battle Leaderboard
    add_dir( get_string(30050), BASE_URL + '/battle-leaderboard/recorded', 3, { 'thumb': 'leader.png' }, {}, 'top' )

    # Categories
    add_dir( get_string(30051), BASE_URL + '/browse', 3, { 'thumb': 'viral.png' }, {}, 'cat_list' )

    # Live Streams
    add_dir( get_string(30052), BASE_URL + '/browse/live', 3, { 'thumb': 'viral.png' }, {}, 'live_stream' )

    # Settings
    add_dir( get_string(5), '', 8, { 'thumb': 'settings.png' } )

    xbmcplugin.endOfDirectory( PLUGIN_ID, cacheToDisc=False )

def search_menu():

    """ Creates search menu """

    # Search Video
    add_dir( get_string(30100), BASE_URL + '/search/video', 2, { 'thumb': 'search.png' }, {}, 'video' )
    # Search Channel
    add_dir( get_string(30101), BASE_URL + '/search/channel', 2, { 'thumb': 'search.png' }, {}, 'channel' )
    # Search User
    add_dir( get_string(30102), BASE_URL + '/search/channel', 2, { 'thumb': 'search.png' }, {}, 'user' )

    xbmcplugin.endOfDirectory(PLUGIN_ID)


def pagination( url, page, cat, search=False ):

    """ list directory items then show pagination """

    if url > '':

        page = int(page)
        page_url = url
        paginated = True
        query_params = {}

        # check what query params need to be added
        if page == 1:
            if search:
                query_params['q'] = search
        elif search and cat == 'video':
            query_params['q'] = search
            query_params['page'] = str( page )
        elif cat in {'channel', 'channel_video', 'cat_video', 'user', 'subscriptions', 'live_stream' }:
            query_params['page'] = str( page )

        # add query params to link
        if query_params:
            page_url += '&' if '?' in page_url else '?'
            page_url += urllib.parse.urlencode(query_params)

        if cat in { 'following', 'top', 'cat_list' }:
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

    # Fix for favorites & search
    if cat in { 'channel' } and '/c/' in url:
        cat = 'channel_video'

    if 'search' in url:
        if cat == 'video':
            amount = dir_list_create( data, cat, 'video', True, 1 )
        else:
            amount = dir_list_create( data, cat, 'channel', True )
    elif cat == 'cat_list':
        amount = dir_list_create( data, cat, cat, False )
    elif TEMPLATE_TYPES.get( cat, False ):
        amount = dir_list_create( data, cat, TEMPLATE_TYPES[ cat ], False, 2 )

    return amount


def dir_list_create( data, cat, template_type='video', search = False, play=0 ):

    """ create and display dir list based upon type """

    amount = 0

    one_line_titles = ADDON.getSetting('one_line_titles') == 'true'

    if template_type == 'video':
        videos = re.compile(r'href=\"([^\"]+)\"(?:\s*data-event-data=[^\>]+)?><div class=\"(?:[^\"]+)\"><img\s*class=\"video-item--img\s*\"\s*src=\"([^\"]+)\"\s*alt=\"(?:[^\"]+)\"\s*>(?:<span class=\"video-item--watching\">[^\<]+</span>)?(?:<div class=video-item--overlay-rank>(?:[0-9]+)</div>)?</div><(?:[^\>]+)></span></a><div class=\"video-item--info\"><time class=\"video-item--meta video-item--time\" datetime=(.+?)-(.+?)-(.+?)T(?:.+?) title\=\"(?:[^\"]+)\">(?:[^\<]+)</time><h3 class=video-item--title>(.+?)</h3><address(?:[^\>]+)><a rel=author class=\"(?:[^\=]+)=(.+?)><div class=ellipsis-1>(.+?)</div>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
        if videos:
            amount = len(videos)
            for link, img, year, month, day, title, channel_link, channel_name in videos:

                info_labels = {}

                if '<svg' in channel_name:
                    channel_name = channel_name.split('<svg')[0] + " (Verified)"

                info_labels[ 'year' ] = year

                video_title = '[B]' + clean_text( title ) + '[/B]'
                video_title += ' - ' if one_line_titles else '\n'
                video_title += '[COLOR gold]' + channel_name + '[/COLOR] - [COLOR lime]' + get_date_formatted( DATE_FORMAT, year, month, day ) + '[/COLOR]'

                images = { 'thumb': str(img), 'fanart': str(img) }

                #open get url and open player
                add_dir( video_title, BASE_URL + link, 4, images, info_labels, cat, False, True, play, { 'name' : channel_link, 'subscribe': True }  )

    elif template_type == 'grid':

        if cat == 'live_stream':
            videos_regex = r'<div class=\"thumbnail__grid\"\s*role=\"list\">(.*)<nav'
        elif cat == 'playlist':
            videos_regex = r'<ol\s*class=\"videostream__list\"(?:[^>]+)>(.*)</ol>'
        else:
            videos_regex = r'<ol\s*class=\"thumbnail__grid\">(.*)</ol>'
        videos = re.compile(videos_regex, re.DOTALL|re.IGNORECASE).findall(data)

        if videos:
            if cat == 'playlist':
                videos = videos[0].split('"videostream videostream__list-item')
            else:
                videos = videos[0].split('"videostream thumbnail__grid-')

            videos.pop(0)
            amount = len(videos)
            for video in videos:

                video_title = ''
                images = {}
                info_labels = {}
                subscribe_context = False

                title = re.compile(r'<h3(?:[^\>]+)?>(.*?)</h3>', re.DOTALL|re.IGNORECASE).findall(video)
                link = re.compile(r'<a\s*class=\"videostream__link\slink\"\s*draggable=\"false\"\shref=\"([^\"]+)\"', re.DOTALL|re.IGNORECASE).findall(video)
                img = re.compile(r'<img\s*class=\"thumbnail__image\s*\"\s*draggable=\"false\"\s*src=\"([^\"]+)\"', re.DOTALL|re.IGNORECASE).findall(video)

                if title:
                    video_title = '[B]' + clean_text( title[0] ) + '[/B]'
                if 'videostream__status--live' in video:
                    video_title += ' [COLOR red](Live)[/COLOR]'
                if 'videostream__status--upcoming' in video:
                    video_title += ' [COLOR yellow](Upcoming)[/COLOR]'

                channel_name = re.compile(r'<span\sclass="channel__name(?:[^\"]+)" title="(?:[^\"]+)">([^\<]+)</span>(\s*<svg class=channel__verified)?', re.DOTALL|re.IGNORECASE).findall(video)
                channel_link = re.compile(r'<a\s*rel=\"author\"\s*class=\"channel__link\slink\s(?:[^\"]+)\"\s*href=\"([^\"]+)\"\s*>', re.DOTALL|re.IGNORECASE).findall(video)

                if channel_name:

                    video_title += ' - ' if one_line_titles else '\n'
                    video_title += '[COLOR gold]' + clean_text( channel_name[0][0] )
                    if channel_name[0][1]:
                        video_title += " (Verified)"
                    video_title += '[/COLOR]'

                    if channel_link:
                        subscribe_context = { 'name' : channel_link[0], 'subscribe': True }

                date_time = re.compile(r'<time\s*class=\"(?:[^\"]+)\"\s*datetime=\"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})-(\d{2}):(\d{2})\"', re.DOTALL|re.IGNORECASE).findall(video)

                if date_time:
                    info_labels[ 'year' ] = date_time[0][0]
                    video_title += ' - [COLOR lime]' + get_date_formatted( DATE_FORMAT, date_time[0][0], date_time[0][1], date_time[0][2] ) + '[/COLOR]'
                elif template_type == 'live_stream':
                    info_labels[ 'year' ] = datetime.now().year

                if img:
                    images = { 'thumb': str(img[0]), 'fanart': str(img[0]) }

                duration = re.compile(r'videostream__status--duration\"\s*>([^<]+)</div>', re.DOTALL|re.IGNORECASE).findall(video)

                if duration:
                    info_labels[ 'duration' ] = duration_to_secs( duration[0].strip() )

                #open get url and open player
                add_dir( video_title, BASE_URL + link[0], 4, images, info_labels, cat, False, True, play, subscribe_context  )

        return amount

    elif template_type == 'cat_list':
        cat_list = re.compile(r'<a\s*class=\"category__link link\"\s*href=\"([^\"]+)\"\s*>\s*<img\s*class=\"category__image\s*\"\s*src=\"([^\"]+)\"\s*alt=(?:[^\>]+)>\s*<strong class=\"(?:[^\"]+)\">([^\<]+)</strong>', re.DOTALL|re.IGNORECASE).findall(data)
        if cat_list:
            amount = len(cat_list)
            for link, img, title in cat_list:

                cat = 'channel_video'
                images = { 'thumb': str(img), 'fanart': str(img) }

                #open get url and open player
                add_dir( clean_text( title ), BASE_URL + link.strip() + '/videos', 3, images, {}, cat )

    elif template_type == 'following':

        videos_regex = r'<ol\s*class=\"followed-channels__list\">(.*)</ol>'
        videos = re.compile(videos_regex, re.DOTALL|re.IGNORECASE).findall(data)
        if videos:
            videos = videos[0].split('"followed-channel flex items-')

            videos.pop(0)
            amount = len(videos)
            for video in videos:

                video_title = ''
                images = {}

                title = re.compile(r'<span\s*class=\"line-clamp-2\">([^<]+)<\/span>', re.DOTALL|re.IGNORECASE).findall(video)
                followers = re.compile(r'<div\s*class=\"followed-channel__followers(?:[^\"]+)\">([^<]+)</div>', re.DOTALL|re.IGNORECASE).findall(video)
                link = re.compile(r'<a\s*class=\"(?:[^\"]+)\"\s*href=\"(\/(?:c|user)\/[^\"]+)\"\s*>', re.DOTALL|re.IGNORECASE).findall(video)
                img = re.compile(r'<(?:img|span)\s*class=\"channel__image([^\"]*)\"\s*(?:src=\"([^\"]+)\")?', re.DOTALL|re.IGNORECASE).findall(video)
                description = re.compile(r'<div\s*class=\"followed-channel__description(?:[^\"]+)\">\s*<div>([^<]+)</div>\s*</div>', re.DOTALL|re.IGNORECASE).findall(video)

                if title:
                    video_title = '[B]' + clean_text( title[0] ) + '[/B]'

                info_labels = {}

                if description:
                    info_labels[ 'plot' ] = html.unescape(description[0].strip())

                if '<use href="#channel_verified" />' in video:
                    video_title += ' [COLOR gold](Verified)[/COLOR]'

                link = link[0] if link else ""

                if img:
                    if 'channel__letter' in img[0][0]:
                        if title:
                            image_url = MEDIA_DIR + 'letters/' + title[0][0].lower() + '.png'
                        else:
                            image_url = ''
                    else:
                        image_url = img[0][1]

                    images = { 'thumb': str(image_url), 'fanart': str(image_url) }

                    if 'channel__live' in img[0][0]:
                        video_title += ' [COLOR red](Live)[/COLOR]'

                if followers:
                    video_title += ' - ' if one_line_titles else '\n'
                    video_title += '[COLOR green]' + followers[0].strip() + '[/COLOR]'

                cat = 'user'
                if '/user/' not in link:
                    cat = 'channel_video'

                #open get url and open player
                add_dir( video_title, BASE_URL + link, 3, images, info_labels, cat, True, True, play, { 'name' : link, 'subscribe': False } )

    else:

        channels_regex = r'<div class=\"main-and-sidebar\">(.*)</main>'
        channels = re.compile(channels_regex, re.DOTALL|re.IGNORECASE).findall(data)
        if channels:
            channels = channels[0].split('<article')

            channels.pop(0)
            amount = len(channels)
            for channel in channels:

                link = re.compile(r'<a\shref=\"?([^\s]+)\"\sclass=\"(?:[^\"]+)\">', re.DOTALL|re.IGNORECASE).findall(channel)
                link = link[0] if link else ""

                # split channel and user
                if search:
                    if cat == 'channel':
                        if '/c/' not in link:
                            continue
                    else:
                        if '/user/' not in link:
                            continue

                images = {}

                channel_name = re.compile(r'<span\sclass=\"block\struncate\">([^<]+)<\/span>', re.DOTALL|re.IGNORECASE).findall(channel)
                channel_name = channel_name[0] if channel_name else ''

                is_verified = re.compile(r'<title>Verified</title>', re.DOTALL|re.IGNORECASE).findall(channel)
                is_verified = True if is_verified else False

                followers = re.compile(r'<span\sclass=\"(?:[^\"]+)\">\s+([^&<]+)&nbsp;\s*Follower(?:s)?\s+<\/span>', re.DOTALL|re.IGNORECASE).findall(channel)
                followers = followers[0] if followers else "0"
                
                img_id = re.compile(r'user-image--img--id-([^\s]+)\s', re.DOTALL|re.IGNORECASE).findall(channel)
                img_id = img_id[0] if img_id else ''

                if img_id:
                    img = str( get_image( data, img_id ) )
                else:
                    img = MEDIA_DIR + 'letters/' + channel_name[0] + '.png'

                images = { 'thumb': str(img), 'fanart': str(img) }

                video_title = '[B]' + channel_name + '[/B]'
                if is_verified:
                    video_title += ' [COLOR gold](Verified)[/COLOR]'
                video_title += ' - ' if one_line_titles else '\n'
                video_title += '[COLOR palegreen]' + followers + '[/COLOR] [COLOR yellow]' + get_string(30156) + '[/COLOR]'

                #open get url and open player
                add_dir( video_title, BASE_URL + link, 3, images, {}, cat, True, True, play, { 'name' : link, 'subscribe': True } )

    return amount

def get_video_id( url ):

    """
    gets a video id from a URL
    helps in resolving
    """

    data = request_get(url)

    # gets embed id from embed url
    video_id = re.compile(
        ',\"embedUrl\":\"' + BASE_URL + '/embed/(.*?)\/\",',
        re.MULTILINE|re.DOTALL|re.IGNORECASE
    ).findall(data)

    if video_id:
        return video_id[0]
    return False

def get_playlist_video_id( url ):

    """
    gets a playlist video id from a URL
    helps in adding video to playlist
    """

    data = request_get(url)

    # gets embed id from embed url
    video_id = re.compile(
        'data-video-id=\"([0-9]+)\"',
        re.MULTILINE|re.DOTALL|re.IGNORECASE
    ).findall(data)

    if video_id:
        return video_id[0]
    return False

def resolver( url ):

    """ Resolves a URL for rumble & returns resolved resouces """

    urls = []
    subtitles = []

    video_id = get_video_id( url )

    if video_id:

        # use site api to get video urls
        data = request_get(BASE_URL + '/embedJS/u3/?request=video&ver=2&v=' + video_id)
        data = json.loads(data)

        if data :
            types = [ 'mp4', 'webm', 'hls' ]

            ua_streams = data.get('ua', False)

            if ua_streams:
                for stream_type in types:

                    streams = ua_streams.get( stream_type, False )
                    if streams:
                        for quality, stream in streams.items():
                            if stream and stream.get( 'url', False ):
                                urls.append(( quality, stream[ 'url' ] ))
                        break

            # get subtitles
            cc = data.get('cc', False)

            if cc:
                for lang, subs in cc.items():
                    path = subs.get( 'path', False )
                    if path:
                        subtitles.append(( subs.get( 'language', lang ), path ))

            if urls:
                # sort sizes
                urls.sort(reverse=True, key=sort_sizes)

    return { 'urls': urls, 'subtitles': subtitles }

def video_quality_select( urls ):

    """ Resolves a URL for rumble & returns resolved resouces """

    # playback options - 0: high auto, 1: low auto, 2: quality select
    playback_method = int( ADDON.getSetting('playbackMethod') )

    media_url = False

    if urls:

        # m3u8 check
        if len( urls ) == 1 and '.m3u8' in urls[0][1]:
            from lib.m3u8 import m3u8
            m3u8_handler = m3u8()
            urls = m3u8_handler.process( request_get( urls[0][1] ) )

        if PLAYBACK_CAP != 'Off':
            urls = [url for url in urls if int(url[0]) <= int( PLAYBACK_CAP ) ]

        if playback_method == 0:
            media_url = urls[0][1]

        # if not automatically selecting highest quality
        elif playback_method > 0:

            # reverses array - small to large
            if playback_method == 1:
                urls = urls[::-1]
                media_url = urls[0][1]


            # quality select
            elif playback_method == 2:

                if len(urls) > 0:

                    if len(urls) == 1:
                        # if only one available, no point asking
                        selected_index = 0
                    else:
                        selected_index = xbmcgui.Dialog().select(
                            'Select Quality', [(sourceItem[0] or '?') for sourceItem in urls]
                        )

                    if selected_index != -1:
                        media_url = urls[selected_index][1]

    return media_url

def subtitles_select( subtitles_in ):

    subtitles = []
    selected_index = -1

    if ADDON.getSetting('subtitles_select') == 'true' and len( subtitles_in ) > 1:
        selected_index = xbmcgui.Dialog().select(
            'Select Subtitle', [(lang[0] or '?') for lang in subtitles_in]
        )

    if selected_index != -1:
        subtitles.append( subtitles_in[selected_index][1] )
    else:
        for subs in subtitles_in:
            subtitles.append( subs[1] )

    return subtitles

def play_video( name, url, thumb, play=2 ):

    """ method to play video """

    # get video link
    resolved = resolver(url)
    url = video_quality_select( resolved[ 'urls' ] )

    if url:

        # Use HTTP
        if ADDON.getSetting('useHTTP') == 'true':
            url = url.replace('https://', 'http://', 1)

        list_item = xbmcgui.ListItem(name, path=url)
        list_item.setArt({'icon': thumb, 'thumb': thumb})

        # set subtitles if available & enabled
        if resolved[ 'subtitles' ] and ADDON.getSetting('subtitles_enabled') == 'true':
            resolved[ 'subtitles' ] = subtitles_select( resolved[ 'subtitles' ] )
            if resolved[ 'subtitles' ]:
                list_item.setSubtitles( resolved[ 'subtitles' ] )

        info_labels={ 'Title': name, 'plot': '' }

        item_set_info( list_item, info_labels )

        if play == 1:
            # Not sure anything uses this
            xbmc.Player().play(item=url, listitem=list_item)
        elif play == 2:

            if '.m3u8' in url and ADDON.getSetting('inputstream_disable') == 'false':

                # Disable Kodi's MIME-type request, since we already know what it is.
                list_item.setContentLookup(False)
                list_item.setMimeType('application/x-mpegURL')

                if KODI_VERSION < 19:
                    list_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
                else:
                    list_item.setProperty('inputstream', 'inputstream.adaptive')

                if KODI_VERSION < 22:
                    list_item.setProperty('inputstream.adaptive.manifest_type', 'hls')

            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)

    else:
        xbmcgui.Dialog().ok( 'Error', 'Video not found' )


def search_items( url, cat ):

    """ Searches rumble  """

    search_str = get_search_string(heading="Search")

    if not search_str:
        return

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
                images = { 'thumb': str(i[3]), 'fanart': str(i[4]) }
                info_labels = { 'plot': str(i[5]) }
                cat = i[6]
                folder = ( i[7] == 'True' )
                play = i[8]

                add_dir( name, url, mode, images, info_labels, cat, folder, True, int(play) )

            xbmcplugin.endOfDirectory(PLUGIN_ID)
        else:
            xbmcgui.Dialog().ok( get_string(14117), get_string(30155) )

    except Exception:

        xbmcplugin.endOfDirectory(PLUGIN_ID)


def favorite_add(name, url, fav_mode, thumb, fanart, plot, cat, folder, play):

    """ add favorite from name """

    data = favorites_load()
    data.append((name, url, fav_mode, thumb, fanart, plot, cat, folder, play))
    fav_file = open( favorites, 'w' )
    fav_file.write(json.dumps(data))
    fav_file.close()

    notify( get_string(30152), name, thumb )


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
    # Session Reset
    notify( get_string(30200) )

def login_test():

    """ Method that resets session, then tests the login """

    RUMBLE_USER.reset_session_details()

    if RUMBLE_USER.has_login_details():
        if RUMBLE_USER.login():
            # Login Success
            notify( get_string(30201) )
        else:
            # Login Failed
            notify( get_string(30202) )
    else:
        # No details detected
        notify( get_string(30203) )

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


def add_dir( name, url, mode, images = {}, info_labels = {}, cat = '', folder=True, fav_context=False, play=0, subscribe_context=False ):

    """ Adds directory items """

    art_dict = {
        'thumb': images.get( 'thumb', HOME_DIR + 'icon.png' ),
        'fanart': images.get( 'fanart', HOME_DIR + 'fanart.jpg' ),
    }

    # set default image location to MEDIA_DIR
    for art_type, art_loc in art_dict.items():
        if art_loc:
            if not art_loc.startswith( HOME_DIR ) and \
                not art_loc.startswith( 'http' ) and \
                not art_loc.startswith( '\\' ):
                art_dict[ art_type ] = MEDIA_DIR + art_dict[ art_type ]

    link_params = {
        'url': url,
        'mode': str( mode ),
        'name': name,
        'thumb': art_dict[ 'thumb' ],
        'fanart': art_dict[ 'fanart' ],
        'plot': info_labels.get( 'plot', '' ),
        'cat': cat,
    }

    context_menu = []

    if play:
        link_params['play'] = str( play )

    link = build_url( link_params )

    list_item = xbmcgui.ListItem( name )
    if folder:
        list_item.setArt({'icon': 'DefaultFolder.png', 'thumb': art_dict[ 'thumb' ]})
    else:
        list_item.setArt({'icon': 'DefaultVideo.png', 'thumb': art_dict[ 'thumb' ]})
        xbmcplugin.setContent(PLUGIN_ID, 'videos')

    if play == 2 and mode == 4:
        list_item.setProperty('IsPlayable', 'true')
        context_menu.append((get_string(30158), 'Action(Queue)'))

        if RUMBLE_USER.has_login_details():
            # need to get current
            params=get_params()
            current_url = params.get( 'url', None )

            if '/playlists/watch-later' in current_url:
                # delete watch later context
                context_menu.append(('Delete from Watch Later','RunPlugin(%s)' % build_url( {'mode': '12','url': url, 'cat':'delete'} )))
            else:
                # add watch later context
                context_menu.append(('Add to Watch Later','RunPlugin(%s)' % build_url( {'mode': '12','url': url, 'cat':'add'} )))

    info_labels['title'] = name
    if play:
        # adds information context menu
        info_labels['mediatype'] = 'tvshow'

    item_set_info( list_item, info_labels )

    list_item.setProperty( 'fanart_image', art_dict[ 'fanart' ] )

    if RUMBLE_USER.has_login_details():

        if subscribe_context:
            if subscribe_context['subscribe']:
                context_menu.append(('Subscribe to ' + subscribe_context['name'],'RunPlugin(%s)' % build_url( {'mode': '11','name': subscribe_context['name'], 'cat': 'subscribe'} )))
            else:
                context_menu.append(('Unsubscribe to ' + subscribe_context['name'],'RunPlugin(%s)' % build_url( {'mode': '11','name': subscribe_context['name'], 'cat': 'unsubscribe'} )))

        if play == 2 and mode == 4:
            context_menu.append(('Comments','RunPlugin(%s)' % build_url( {'mode': '13','url': url} )))

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
                    'thumb': art_dict[ 'thumb' ],
                    'fanart': art_dict[ 'fanart' ],
                    'plot': info_labels.get( 'plot', '' ),
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

def playlist_manage( url, action="add" ):

    """ Adds to Rumble's Playlist """
    video_id = get_playlist_video_id( url )

    if video_id:
        if action == "add":
            RUMBLE_USER.playlist_add_video( video_id )
            message = "Added to playlist"
        else:
            RUMBLE_USER.playlist_delete_video( video_id )
            message = "Deleted from playlist"
    else:
        if action == "add":
            message = "Cannot add to playlist"
        else:
            message = "Cannot delete from playlist"

    notify( message, "Playlist" )

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

    thumb=params.get( 'thumb', None )
    if thumb:
        thumb=urllib.parse.unquote_plus(thumb)

    fanart=params.get( 'fanart', None )
    if fanart:
        fanart=urllib.parse.unquote_plus(fanart)

    plot=params.get( 'plot', None )
    if plot:
        plot=urllib.parse.unquote_plus(plot)

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
        play_video(name, url, thumb, play)
    elif mode in [5,6]:
        if '\\ ' in name:
            name = name.split('\\ ')[1]
        if '  - ' in name:
            name = name.split('  - ')[0]
        if mode == 5:
            favorite_add( name, url, fav_mode, thumb, fanart, plot, cat, str(folder), str(play) )
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
        playlist_manage(url, cat)
    elif mode==13:
        comments_show(url)
    elif mode==14:
        login_test()

if __name__ == "__main__":
    main()
