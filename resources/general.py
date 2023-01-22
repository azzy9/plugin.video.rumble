# -*- coding: utf-8 -*-
import sys
import six

from six.moves import urllib

PLUGIN_URL = sys.argv[0]

def buildURL(query):

    # Helper function to build a Kodi xbmcgui.ListItem URL.
    # :param query: Dictionary of url parameters to put in the URL.
    # :returns: A formatted and urlencoded URL string.

    return (PLUGIN_URL + '?' + urllib.parse.urlencode({k: v.encode('utf-8') if isinstance(v, six.text_type)
                                         else unicode(v, errors='ignore').encode('utf-8')
                                         for k, v in query.items()}))


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


def get_params():
    return dict(urllib.parse.parse_qsl(sys.argv[2][1:], keep_blank_values=True))
