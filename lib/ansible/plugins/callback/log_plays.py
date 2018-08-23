# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2018, Luka Matijevic <lumatijev@gmail.com>
# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: log_plays
    type: notification
    short_description: write playbook output to log file
    version_added: historical
    author:
      - Michael DeHaan (@mpdehaan)
      - Luka Matijevic (@lumatijev)
    description:
      - This callback writes playbook output to a file per host in the configured log directory
    extends_documentation_fragment:
      - default_callback
    requiremets:
      - whitelist in configuration
      - configured log directory must be writeable by the user executing Ansible on the controller
    notes:
      - log_filename_timestamp_format and timestamp_format options must be strftime valid format codes
      - log_format option has access to timestamp, category and data named variables
      - data_format option value raw will cause callback to output json plus stdout and stderr each in it's own line
    options:
      log_directory:
        description: The directory where log files will be stored
        env:
          - name: LOG_PLAYS_DIRECTORY
        ini:
          - section: callback_log_plays
            key: log_directory
        default: /var/log/ansible/hosts
        name: Log directory
        type: path
      log_filename_timestamp:
        description: Toggle to control diplaying timestamp in log filename
        env:
          - name: LOG_PLAYS_FILENAME_TIMESTAMP
        ini:
          - section: callback_log_plays
            key: log_filename_timestamp
        default: False
        name: Log filename timestamp
        type: boolean
      log_filename_timestamp_format:
        description: The format to use when diplaying timestamp in log filename
        env:
          - name: LOG_PLAYS_FILENAME_TIMESTAMP_FORMAT
        ini:
          - section: callback_log_plays
            key: log_filename_timestamp_format
        default: '%s'
        name: Log filename timestamp format
        type: string
      log_format:
        description: The format to use when writing output to log files
        env:
          - name: LOG_PLAYS_LOG_FORMAT
        ini:
          - section: callback_log_plays
            key: log_format
        default: '%(timestamp)s - %(task)s - %(module)s - %(category)s - %(data)s\\n\\n'
        name: Log format
        type: string
      timestamp_format:
        description: The format to use when writing timestamp in output to log files
        env:
          - name: LOG_PLAYS_TIME_FORMAT
        ini:
          - section: callback_log_plays
            key: timestamp_format
        default: '%b %d %Y %H:%M:%S'
        name: Log timestamp format
        type: string
      data_format:
        description: The data format to use when writing output to log files
        choices: [json, yaml, raw]
        env:
          - name: LOG_PLAYS_DATA_FORMAT
        ini:
          - section: callback_log_plays
            key: data_format
        default: json
        name: Log data format
        type: choice
'''

import os
import time
import json
import yaml

from collections import MutableMapping
from datetime import datetime

from ansible.plugins.callback import CallbackBase
from ansible.module_utils._text import to_bytes
from ansible.parsing.yaml.dumper import AnsibleDumper

# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.


class CallbackModule(CallbackBase):
    '''
    log playbook results, per host, in the configured directory
    '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'log_plays'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.log_directory = self.get_option('log_directory')
        self.log_filename_timestamp = self.get_option('log_filename_timestamp')
        self.log_filename_timestamp_format = self.get_option('log_filename_timestamp_format')
        self.log_format = self.get_option('log_format')
        self.timestamp_format = self.get_option('timestamp_format')
        self.data_format = self.get_option('data_format')

        if not os.path.isdir(self.log_directory) or not os.access(self.log_directory, os.W_OK | os.X_OK):
            self.disabled = True
            self._display.error('Configured log directory does not exist or it is not writable. Disabling the log_plays callback plugin.')

        if self.data_format not in ('json', 'yaml', 'raw'):
            self.data_format = 'json'
            self._display.warning('Incorrect data format for log_plays callback plugin. Using default (json).')

    def log(self, host, category, data):
        if isinstance(data, MutableMapping):
            if '_ansible_verbose_override' in data:
                # avoid logging extraneous data
                data = 'omitted'
            else:
                task = self.task
                module = self.module
                data = data.copy()

                if self.data_format == 'json' or self.data_format == 'raw':
                    invocation = data.pop('invocation', None)
                    json_data = '%s => %s' % (json.dumps(invocation), json.dumps(data)) if invocation is not None else json.dumps(data)

                    if self.data_format == 'raw':
                        data.pop('stdout_lines', None)
                        data.pop('stderr_lines', None)

                        stdout = data.pop('stdout', '')
                        stderr = data.pop('stderr', '')

                        if stdout != '':
                            stdout = '\n\nSTDOUT:\n\n%s' % stdout

                        if stderr != '':
                            stderr = '\n\nSTDERR:\n\n%s' % stderr

                        data = '%s%s%s' % (json_data, stdout, stderr)
                    else:
                        data = json_data
                elif self.data_format == 'yaml':
                    data = yaml.dump(data, width=1000, Dumper=AnsibleDumper, default_flow_style=False)

            path = os.path.join(self.log_directory, host)

            if self.log_filename_timestamp:
                path += '-%s' % datetime.fromtimestamp(self.start_timestamp).strftime(self.log_filename_timestamp_format)

            timestamp = time.strftime(self.timestamp_format, time.localtime())
            msg = to_bytes(self.log_format.decode('string_escape') % dict(timestamp=timestamp, task=task, module=module, category=category, data=data))

            with open(path, 'ab') as fd:
                fd.write(msg)

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.log(host, 'FAILED', res)

    def runner_on_ok(self, host, res):
        self.log(host, 'OK', res)

    def runner_on_skipped(self, host, item=None):
        self.log(host, 'SKIPPED', '...')

    def runner_on_unreachable(self, host, res):
        self.log(host, 'UNREACHABLE', res)

    def runner_on_async_failed(self, host, res, jid):
        self.log(host, 'ASYNC_FAILED', res)

    def playbook_on_import_for_host(self, host, imported_file):
        self.log(host, 'IMPORTED', imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        self.log(host, 'NOTIMPORTED', missing_file)

    def v2_playbook_on_start(self, playbook):
        self.start_timestamp = time.time()
        self.playbook_on_start()

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task = task.name
        self.module = task.action
        self.playbook_on_task_start(task.name, is_conditional)
