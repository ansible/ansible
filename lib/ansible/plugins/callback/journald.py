from __future__ import (absolute_import, division, print_function)

import uuid

__metaclass__ = type

DOCUMENTATION = '''
    callback: journald
    callback_type: notification
    requirements:
      - whitelist in configuration
      - systemd-python (python library)
    short_description: Sends play events to systemd's journal
    version_added: "2.5.4"
    description:
        - This is an ansible callback plugin that sends status updates to the system journal during playbook execution.
    options:
      logger_name:
        required: False
        description: unit name the logs are written against
        env:
          - name: JOURNALD_LOGGER_NAME
        ini:
          - section: callback_journald
            key: logger_name
'''

import logging
import getpass
import os
from systemd.journal import JournalHandler
from ansible.plugins.callback import CallbackBase
from ansible.playbook.task_include import TaskInclude


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'journald'
    CALLBACK_TYPE = 'notification'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.logger = None
        self.logger_name = None
        self.username = getpass.getuser()
        self.playbook_name = None

        # use a random uuid to identify each playbook run
        self.playbook_id = uuid.uuid4()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys,
                                                var_options=var_options,
                                                direct=direct)

        self.logger_name = self.get_option('logger_name') or 'ansible'

        self.logger = logging.getLogger(self.logger_name)
        self.logger.addHandler(JournalHandler())
        self.logger.setLevel(logging.INFO)

    def _send_log(self, status, message):
        self.logger.info('%s - PlaybookId[%s] %s: %s', self.username, self.playbook_id, status, message)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if ignore_errors:
            return
        host = result._host
        self._send_log('failed: ', '[%s]' % (host.get_name()))

    def v2_runner_on_ok(self, _result):
        host = _result._host
        task = _result._task
        result = _result._result

        if isinstance(task, TaskInclude):
            return
        elif result.get('changed', False):
            status = 'changed'
        else:
            status = 'ok'

        delegated_vars = result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            msg = "[%s -> %s]" % (host.get_name(), delegated_vars['ansible_host'])
        else:
            msg = "[%s]" % (host.get_name())

        if task.loop and 'results' in result:
            self._process_items(_result)
        else:
            self._clean_results(result, task.action)

            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result) \
                    and '_ansible_verbose_override' not in result:
                msg += " => %s" % (result)
        self._send_log(status, msg)

    def v2_runner_on_skipped(self, result):
        host = result._host
        self._send_log('skipped: ', '[%s]' % (host.get_name()))

    def v2_runner_on_unreachable(self, result):
        host = result._host
        self._send_log('unreachable: ', '[%s]' % (host.get_name))

    def v2_playbook_on_start(self, playbook):
        self.playbook_name = os.path.basename(playbook._file_name)
        self._send_log('playbook started', self.playbook_name)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._send_log('task started', task)

    def v2_playbook_on_play_start(self, play):
        name = play.name or 'Play name not specified'
        self._send_log('play started', name)

    def v2_runner_item_on_failed(self, result):
        host = result._host
        self._send_log('item failed', '[%s]' % (host.get_name()))

    def v2_runner_item_on_skipped(self, result):
        host = result._host
        self._send_log('item skipped', '[%s]' % (host.get_name()))

    def v2_runner_retry(self, result):
        host = result._host
        self._send_log('retry', '[%s]' % (host.get_name()))

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""
        hosts = sorted(stats.processed.keys())
        ok = 0
        changed = 0
        failures = 0
        unreachable = 0
        for h in hosts:
            s = stats.summarize(h)
            ok += s['ok']
            changed += s['changed']
            failures += s['failures']
            unreachable += s['unreachable']

        status_line = 'OK:%s CHANGED:%s FAILURES:%s UNREACHABLE:%s' % (
            ok, changed, failures, unreachable
        )

        if failures or unreachable:
            final_status = 'Failed'
        else:
            final_status = 'Succeeded'

        self._send_log('COMPLETE', 'Playbook %s. %s' % (final_status, status_line))
