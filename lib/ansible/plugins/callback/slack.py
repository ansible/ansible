# (C) 2014-2015, Matt Martz <matt@sivel.net>
# (C) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: slack
    callback_type: notification
    requirements:
      - whitelist in configuration
      - prettytable (python library)
    short_description: Sends play events to a Slack channel
    version_added: "2.1"
    description:
        - This is an ansible callback plugin that sends status updates to a Slack channel during playbook execution.
        - Before 2.4 only environment variables were available for configuring this plugin
    options:
      webhook_url:
        required: True
        description: Slack Webhook URL
        env:
          - name: SLACK_WEBHOOK_URL
        ini:
          - section: callback_slack
            key: webhook_url
      channel:
        default: "#ansible"
        description: Slack room to post in.
        env:
          - name: SLACK_CHANNEL
        ini:
          - section: callback_slack
            key: channel
      username:
        description: Username to post as.
        env:
          - name: SLACK_USERNAME
        default: ansible
        ini:
          - section: callback_slack
            key: username
'''

import json
import os
import uuid

try:
    from __main__ import cli
except ImportError:
    cli = None

from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase

try:
    import prettytable
    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False


class CallbackModule(CallbackBase):
    """This is an ansible callback plugin that sends status
    updates to a Slack channel during playbook execution.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'slack'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):

        super(CallbackModule, self).__init__(display=display)

        if not HAS_PRETTYTABLE:
            self.disabled = True
            self._display.warning('The `prettytable` python module is not '
                                  'installed. Disabling the Slack callback '
                                  'plugin.')

        self.playbook_name = None

        # This is a 6 character identifier provided with each message
        # This makes it easier to correlate messages when there are more
        # than 1 simultaneous playbooks running
        self.guid = uuid.uuid4().hex[:6]

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.webhook_url = self.get_option('webhook_url')
        self.channel = self.get_option('channel')
        self.username = self.get_option('username')
        self.show_invocation = (self._display.verbosity > 1)

        if self.webhook_url is None:
            self.disabled = True
            self._display.warning('Slack Webhook URL was not provided. The '
                                  'Slack Webhook URL can be provided using '
                                  'the `SLACK_WEBHOOK_URL` environment '
                                  'variable.')

    def send_msg(self, attachments):
        payload = {
            'channel': self.channel,
            'username': self.username,
            'attachments': attachments,
            'parse': 'none',
            'icon_url': ('http://cdn2.hubspot.net/hub/330046/'
                         'file-449187601-png/ansible_badge.png'),
        }

        data = json.dumps(payload)
        self._display.debug(data)
        self._display.debug(self.webhook_url)
        try:
            response = open_url(self.webhook_url, data=data)
            return response.read()
        except Exception as e:
            self._display.warning('Could not submit message to Slack: %s' %
                                  str(e))

    def v2_playbook_on_start(self, playbook):
        self.playbook_name = os.path.basename(playbook._file_name)

        title = [
            '*Playbook initiated* (_%s_)' % self.guid
        ]
        invocation_items = []
        if self._plugin_options and self.show_invocation:
            tags = self.get_option('tags')
            skip_tags = self.get_option('skip_tags')
            extra_vars = self.get_option('extra_vars')
            subset = self.get_option('subset')
            inventory = os.path.basename(
                os.path.realpath(self.get_option('inventory'))
            )

            invocation_items.append('Inventory:  %s' % inventory)
            if tags and tags != 'all':
                invocation_items.append('Tags:       %s' % tags)
            if skip_tags:
                invocation_items.append('Skip Tags:  %s' % skip_tags)
            if subset:
                invocation_items.append('Limit:      %s' % subset)
            if extra_vars:
                invocation_items.append('Extra Vars: %s' %
                                        ' '.join(extra_vars))

            title.append('by *%s*' % self.get_option('remote_user'))

        title.append('\n\n*%s*' % self.playbook_name)
        msg_items = [' '.join(title)]
        if invocation_items:
            msg_items.append('```\n%s\n```' % '\n'.join(invocation_items))

        msg = '\n'.join(msg_items)

        attachments = [{
            'fallback': msg,
            'fields': [
                {
                    'value': msg
                }
            ],
            'color': 'warning',
            'mrkdwn_in': ['text', 'fallback', 'fields'],
        }]

        self.send_msg(attachments=attachments)

    def v2_playbook_on_play_start(self, play):
        """Display Play start messages"""

        name = play.name or 'Play name not specified (%s)' % play._uuid
        msg = '*Starting play* (_%s_)\n\n*%s*' % (self.guid, name)
        attachments = [
            {
                'fallback': msg,
                'text': msg,
                'color': 'warning',
                'mrkdwn_in': ['text', 'fallback', 'fields'],
            }
        ]
        self.send_msg(attachments=attachments)

    def v2_playbook_on_stats(self, stats):
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

        attachments = []
        msg_items = [
            '*Playbook Complete* (_%s_)' % self.guid
        ]
        if failures or unreachable:
            color = 'danger'
            msg_items.append('\n*Failed!*')
        else:
            color = 'good'
            msg_items.append('\n*Success!*')

        msg_items.append('```\n%s\n```' % t)

        msg = '\n'.join(msg_items)

        attachments.append({
            'fallback': msg,
            'fields': [
                {
                    'value': msg
                }
            ],
            'color': color,
            'mrkdwn_in': ['text', 'fallback', 'fields']
        })

        self.send_msg(attachments=attachments)
