# -*- coding: utf-8 -*-

import os

import xbmc
import xbmcaddon

from collections import OrderedDict

from lib.general import translate_path, url_path_get

try:
    import json
except ImportError:
    import simplejson as json

ADDON = xbmcaddon.Addon()

FAVORITES_DIR = translate_path(os.path.join(ADDON.getAddonInfo('profile'), 'favorites.dat'))

def favorites_create():

    """ creates favorite directory if doesn't exist """

    addon_data_path = translate_path(ADDON.getAddonInfo('profile'))

    if os.path.exists(addon_data_path) is False:
        os.mkdir(addon_data_path)

    xbmc.sleep(1)


def favorites_load():

    """ load favorites from file into variable """

    if os.path.exists( FAVORITES_DIR ):
        favorites = open( FAVORITES_DIR ).read()
        if favorites:
            favorites = json.loads( favorites, object_pairs_hook=OrderedDict )
            if favorites:
                favorites = favorites_convert( favorites )
                return favorites
    else:
        favorites_create()

    return OrderedDict({})

def favorites_add( data ):

    """ add data and save favorites """

    if 'url' in data:
        favorites = favorites_load()
        # if exists, this will update the data
        favorites[ url_path_get( data[ 'url' ] ) ] = data
        favorites_save( favorites )

def favorites_remove( url ):

    """ add data and save favorites """

    removed = False

    url = url_path_get( url )

    favorites = favorites_load()
    if favorites.get( url ):
        del favorites[url]
        favorites_save( favorites )
        removed = True

    return removed

def favorites_save( data ):

    """ load favorites from file into variable """

    if not os.path.exists( FAVORITES_DIR ):
        favorites_create()

    fav_file = open( FAVORITES_DIR, 'w' )
    fav_file.write(json.dumps(data))
    fav_file.close()

    return True

def favorites_exists( url ):

    """ check if item exists within favorites """

    return url_path_get(url) in favorites_load()

def favorites_convert( data ):

    """ Converts old favorite file format to new """

    if data and isinstance(data, (list, tuple)):

        dict_out = OrderedDict({})

        for record in data:
            url = url_path_get( record[1] )
            dict_out[ url ] = {
                'name': record[0],
                'url': url,
                'mode': record[2],
                'thumb': str(record[3]),
                'fanart': str(record[4]),
                'plot': str(record[5]),
                'cat': record[6],
                'folder': ( record[7] == 'True' ),
                'play': record[8],
            }

        return dict_out

    return data
