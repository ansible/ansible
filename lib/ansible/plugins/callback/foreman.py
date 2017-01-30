# -*- coding: utf-8 -*-
# (C) 2015, 2016 Daniel Lobato <elobatocs@gmail.com>
#     2016 Guido Günther <agx@sigxcpu.org>
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
from datetime import datetime
from collections import defaultdict
import json
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    This callback will report facts and reports to Foreman https://theforeman.org/

    It makes use of the following environment variables:

    FOREMAN_URL: URL to the Foreman server
    FOREMAN_SSL_CERT: X509 certificate to authenticate to Foreman if
      https is used
    FOREMAN_SSL_KEY: the corresponding private key
    FOREMAN_SSL_VERIFY: whether to verify the Foreman certificate
      It can be set to '1' to verify SSL certificates using the
      installed CAs or to a path pointing to a CA bundle. Set to '0'
      to disable certificate checking.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'foreman'
    CALLBACK_NEEDS_WHITELIST = True

    FOREMAN_URL = os.getenv('FOREMAN_URL', "http://localhost:3000")
    FOREMAN_SSL_CERT = (os.getenv('FOREMAN_SSL_CERT',
                                  "/etc/foreman/client_cert.pem"),
                        os.getenv('FOREMAN_SSL_KEY',
                                  "/etc/foreman/client_key.pem"))
    FOREMAN_SSL_VERIFY = os.getenv('FOREMAN_SSL_VERIFY', "1")
    FOREMAN_HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S %f"

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.items = defaultdict(list)
        self.start_time = int(time.time())

        if HAS_REQUESTS:
            requests_major = int(requests.__version__.split('.')[0])
            if requests_major >= 2:
                self.ssl_verify = self._ssl_verify()
            else:
                self._disable_plugin('The `requests` python module is too old.')
        else:
            self._disable_plugin('The `requests` python module is not installed.')

    def _disable_plugin(self, msg):
        self.disabled = True
        self._display.warning(msg + ' Disabling the Foreman callback plugin.')

    def _ssl_verify(self):
        if self.FOREMAN_SSL_VERIFY.lower() in ["1", "true", "on"]:
            verify = True
        elif self.FOREMAN_SSL_VERIFY.lower() in ["0", "false", "off"]:
            requests.packages.urllib3.disable_warnings()
            self._display.warning("SSL verification of %s disabled" %
                                  self.FOREMAN_URL)
            verify = False
        else:  # Set ta a CA bundle:
            verify = self.FOREMAN_SSL_VERIFY
        return verify

    def send_facts(self, host, data):
        """
        Sends facts to Foreman, to be parsed by foreman_ansible fact
        parser.  The default fact importer should import these facts
        properly.
        """
        data["_type"] = "ansible"
        data["_timestamp"] = datetime.now().strftime(self.TIME_FORMAT)
        facts = {"name": host,
                 "facts": data,
                 }
        requests.post(url=self.FOREMAN_URL + '/api/v2/hosts/facts',
                      data=json.dumps(facts),
                      headers=self.FOREMAN_HEADERS,
                      cert=self.FOREMAN_SSL_CERT,
                      verify=self.ssl_verify)

    def _build_log(self, data):
        logs = []
        for entry in data:
            source, msg = entry
            if 'failed' in msg:
                level = 'err'
            else:
                level = 'notice' if 'changed' in msg and msg['changed'] else 'info'
            logs.append({"log": {
                'sources': {'source': source},
                'messages': {'message': json.dumps(msg)},
                'level':     level
                }})
        return logs

    def send_reports(self, stats):
        """
        Send reports to Foreman to be parsed by its config report
        importer. THe data is in a format that Foreman can handle
        without writing another report importer.
        """
        status = defaultdict(lambda: 0)
        metrics = {}

        for host in stats.processed.keys():
            sum = stats.summarize(host)
            status["applied"] = sum['changed']
            status["failed"] = sum['failures'] + sum['unreachable']
            status["skipped"] = sum['skipped']
            log = self._build_log(self.items[host])
            metrics["time"] = {"total": int(time.time()) - self.start_time}
            now = datetime.now().strftime(self.TIME_FORMAT)
            report = {
                "report": {
                    "host": host,
                    "reported_at": now,
                    "metrics": metrics,
                    "status": status,
                    "logs": log,
                    }
                }
            # To be changed to /api/v2/config_reports in 1.11.  Maybe we
            # could make a GET request to get the Foreman version & do
            # this automatically.
            requests.post(url=self.FOREMAN_URL + '/api/v2/reports',
                          data=json.dumps(report),
                          headers=self.FOREMAN_HEADERS,
                          cert=self.FOREMAN_SSL_CERT,
                          verify=self.ssl_verify)
            self.items[host] = []

    def append_result(self, result):
        name = result._task.get_name()
        host = result._host.get_name()
        self.items[host].append((name, result._result))

    # Ansible callback API
    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.append_result(result)

    def v2_runner_on_unreachable(self, result):
        self.append_result(result)

    def v2_runner_on_async_ok(self, result, jid):
        self.append_result(result)

    def v2_runner_on_async_failed(self, result, jid):
        self.append_result(result)

    def v2_playbook_on_stats(self, stats):
        self.send_reports(stats)

    def v2_runner_on_ok(self, result):
        res = result._result
        try:
            module = res['invocation']['module_name']
        except KeyError:
            module = None
        if module == 'setup':
            host = result._host.get_name()
            self.send_facts(host, res)
        else:
            self.append_result(result)
