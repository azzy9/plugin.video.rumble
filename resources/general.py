# -*- coding: utf-8 -*-
import sys, requests
import xbmc, xbmcaddon
import six

from six.moves import urllib

PLUGIN_URL = sys.argv[0]

ADDON = xbmcaddon.Addon()
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')

#language
__language__ = ADDON.getLocalizedString

# Disable urllib3's "InsecureRequestWarning: Unverified HTTPS request is being made" warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

s = requests.session()


def getRequest(url, data=None, extraHeaders=None):

    try:

        myHeaders = {
            'Accept-Language': 'en-gb,en;q=0.5',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': url,
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        }

        if extraHeaders:
            myHeaders.update(extraHeaders)

        if data:
            response = s.post(url, data=data, headers=myHeaders, verify=False, cookies=None, timeout=10)
        else:
            response = s.get(url, headers=myHeaders, verify=False, cookies=None, timeout=10)

        return response.text

    except:
        return ''


def buildURL(query):

    # Helper function to build a Kodi xbmcgui.ListItem URL.
    # :param query: Dictionary of url parameters to put in the URL.
    # :returns: A formatted and urlencoded URL string.

    return (PLUGIN_URL + '?' + urllib.parse.urlencode({k: v.encode('utf-8') if isinstance(v, six.text_type)
                                         else unicode(v, errors='ignore').encode('utf-8')
                                         for k, v in query.items()}))


def notify(message,name=False,iconimage=False,timeShown=5000):

    if not name:
        name = ADDON_NAME
    if not iconimage:
        iconimage = ADDON_ICON

    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (name, message, timeShown, iconimage))


def SetView(name):

    views = {
        'fanart': 502,
        'wall': 500,
        'widelist': 55,
        'infowall': 54,
        'shift': 53,
        'poster': 51,
        'list': 50,
    }

    view_num = views.get( name.lower(), 0 )

    if view_num > 0:
        try:
            xbmc.executebuiltin('Container.SetViewMode(' + str( view_num ) + ')')
        except:
            pass


def get_string( string_id ):
    if string_id >= 30000:
        return __language__( string_id )
    else:
        return xbmc.getLocalizedString( string_id )


def get_params():
    return dict(urllib.parse.parse_qsl(sys.argv[2][1:], keep_blank_values=True))
