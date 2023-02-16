# -*- coding: utf-8 -*-
import sys, requests
import xbmc, xbmcaddon
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

#language
__language__ = ADDON.getLocalizedString

# Disable urllib3's "InsecureRequestWarning: Unverified HTTPS request is being made" warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

reqs = requests.session()


def getRequest(url, data=None, extraHeaders=None):

    try:

        # headers
        myHeaders = {
            'Accept-Language': 'en-gb,en;q=0.5',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': url,
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        }

        # add extra headers
        if extraHeaders:
            myHeaders.update(extraHeaders)

        # get stored cookie string
        cookies = ADDON.getSetting('cookies')

        # split cookies into dictionary
        if cookies:
            cookieDict = json.loads( cookies )
        else:
            cookieDict = None

        # make request
        if data:
            response = reqs.post(url, data=data, headers=myHeaders, verify=False, cookies=cookieDict, timeout=10)
        else:
            response = reqs.get(url, headers=myHeaders, verify=False, cookies=cookieDict, timeout=10)

        if response.cookies.get_dict():
            if cookieDict:
                cookieDict.update( response.cookies.get_dict() )
            else:
                cookieDict = response.cookies.get_dict()
            # store cookies
            ADDON.setSetting('cookies', json.dumps(cookieDict))

        return response.text

    except:
        return ''


# Helper function to build a Kodi xbmcgui.ListItem URL
# :param query: Dictionary of url parameters to put in the URL
# :returns: A formatted and urlencoded URL string
def buildURL(query):

    return (PLUGIN_URL + '?' + urllib.parse.urlencode({k: v.encode('utf-8') if isinstance(v, six.text_type)
                                         else unicode(v, errors='ignore').encode('utf-8')
                                         for k, v in query.items()}))


def notify(message,name=False,iconimage=False,timeShown=5000):

    if not name:
        name = ADDON_NAME
    if not iconimage:
        iconimage = ADDON_ICON

    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (name, message, timeShown, iconimage))


# set view
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


# gets language string based upon id
def get_string( string_id ):
    if string_id >= 30000:
        return __language__( string_id )
    else:
        return xbmc.getLocalizedString( string_id )


# puts date into format based upon setting
def get_date_formatted( format_id, year, month, day ):

    if format_id == '1':
        return month + '/' + day + '/' + year
    if format_id == '2':
        return day + '/' + month + '/' + year
    else:
        return year + '/' + month + '/' + day


# gets params from request
def get_params():
    return dict(urllib.parse.parse_qsl(sys.argv[2][1:], keep_blank_values=True))
