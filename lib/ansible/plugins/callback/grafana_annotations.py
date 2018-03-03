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

try:
    import httplib
except ImportError:
    # Python 3
    import http.client as httplib

from ansible.plugins.callback import CallbackBase

DOCUMENTATION = '''
    callback: grafana_annotations
    type: notification
    short_description: send ansible events as annotations on charts to grafana over http api.
    description:
      - This callback will report start, failed and stats events to Grafana as annotations (https://grafana.com)
    version_added: "2.5"
    requirements:
      - whitelisting in configuration
    options:
      grafana_host:
        description: Grafana server address and port
        env:
          - name: GRAFANA_HOST
        default: 127.0.0.1:3000
      api_key:
        description: Grafana API key, allowing to authenticate when posting on the HTTP API.
                     If not provided, grafana_login and grafana_password will
                     be required.
        env:
          - name: GRAFANA_API_KEY
      grafana_user:
        description: Grafana user used for authentication. Ignored if api_key is provided.
        env:
          - name: GRAFANA_USER
      grafana_password:
        description: Grafana password used for authentication. Ignored if api_key is provided.
        env:
          - name: GRAFANA_PASSWORD
      grafana_dashboard_id:
        description: The grafana dashboard id where the annotation shall be created.
        env:
          - name: GRAFANA_DASHBOARD_ID
      grafana_panel_id:
        description: The grafana panel id where the annotation shall be created.
        env:
          - name: GRAFANA_PANEL_ID
'''


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

    CALLBACK_VERSION = 1.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'grafana_annotations'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        self.grafana_host = os.getenv('GRAFANA_HOST', '127.0.0.1:3000')
        self.secure = int(os.getenv('GRAFANA_SECURE', 0))
        if self.secure not in [0, 1]:
            self.secure = 0
        api_key = os.getenv('GRAFANA_API_KEY', None)
        grafana_user = os.getenv('GRAFANA_USER', None)
        grafana_password = os.getenv('GRAFANA_PASSWORD', '')
        self.dashboard_id = os.getenv('GRAFANA_DASHBOARD_ID', None)
        self.panel_id = os.getenv('GRAFANA_PANEL_ID', None)

        if api_key:
            authorization = "Bearer %s" % api_key
        elif grafana_user is not None:
            authorization = "Basic %s" % b64encode("%s:%s" % (grafana_user, grafana_password))
        else:
            self.disabled = True
            self._display.warning("Authentcation required, please set GRAFANA_API_KEY or GRAFANA_USER/GRAFANA_PASSWORD")
            return

        self.headers = {'Content-Type': 'application/json',
                        'Authorization': authorization}
        self.errors = 0
        self.hostname = socket.gethostname()
        self.username = getpass.getuser()
        self.start_time = datetime.now()

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
        if int(self.secure) == 1:
            self.http = httplib.HTTPSConnection(self.grafana_host)
        else:
            self.http = httplib.HTTPConnection(self.grafana_host)
        self.http.request("POST", "/api/annotations", annotation, self.headers)
        response = self.http.getresponse()
        if response.status != 200:
            self._display.warning("Grafana server responded with HTTP %d" % response.status)
