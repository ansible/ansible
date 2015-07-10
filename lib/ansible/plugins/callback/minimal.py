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
        if 'exception' in result._result:
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + result._result['exception']

            self._display.display(msg, color='red')

            # finally, remove the exception from the result so it's not shown every time
            del result._result['exception']

        self._display.display("%s | FAILED! => %s" % (result._host.get_name(), result._result), color='red')

    def v2_runner_on_ok(self, result):
        self._display.display("%s | SUCCESS => %s" % (result._host.get_name(), json.dumps(result._result, indent=4)), color='green')

    def v2_runner_on_skipped(self, result):
        pass

    def v2_runner_on_unreachable(self, result):
        self._display.display("%s | UNREACHABLE!" % result._host.get_name(), color='yellow')

    def v2_runner_on_no_hosts(self, task):
        pass

    def v2_runner_on_async_poll(self, host, res, jid, clock):
        pass

    def v2_runner_on_async_ok(self, host, res, jid):
        pass

    def v2_runner_on_async_failed(self, host, res, jid):
        pass

    def v2_playbook_on_start(self):
        pass

    def v2_playbook_on_notify(self, host, handler):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        pass

    def v2_playbook_on_no_hosts_remaining(self):
        pass

    def v2_playbook_on_task_start(self, task, is_conditional):
        pass

    def v2_playbook_on_cleanup_task_start(self, task):
        pass

    def v2_playbook_on_handler_task_start(self, task):
        pass

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def v2_playbook_on_setup(self):
        pass

    def v2_playbook_on_import_for_host(self, result, imported_file):
        pass

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        pass

    def v2_playbook_on_play_start(self, play):
        pass

    def v2_playbook_on_stats(self, stats):
        pass

    def v2_playbook_on_exception(self, exception):
        pass

