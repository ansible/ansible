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
import sys
import socket
import time
from uuid import getnode
from ansible.plugins.callback import CallbackBase
from ansible.module_utils.urls import open_url

try:
    from logdna import LogDNAHandler
    HAS_LOGDNA = True
except ImportError:
    HAS_LOGDNA = False
    IS_PY2 = (sys.version_info[0] == 2)
    LOGDNA_URL = 'https://logs.logdna.com/logs/ingest'
    MAX_LINE_LENGTH = 32000
    if IS_PY2:
        from urllib import urlencode
    else:
        from urllib.parse import urlencode


# Getting MAC Address of system:
def get_mac():
    mac = "%012x" % getnode()
    return ":".join(map(lambda index: mac[index:index + 2], range(int(len(mac) / 2))))


# Getting hostname of system:
def get_hostname():
    return str(socket.gethostname()).split('.local')[0]


# Getting IP of system:
def get_ip():
    try:
        return socket.gethostbyname(get_hostname())
    except:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP


# Is it JSON?
def isJSONable(obj):
    try:
        json.dumps(obj)
        return True
    except:
        return False


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
        self.mac = get_mac()
        self.ip = get_ip()

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
            if HAS_LOGDNA:
                self.log = logging.getLogger('logdna')
                self.log.setLevel(logging.INFO)
                self.options = {'hostname': self.conf_hostname, 'mac': self.mac, 'index_meta': True}
                self.log.addHandler(LogDNAHandler(self.conf_key, self.options))
            else:
                self.params = dict()
                self.params['hostname'] = self.conf_hostname
                self.params['ip'] = self.ip
                self.params['mac'] = self.mac
                self.params['tags'] = self.conf_tags

    def metaIndexing(self, meta):
        invalidKeys = []
        ninvalidKeys = 0
        for key, value in meta.items():
            if not isJSONable(value):
                invalidKeys.append(key)
                ninvalidKeys += 1
        if ninvalidKeys > 0:
            for key in invalidKeys:
                del meta[key]
            meta['__errors'] = 'These keys have been sanitized: ' + ', '.join(invalidKeys)
        return meta

    def flush(self, log, options):
        if HAS_LOGDNA:
            self.log.info(json.dumps(log), options)
        else:
            message = dict()
            message['hostname'] = self.conf_hostname
            message['timestamp'] = int(time.time() * 1000)
            message['line'] = json.dumps(log)
            message['level'] = 'info'
            message['app'] = options['app']
            message['env'] = ''
            message['meta'] = self.metaIndexing(options['meta'])
            if len(message['line']) > MAX_LINE_LENGTH:
                message['line'] = message['line'][:MAX_LINE_LENGTH] + ' (cut off, too long...)'
            url = LOGDNA_URL + '?' + urlencode(self.params)
            data = {'e': 'ls', 'ls': [message]}
            open_url(url, data=data, method='POST', force=True, timeout=30, url_username='user', url_password=self.conf_key)

    def sendLog(self, host, category, logdata):
        if not self.disabled:
            options = {'app': 'ansible', 'meta': {'playbook': self.playbook_name, 'host': host, 'category': category}}
            logdata['result'].pop('invocation', None)
            warnings = logdata['result'].pop('warnings', None)
            if warnings is not None:
                self.flush({'warn': warnings}, options)
            self.flush((logdata), options)

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook
        self.playbook_name = playbook._file_name

    def v2_playbook_on_stats(self, stats):
        result = dict()
        for host in stats.processed.keys():
            result[host] = stats.summarize(host)
        self.sendLog(self.conf_hostname, 'STATS', {'info': result})

    def runner_on_failed(self, host, res, ignore_errors=False):
        if self.plugin_ignore_errors:
            ignore_errors = self.plugin_ignore_errors
        self.sendLog(host, 'FAILED', {'info': res, 'ignore_errors': ignore_errors})

    def runner_on_ok(self, host, res):
        self.sendLog(host, 'OK', {'info': res})

    def runner_on_async_failed(self, host, res, jid):
        self.sendLog(host, 'ASYNC_FAILED', {'info': res, 'job_id': jid})

    def runner_on_async_ok(self, host, res, jid):
        self.sendLog(host, 'ASYNC_OK', {'info': res, 'job_id': jid})
