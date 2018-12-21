# (c) 2018, Samir Musali <samir.musali@logdna.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: logdna
    callback_type: aggregate
    short_description: Sends playbook logs to LogDNA
    description:
      - This callback will report logs from playbook actions, tasks, and events to LogDNA (https://app.logdna.com)
    version_added: "2.7"
    requirements:
      - LogDNA Python Library (https://github.com/logdna/python)
      - whitelisting in configuration
    options:
      conf_key:
        required: True
        description: LogDNA Ingestion Key
        type: string
        env:
          - name: LOGDNA_INGESTION_KEY
        ini:
          - section: callback_logdna
            key: conf_key
      plugin_ignore_errors:
        required: False
        description: Whether to ignore errors on failing or not
        type: boolean
        env:
          - name: ANSIBLE_IGNORE_ERRORS
        ini:
          - section: callback_logdna
            key: plugin_ignore_errors
        default: False
      conf_hostname:
        required: False
        description: Alternative Host Name; the current host name by default
        type: string
        env:
          - name: LOGDNA_HOSTNAME
        ini:
          - section: callback_logdna
            key: conf_hostname
      conf_tags:
        required: False
        description: Tags
        type: string
        env:
          - name: LOGDNA_TAGS
        ini:
          - section: callback_logdna
            key: conf_tags
        default: ansible
'''

import logging
import json
import socket
from uuid import getnode
from ansible.plugins.callback import CallbackBase
from ansible.parsing.ajson import AnsibleJSONEncoder

try:
    from logdna import LogDNAHandler
    HAS_LOGDNA = True
except ImportError:
    HAS_LOGDNA = False


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
    except Exception:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP


# Is it JSON?
def isJSONable(obj):
    try:
        json.dumps(obj, sort_keys=True, cls=AnsibleJSONEncoder)
        return True
    except Exception:
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

        if self.conf_hostname is None:
            self.conf_hostname = get_hostname()

        self.conf_tags = self.conf_tags.split(',')

        if HAS_LOGDNA:
            self.log = logging.getLogger('logdna')
            self.log.setLevel(logging.INFO)
            self.options = {'hostname': self.conf_hostname, 'mac': self.mac, 'index_meta': True}
            self.log.addHandler(LogDNAHandler(self.conf_key, self.options))
            self.disabled = False
        else:
            self.disabled = True
            self._display.warning('WARNING:\nPlease, install LogDNA Python Package: `pip install logdna`')

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

    def sanitizeJSON(self, data):
        try:
            return json.loads(json.dumps(data, sort_keys=True, cls=AnsibleJSONEncoder))
        except Exception:
            return {'warnings': ['JSON Formatting Issue', json.dumps(data, sort_keys=True, cls=AnsibleJSONEncoder)]}

    def flush(self, log, options):
        if HAS_LOGDNA:
            self.log.info(json.dumps(log), options)

    def sendLog(self, host, category, logdata):
        options = {'app': 'ansible', 'meta': {'playbook': self.playbook_name, 'host': host, 'category': category}}
        logdata['info'].pop('invocation', None)
        warnings = logdata['info'].pop('warnings', None)
        if warnings is not None:
            self.flush({'warn': warnings}, options)
        self.flush(logdata, options)

    def v2_playbook_on_start(self, playbook):
        self.playbook = playbook
        self.playbook_name = playbook._file_name

    def v2_playbook_on_stats(self, stats):
        result = dict()
        for host in stats.processed.keys():
            result[host] = stats.summarize(host)
        self.sendLog(self.conf_hostname, 'STATS', {'info': self.sanitizeJSON(result)})

    def runner_on_failed(self, host, res, ignore_errors=False):
        if self.plugin_ignore_errors:
            ignore_errors = self.plugin_ignore_errors
        self.sendLog(host, 'FAILED', {'info': self.sanitizeJSON(res), 'ignore_errors': ignore_errors})

    def runner_on_ok(self, host, res):
        self.sendLog(host, 'OK', {'info': self.sanitizeJSON(res)})

    def runner_on_unreachable(self, host, res):
        self.sendLog(host, 'UNREACHABLE', {'info': self.sanitizeJSON(res)})

    def runner_on_async_failed(self, host, res, jid):
        self.sendLog(host, 'ASYNC_FAILED', {'info': self.sanitizeJSON(res), 'job_id': jid})

    def runner_on_async_ok(self, host, res, jid):
        self.sendLog(host, 'ASYNC_OK', {'info': self.sanitizeJSON(res), 'job_id': jid})
