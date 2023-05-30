"""
Rumble User Class
Created by Azzy9
Class to handle all the rumble subscription methods
"""

import math
import time

import xbmcaddon

from lib.general import *
from lib.md5ex import MD5Ex

try:
    import json
except ImportError:
    import simplejson as json

ADDON = xbmcaddon.Addon()

class rumbleUser:

    """ main rumble user class """

    baseUrl = 'https://rumble.com'
    username = ''
    password = ''
    session = ''
    expiry = ''

    def __init__( self ):

        """ Construct to get the saved details """

        self.getLoginDetails()

    def getLoginDetails( self ):

        """ get the saved login details """

        self.username = ADDON.getSetting( 'username' )
        self.password = ADDON.getSetting( 'password' )
        self.session = ADDON.getSetting( 'session' )
        self.expiry = ADDON.getSetting( 'expiry' )

        if self.expiry:
            self.expiry = float( self.expiry )

    def hasLoginDetails( self ):

        """ if there is login details """

        return ( self.username and self.password )

    def setSessionDetails( self ):

        """
        sets the session details
        Used for login in & when token is expired
        """

        ADDON.setSetting( 'session', self.session )
        ADDON.setSetting( 'expiry', str( self.expiry ) )
        self.setSessionCookie()

    def resetSessionDetails( self ):

        """ resets the session details to force a login """

        self.session = ''
        self.expiry = ''
        self.setSessionDetails()

    def hasSession( self, login=True ):

        """ resets the session details to force a login """

        has_session = self.session and self.expiry and self.expiry > time.time()
        if not has_session and login and self.hasLoginDetails():
            self.login()
            return self.hasSession(False)
        return has_session

    def getSalts( self ):

        """
        method to get the salts from rumble
        these are used to generate the login hashes
        """

        if self.hasLoginDetails():
            # gets salts
            data = request_get(
                self.baseUrl + '/service.php?name=user.get_salts',
                {'username': self.username},
                [ ( 'Referer', self.baseUrl ), ( 'Content-type', 'application/x-www-form-urlencoded' ) ]
            )
            if data:
                salts = json.loads(data)['data']['salts']
                if salts:
                    return salts
        return False

    def login( self ):

        """ method to generate the hashes and login """

        salts = self.getSalts()
        if salts:
            login_hash = MD5Ex()
            hashes = login_hash.hash( login_hash.hashStretch( self.password, salts[0], 128) + salts[1] ) + ',' + login_hash.hashStretch( self.password, salts[2], 128 ) + ',' + salts[1]

            # login
            data = request_get(
                self.baseUrl + '/service.php?name=user.login',
                {'username': self.username, 'password_hashes': hashes},
                [ ( 'Referer', self.baseUrl ), ( 'Content-type', 'application/x-www-form-urlencoded' ) ]
            )

            if data:
                session = json.loads(data)['data']['session']
                if session:
                    self.session = session
                    # Expiry is 30 Days
                    self.expiry = math.floor( time.time() ) + 2592000
                    self.setSessionDetails()
                    return session

        return False


    def setSessionCookie( self ):

        if self.session:
            # get stored cookie string
            cookies = ADDON.getSetting('cookies')

            # split cookies into dictionary
            if cookies:
                cookieDict = json.loads( cookies )
            else:
                cookieDict = {}

            cookieDict[ 'u_s' ] = self.session

            # store cookies
            ADDON.setSetting('cookies', json.dumps(cookieDict))
        else:
            ADDON.setSetting('cookies', '')

    def subscribe( self, action, action_type, name ):

        """ method to subscribe and unsubscribe to a channel or user """

        if self.hasSession():

            post_content = {
                'slug': name,
                'type': action_type,
                'action': action,
            }

            headers = {
                'Referer': self.baseUrl + name,
                'Content-type': 'application/x-www-form-urlencoded'
            }

            data = request_get( self.baseUrl + '/service.php?api=2&name=user.subscribe', post_content, headers )
            return data

        return False
