# (c) 2012-2014, rongzeng54 <rongzeng54@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: binjson
    type: stdout
    short_description: Ansible screen output as JSON
    version_added: "2.6"
    description:
        - This callback converts ansible command (ad-hoc) into JSON output to stdout
    requirements:
      - Set as stdout in config
      - Set bin_ansible_callbacks = True
'''

import json

from ansible.plugins.callback import CallbackBase
from ansible import constants as C


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'binjson'

    def _command_generic_msg(self, host, result, caption):
        ''' output the result of a command run '''

        buf = {
            "host": host,
            "status": caption
        }

        if result._task.action in C.MODULE_NO_JSON and 'module_stderr' not in result._result:
            buf['rc'] = result._result.get('rc', -1)
            buf['stdout'] = result._result.get('stdout', '')
            buf['stderr'] = result._result.get('stderr', '')
            buf['msg'] = result._result.get('msg', '')
        else:
            buf['result'] = result._result

        return self._dump_results(buf, indent=4)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._handle_exception(result._result)
        self._handle_warnings(result._result)

        self._display.display(self._command_generic_msg(result._host.get_name(), result, "FAILED"), color=C.COLOR_ERROR)

    def v2_runner_on_ok(self, result):
        self._clean_results(result._result, result._task.action)
        self._handle_warnings(result._result)

        color = C.COLOR_OK
        if 'changed' in result._result and result._result['changed']:
            color = C.COLOR_CHANGED

        self._display.display(self._command_generic_msg(result._host.get_name(), result, "SUCCESS"), color=color)

    def v2_runner_on_skipped(self, result):
        self._display.display(self._command_generic_msg(result._host.get_name(), result, "SKIPPED"), color=C.COLOR_SKIP)

    def v2_runner_on_unreachable(self, result):
        self._display.display(self._command_generic_msg(result._host.get_name(), result, "UNREACHABLE"), color=C.COLOR_UNREACHABLE)
