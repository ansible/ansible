# (C) 2014, Matt Martz <matt@sivel.net>

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import urllib

try:
    import prettytable
    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False

from ansible.plugins.callback import CallbackBase
from ansible.module_utils.urls import open_url

class CallbackModule(CallbackBase):
    """This is an example ansible callback plugin that sends status
    updates to a HipChat channel during playbook execution.

    This plugin makes use of the following environment variables:
        HIPCHAT_TOKEN (required): HipChat API token
        HIPCHAT_ROOM  (optional): HipChat room to post in. Default: ansible
        HIPCHAT_FROM  (optional): Name to post as. Default: ansible
        HIPCHAT_NOTIFY (optional): Add notify flag to important messages ("true" or "false"). Default: true

    Requires:
        prettytable

    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'hipchat'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

        if not HAS_PRETTYTABLE:
            self.disabled = True
            self.display.warning('The `prettytable` python module is not installed. '
                          'Disabling the HipChat callback plugin.')

        self.msg_uri = 'https://api.hipchat.com/v1/rooms/message'
        self.token = os.getenv('HIPCHAT_TOKEN')
        self.room = os.getenv('HIPCHAT_ROOM', 'ansible')
        self.from_name = os.getenv('HIPCHAT_FROM', 'ansible')
        self.allow_notify = (os.getenv('HIPCHAT_NOTIFY') != 'false')

        if self.token is None:
            self.disabled = True
            self.display.warning('HipChat token could not be loaded. The HipChat '
                          'token can be provided using the `HIPCHAT_TOKEN` '
                          'environment variable.')

        self.printed_playbook = False
        self.playbook_name = None
        self.play = None

    def send_msg(self, msg, msg_format='text', color='yellow', notify=False):
        """Method for sending a message to HipChat"""

        params = {}
        params['room_id'] = self.room
        params['from'] = self.from_name[:15]  # max length is 15
        params['message'] = msg
        params['message_format'] = msg_format
        params['color'] = color
        params['notify'] = int(self.allow_notify and notify)

        url = ('%s?auth_token=%s' % (self.msg_uri, self.token))
        try:
            response = open_url(url, data=urllib.urlencode(params))
            return response.read()
        except:
            self.display.warning('Could not submit message to hipchat')


    def v2_playbook_on_play_start(self, play):
        """Display Playbook and play start messages"""

        self.play = play
        name = play.name
        # This block sends information about a playbook when it starts
        # The playbook object is not immediately available at
        # playbook_on_start so we grab it via the play
        #
        # Displays info about playbook being started by a person on an
        # inventory, as well as Tags, Skip Tags and Limits
        if not self.printed_playbook:
            self.playbook_name, _ = os.path.splitext(
                os.path.basename(self.play.playbook.filename))
            host_list = self.play.playbook.inventory.host_list
            inventory = os.path.basename(os.path.realpath(host_list))
            self.send_msg("%s: Playbook initiated by %s against %s" %
                          (self.playbook_name,
                           self.play.playbook.remote_user,
                           inventory), notify=True)
            self.printed_playbook = True
            subset = self.play.playbook.inventory._subset
            skip_tags = self.play.playbook.skip_tags
            self.send_msg("%s:\nTags: %s\nSkip Tags: %s\nLimit: %s" %
                          (self.playbook_name,
                           ', '.join(self.play.playbook.only_tags),
                           ', '.join(skip_tags) if skip_tags else None,
                           ', '.join(subset) if subset else subset))

        # This is where we actually say we are starting a play
        self.send_msg("%s: Starting play: %s" %
                      (self.playbook_name, name))

    def playbook_on_stats(self, stats):
        """Display info about playbook statistics"""
        hosts = sorted(stats.processed.keys())

        t = prettytable.PrettyTable(['Host', 'Ok', 'Changed', 'Unreachable',
                                     'Failures'])

        failures = False
        unreachable = False

        for h in hosts:
            s = stats.summarize(h)

            if s['failures'] > 0:
                failures = True
            if s['unreachable'] > 0:
                unreachable = True

            t.add_row([h] + [s[k] for k in ['ok', 'changed', 'unreachable',
                                            'failures']])

        self.send_msg("%s: Playbook complete" % self.playbook_name,
                      notify=True)

        if failures or unreachable:
            color = 'red'
            self.send_msg("%s: Failures detected" % self.playbook_name,
                          color=color, notify=True)
        else:
            color = 'green'

        self.send_msg("/code %s:\n%s" % (self.playbook_name, t), color=color)
