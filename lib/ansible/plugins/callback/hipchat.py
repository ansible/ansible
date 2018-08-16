# (C) 2014, Matt Martz <matt@sivel.net>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: hipchat
    callback_type: notification
    requirements:
      - whitelist in configuration.
      - prettytable (python lib)
    short_description: post task events to hipchat
    description:
      - This callback plugin sends status updates to a HipChat channel during playbook execution.
      - Before 2.4 only environment variables were available for configuring this plugin.
    version_added: "1.6"
    options:
      token:
        description: HipChat API token for v1 or v2 API.
        required: True
        env:
          - name: HIPCHAT_TOKEN
        ini:
          - section: callback_hipchat
          - key: token
      api_version:
        description: HipChat API version, v1 or v2.
        required: False
        default: v1
        env:
          - name: HIPCHAT_API_VERSION
        ini:
          - section: callback_hipchat
          - key: api_version
      room:
        description: HipChat room to post in.
        default: ansible
        env:
          - name: HIPCHAT_ROOM
        ini:
          - section: callback_hipchat
          - key: room
      from:
        description:  Name to post as
        default: ansible
        env:
          - name: HIPCHAT_FROM
        ini:
          - section: callback_hipchat
          - key: from
      notify:
        description: Add notify flag to important messages
        type: bool
        default: True
        env:
          - name: HIPCHAT_NOTIFY
        ini:
          - section: callback_hipchat
          - key: notify

'''

import os
import json

try:
    import prettytable
    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False

from ansible.plugins.callback import CallbackBase
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import open_url


class CallbackModule(CallbackBase):
    """This is an example ansible callback plugin that sends status
    updates to a HipChat channel during playbook execution.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'hipchat'
    CALLBACK_NEEDS_WHITELIST = True

    API_V1_URL = 'https://api.hipchat.com/v1/rooms/message'
    API_V2_URL = 'https://api.hipchat.com/v2/'

    def __init__(self):

        super(CallbackModule, self).__init__()

        if not HAS_PRETTYTABLE:
            self.disabled = True
            self._display.warning('The `prettytable` python module is not installed. '
                                  'Disabling the HipChat callback plugin.')
        self.printed_playbook = False
        self.playbook_name = None
        self.play = None

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.token = self.get_option('token')
        self.api_version = self.get_option('api_version')
        self.from_name = self.get_option('from')
        self.allow_notify = self.get_option('notify')
        self.room = self.get_option('room')

        if self.token is None:
            self.disabled = True
            self._display.warning('HipChat token could not be loaded. The HipChat '
                                  'token can be provided using the `HIPCHAT_TOKEN` '
                                  'environment variable.')

        # Pick the request handler.
        if self.api_version == 'v2':
            self.send_msg = self.send_msg_v2
        else:
            self.send_msg = self.send_msg_v1

    def send_msg_v2(self, msg, msg_format='text', color='yellow', notify=False):
        """Method for sending a message to HipChat"""

        headers = {'Authorization': 'Bearer %s' % self.token, 'Content-Type': 'application/json'}

        body = {}
        body['room_id'] = self.room
        body['from'] = self.from_name[:15]  # max length is 15
        body['message'] = msg
        body['message_format'] = msg_format
        body['color'] = color
        body['notify'] = self.allow_notify and notify

        data = json.dumps(body)
        url = self.API_V2_URL + "room/{room_id}/notification".format(room_id=self.room)
        try:
            response = open_url(url, data=data, headers=headers, method='POST')
            return response.read()
        except Exception as ex:
            self._display.warning('Could not submit message to hipchat: {0}'.format(ex))

    def send_msg_v1(self, msg, msg_format='text', color='yellow', notify=False):
        """Method for sending a message to HipChat"""

        params = {}
        params['room_id'] = self.room
        params['from'] = self.from_name[:15]  # max length is 15
        params['message'] = msg
        params['message_format'] = msg_format
        params['color'] = color
        params['notify'] = int(self.allow_notify and notify)

        url = ('%s?auth_token=%s' % (self.API_V1_URL, self.token))
        try:
            response = open_url(url, data=urlencode(params))
            return response.read()
        except Exception as ex:
            self._display.warning('Could not submit message to hipchat: {0}'.format(ex))

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
