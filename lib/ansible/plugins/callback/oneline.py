# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: oneline
    type: stdout
    short_description: oneline Ansible screen output
    version_added: historical
    description:
        - This is the output callback used by the C(-o)/C(--one-line) command line option.
"""

from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.template import Templar
from ansible.executor.task_result import CallbackTaskResult
from ansible.module_utils._internal import _deprecator


class CallbackModule(CallbackBase):

    """
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'oneline'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._display.deprecated(  # pylint: disable=ansible-deprecated-unnecessary-collection-name
            msg='The oneline callback plugin is deprecated.',
            version='2.23',
            deprecator=_deprecator.ANSIBLE_CORE_DEPRECATOR,  # entire plugin being removed; this improves the messaging
        )

    def _command_generic_msg(self, hostname, result, caption):
        stdout = result.get('stdout', '').replace('\n', '\\n').replace('\r', '\\r')
        if 'stderr' in result and result['stderr']:
            stderr = result.get('stderr', '').replace('\n', '\\n').replace('\r', '\\r')
            return "%s | %s | rc=%s | (stdout) %s (stderr) %s" % (hostname, caption, result.get('rc', -1), stdout, stderr)
        else:
            return "%s | %s | rc=%s | (stdout) %s" % (hostname, caption, result.get('rc', -1), stdout)

    def v2_runner_on_failed(self, result: CallbackTaskResult, ignore_errors: bool = False) -> None:
        if 'exception' in result.result:
            error_text = Templar().template(result.result['exception'])  # transform to a string
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = error_text.strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + error_text.replace('\n', '')

            if result.task.action in C.MODULE_NO_JSON and 'module_stderr' not in result.result:
                self._display.display(self._command_generic_msg(result.host.get_name(), result.result, 'FAILED'), color=C.COLOR_ERROR)
            else:
                self._display.display(msg, color=C.COLOR_ERROR)

        self._display.display("%s | FAILED! => %s" % (result.host.get_name(), self._dump_results(result.result, indent=0).replace('\n', '')),
                              color=C.COLOR_ERROR)

    def v2_runner_on_ok(self, result: CallbackTaskResult) -> None:

        if result.result.get('changed', False):
            color = C.COLOR_CHANGED
            state = 'CHANGED'
        else:
            color = C.COLOR_OK
            state = 'SUCCESS'

        if result.task.action in C.MODULE_NO_JSON and 'ansible_job_id' not in result.result:
            self._display.display(self._command_generic_msg(result.host.get_name(), result.result, state), color=color)
        else:
            self._display.display("%s | %s => %s" % (result.host.get_name(), state, self._dump_results(result.result, indent=0).replace('\n', '')),
                                  color=color)

    def v2_runner_on_unreachable(self, result: CallbackTaskResult) -> None:
        self._display.display("%s | UNREACHABLE!: %s" % (result.host.get_name(), result.result.get('msg', '')), color=C.COLOR_UNREACHABLE)

    def v2_runner_on_skipped(self, result: CallbackTaskResult) -> None:
        self._display.display("%s | SKIPPED" % (result.host.get_name()), color=C.COLOR_SKIP)
