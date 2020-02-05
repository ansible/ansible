# (c) 2020 Dzogovic Vehbo <dzove855@gmail.com>
# Forked from minimal plugin
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: customable
    type: stdout
    short_description: minimal Ansible screen output with customable args
    version_added: historical
    description:
        - Env Vars:
            ANSIBLE_CUSTOMABLE_SHOW_ONLY_HOST   - Display only the Hostnaöe
            ANSIBLE_CUSTOMABLE_NO_COLOR         - Disable Color Output 
            ANSIBLE_CUSTOMABLE_ONE_LINER        - Display as one liner
            ANSIBLE_CUSTOMABLE_SHOW_NO_HOST     - Don't show the hostname only the result
            ANSIBLE_CUSTOMABLE_SHOW_SUCCESS     - Display success result
            ANSIBLE_CUSTOMABLE_SHOW_CHANGED     - Display changed result
            ANSIBLE_CUSTOMABLE_SHOW_FAILED      - Display failed Result

        Note: To use only with Ad-Hoc commands
'''

import os
from ansible.plugins.callback import CallbackBase
from ansible import constants as C

class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 0.1
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'customable'
    toDisplayArr = []
    showOnlyHost = False
    color = True
    oneLiner = False
    showNoHost = False

    if os.getenv('ANSIBLE_CUSTOMABLE_SHOW_ONLY_HOST'): showOnlyHost = True
    if os.getenv('ANSIBLE_CUSTOMABLE_NO_COLOR'): color = False
    if os.getenv('ANSIBLE_CUSTOMABLE_ONE_LINER'): oneLiner = True
    if os.getenv('ANSIBLE_CUSTOMABLE_SHOW_NO_HOST'): showNoHost = True
    if os.getenv('ANSIBLE_CUSTOMABLE_SHOW_SUCCESS'): toDisplayArr.append('success')
    if os.getenv('ANSIBLE_CUSTOMABLE_SHOW_CHANGED'): toDisplayArr.append('changed')
    if os.getenv('ANSIBLE_CUSTOMABLE_SHOW_FAILED'): toDisplayArr.append('failed') 
    if not toDisplayArr: toDisplayArr = ['success','changed','failed']

    def _command_generic_msg(self, host, result, caption):
        ''' output the result of a command run '''

        if self.oneLiner is True:
            buf = "%s | %s | rc=%s >> " % (host, caption, result.get('rc', -1))
            buf += repr(result.get('stdout', ''))
            return buf
        else:
            if self.showNoHost is False:
                buf = "%s | %s | rc=%s >>\n" % (host, caption, result.get('rc', -1))
            else
                buf = ""
        buf += result.get('stdout', '')
        buf += result.get('stderr', '')
        buf += result.get('msg', '')

        return buf + "\n"

    def v2_runner_on_failed(self, result, ignore_errors=False):

        self._handle_exception(result._result)
        self._handle_warnings(result._result)

        if 'failed' in self.toDisplayArr:
            if self.showOnlyHost is True:
                self._display.display("%s" % (result._host.get_name()))
            else:
                if self.color is True:
                    self._display.display(self._command_generic_msg(result._host.get_name(), result._result, "FAILED"), color=C.COLOR_ERROR)
                else:
                    self._display.display(self._command_generic_msg(result._host.get_name(), result._result, "FAILED"))

    def v2_runner_on_ok(self, result):
        self._clean_results(result._result, result._task.action)

        self._handle_warnings(result._result)

        if result._result.get('changed', False):
            color = C.COLOR_CHANGED
            state = 'CHANGED'
        else:
            color = C.COLOR_OK
            state = 'SUCCESS'

        if state.lower() in self.toDisplayArr:
            if self.showOnlyHost is True:
                self._display.display("%s" % (result._host.get_name()))
            else:
                if self.color is True:
                    self._display.display(self._command_generic_msg(result._host.get_name(), result._result, state), color=color)
                else:
                    self._display.display(self._command_generic_msg(result._host.get_name(), result._result, state))

    def v2_runner_on_skipped(self, result):
        self._display.display("%s | SKIPPED" % (result._host.get_name()), color=C.COLOR_SKIP)

    def v2_runner_on_unreachable(self, result):
#        self._display.display("%s | UNREACHABLE! => %s" % (result._host.get_name(), self._dump_results(result._result, indent=4)), color=C.COLOR_UNREACHABLE)
        pass

    def v2_on_file_diff(self, result):
        if 'diff' in result._result and result._result['diff']:
            self._display.display(self._get_diff(result._result['diff']))
