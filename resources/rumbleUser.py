#
# Rumble User Class
# Created by Azzy9
#
# Class to handle all the rumble subscription methods
#

import xbmcaddon
import math, time

from resources.general import *
from resources.md5ex import *

try:
    import json
except ImportError:
    import simplejson as json

ADDON = xbmcaddon.Addon()

class rumbleUser:

    baseUrl = 'https://rumble.com'
    username = ''
    password = ''
    session = ''
    expiry = ''

    # Construct to get the saved details
    def __init__( self ):
        self.getLoginDetails()

    # get the saved login details
    def getLoginDetails( self ):
        self.username = ADDON.getSetting( 'username' )
        self.password = ADDON.getSetting( 'password' )
        self.session = ADDON.getSetting( 'session' )
        self.expiry = ADDON.getSetting( 'expiry' )

        if self.expiry:
            self.expiry = float( self.expiry )

    # if there is login details
    def hasLoginDetails( self ):
        return ( self.username and self.password )

    # sets the session details
    # Used for login in & when token is expired
    def setSessionDetails( self ):
        ADDON.setSetting( 'session', self.session )
        ADDON.setSetting( 'expiry', str( self.expiry ) )
        self.setSessionCookie()

    # resets the session details to force a login
    def resetSessionDetails( self ):
        self.session = ''
        self.expiry = ''
        self.setSessionDetails()

    # checks if there is a valid session
    # if not attempt to login
    def hasSession( self, login=True ):
        hasSession = self.session and self.expiry and self.expiry > time.time()
        if not hasSession and login and self.hasLoginDetails():
            self.login()
            return self.hasSession(False)
        return hasSession

    # method to get the salts from rumble
    # these are used to generate the login hashes
    def getSalts( self ):
        if self.hasLoginDetails():
            # gets salts
            data = getRequest(
                self.baseUrl + '/service.php?name=user.get_salts',
                {'username': self.username},
                [ ( 'Referer', self.baseUrl ), ( 'Content-type', 'application/x-www-form-urlencoded' ) ]
            )
            if data:
                salts = json.loads(data)['data']['salts']
                if salts:
                    return salts
        return False

    # method to generate the hashes and login
    def login( self ):

        salts = self.getSalts()
        if salts:
            login_hash = MD5Ex()
            hashes = login_hash.hash( login_hash.hashStretch( self.password, salts[0], 128) + salts[1] ) + ',' + login_hash.hashStretch( self.password, salts[2], 128 ) + ',' + salts[1]

            # login
            data = getRequest( self.baseUrl + '/service.php?name=user.login', {'username': self.username, 'password_hashes': hashes}, [ ( 'Referer', self.baseUrl ), ( 'Content-type', 'application/x-www-form-urlencoded' ) ] )

            if data:
                session = json.loads(data)['data']['session']
                if session:
                    self.session = session
                    # Expiry is 30 Days
                    self.expiry = ( math.floor( time.time() ) + 2592000 )
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


    #method to subscribe and unsubscribe to a channel or user
    def subscribe( self, action, type, name ):

        if self.hasSession():

            post_content = {
                'slug': name,
                'type': type,
                'action': action,
            }

            headers = {
                'Referer': self.baseUrl + name,
                'Content-type': 'application/x-www-form-urlencoded'
            }

            data = getRequest( self.baseUrl + '/service.php?api=2&name=user.subscribe', post_content, headers )
            return data

        return False