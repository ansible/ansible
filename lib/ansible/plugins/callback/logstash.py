# (C) 2018, Yevhen Khmelenko <ujenmr@gmail.com>
# (C) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: logstash
    type: notification
    author: Yevhen Khmelenko <ujenmr@gmail.com>
    short_description: Sends events to Logstash
    description:
      - This callback will report facts and task events to Logstash https://www.elastic.co/products/logstash
    version_added: "2.3"
    requirements:
      - whitelisting in configuration
      - logstash (python library)
    options:
      server:
        description: Address of the Logstash server
        env:
          - name: LOGSTASH_SERVER
        default: localhost
        ini:
          - section: callback_logstash
            key: server
      port:
        description: Port on which logstash is listening
        env:
          - name: LOGSTASH_PORT
        default: 5000
        ini:
          - section: callback_logstash
            key: port
      pre_command:
        description: Execute command before playbook start and set result to ansible_pre_command_output field
        env:
          - name: LOGSTASH_PRE_COMMAND
        version_added: "2.8"
        ini:
          - section: callback_logstash
            key: pre_command
      type:
        description: Message type
        env:
          - name: LOGSTASH_TYPE
        default: ansible
        ini:
          - section: callback_logstash
            key: type
'''

EXAMPLES = '''
examples: >
    1. Install python module python-logstash
        pip install python-logstash

    2. Enable callback plugin
    ansible.cfg:
        [defaults]
            callback_whitelist = logstash

    3. Setup logstash connection via environment variables or ansible.cfg
    environment variables:
        export LOGSTASH_SERVER=logstash.example.com
        export LOGSTASH_PORT=5000
        export LOGSTASH_PRE_COMMAND="git rev-parse HEAD"
        export LOGSTASH_TYPE=ansible

    or same in ansible.cfg:
        [callback_logstash]
        server = logstash.example.com
        port = 5000
        pre_command = git rev-parse HEAD
        type = ansible

    4. Add to logstash tcp-input
        logstash config:
            input {
                tcp {
                    port => 5000
                    codec => json
                }
            }
