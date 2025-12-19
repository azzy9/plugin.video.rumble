import xbmc
import xbmcgui

import requests

from lib.general import *
from lib.rumble_user import RumbleUser

RUMBLE_USER = RumbleUser()

class CommentWindow(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        self.video_id = kwargs['video_id']
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        self.refresh()

    def fetch_comment_list(self):

        """ fetches comment list from rumble """

        return RUMBLE_USER.get_comments( self.video_id )

    def refresh(self):

        """ Refreshes comment list """

        ccl = self.get_comment_control_list()

        results = self.fetch_comment_list()

        if results:
            for comment_author_url, comment_author_name, comment_id, \
                comment_post_day, comment_post_month, comment_post_date, comment_post_year, \
                comment_post_hour, comment_post_minute, comment_post_meridiem, \
                comment_post_time_ago, comment in results:

                ccl.addItem(
                    self.create_list_item(
                        comment_id,
                        comment_author_name,
                        comment_post_time_ago,
                        comment
                    )
                )
        else:
            if ccl.size() == 0:
                ccl.addItem(xbmcgui.ListItem(label="No Comments Found"))

    def get_comment_control_list(self):

        """ gets comment control list """

        return self.getControl(1)

    def create_list_item(self, comment_id, comment_author_name, comment_post_time_ago, comment):

        """ creates list that will view comment """

        line_item = xbmcgui.ListItem(
            label=self.create_label(
                comment_id,
                comment_author_name,
                comment_post_time_ago,
                comment
            )
        )
        line_item.setProperty('id', comment_id)
        line_item.setProperty('comment_author_name', comment_author_name)
        line_item.setProperty('comment_post_time_ago', comment_post_time_ago)
        line_item.setProperty('comment', comment)
        return line_item

    def refresh_label(self, line_item, selected=True):

        """ Refreshes comment label """

        comment_id = line_item.getProperty('id')
        comment_author_name = line_item.getProperty('comment_author_name')
        comment_post_time_ago = line_item.getProperty('comment_post_time_ago')
        comment = line_item.getProperty('comment')
        line_item.setLabel(
            self.create_label(
                comment_id,
                comment_author_name,
                comment_post_time_ago,
                comment,
                selected
            )
        )

    def create_label(self, comment_id, comment_author_name, comment_post_time_ago, comment, selected=False):

        """ Creates label to view comments """

        return comment_author_name + ' [COLOR white]' + clean_text( comment ) \
            + '[/COLOR] [COLOR orange](' + comment_post_time_ago + ')[/COLOR]'
