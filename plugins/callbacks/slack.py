# (C) 2014, George Yoshida <dynkin+dev@gmail.com>

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
import urllib2
import json

from ansible import utils

try:
    import prettytable
    HAS_PRETTYTABLE = True
except ImportError:
    HAS_PRETTYTABLE = False

SLACK_WEBHOOK_URL = 'https://%s.slack.com/services/hooks/incoming-webhook?token=%s'


class CallbackModule(object):
    """This is an example ansible callback plugin that sends status
    updates to a Slack channel during playbook execution.

    This plugin makes use of the following environment variables:
        SLACK_TOKEN    (required): Slack API token
        SLACK_DOMAIN   (required): Slack team URL
        SLACK_CHANNEL  (optional): Slack channel to post in. Default: #ansible
        SLACK_USERNAME (optional): Name to post as. Default: ansible

    Requires:
        prettytable

    """

    def __init__(self):
        if not HAS_PRETTYTABLE:
            self.disabled = True
            utils.warning('The `prettytable` python module is not installed. '
                          'Disabling the Slack callback plugin.')

        self.token = os.getenv('SLACK_TOKEN')
        self.domain = os.getenv('SLACK_DOMAIN')
        self.slack_webhook_url = SLACK_WEBHOOK_URL % (self.domain, self.token)
        self.channel = os.getenv('SLACK_CHANNEL', '#ansible')
        self.username = os.getenv('SLACK_USERNAME', 'ansible')

        if self.token is None:
            self.disabled = True
            utils.warning('Slack token could not be loaded. The Slack '
                          'token can be provided using the `SLACK_TOKEN` '
                          'environment variable.')

        if self.domain is None:
            self.disabled = True
            utils.warning('Slack domain could not be loaded. The Slack '
                          'domain can be provided using the `SLACK_DOMAIN` '
                          'environment variable.')


        self.printed_playbook = False
        self.playbook_name = None

    def send_msg(self, msg, parse=None):
        """Method for sending a message to Slack"""

        try:
            payload = {}
            payload['text' ] = msg
            payload['channel' ] = self.channel
            payload['username' ] = self.username
            if parse:
                payload['parse' ] = parse
            
            data = json.dumps(payload)
            req = urllib2.Request(self.slack_webhook_url, data)
            urllib2.urlopen(req)
        except:
            utils.warning('Could not submit message to Slack')

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        pass

    def runner_on_ok(self, host, res):
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
        pass

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

    def playbook_on_play_start(self, name):
        """Display Playbook and play start messages"""

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
                           inventory))
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

        self.send_msg("%s: Playbook complete" % self.playbook_name)

        if failures or unreachable:
            self.send_msg("%s: Failures detected" % self.playbook_name)

        self.send_msg("```\n%s:\n%s\n```" % (self.playbook_name, t))
