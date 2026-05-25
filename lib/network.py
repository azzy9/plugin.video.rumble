# -*- coding: utf-8 -*-

import ssl
import re
import requests

import xbmc
import xbmcaddon
import xbmcgui

from six.moves import urllib

try:
    import json
except ImportError:
    import simplejson as json

ADDON = xbmcaddon.Addon()

BYPASS_CF_ENABLED = ADDON.getSettingBool('bypassCloudflare')
USE_CLOUDREQUEST = ADDON.getSettingBool('cloudRequest')

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

# if we are not using a bypass tool
# see if we can use the cloudrequest module
if BYPASS_CF_ENABLED is False and USE_CLOUDREQUEST:
    try:
        import cloudscraper
        reqs = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
            delay=4
        )
        xbmc.log( 'Using cloudrequest', xbmc.LOGWARNING )
    except ImportError:
        reqs = requests.session()
        USE_CLOUDREQUEST = False
else:
    reqs = requests.session()

tls_adapters = [TLS12HttpAdapter(), TLS11HttpAdapter()]

def bypass_cloudflare(url, data):

    """
    When active, this method will try to bypass cloudflare
    using either Flaresolverr or Byparr
    """

    xbmc.log("Bypass Cloudflare: attempting")

    try:
        # get stored cookie string
        cookies = ADDON.getSetting('cookies')

        # split cookies into dictionary
        if cookies:
            cookie_dict = json.loads( cookies )
        else:
            cookie_dict = None

        bypass_cf_headers = {"Content-Type": "application/json"}

        timeout = ADDON.getSettingInt('flareSolverrTimeout')

        bypass_cf_data = {
            'url': url,
            'maxTimeout': 1000 * timeout,
            'disableMedia': True,
        }

        if data:
            bypass_cf_data['cmd'] = 'request.post'
            bypass_cf_data['postData'] = urllib.parse.urlencode(data)
        else:
            bypass_cf_data['cmd'] = 'request.get'

        # add authentication cookie
        if cookie_dict and cookie_dict.get( 'u_s', False ):
            bypass_cf_data['cookies'] = [{"name":"u_s","value":cookie_dict[ 'u_s' ]}]

        response = reqs.post(
            ADDON.getSetting('flareSolverrUrl'),
            headers=bypass_cf_headers,
            json=bypass_cf_data,
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
        xbmc.log("Bypass Cloudflare: failed - " + str(err_str), xbmc.LOGWARNING)
    return False

def request_get( url, data=None, extra_headers=None, redirects=True ):

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
        if BYPASS_CF_ENABLED:
            bypass_cf_useragent = ADDON.getSetting('flareSolverrUserAgent')
            if bypass_cf_useragent:
                my_headers[ 'User-Agent' ] = bypass_cf_useragent

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

        try_to_bypass_cloudflare = BYPASS_CF_ENABLED
        while status != 200 and i < 2:
            # make request
            if data:
                response = reqs.post(url, data=data, headers=my_headers, cookies=cookie_dict, timeout=10, allow_redirects=redirects)
            else:
                response = reqs.get(url, headers=my_headers, cookies=cookie_dict, timeout=10, allow_redirects=redirects)

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
