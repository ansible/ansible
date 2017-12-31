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
from datetime import datetime

try:
    import httplib
except ImportError:
    # Python 3
    import http.client as httplib

from ansible.plugins.callback import CallbackBase


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
        callback_whitelist = grafana
    and put the plugin in <path_to_callback_plugins_folder>

    This plugin makes use of the following environment variables:
        GRAFANA_SERVER   (optional): defaults to localhost
        GRAFANA_PORT     (optional): defaults to 3000
        GRAFANA_SECURE   (optional): Set to 1 if HTTPs is implemented on Grafana.
                                     defaults to 0 (false)
        GRAFANA_API_TOKEN          : Grafana API authentication token
    """

    CALLBACK_VERSION = 1.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'grafana'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        token = os.getenv('GRAFANA_API_TOKEN')
        self.secure = os.getenv('GRAFANA_SECURE', 0)
        if self.secure not in [0, 1]:
            self.secure = 0
        if token is None:
            self.disabled = True
            self._display.warning("GRAFANA_API_TOKEN not defined in the environment")
        self.grafana_server = os.getenv('GRAFANA_SERVER', 'localhost')
        self.grafana_port = int(os.getenv('GRAFANA_PORT', 3000))
        self.headers = {'Content-Type': 'application/json',
                        'Authorization': 'Bearer %s' % token}
        self.errors = 0
        self.hostname = socket.gethostname()
        self.username = getpass.getuser()
        self.start_time = datetime.now()

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook._file_name
        text = PLAYBOOK_START_TXT.format(playbook=self.playbook,
                                         hostname=self.hostname, username=self.username)
        data = {
            'time': to_millis(self.start_time),
            'text': text,
            'tags': ['ansible', 'ansible_event_start', self.playbook]
        }
        if int(self.secure) == 1:
            self.http = httplib.HTTPConnection(self.grafana_server, self.grafana_port)
        else:
            self.http = httplib.HTTPSConnection(self.grafana_server, self.grafana_port)
        self.http.request("POST", "/api/annotations", json.dumps(data), self.headers)
        print(json.dumps(data))

    def v2_playbook_on_stats(self, stats):
        end_time = datetime.now()
        duration = end_time - self.start_time
        summarize_stat = {}
        for host in stats.processed.keys():
            summarize_stat[host] = stats.summarize(host)

        if self.errors == 0:
            status = "OK"
        else:
            status = "FAILED"

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
        self.http = httplib.HTTPConnection(self.grafana_server, self.grafana_port)
        self.http.request("POST", "/api/annotations", json.dumps(data), self.headers)
        print(json.dumps(data))

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
        self.http = httplib.HTTPConnection(self.grafana_server, self.grafana_port)
        self.http.request("POST", "/api/annotations", json.dumps(data), self.headers)
        print(json.dumps(data))
