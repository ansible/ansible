# (c) 2017, Ismael Puerto <ipuertofreire@gmail.com>
#
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
import logging
import socket
import uuid
import json

try:
    import graypy
    HAS_GRAYPY = True
except ImportError:
    HAS_GRAYPY = False

from datetime import datetime

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    ansible gelf callback plugin
    make sure you have in ansible.cfg:
        callback_plugins   = <path_to_callback_plugins_folder>
    and put the plugin in <path_to_callback_plugins_folder>

    Requires:
        python-graypy

    This plugin makes use of the following environment variables:
        GRAYLOG_SERVER   (optional): defaults to localhost
        GRAYLOG_PORT     (optional): defaults to 12201
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'gelf'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

        if not HAS_GRAYPY:
            self.disabled = True
            self._display.warning('The `graypy` python module is not installed.')

        else:
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.DEBUG)

            self.handler = graypy.GELFHandler(
                os.getenv('GRAYLOG_SERVER', 'localhost'),
                int(os.getenv('GRAYLOG_PORT', 12201)),
                debugging_fields=False,
            )
            self.logger.addHandler(self.handler)
            self.hostname = socket.gethostname()
            self.session = str(uuid.uuid1())
            self.errors = 0
            self.start_time = datetime.utcnow()

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook._file_name
        data = {
            'status': "OK",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "start",
            'ansible_playbook': self.playbook,
        }
        self.logger.info("ansible start", extra=data)

    def v2_playbook_on_stats(self, stats):
        end_time = datetime.utcnow()
        runtime = end_time - self.start_time
        summarize_stat = {}
        for host in stats.processed.keys():
            summarize_stat[host] = stats.summarize(host)

        if self.errors == 0:
            status = "OK"
        else:
            status = "FAILED"

        data = {
            'status': status,
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "finish",
            'ansible_playbook': self.playbook,
            'ansible_playbook_duration': runtime.total_seconds(),
            'ansible_result': json.dumps(summarize_stat),
        }
        self.logger.info("ansible stats", extra=data)

    def v2_runner_on_ok(self, result, **kwargs):
        data = {
            'status': "OK",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "task",
            'ansible_playbook': self.playbook,
            'ansible_host': result._host.name,
            'ansible_task': result._task,
            'ansible_result': self._dump_results(result._result)
        }
        self.logger.info("ansible ok", extra=data)

    def v2_runner_on_skipped(self, result, **kwargs):
        data = {
            'status': "SKIPPED",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "task",
            'ansible_playbook': self.playbook,
            'ansible_task': result._task,
            'ansible_host': result._host.name
        }
        self.logger.info("ansible skipped", extra=data)

    def v2_playbook_on_import_for_host(self, result, imported_file):
        data = {
            'status': "IMPORTED",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "import",
            'ansible_playbook': self.playbook,
            'ansible_host': result._host.name,
            'imported_file': imported_file
        }
        self.logger.info("ansible import", extra=data)

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        data = {
            'status': "NOT IMPORTED",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "import",
            'ansible_playbook': self.playbook,
            'ansible_host': result._host.name,
            'missing_file': missing_file
        }
        self.logger.info("ansible import", extra=data)

    def v2_runner_on_failed(self, result, **kwargs):
        data = {
            'status': "FAILED",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "task",
            'ansible_playbook': self.playbook,
            'ansible_host': result._host.name,
            'ansible_task': result._task,
            'ansible_result': self._dump_results(result._result)
        }
        self.errors += 1
        self.logger.error("ansible failed", extra=data)

    def v2_runner_on_unreachable(self, result, **kwargs):
        data = {
            'status': "UNREACHABLE",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "task",
            'ansible_playbook': self.playbook,
            'ansible_host': result._host.name,
            'ansible_task': result._task,
            'ansible_result': self._dump_results(result._result)
        }
        self.logger.error("ansbile unreachable", extra=data)

    def v2_runner_on_async_failed(self, result, **kwargs):
        data = {
            'status': "FAILED",
            'host': self.hostname,
            'session': self.session,
            'ansible_type': "task",
            'ansible_playbook': self.playbook,
            'ansible_host': result._host.name,
            'ansible_task': result._task,
            'ansible_result': self._dump_results(result._result)
        }
        self.errors += 1
        self.logger.error("ansible async", extra=data)
