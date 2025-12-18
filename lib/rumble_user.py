"""
Rumble User Class
Created by Azzy9
Class to handle all the rumble subscription methods
"""

import math
import time
import re

import xbmcaddon

from lib.general import request_get
from lib.md5ex import MD5Ex

try:
    import json
except ImportError:
    import simplejson as json

ADDON = xbmcaddon.Addon()

class RumbleUser:

    """ main rumble user class """

    base_url = 'https://rumble.com'
    username = ''
    password = ''
    session = ''
    expiry = ''

    def __init__( self ):

        """ Construct to get the saved details """

        self.get_login_details()

    def get_login_details( self ):

        """ get the saved login details """

        self.username = ADDON.getSetting( 'username' )
        self.password = ADDON.getSetting( 'password' )
        self.session = ADDON.getSetting( 'session' )
        self.expiry = ADDON.getSetting( 'expiry' )

        if self.expiry:
            self.expiry = float( self.expiry )

    def has_login_details( self ):

        """ if there is login details """

        return ( self.username and self.password )

    def set_session_details( self ):

        """
        sets the session details
        Used for login in & when token is expired
        """

        ADDON.setSetting( 'session', self.session )
        ADDON.setSetting( 'expiry', str( self.expiry ) )
        self.set_session_cookie()

    def reset_session_details( self ):

        """ resets the session details to force a login """

        self.session = ''
        self.expiry = ''
        self.set_session_details()

    def has_session( self, login=True ):

        """ resets the session details to force a login """

        has_session = self.session and self.expiry and self.expiry > time.time()
        if not has_session and login and self.has_login_details():
            self.login()
            return self.has_session(False)
        return has_session

    def get_salts( self ):

        """
        method to get the salts from rumble
        these are used to generate the login hashes
        """

        if self.has_login_details():
            # gets salts
            data = request_get(
                self.base_url + '/service.php?name=user.get_salts',
                {'username': self.username},
                [('Referer', self.base_url), ('Content-type', 'application/x-www-form-urlencoded')]
            )
            if data:
                salts = json.loads(data)['data']['salts']
                if salts:
                    return salts
        return False

    def login( self ):

        """ method to generate the hashes and login """

        salts = self.get_salts()
        if salts:
            login_hash = MD5Ex()
            hashes = login_hash.hash(
                login_hash.hashStretch( self.password, salts[0], 128) + salts[1] ) + ',' \
                + login_hash.hashStretch( self.password, salts[2], 128
            ) + ',' + salts[1]

            # login
            data = request_get(
                self.base_url + '/service.php?name=user.login',
                {'username': self.username, 'password_hashes': hashes},
                [('Referer', self.base_url), ('Content-type', 'application/x-www-form-urlencoded')]
            )

            if data:
                session = json.loads(data)['data']['session']
                if session:
                    self.session = session
                    # Expiry is 30 Days
                    self.expiry = math.floor( time.time() ) + 2592000
                    self.set_session_details()
                    return session

        return False

    def get_comments( self, video_id ):

        """ method to get comments for video """

        if video_id and self.has_session():

            headers = {
                'Referer': self.base_url + video_id,
                'Content-type': 'application/x-www-form-urlencoded'
            }

            # for some strange reason the first letter needs to be removed
            data = request_get(
                self.base_url + '/service.php?name=comment.list&video=' + video_id[1:],
                None,
                headers
            )

            if data:
                comment_data = json.loads(data)
                if comment_data.get('html'):
                    return re.compile(
                        r"<a\sclass=\"comments-meta-author[^\"]*\"\shref=\"([^\"]+)\">([^\<]+)</a>(?:[\s|\n||\\n|\\t]+)<a\sclass='comments-meta-post-time[^']*'\shref='#comment-([0-9]+)' title='([A-Z][^\,]+),\s([A-Z][^\s]+)\s([0-9]+),\s([0-9]+)\s([0-9]{2}):([0-9]{2})\s(AM|PM)\s-(?:[0-9]+)'>([^\<]+)</a>(?:[\s|\n||\\n|\\t]+)</div>(?:[\s|\n||\\n|\\t]+)<p class=\"comment-text[^\"]*\">([^\<]+)</p>",
                        re.MULTILINE|re.DOTALL|re.IGNORECASE
                    ).findall(comment_data.get('html',''))
        return {}

    def set_session_cookie( self ):

        """ Sets the cookie to be used in the session """

        if self.session:
            # get stored cookie string
            cookies = ADDON.getSetting('cookies')

            # split cookies into dictionary
            if cookies:
                cookie_dict = json.loads( cookies )
            else:
                cookie_dict = {}

            cookie_dict[ 'u_s' ] = self.session

            # store cookies
            ADDON.setSetting('cookies', json.dumps(cookie_dict))
        else:
            ADDON.setSetting('cookies', '')

    def subscribe( self, action, action_type, name ):

        """ method to subscribe and unsubscribe to a channel or user """

        if self.has_session():

            post_content = {
                'slug': name,
                'type': action_type,
                'action': action,
            }

            headers = {
                'Referer': self.base_url + name,
                'Content-type': 'application/x-www-form-urlencoded'
            }

            data = request_get(
                self.base_url + '/service.php?api=2&name=user.subscribe',
                post_content,
                headers
            )

            return data

        return False

    def playlist_add_video( self, video_id, playlist_id = 'watch-later' ):

        """ method to add video to playlist """

        if self.has_session():

            post_content = {
                'playlist_id': playlist_id,
                'video_id': video_id,
            }

            headers = {
                'Referer': self.base_url,
                'Content-type': 'application/x-www-form-urlencoded'
            }

            data = request_get(
                self.base_url + '/service.php?name=playlist.add_video',
                post_content,
                headers
            )

            return data

        return False

    def playlist_delete_video( self, video_id, playlist_id = 'watch-later' ):

        """ method to delete video from playlist """

        if self.has_session():

            post_content = {
                'playlist_id': playlist_id,
                'video_id': video_id,
            }

            headers = {
                'Referer': self.base_url,
                'Content-type': 'application/x-www-form-urlencoded'
            }

            data = request_get(
                self.base_url + '/service.php?name=playlist.delete_video',
                post_content,
                headers
            )

            return data

        return False
