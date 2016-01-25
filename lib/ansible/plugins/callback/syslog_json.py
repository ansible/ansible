# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json

import logging
import logging.handlers

import socket

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    """
    logs ansible-playbook and ansible runs to a syslog server in json format
    make sure you have in ansible.cfg:
        callback_plugins   = <path_to_callback_plugins_folder>
    and put the plugin in <path_to_callback_plugins_folder>
    
    This plugin makes use of the following environment variables:
        SYSLOG_SERVER   (optional): defaults to localhost
        SYSLOG_PORT     (optional): defaults to 514
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'syslog_json'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

        self.logger =  logging.getLogger('ansible logger')
        self.logger.setLevel(logging.DEBUG)

        self.handler = logging.handlers.SysLogHandler(
            address = (os.getenv('SYSLOG_SERVER','localhost'),
                       os.getenv('SYSLOG_PORT',514)), 
            facility=logging.handlers.SysLogHandler.LOG_USER
        )
        self.logger.addHandler(self.handler)
        self.hostname = socket.gethostname()


    def runner_on_failed(self, host, res, ignore_errors=False):
        self.logger.error('%s ansible-command: task execution FAILED; host: %s; message: %s' % (self.hostname,host,self._dump_results(res)))

    def runner_on_ok(self, host, res):
        self.logger.info('%s ansible-command: task execution OK; host: %s; message: %s' % (self.hostname,host,self._dump_results(res)))

    def runner_on_skipped(self, host, item=None):
        self.logger.info('%s ansible-command: task execution SKIPPED; host: %s; message: %s' % (self.hostname,host, 'skipped'))

    def runner_on_unreachable(self, host, res):
        self.logger.error('%s ansible-command: task execution UNREACHABLE; host: %s; message: %s' % (self.hostname,host,self._dump_results(res)))

    def runner_on_async_failed(self, host, res):
        self.logger.error('%s ansible-command: task execution FAILED; host: %s; message: %s' % (self.hostname,host,self._dump_results(res)))

    def playbook_on_import_for_host(self, host, imported_file):
        self.logger.info('%s ansible-command: playbook IMPORTED; host: %s; message: imported file %s' % (self.hostname,host,imported_file))

    def playbook_on_not_import_for_host(self, host, missing_file):
        self.logger.info('%s ansible-command: playbook NOT IMPORTED; host: %s; message: missing file %s' % (self.hostname,host,missing_file))
