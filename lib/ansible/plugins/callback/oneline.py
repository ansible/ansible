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

from ansible.plugins.callback import CallbackBase
from ansible import constants as C


class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'oneline'

    def _command_generic_msg(self, hostname, result,  caption):
        stdout = result.get('stdout','').replace('\n', '\\n')
        if 'stderr' in result and result['stderr']:
            stderr = result.get('stderr','').replace('\n', '\\n')
            return "%s | %s | rc=%s | (stdout) %s (stderr) %s" % (hostname, caption, result.get('rc',0), stdout, stderr)
        else:
            return "%s | %s | rc=%s | (stdout) %s" % (hostname, caption, result.get('rc',0), stdout)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if 'exception' in result._result:
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + result._result['exception'].replace('\n','')

            if result._task.action in C.MODULE_NO_JSON:
                self._display.display(self._command_generic_msg(result._host.get_name(), result._result,'FAILED'), color=C.COLOR_ERROR)
            else:
                self._display.display(msg, color=C.COLOR_ERROR)

            # finally, remove the exception from the result so it's not shown every time
            del result._result['exception']

        self._display.display("%s | FAILED! => %s" % (result._host.get_name(), self._dump_results(result._result, indent=0).replace('\n','')), color=C.COLOR_ERROR)

    def v2_runner_on_ok(self, result):
        if result._task.action in C.MODULE_NO_JSON:
            self._display.display(self._command_generic_msg(result._host.get_name(), result._result,'SUCCESS'), color=C.COLOR_OK)
        else:
            self._display.display("%s | SUCCESS => %s" % (result._host.get_name(), self._dump_results(result._result, indent=0).replace('\n','')), color=C.COLOR_OK)


    def v2_runner_on_unreachable(self, result):
        self._display.display("%s | UNREACHABLE!" % result._host.get_name(), color=C.COLOR_UNREACHABLE)

    def v2_runner_on_skipped(self, result):
        self._display.display("%s | SKIPPED" % (result._host.get_name()), color=C.COLOR_SKIP)