'''

import os
import json
import socket
import uuid
import logging
from datetime import datetime

try:
    import logstash
    HAS_LOGSTASH = True
except ImportError:
    HAS_LOGSTASH = False

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'logstash'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        if not HAS_LOGSTASH:
            self.disabled = True
            self._display.warning("The required python-logstash is not installed. "
                                  "pip install python-logstash")

        self.start_time = datetime.utcnow()

    def _init_plugin(self):
        self.logger = logging.getLogger('python-logstash-logger')
        self.logger.setLevel(logging.DEBUG)

        self.handler = logstash.TCPLogstashHandler(
            self.ls_server,
            self.ls_port,
            version=1,
            message_type=self.ls_type
        )

        self.logger.addHandler(self.handler)
        self.hostname = socket.gethostname()
        self.session = str(uuid.uuid4())
        self.errors = 0

        self.base_data = {
            'session': self.session,
            'host': self.hostname
        }

        if self.ls_pre_command is not None:
            self.base_data['ansible_pre_command_output'] = os.popen(
                self.ls_pre_command).read()

        if self._options is not None:
            self.base_data['ansible_checkmode'] = self._options.check
            self.base_data['ansible_tags'] = self._options.tags
            self.base_data['ansible_skip_tags'] = self._options.skip_tags
            self.base_data['inventory'] = self._options.inventory

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys,
                                                var_options=var_options,
                                                direct=direct)

        self.ls_server = self.get_option('server')
        self.ls_port = int(self.get_option('port'))
        self.ls_type = self.get_option('type')
        self.ls_pre_command = self.get_option('pre_command')

        self._init_plugin()

    def v2_playbook_on_start(self, playbook):
        data = self.base_data.copy()
        data['ansible_type'] = "start"
        data['status'] = "OK"
        data['ansible_playbook'] = playbook._file_name
        self.logger.info("START PLAYBOOK | %s", data['ansible_playbook'], extra=data)

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

        data = self.base_data.copy()
        data['ansible_type'] = "finish"
        data['status'] = status
        data['ansible_playbook_duration'] = runtime.total_seconds()
        data['ansible_result'] = json.dumps(summarize_stat)

        self.logger.info("FINISH PLAYBOOK | %s", json.dumps(summarize_stat), extra=data)

    def v2_playbook_on_play_start(self, play):
        self.play_id = str(play._uuid)

        if play.name:
            self.play_name = play.name

        data = self.base_data.copy()
        data['ansible_type'] = "start"
        data['status'] = "OK"
        data['ansible_play_id'] = self.play_id
        data['ansible_play_name'] = self.play_name

        self.logger.info("START PLAY | %s", self.play_name, extra=data)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task_id = str(task._uuid)

    '''
    Tasks and handler tasks are dealt with here
    '''

    def v2_runner_on_ok(self, result, **kwargs):
        task_name = str(result._task).replace('TASK: ', '').replace('HANDLER: ', '')

        data = self.base_data.copy()
        data['status'] = "OK"
        data['ansible_host'] = result._host.name
        data['ansible_play_id'] = self.play_id
        data['ansible_play_name'] = self.play_name
        data['ansible_task'] = task_name

        if task_name == 'setup':
            data['ansible_type'] = "setup"
            data['ansible_facts'] = self._dump_results(result._result)

            self.logger.info("SETUP FACTS | %s", self._dump_results(result._result), extra=data)
        else:
            if 'changed' in result._result.keys():
                data['ansible_changed'] = result._result['changed']
            else:
                data['ansible_changed'] = False
            data['ansible_type'] = "task"
            data['ansible_task_id'] = self.task_id
            data['ansible_result'] = self._dump_results(result._result)

            self.logger.info("TASK OK | %s | RESULT | %s",
                             task_name, self._dump_results(result._result), extra=data)

    def v2_runner_on_skipped(self, result, **kwargs):
        task_name = str(result._task).replace('TASK: ', '').replace('HANDLER: ', '')

        data = self.base_data.copy()
        if 'changed' in result._result.keys():
            data['ansible_changed'] = result._result['changed']
        else:
            data['ansible_changed'] = False
        data['ansible_type'] = "task"
        data['status'] = "SKIPPED"
        data['ansible_host'] = result._host.name
        data['ansible_play_id'] = self.play_id
        data['ansible_play_name'] = self.play_name
        data['ansible_task'] = task_name
        data['ansible_task_id'] = self.task_id
        data['ansible_result'] = self._dump_results(result._result)

        self.logger.info("TASK SKIPPED | %s", task_name, extra=data)

    def v2_playbook_on_import_for_host(self, result, imported_file):
        data = self.base_data.copy()
        data['ansible_type'] = "import"
        data['status'] = "IMPORTED"
        data['ansible_host'] = result._host.name
        data['ansible_play_id'] = self.play_id
        data['ansible_play_name'] = self.play_name
        data['imported_file'] = imported_file

        self.logger.info("IMPORT | %s", imported_file, extra=data)

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        data = self.base_data.copy()
        data['ansible_type'] = "import"
        data['status'] = "NOT IMPORTED"
        data['ansible_host'] = result._host.name
        data['ansible_play_id'] = self.play_id
        data['ansible_play_name'] = self.play_name
        data['imported_file'] = missing_file

        self.logger.info("NOT IMPORTED | %s", missing_file, extra=data)

    def v2_runner_on_failed(self, result, **kwargs):
        task_name = str(result._task).replace('TASK: ', '').replace('HANDLER: ', '')

        data = self.base_data.copy()
        if 'changed' in result._result.keys():
            data['ansible_changed'] = result._result['changed']
        else:
            data['ansible_changed'] = False

        data['ansible_type'] = "task"
        data['status'] = "FAILED"
        data['ansible_host'] = result._host.name
        data['ansible_play_id'] = self.play_id
        data['ansible_play_name'] = self.play_name
        data['ansible_task'] = task_name
        data['ansible_task_id'] = self.task_id
        data['ansible_result'] = self._dump_results(result._result)

        self.errors += 1
        self.logger.error("TASK FAILED | %s | HOST | %s | RESULT | %s", task_name,
                          self.hostname, self._dump_results(result._result), extra=data)

    def v2_runner_on_unreachable(self, result, **kwargs):
        task_name = str(result._task).replace('TASK: ', '').replace('HANDLER: ', '')

        data = self.base_data.copy()
        data['ansible_type'] = "task"
        data['status'] = "UNREACHABLE"
        data['ansible_host'] = result._host.name
        data['ansible_play_id'] = self.play_id
        data['ansible_play_name'] = self.play_name
        data['ansible_task'] = task_name
        data['ansible_task_id'] = self.task_id
        data['ansible_result'] = self._dump_results(result._result)

        self.errors += 1
        self.logger.error("UNREACHABLE | %s | HOST | %s | RESULT | %s", task_name,
                          self.hostname, self._dump_results(result._result), extra=data)

    def v2_runner_on_async_failed(self, result, **kwargs):
        task_name = str(result._task).replace('TASK: ', '').replace('HANDLER: ', '')

        data = self.base_data.copy()
        data['ansible_type'] = "task"
        data['status'] = "FAILED"
        data['ansible_host'] = result._host.name
        data['ansible_play_id'] = self.play_id
        data['ansible_play_name'] = self.play_name
        data['ansible_task'] = task_name
        data['ansible_task_id'] = self.task_id
        data['ansible_result'] = self._dump_results(result._result)

        self.errors += 1
        self.logger.error("ASYNC FAILED | %s | HOST | %s | RESULT | %s", task_name,
                          self.hostname, self._dump_results(result._result), extra=data)
