# (C) 2018, Samir Musali <samir.musali@logdna.com>

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: logdna
    callback_type: aggregate
    short_description: Sends playbook logs to LogDNA
    description:
      - This callback will report logs from playbook actions, tasks, and events to LogDNA (https://app.logdna.com)
    version_added: 0.1
    requirements:
      - whitelisting in configuration
    options:
      conf_key:
        required: True
        description: LogDNA Ingestion Key
        env:
          - name: LOGDNA_INGESTION_KEY
      plugin_ignore_errors:
        required: False
        description: Whether to ignore errors on failing or not
        env:
          - name: ANSIBLE_IGNORE_ERRORS
        default: False
      conf_hostname:
        required: False
        description: Alternative Host Name
        env:
          - name: LOGDNA_HOSTNAME
      conf_tags:
        required: False
        description: Tags
        env:
          - name: LOGDNA_TAGS
'''

import logging
import json
import pip
try:
    import logdna
except ImportError:
    pip.main(['install', 'logdna'])
from logdna import LogDNAHandler
from uuid import getnode
from socket import gethostname

from ansible.plugins.callback import CallbackBase

# Getting MAC Address of system:


def get_mac():
    mac = "%012x" % getnode()
    return ":".join(map(lambda index: mac[index:index + 2], xrange(int(len(mac) / 2))))

# Getting hostname of system


def get_hostname():
    return str(gethostname()).split('.local')[0]

# LogDNA Callback Module:


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 0.1
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'logdna'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):

        super(CallbackModule, self).__init__(display=display)

        self.disabled = True
        self.playbook_name = None
        self.playbook = None
        self.conf_key = None
        self.plugin_ignore_errors = None
        self.conf_hostname = None
        self.conf_tags = None

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.conf_key = self.get_option('conf_key')
        self.plugin_ignore_errors = self.get_option('plugin_ignore_errors')
        self.conf_hostname = self.get_option('conf_hostname')
        self.conf_tags = self.get_option('conf_tags')

        if self.plugin_ignore_errors is None:
            self.plugin_ignore_errors = False

        if self.conf_hostname is None:
            self.conf_hostname = get_hostname()

        if self.conf_tags is None:
            self.conf_tags = ['ansible']
        else:
            if type(self.conf_tags) is str:
                self.conf_tags = self.conf_tags.split(',')
            elif type(self.conf_tags) is not list:
                self.conf_tags = [str(self.conf_tags)]

        if self.conf_key is None:
            self.disabled = True
            self._display.warning('LogDNA Ingestion Key has not been provided!')
        else:
            self.disabled = False
            self.log = logging.getLogger('logdna')
            self.log.setLevel(logging.INFO)
            self.options = {'hostname': self.conf_hostname, 'mac': get_mac(), 'index_meta': True}
            self.log.addHandler(LogDNAHandler(self.conf_key, self.options))

    def sendLog(self, host, category, logdata):
        if not self.disabled:
            invocation = logdata['result'].pop('invocation', None)
            self.log.info(json.dumps(logdata), {'app': 'ansible', 'meta': {'playbook': self.playbook_name, 'host': host, 'category': category}})

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook
        self.playbook_name = playbook._file_name
        self.sendLog(self.conf_hostname, 'START', {'result': self.playbook_name})

    def v2_playbook_on_stats(self, stats):
        result = dict()
        for host in stats.processed.keys():
            result[host] = stats.summarize(host)
        self.sendLog(self.conf_hostname, 'STATS', {'result': result})

    def runner_on_failed(self, host, res, ignore_errors=False):
        if self.plugin_ignore_errors:
            ignore_errors = self.plugin_ignore_errors
        self.sendLog(host, 'FAILED', {'result': res, 'ignore_errors': ignore_errors})

    def runner_on_ok(self, host, res):
        self.sendLog(host, 'OK', {'result': res})

    def runner_on_async_failed(self, host, res, jid):
        self.sendLog(host, 'ASYNC_FAILED', {'result': res, 'job_id': jid})

    def runner_on_async_ok(self, host, res, jid):
        self.sendLog(host, 'ASYNC_OK', {'result': res, 'job_id': jid})
