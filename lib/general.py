# -*- coding: utf-8 -*-
import sys
import requests

import xbmc
import xbmcaddon

import six
from six.moves import urllib

try:
    import json
except ImportError:
    import simplejson as json

PLUGIN_URL = sys.argv[0]

ADDON = xbmcaddon.Addon()
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')

KODI_VERSION = float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4])

#language
__language__ = ADDON.getLocalizedString

# Disable urllib3's "InsecureRequestWarning: Unverified HTTPS request is being made" warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

reqs = requests.session()

def request_get( url, data=None, extra_headers=None ):

    """ makes a request """

    try:

        # headers
        my_headers = {
            'Accept-Language': 'en-gb,en;q=0.5',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': url,
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        }

        # add extra headers
        if extra_headers:
            my_headers.update(extra_headers)

        # get stored cookie string
        cookies = ADDON.getSetting('cookies')

        # split cookies into dictionary
        if cookies:
            cookie_dict = json.loads( cookies )
        else:
            cookie_dict = None

        # make request
        if data:
            response = reqs.post(url, data=data, headers=my_headers, cookies=cookie_dict, timeout=10)
        else:
            response = reqs.get(url, headers=my_headers, cookies=cookie_dict, timeout=10)

        if response.cookies.get_dict():
            if cookie_dict:
                cookie_dict.update( response.cookies.get_dict() )
            else:
                cookie_dict = response.cookies.get_dict()

            # store cookies
            ADDON.setSetting('cookies', json.dumps(cookie_dict))

        return response.text

    except Exception:
        return ''

def build_url(query):

    """
    Helper function to build a Kodi xbmcgui.ListItem URL
    :param query: Dictionary of url parameters to put in the URL
    :returns: A formatted and urlencoded URL string
    """

    return (PLUGIN_URL + '?' + urllib.parse.urlencode({
        k: v.encode('utf-8') if isinstance(v, six.text_type)
        else unicode(v, errors='ignore').encode('utf-8')
        for k, v in query.items()
    }))


def notify( message, name=False, iconimage=False, time_shown=5000 ):

    """ Show notification to user """

    if not name:
        name = ADDON_NAME

    if not iconimage:
        iconimage = ADDON_ICON

    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (name, message, time_shown, iconimage))

def get_string( string_id ):

    """ gets language string based upon id """

    if string_id >= 30000:
        return __language__( string_id )
    return xbmc.getLocalizedString( string_id )

def get_date_formatted( format_id, year, month, day ):

    """ puts date into format based upon setting """

    if format_id == '1':
        return month + '/' + day + '/' + year
    if format_id == '2':
        return day + '/' + month + '/' + year
    return year + '/' + month + '/' + day

def duration_to_secs( duration, fail_return = '' ):

    """ converts video duration to seconds """

    if duration:
        if ':' in duration:

            time_element_amount = len( duration.split( ':' ) )

            # ensure time string is complete
            if time_element_amount == 2:
                duration = '0:' + duration

            h, m, s = duration.split(':')
            return str( int(h) * 3600 + int(m) * 60 + int(s) )
        else:
            # should only be seconds
            return duration

    return fail_return

def get_params():

    """ gets params from request """

    return dict(urllib.parse.parse_qsl(sys.argv[2][1:], keep_blank_values=True))

def clean_text( text ):

    """ Removes characters that can cause trouble """

    if six.PY2:
        # Python 2 Fix
        # TODO: Provide a proper fix that doesn't revolve removing characters
        text = text.encode('ascii', 'ignore').decode('ascii')

    text = text.strip()

    if r'&' in text:
        text = text.replace(r'&amp;', r'&')

        if r'&#' in text:
            # replace common ascii codes, will expand if needed
            text = text.replace(r'&#34;', r'"').replace(r'&#38;', r'&').replace(r'&#39;', r"'")

    return text

def item_set_info( line_item, properties ):

    """ line item set info """

    if KODI_VERSION > 19.8:
        vidtag = line_item.getVideoInfoTag()
        if properties.get( 'year' ):
            vidtag.setYear( int( properties.get( 'year' ) ) )
        if properties.get( 'episode' ):
            vidtag.setEpisode( properties.get( 'episode' ) )
        if properties.get( 'season' ):
            vidtag.setSeason( properties.get( 'season' ) )
        if properties.get( 'plot' ):
            vidtag.setPlot( properties.get( 'plot' ) )
        if properties.get( 'title' ):
            vidtag.setTitle( properties.get( 'title' ) )
        if properties.get( 'studio' ):
            vidtag.setStudios([ properties.get( 'studio' ) ])
        if properties.get( 'writer' ):
            vidtag.setWriters([ properties.get( 'writer' ) ])
        if properties.get( 'duration' ):
            vidtag.setDuration( int( properties.get( 'duration' ) ) )
        if properties.get( 'tvshowtitle' ):
            vidtag.setTvShowTitle( properties.get( 'tvshowtitle' ) )
        if properties.get( 'mediatype' ):
            vidtag.setMediaType( properties.get( 'mediatype' ) )
        if properties.get('premiered'):
            vidtag.setPremiered( properties.get( 'premiered' ) )

    else:
        line_item.setInfo('video', properties)
