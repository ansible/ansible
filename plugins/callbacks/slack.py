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

import os
import json
import uuid
import urllib2

from ansible import utils

try:
    import prettytable
    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False


class CallbackModule(object):
    """This is an example ansible callback plugin that sends status
    updates to a Slack channel during playbook execution.

    This plugin makes use of the following environment variables:
        SLACK_TOKEN    (required): Slack Integration token
        SLACK_TEAM     (required): Slack team name TEAM.slack.com
        SLACK_CHANNEL  (optional): Slack room to post in. Default: #ansible
        SLACK_USERNAME (optional): Username to post as. Default: ansible

    Requires:
        prettytable

    """

    def __init__(self):
        self.disabled = False

        if not HAS_PRETTYTABLE:
            self.disabled = True
            utils.warning('The `prettytable` python module is not installed. '
                          'Disabling the Slack callback plugin.')

        self.webhook_url = ('https://%s.slack.com/services/hooks/'
                            'incoming-webhook?token=%s')

        self.token = os.getenv('SLACK_TOKEN')
        self.team = os.getenv('SLACK_TEAM')
        self.channel = os.getenv('SLACK_CHANNEL', '#ansible')
        self.username = os.getenv('SLACK_USERNAME', 'ansible')

        if self.token is None:
            self.disabled = True
            utils.warning('Slack token could not be loaded. The Slack '
                          'token can be provided using the `SLACK_TOKEN` '
                          'environment variable.')

        if self.token is None:
            self.disabled = True
            utils.warning('Slack team could not be loaded. The Slack '
                          'token can be provided using the `SLACK_TEAM` '
                          'environment variable.')

        self.playbook_name = None

        # This is a 6 character identifier provided with each message
        # This makes it easier to correlate messages when there are more
        # than 1 simultaneous playbooks running
        self.guid = uuid.uuid4().hex[:6]

    def send_msg(self, msg, attachments=[], parse=False):
        parse = 'full' if parse else 'none'
        payload = {
            'text': '%s (_%s_)' % (msg, self.guid),
            'channel': self.channel,
            'username': self.username,
            'attachments': attachments,
            'parse': parse,
            'icon_url': ('http://cdn2.hubspot.net/'
                         'hub/330046/file-449187601-png/ansible_badge.png'),
        }

        data = json.dumps(payload)
        url = self.webhook_url % (self.team, self.token)
        req = urllib2.Request(url, data)
        try:
            urllib2.urlopen(req)
        except:
            utils.warning('Could not submit message to Slack')

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        pass

    def runner_on_ok(self, host, res):
        pass

    def runner_on_error(self, host, msg):
        pass

    def runner_on_skipped(self, host, item=None):
        pass

    def runner_on_unreachable(self, host, res):
        pass

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        pass

    def playbook_on_start(self):
        """Display Playbook start messages"""

        self.playbook_name, _ = os.path.splitext(
            os.path.basename(self.playbook.filename))
        inventory = os.path.basename(
            os.path.realpath(self.playbook.inventory.host_list))
        subset = self.playbook.inventory._subset
        skip_tags = self.playbook.skip_tags

        msg = ('```\nEnv:       %s\nTags:      %s\n'
               'Skip Tags: %s\nLimit:     %s\n```' %
               (inventory,
                ', '.join(self.playbook.only_tags),
                ', '.join(skip_tags) if skip_tags else None,
                ', '.join(subset) if subset else subset))
        attachments = [{
            'fallback': msg,
            'color': 'warning',
            'text': msg,
            'mrkdwn_in': ['text', 'fallback'],
        }]
        self.send_msg("*%s*: Playbook initiated by *%s*" %
                      (self.playbook_name, self.playbook.remote_user),
                      attachments=attachments)

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, pattern):
        """Display Play start messages"""

        attachments = [
            {
                'fallback': '```\n%s\n```' % pattern,
                'text': '```\n%s\n```' % pattern,
                'color': 'warning',
                'mrkdwn_in': ['text', 'fallback'],
            }
        ]
        self.send_msg('*%s*: Starting play' % self.playbook_name,
                      attachments=attachments)

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

        attachments = []
        if failures or unreachable:
            msg = 'Failures detected!'
            attachments.append({
                'fallback': msg,
                'color': 'danger',
                'fields': [
                    {
                        'title': 'Failed!',
                        'value': '```\n%s\n```' % t
                    }
                ],
                'mrkdwn_in': ['text', 'fallback', 'fields']
            })
        else:
            msg = 'Success!'
            attachments.append({
                'fallback': msg,
                'color': 'good',
                'fields': [
                    {
                        'title': 'Success!',
                        'value': '```\n%s\n```' % t
                    }
                ],
                'mrkdwn_in': ['text', 'fallback', 'fields']
            })

        self.send_msg("*%s*: Playbook complete" % self.playbook_name,
                      attachments=attachments)
