from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    """This is an ansible callback plugin that sends full
    play recap to github gist and sends colored notification
    to  a Slack channel after play ends.

    This plugin makes use of file `slack.json` in your playbook folder
    with following contents:
    ```json
    {
        "webhook": "Slack incoming webhook url",
        "channel": "#slackchannel",
        "username": "Ansible"
    }
    ```

    Output: https://gist.github.com/anonymous/f75e04a115ea86b730e41e2ef03cc5f0
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'slack_github'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.github_api = 'https://api.github.com/'
        self.log = u'';

    def _init_config(self, playbook):
        self.playbook_name = os.path.basename(playbook._file_name)
        config_file = playbook._basedir.encode('ascii','ignore') + '/slack.json'
        if os.path.isfile(config_file) == False:
            self._display.warning('File ' + config_file + ' not found. SlackGithub callback has been disabled')
        with open(config_file) as config_file:
            self.config = json.load(config_file)

    def _log(self, text):
        self.log += text

    def _send(self, color='good'):
        raw_gist = {
            'description': 'Ansible play recap',
            'public': False,
            'files': {
                'recap.md': {
                    'content': self.log
                }
            }
        }

        data = json.dumps(raw_gist)
        try:
            response = open_url(self.github_api + 'gists', data=data, method='POST')
        except Exception as e:
            self._display.warning('Could not submit play recap: %s' % str(e))

        gist = json.loads(response.read())
        url = gist[u'html_url'].encode('ascii','ignore')
        message = 'Playbook *' + self.playbook_name + '* has been played. '
        message+= '*<' + url + '#file-recap-md|Details>*'
        payload = {
            'channel': self.config['channel'],
            'username': self.config['username'],
            'attachments': [{
                'fallback': message,
                'fields': [{
                    'value': message
                }],
                'color': color,
                'mrkdwn_in': ['text', 'fallback', 'fields'],
            }],
            'parse': 'none',
            'icon_url': ('http://cdn2.hubspot.net/hub/330046/file-449187601-png/ansible_badge.png'),
        }

        data = json.dumps(payload)
        try:
            response = open_url(self.config['webhook'], data=data)
        except Exception as e:
            self._display.warning('Could not submit notification to Slack: %s' % str(e))

    def v2_playbook_on_start(self, playbook):
        self._init_config(playbook)
        self._log('**Playbook**: ' + self.playbook_name + '\n\n')

    def v2_playbook_on_play_start(self, play):
        name = play.name or 'Not specified #' + play._uuid
        self._log('# Play: ' + name + '\n\n')

    def v2_playbook_on_stats(self, stats):
        color = 'good'
        self._log('# Stats\n\n')
        hosts = sorted(stats.processed.keys())
        for host in hosts:
            summary = stats.summarize(host)
            self._log('**Host**: ' + host + '\n')
            for item, count in summary.iteritems():
                self._log('> **' + item + '**: ' + str(count) + '\n\n')
                if item == 'failures' and count > 0:
                    color = 'danger'
        self._send(color)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._log('**_FAILED_ ' + result._host.get_name() + '** | ' + result._task.get_name().strip() + '\n\n')
        self._log('```json\n' + json.dumps(result._result, indent=1, sort_keys=True) + '\n```\n\n')

    def v2_runner_on_ok(self, result):
        self._log('**' + result._host.get_name() + '** | ' + result._task.get_name().strip() + '\n\n')

    def v2_runner_on_unreachable(self, result):
        self._log('**_UNREACHABLE_ ' + result._host.get_name() + '** | ' + result._task.get_name().strip() + '\n\n')
        self._log('```json\n' + json.dumps(result._result, indent=1, sort_keys=True) + '\n```\n\n')
