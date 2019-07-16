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

import os
import json
import socket
import getpass
from base64 import b64encode
from datetime import datetime

from ansible.module_utils._text import to_text
from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase


DOCUMENTATION = """
    callback: grafana_annotations
    callback_type: notification
    short_description: send ansible events as annotations on charts to grafana over http api.
    author: "Rémi REY (@rrey)"
    description:
      - This callback will report start, failed and stats events to Grafana as annotations (https://grafana.com)
    version_added: "2.6"
    requirements:
      - whitelisting in configuration
    options:
      grafana_url:
        description: Grafana annotations api URL
        required: True
        env:
          - name: GRAFANA_URL
        ini:
          - section: callback_grafana_annotations
            key: grafana_url
      validate_certs:
        description: validate the SSL certificate of the Grafana server. (For HTTPS url)
        env:
          - name: GRAFANA_VALIDATE_CERT
        ini:
          - section: callback_grafana_annotations
            key: validate_grafana_certs
          - section: callback_grafana_annotations
            key: validate_certs
        default: True
        type: bool
        aliases: [ validate_grafana_certs ]
      http_agent:
        description: The HTTP 'User-agent' value to set in HTTP requets.
        env:
          - name: HTTP_AGENT
        ini:
          - section: callback_grafana_annotations
            key: http_agent
        default: 'Ansible (grafana_annotations callback)'
      grafana_api_key:
        description: Grafana API key, allowing to authenticate when posting on the HTTP API.
                     If not provided, grafana_login and grafana_password will
                     be required.
        env:
          - name: GRAFANA_API_KEY
        ini:
          - section: callback_grafana_annotations
            key: grafana_api_key
      grafana_user:
        description: Grafana user used for authentication. Ignored if grafana_api_key is provided.
        env:
          - name: GRAFANA_USER
        ini:
          - section: callback_grafana_annotations
            key: grafana_user
        default: ansible
      grafana_password:
        description: Grafana password used for authentication. Ignored if grafana_api_key is provided.
        env:
          - name: GRAFANA_PASSWORD
        ini:
          - section: callback_grafana_annotations
            key: grafana_password
        default: ansible
      grafana_dashboard_id:
        description: The grafana dashboard id where the annotation shall be created.
        env:
          - name: GRAFANA_DASHBOARD_ID
        ini:
          - section: callback_grafana_annotations
            key: grafana_dashboard_id
      grafana_panel_id:
        description: The grafana panel id where the annotation shall be created.
        env:
          - name: GRAFANA_PANEL_ID
        ini:
          - section: callback_grafana_annotations
            key: grafana_panel_id
"""


PLAYBOOK_START_TXT = """\
Started playbook {playbook}

From '{hostname}'
By user '{username}'
"""

PLAYBOOK_ERROR_TXT = """\
Playbook {playbook} Failure !

From '{hostname}'
By user '{username}'

'{task}' failed on {host}

debug: {result}
"""

PLAYBOOK_STATS_TXT = """\
Playbook {playbook}
Duration: {duration}
Status: {status}

From '{hostname}'
By user '{username}'

Result:
{summary}
"""


def to_millis(dt):
    return int(dt.strftime('%s')) * 1000


class CallbackModule(CallbackBase):
    """
    ansible grafana callback plugin
    ansible.cfg:
        callback_plugins   = <path_to_callback_plugins_folder>
        callback_whitelist = grafana_annotations
    and put the plugin in <path_to_callback_plugins_folder>
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'grafana_annotations'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):

        super(CallbackModule, self).__init__(display=display)

        self.headers = {'Content-Type': 'application/json'}
        self.force_basic_auth = False
        self.hostname = socket.gethostname()
        self.username = getpass.getuser()
        self.start_time = datetime.now()
        self.errors = 0

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.grafana_api_key = self.get_option('grafana_api_key')
        self.grafana_url = self.get_option('grafana_url')
        self.validate_grafana_certs = self.get_option('validate_certs')
        self.http_agent = self.get_option('http_agent')
        self.grafana_user = self.get_option('grafana_user')
        self.grafana_password = self.get_option('grafana_password')
        self.dashboard_id = self.get_option('grafana_dashboard_id')
        self.panel_id = self.get_option('grafana_panel_id')

        if self.grafana_api_key:
            self.headers['Authorization'] = "Bearer %s" % self.grafana_api_key
        else:
            self.force_basic_auth = True

        if self.grafana_url is None:
            self.disabled = True
            self._display.warning('Grafana URL was not provided. The '
                                  'Grafana URL can be provided using '
                                  'the `GRAFANA_URL` environment variable.')
        self._display.debug('Grafana URL: %s' % self.grafana_url)

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook._file_name
        text = PLAYBOOK_START_TXT.format(playbook=self.playbook, hostname=self.hostname,
                                         username=self.username)
        data = {
            'time': to_millis(self.start_time),
            'text': text,
            'tags': ['ansible', 'ansible_event_start', self.playbook]
        }
        if self.dashboard_id:
            data["dashboardId"] = int(self.dashboard_id)
        if self.panel_id:
            data["panelId"] = int(self.panel_id)
        self._send_annotation(json.dumps(data))

    def v2_playbook_on_stats(self, stats):
        end_time = datetime.now()
        duration = end_time - self.start_time
        summarize_stat = {}
        for host in stats.processed.keys():
            summarize_stat[host] = stats.summarize(host)

        status = "FAILED"
        if self.errors == 0:
            status = "OK"

        text = PLAYBOOK_STATS_TXT.format(playbook=self.playbook, hostname=self.hostname,
                                         duration=duration.total_seconds(),
                                         status=status, username=self.username,
                                         summary=json.dumps(summarize_stat))

        data = {
            'time': to_millis(self.start_time),
            'timeEnd': to_millis(end_time),
            'isRegion': True,
            'text': text,
            'tags': ['ansible', 'ansible_report', self.playbook]
        }
        if self.dashboard_id:
            data["dashboardId"] = int(self.dashboard_id)
        if self.panel_id:
            data["panelId"] = int(self.panel_id)
        self._send_annotation(json.dumps(data))

    def v2_runner_on_failed(self, result, **kwargs):
        text = PLAYBOOK_ERROR_TXT.format(playbook=self.playbook, hostname=self.hostname,
                                         username=self.username, task=result._task,
                                         host=result._host.name, result=self._dump_results(result._result))
        data = {
            'time': to_millis(datetime.now()),
            'text': text,
            'tags': ['ansible', 'ansible_event_failure', self.playbook]
        }
        self.errors += 1
        if self.dashboard_id:
            data["dashboardId"] = int(self.dashboard_id)
        if self.panel_id:
            data["panelId"] = int(self.panel_id)
        self._send_annotation(json.dumps(data))

    def _send_annotation(self, annotation):
        try:
            response = open_url(self.grafana_url, data=annotation, headers=self.headers,
                                method="POST",
                                validate_certs=self.validate_grafana_certs,
                                url_username=self.grafana_user, url_password=self.grafana_password,
                                http_agent=self.http_agent, force_basic_auth=self.force_basic_auth)
        except Exception as e:
            self._display.error(u'Could not submit message to Grafana: %s' % to_text(e))
