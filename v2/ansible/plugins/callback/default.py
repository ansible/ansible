# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'

    def v2_on_any(self, *args, **kwargs):
        pass

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if 'exception' in result._result and self._display.verbosity < 3:
            del result._result['exception']
        self._display.display("fatal: [%s]: FAILED! => %s" % (result._host.get_name(), json.dumps(result._result, ensure_ascii=False)), color='red')

    def v2_runner_on_ok(self, result):

        if result._task.action == 'include':
            msg = 'included: %s for %s' % (result._task.args.get('_raw_params'), result._host.name)
            color = 'cyan'
        elif result._result.get('changed', False):
            msg = "changed: [%s]" % result._host.get_name()
            color = 'yellow'
        else:
            msg = "ok: [%s]" % result._host.get_name()
            color = 'green'

        if (self._display._verbosity > 0 or 'verbose_always' in result._result) and result._task.action not in ('setup', 'include'):
            indent = None
            if 'verbose_always' in result._result:
                indent = 4
                del result._result['verbose_always']
            msg += " => %s" % json.dumps(result._result, indent=indent, ensure_ascii=False)
        self._display.display(msg, color=color)

    def v2_runner_on_skipped(self, result):
        msg = "skipping: [%s]" % result._host.get_name()
        if self._display._verbosity > 0 or 'verbose_always' in result._result:
            indent = None
            if 'verbose_always' in result._result:
                indent = 4
                del result._result['verbose_always']
            msg += " => %s" % json.dumps(result._result, indent=indent, ensure_ascii=False)
        self._display.display(msg, color='cyan')

    def v2_runner_on_unreachable(self, result):
        self._display.display("fatal: [%s]: UNREACHABLE! => %s" % (result._host.get_name(), result._result), color='red')

    def v2_runner_on_no_hosts(self, task):
        pass

    def v2_runner_on_async_poll(self, result):
        pass

    def v2_runner_on_async_ok(self, result):
        pass

    def v2_runner_on_async_failed(self, result):
        pass

    def v2_runner_on_file_diff(self, result, diff):
        pass

    def v2_playbook_on_start(self):
        pass

    def v2_playbook_on_notify(self, result, handler):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        self._display.display("skipping: no hosts matched", color='cyan')

    def v2_playbook_on_no_hosts_remaining(self):
        self._display.banner("NO MORE HOSTS LEFT")

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._display.banner("TASK [%s]" % task.get_name().strip())

    def v2_playbook_on_cleanup_task_start(self, task):
        self._display.banner("CLEANUP TASK [%s]" % task.get_name().strip())

    def v2_playbook_on_handler_task_start(self, task):
        self._display.banner("RUNNING HANDLER [%s]" % task.get_name().strip())

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def v2_playbook_on_setup(self):
        pass

    def v2_playbook_on_import_for_host(self, result, imported_file):
        pass

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        pass

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        if not name:
            msg = "PLAY"
        else:
            msg = "PLAY [%s]" % name

        self._display.banner(name)

    def v2_playbook_on_stats(self, stats):
        pass

