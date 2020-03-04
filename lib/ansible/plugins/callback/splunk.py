# -*- coding: utf-8 -*-
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: splunk
    type: aggregate
    short_description: Sends task result events to Splunk HTTP Event Collector
    author: "Stuart Hirst <support@convergingdata.com>"
    description:
      - This callback plugin will send task results as JSON formatted events to a Splunk HTTP collector.
      - The companion Splunk Monitoring & Diagnostics App is available here "https://splunkbase.splunk.com/app/4023/"
      - Credit to "Ryan Currah (@ryancurrah)" for original source upon which this is based.
    version_added: "2.7"
    requirements:
      - Whitelisting this callback plugin
      - 'Create a HTTP Event Collector in Splunk'
      - 'Define the url and token in ansible.cfg'
    options:
      url:
        description: URL to the Splunk HTTP collector source
        env:
          - name: SPLUNK_URL
        ini:
          - section: callback_splunk
            key: url
      authtoken:
        description: Token to authenticate the connection to the Splunk HTTP collector
        env:
          - name: SPLUNK_AUTHTOKEN
        ini:
          - section: callback_splunk
            key: authtoken
'''

EXAMPLES = '''
examples: >
  To enable, add this to your ansible.cfg file in the defaults block
    [defaults]
    callback_whitelist = splunk
  Set the environment variable
    export SPLUNK_URL=http://mysplunkinstance.datapaas.io:8088/services/collector/event
    export SPLUNK_AUTHTOKEN=f23blad6-5965-4537-bf69-5b5a545blabla88
  Set the ansible.cfg variable in the callback_splunk block
    [callback_splunk]
    url = http://mysplunkinstance.datapaas.io:8088/services/collector/event
    authtoken = f23blad6-5965-4537-bf69-5b5a545blabla88
'''

import json
import uuid
import socket
import getpass

from datetime import datetime
from os.path import basename

from ansible.module_utils.urls import open_url
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins.callback import CallbackBase


class SplunkHTTPCollectorSource(object):
    def __init__(self):
        self.ansible_check_mode = False
        self.ansible_playbook = ""
        self.ansible_version = ""
        self.session = str(uuid.uuid4())
        self.host = socket.gethostname()
        self.ip_address = socket.gethostbyname(socket.gethostname())
        self.user = getpass.getuser()

    def send_event(self, url, authtoken, state, result, runtime):
        if result._task_fields['args'].get('_ansible_check_mode') is True:
            self.ansible_check_mode = True

        if result._task_fields['args'].get('_ansible_version'):
            self.ansible_version = \
                result._task_fields['args'].get('_ansible_version')

        if result._task._role:
            ansible_role = str(result._task._role)
        else:
            ansible_role = None

        if 'args' in result._task_fields:
            del result._task_fields['args']

        data = {}
        data['uuid'] = result._task._uuid
        data['session'] = self.session
        data['status'] = state
        data['timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S '
                                                       '+0000')
        data['host'] = self.host
        data['ip_address'] = self.ip_address
        data['user'] = self.user
        data['runtime'] = runtime
        data['ansible_version'] = self.ansible_version
        data['ansible_check_mode'] = self.ansible_check_mode
        data['ansible_host'] = result._host.name
        data['ansible_playbook'] = self.ansible_playbook
        data['ansible_role'] = ansible_role
        data['ansible_task'] = result._task_fields
        data['ansible_result'] = result._result

        # This wraps the json payload in and outer json event needed by Splunk
        jsondata = json.dumps(data, cls=AnsibleJSONEncoder, sort_keys=True)
        jsondata = '{"event":' + jsondata + "}"

        open_url(
            url,
            jsondata,
            headers={
                'Content-type': 'application/json',
                'Authorization': 'Splunk ' + authtoken
            },
            method='POST'
        )


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'splunk'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.start_datetimes = {}  # Collect task start times
        self.url = None
        self.authtoken = None
        self.splunk = SplunkHTTPCollectorSource()

    def _runtime(self, result):
        return (
            datetime.utcnow() -
            self.start_datetimes[result._task._uuid]
        ).total_seconds()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.url = self.get_option('url')

        if self.url is None:
            self.disabled = True
            self._display.warning('Splunk HTTP collector source URL was '
                                  'not provided. The Splunk HTTP collector '
                                  'source URL can be provided using the '
                                  '`SPLUNK_URL` environment variable or '
                                  'in the ansible.cfg file.')

        self.authtoken = self.get_option('authtoken')

        if self.authtoken is None:
            self.disabled = True
            self._display.warning('Splunk HTTP collector requires an authentication'
                                  'token. The Splunk HTTP collector '
                                  'authentication token can be provided using the '
                                  '`SPLUNK_AUTHTOKEN` environment variable or '
                                  'in the ansible.cfg file.')

    def v2_playbook_on_start(self, playbook):
        self.splunk.ansible_playbook = basename(playbook._file_name)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.start_datetimes[task._uuid] = datetime.utcnow()

    def v2_playbook_on_handler_task_start(self, task):
        self.start_datetimes[task._uuid] = datetime.utcnow()

    def v2_runner_on_ok(self, result, **kwargs):
        self.splunk.send_event(
            self.url,
            self.authtoken,
            'OK',
            result,
            self._runtime(result)
        )

    def v2_runner_on_skipped(self, result, **kwargs):
        self.splunk.send_event(
            self.url,
            self.authtoken,
            'SKIPPED',
            result,
            self._runtime(result)
        )

    def v2_runner_on_failed(self, result, **kwargs):
        self.splunk.send_event(
            self.url,
            self.authtoken,
            'FAILED',
            result,
            self._runtime(result)
        )

    def runner_on_async_failed(self, result, **kwargs):
        self.splunk.send_event(
            self.url,
            self.authtoken,
            'FAILED',
            result,
            self._runtime(result)
        )

    def v2_runner_on_unreachable(self, result, **kwargs):
        self.splunk.send_event(
            self.url,
            self.authtoken,
            'UNREACHABLE',
            result,
            self._runtime(result)
        )
