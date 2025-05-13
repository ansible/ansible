# (c) 2024 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'callback_host_count'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._executing_hosts_counter = 0

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._display.display(task.name or task.action)

        if task.name == "start":
            self._executing_hosts_counter += 1

        # NOTE assumes 2 forks
        num_forks = 2
        if self._executing_hosts_counter > num_forks:
            # Exception is caught and turned into just a warning in TQM,
            # so raise BaseException to fail the test
            # To prevent seeing false positives in case the exception handling
            # in TQM is changed and BaseException is swallowed, print something
            # and ensure the test fails in runme.sh in such a case.
            self._display.display("host_pinned_test_failed")
            raise BaseException(
                "host_pinned test failed, number of hosts executing: "
                f"{self._executing_hosts_counter}, expected: {num_forks}"
            )

    def v2_playbook_on_handler_task_start(self, task):
        self._display.display(task.name or task.action)

    def v2_runner_on_ok(self, result):
        if result.task.name == "end":
            self._executing_hosts_counter -= 1
