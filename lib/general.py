# -*- coding: utf-8 -*-
import sys
import ssl
import re
import requests

import xbmc
import xbmcaddon
import xbmcgui

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

FLARESOLVERR_ENABLED = ADDON.getSettingBool('bypassCloudflare')

#language
__language__ = ADDON.getLocalizedString

# Disable urllib3's "InsecureRequestWarning: Unverified HTTPS request is being made" warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter

class TLS11HttpAdapter(HTTPAdapter):

    """Transport adapter" that allows us to use TLSv1.1"""

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1_1
        )


class TLS12HttpAdapter(HTTPAdapter):

    """Transport adapter" that allows us to use TLSv1.2"""

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1_2
        )

reqs = requests.session()
tls_adapters = [TLS12HttpAdapter(), TLS11HttpAdapter()]

def bypass_cloudflare(url, data):

    xbmc.log("Flaresolverr: Bypassing Cloudflare challenge")

    try:
        # get stored cookie string
        cookies = ADDON.getSetting('cookies')

        # split cookies into dictionary
        if cookies:
            cookie_dict = json.loads( cookies )
        else:
            cookie_dict = None

        flaresolverr_headers = {"Content-Type": "application/json"}

        timeout = ADDON.getSettingInt('flareSolverrTimeout')

        flaresolverr_data = {
            'url': url,
            'maxTimeout': 1000 * timeout,
            'disableMedia': True,
        }
        
        if data:
            flaresolverr_data['cmd'] = 'request.post'
            flaresolverr_data['postData'] = urllib.parse.urlencode(data)
        else:
            flaresolverr_data['cmd'] = 'request.get'

        # add authentication cookie
        if cookie_dict and cookie_dict.get( 'u_s', False ):
            flaresolverr_data['cookies'] = [{"name":"u_s","value":cookie_dict[ 'u_s' ]}]

        response = reqs.post(
            ADDON.getSetting('flareSolverrUrl'),
            headers=flaresolverr_headers,
            json=flaresolverr_data,
            verify=False,
            timeout=timeout
        )
        response.raise_for_status()

        js = response.json()

        cookies = {}
        for cookie in js['solution']['cookies']:
            cookies[cookie['name']] = cookie['value']

        if cookie_dict:
            cookie_dict.update( cookies )
        else:
            cookie_dict = cookies

        # set cloudflare cookies
        ADDON.setSetting('cookies', json.dumps(cookie_dict))
        # Set returned user-agent to use with future requests
        ADDON.setSetting('flareSolverrUserAgent', js['solution']['userAgent'])

        return_response = js['solution']['response']

        if '</pre>' in return_response and 'json-formatter-container' in return_response:
            json_body = re.compile(r'<pre>(.*)<\/pre>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(return_response)
            if json_body:
                return_response = json_body[0]

        return return_response

    except Exception as err_str:
        dialog = xbmcgui.Dialog()
        dialog.notification("Cloudflare bypass failed", str(err_str), icon=xbmcgui.NOTIFICATION_ERROR)
        xbmc.log("Flaresolverr: Cloudflare bypass failed - " + str(err_str), xbmc.LOGWARNING)
    return False

def request_get( url, data=None, extra_headers=None ):

    """ makes a request """

    try:

        # headers
        my_headers = {
            'Accept-Language': 'en-gb,en;q=0.5',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': url,
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1',
        }

        # add extra headers
        if extra_headers:
            my_headers.update(extra_headers)

        # if we need to insert flaresolverr useragent
        if FLARESOLVERR_ENABLED:
            flaresolverr_useragent = ADDON.getSetting('flareSolverrUserAgent')
            if flaresolverr_useragent:
                my_headers[ 'User-Agent' ] = flaresolverr_useragent

        # get stored cookie string
        cookies = ADDON.getSetting('cookies')

        # split cookies into dictionary
        if cookies:
            cookie_dict = json.loads( cookies )
        else:
            cookie_dict = None

        uri = urllib.parse.urlparse(url)
        domain = uri.scheme + '://' + uri.netloc

        status = 0
        i = 0

        try_to_bypass_cloudflare = FLARESOLVERR_ENABLED
        while status != 200 and i < 2:
            # make request
            if data:
                response = reqs.post(url, data=data, headers=my_headers, verify=False, cookies=cookie_dict, timeout=10)
            else:
                response = reqs.get(url, headers=my_headers, verify=False, cookies=cookie_dict, timeout=10)

            status = response.status_code
            if status != 200:
                if status == 403 and response.headers.get('server', '') == 'cloudflare':
                    if try_to_bypass_cloudflare:
                        result = bypass_cloudflare(url, data)
                        if result:
                            return result

                        # Only attempt to bypass once
                        try_to_bypass_cloudflare = False

                    reqs.mount(domain, tls_adapters[i])
                i += 1

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

def sort_sizes(e):

    """ method to use to sort sizes """

    try:
        return int( e[0] )
    except ValueError:
        return e[0]

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

def strip_query_params( url ):

    """ checks if there is any query params, then remove """

    if url and '?' in url:
        url = url.split('?')[0]

    return url

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
