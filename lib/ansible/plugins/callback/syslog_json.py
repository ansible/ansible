# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: syslog_json
    callback_type: notification
    requirements:
      - whitelist in configuration
    short_description: sends JSON events to syslog
    version_added: "1.9"
    description:
      - This plugin logs ansible-playbook and ansible runs to a syslog server in JSON format
      - Before 2.4 only environment variables were available for configuration
    options:
      server:
        description: syslog server that will receive the event
        env:
        - name: SYSLOG_SERVER
        default: localhost
        ini:
          - section: callback_syslog_json
            key: syslog_server
      port:
        description: port on which the syslog server is listening
        env:
          - name: SYSLOG_PORT
        default: 514
        ini:
          - section: callback_syslog_json
            key: syslog_port
      facility:
        description: syslog facility to log as
        env:
          - name: SYSLOG_FACILITY
        default: user
        ini:
          - section: callback_syslog_json
            key: syslog_facility
'''

import os
import json

import logging
import logging.handlers

import socket

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    logs ansible-playbook and ansible runs to a syslog server in json format
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'syslog_json'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

        self.logger = logging.getLogger('ansible logger')
        self.logger.setLevel(logging.DEBUG)

        self.handler = logging.handlers.SysLogHandler(
            address=(os.getenv('SYSLOG_SERVER', 'localhost'), int(os.getenv('SYSLOG_PORT', 514))),
            facility=os.getenv('SYSLOG_FACILITY', logging.handlers.SysLogHandler.LOG_USER)
        )
        self.logger.addHandler(self.handler)
        self.hostname = socket.gethostname()

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.logger.error('%s ansible-command: task execution FAILED; host: %s; message: %s', self.hostname, host, self._dump_results(res))

    def runner_on_ok(self, host, res):
        self.logger.info('%s ansible-command: task execution OK; host: %s; message: %s', self.hostname, host, self._dump_results(res))

    def runner_on_skipped(self, host, item=None):
        self.logger.info('%s ansible-command: task execution SKIPPED; host: %s; message: %s', self.hostname, host, 'skipped')

    def runner_on_unreachable(self, host, res):
        self.logger.error('%s ansible-command: task execution UNREACHABLE; host: %s; message: %s', self.hostname, host, self._dump_results(res))

    def runner_on_async_failed(self, host, res, jid):
        self.logger.error('%s ansible-command: task execution FAILED; host: %s; message: %s', self.hostname, host, self._dump_results(res))

    def playbook_on_import_for_host(self, host, imported_file):
        self.logger.info('%s ansible-command: playbook IMPORTED; host: %s; message: imported file %s', self.hostname, host, imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        self.logger.info('%s ansible-command: playbook NOT IMPORTED; host: %s; message: missing file %s', self.hostname, host, missing_file)
