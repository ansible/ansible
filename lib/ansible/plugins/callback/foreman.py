# -*- coding: utf-8 -*-
# (c) 2015, 2016 Daniel Lobato <elobatocs@gmail.com>
# (c) 2016 Guido Günther <agx@sigxcpu.org>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: foreman
    type: notification
    short_description: Sends events to Foreman
    description:
      - This callback will report facts and task events to Foreman https://theforeman.org/
      - Before 2.4, if you wanted to use an ini configuration, the file must be placed in the same directory as this plugin and named foreman.ini
      - In 2.4 and above you can just put it in the main Ansible configuration file.
    version_added: "2.2"
    requirements:
      - whitelisting in configuration
      - requests (python library)
    options:
      url:
        description: URL to the Foreman server
        env:
          - name: FOREMAN_URL
        required: True
        default: http://localhost:3000
        ini:
          - section: callback_foreman
            key: url
      client_cert:
        description: X509 certificate to authenticate to Foreman if https is used
        env:
            - name: FOREMAN_SSL_CERT
        default: /etc/foreman/client_cert.pem
        ini:
          - section: callback_foreman
            key: ssl_cert
          - section: callback_foreman
            key: client_cert
        aliases: [ ssl_cert ]
      client_key:
        description: the corresponding private key
        env:
          - name: FOREMAN_SSL_KEY
        default: /etc/foreman/client_key.pem
        ini:
          - section: callback_foreman
            key: ssl_key
          - section: callback_foreman
            key: client_key
        aliases: [ ssl_key ]
      verify_certs:
        description:
          - Toggle to decide whether to verify the Foreman certificate.
          - It can be set to '1' to verify SSL certificates using the installed CAs or to a path pointing to a CA bundle.
          - Set to '0' to disable certificate checking.
        env:
          - name: FOREMAN_SSL_VERIFY
        default: 1
        ini:
          - section: callback_foreman
            key: verify_certs
'''

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

from ansible.module_utils._text import to_text
from ansible.plugins.callback import CallbackBase


def build_log(data):
    """
    Transform the internal log structure to one accepted by Foreman's
    config_report API.
    """
    for source, msg in data:
        if 'failed' in msg:
            level = 'err'
        elif 'changed' in msg and msg['changed']:
            level = 'notice'
        else:
            level = 'info'

        yield {
            "log": {
                'sources': {
                    'source': source,
                },
                'messages': {
                    'message': json.dumps(msg),
                },
                'level': level,
            }
        }


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'foreman'
    CALLBACK_NEEDS_WHITELIST = True

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S %f"

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.items = defaultdict(list)
        self.facts = defaultdict(dict)
        self.start_time = int(time.time())

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.FOREMAN_URL = self.get_option('url')
        self.FOREMAN_SSL_CERT = (self.get_option('client_cert'), self.get_option('client_key'))
        self.FOREMAN_SSL_VERIFY = str(self.get_option('verify_certs'))

        self.ssl_verify = self._ssl_verify()

        if HAS_REQUESTS:
            requests_version = requests.__version__.split('.')
            if int(requests_version[0]) < 2 or int(requests_version[1]) < 14:
                self._disable_plugin(u'The `requests` python module is too old.')
        else:
            self._disable_plugin(u'The `requests` python module is not installed.')

        if self.FOREMAN_URL.startswith('https://'):
            if not os.path.exists(self.FOREMAN_SSL_CERT[0]):
                self._disable_plugin(u'FOREMAN_SSL_CERT %s not found.' % self.FOREMAN_SSL_CERT[0])

            if not os.path.exists(self.FOREMAN_SSL_CERT[1]):
                self._disable_plugin(u'FOREMAN_SSL_KEY %s not found.' % self.FOREMAN_SSL_CERT[1])

    def _disable_plugin(self, msg):
        self.disabled = True
        if msg:
            self._display.warning(msg + u' Disabling the Foreman callback plugin.')
        else:
            self._display.warning(u'Disabling the Foreman callback plugin.')

    def _ssl_verify(self):
        if self.FOREMAN_SSL_VERIFY.lower() in ["1", "true", "on"]:
            verify = True
        elif self.FOREMAN_SSL_VERIFY.lower() in ["0", "false", "off"]:
            requests.packages.urllib3.disable_warnings()
            self._display.warning(u"SSL verification of %s disabled" %
                                  self.FOREMAN_URL)
            verify = False
        else:  # Set to a CA bundle:
            verify = self.FOREMAN_SSL_VERIFY
        return verify

    def send_facts(self):
        """
        Sends facts to Foreman, to be parsed by foreman_ansible fact
        parser.  The default fact importer should import these facts
        properly.
        """
        for host, facts in self.facts.items():
            facts = {
                "name": host,
                "facts": {
                    "ansible_facts": self.facts[host],
                    "_type": "ansible",
                    "_timestamp": datetime.now().strftime(self.TIME_FORMAT),
                },
            }

            try:
                r = requests.post(url=self.FOREMAN_URL + '/api/v2/hosts/facts',
                                  json=facts,
                                  cert=self.FOREMAN_SSL_CERT,
                                  verify=self.ssl_verify)
                r.raise_for_status()
            except requests.exceptions.RequestException as err:
                self._display.warning(u'Sending facts to Foreman at {url} failed for {host}: {err}'.format(
                    host=host, err=to_text(err), url=self.FOREMAN_URL))

    def send_reports(self, stats):
        """
        Send reports to Foreman to be parsed by its config report
        importer. THe data is in a format that Foreman can handle
        without writing another report importer.
        """
        status = defaultdict(lambda: 0)
        metrics = {}

        for host in stats.processed.keys():
            total = stats.summarize(host)
            status["applied"] = total['changed']
            status["failed"] = total['failures'] + total['unreachable']
            status["skipped"] = total['skipped']
            log = list(build_log(self.items[host]))
            metrics["time"] = {"total": int(time.time()) - self.start_time}
            now = datetime.now().strftime(self.TIME_FORMAT)
            report = {
                "config_report": {
                    "host": host,
                    "reported_at": now,
                    "metrics": metrics,
                    "status": status,
                    "logs": log,
                }
            }
            try:
                r = requests.post(url=self.FOREMAN_URL + '/api/v2/config_reports',
                                  json=report,
                                  cert=self.FOREMAN_SSL_CERT,
                                  verify=self.ssl_verify)
                r.raise_for_status()
            except requests.exceptions.RequestException as err:
                self._display.warning(u'Sending report to Foreman at {url} failed for {host}: {err}'.format(
                    host=host, err=to_text(err), url=self.FOREMAN_URL))
            self.items[host] = []

    def append_result(self, result):
        name = result._task.get_name()
        host = result._host.get_name()
        value = result._result
        self.items[host].append((name, value))
        if 'ansible_facts' in value:
            self.facts[host].update(value['ansible_facts'])

    # Ansible callback API
    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.append_result(result)

    def v2_runner_on_unreachable(self, result):
        self.append_result(result)

    def v2_runner_on_async_ok(self, result):
        self.append_result(result)

    def v2_runner_on_async_failed(self, result):
        self.append_result(result)

    def v2_playbook_on_stats(self, stats):
        self.send_facts()
        self.send_reports(stats)

    def v2_runner_on_ok(self, result):
        self.append_result(result)
