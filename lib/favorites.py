# -*- coding: utf-8 -*-

import os

import xbmc
import xbmcaddon

from lib.general import translate_path

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


def favorites_load( return_string = False ):

    """ load favorites from file into variable """

    if os.path.exists( FAVORITES_DIR ):
        fav_str = open( FAVORITES_DIR ).read()
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

def favorites_save( data ):

    """ load favorites from file into variable """

    if not os.path.exists( FAVORITES_DIR ):
        favorites_create()

    fav_file = open( FAVORITES_DIR, 'w' )
    fav_file.write(json.dumps(data))
    fav_file.close()

    return True

def favorites_exists( item ):

    """ check if item exists within favorites """

    favorite_str = favorites_load( True )

    # checks fav name via string
    # I do not like how this is done,
    # so will redo in future when favorites are redone

    return item in favorite_str
