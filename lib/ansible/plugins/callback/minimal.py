# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: minimal
    type: stdout
    short_description: minimal Ansible screen output
    version_added: historical
    description:
        - This is the default output callback used by the ansible command (ad-hoc)
    extends_documentation_fragment:
      - result_format_callback
"""

from ansible.executor.task_result import CallbackTaskResult
from ansible.plugins.callback import CallbackBase
from ansible import constants as C


class CallbackModule(CallbackBase):

    """
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'minimal'

    def _command_generic_msg(self, host, result, caption):
        """ output the result of a command run """

        buf = "%s | %s | rc=%s >>\n" % (host, caption, result.get('rc', -1))
        buf += result.get('stdout', '')
        buf += result.get('stderr', '')
        buf += result.get('msg', '')

        return buf + "\n"

    def v2_runner_on_failed(self, result: CallbackTaskResult, ignore_errors: bool = False) -> None:
        self._handle_warnings_and_exception(result)

        if result.task.action in C.MODULE_NO_JSON and 'module_stderr' not in result.result:
            self._display.display(self._command_generic_msg(result.host.get_name(), result.result, "FAILED"), color=C.COLOR_ERROR)
        else:
            self._display.display("%s | FAILED! => %s" % (result.host.get_name(), self._dump_results(result.result, indent=4)), color=C.COLOR_ERROR)

    def v2_runner_on_ok(self, result: CallbackTaskResult) -> None:
        self._handle_warnings_and_exception(result)

        self._clean_results(result.result, result.task.action)

        if result.result.get('changed', False):
            color = C.COLOR_CHANGED
            state = 'CHANGED'
        else:
            color = C.COLOR_OK
            state = 'SUCCESS'

        if result.task.action in C.MODULE_NO_JSON and 'ansible_job_id' not in result.result:
            self._display.display(self._command_generic_msg(result.host.get_name(), result.result, state), color=color)
        else:
            self._display.display("%s | %s => %s" % (result.host.get_name(), state, self._dump_results(result.result, indent=4)), color=color)

    def v2_runner_on_skipped(self, result: CallbackTaskResult) -> None:
        self._handle_warnings_and_exception(result)

        self._display.display("%s | SKIPPED" % (result.host.get_name()), color=C.COLOR_SKIP)

    def v2_runner_on_unreachable(self, result: CallbackTaskResult) -> None:
        self._handle_warnings_and_exception(result)

        self._display.display("%s | UNREACHABLE! => %s" % (result.host.get_name(), self._dump_results(result.result, indent=4)), color=C.COLOR_UNREACHABLE)

    def v2_on_file_diff(self, result):
        if 'diff' in result.result and result.result['diff']:
            self._display.display(self._get_diff(result.result['diff']))
