# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: display_resolved_action
    type: aggregate
    short_description: Displays the requested and resolved actions at the end of a playbook.
    description:
        - Displays the requested and resolved actions in the format "requested == resolved".
    options:
      test_on_task_start:
        description: Test using task.resolved_action before it is reliably resolved.
        default: False
        env:
          - name: ANSIBLE_TEST_ON_TASK_START
    requirements:
      - Enable in configuration.
"""

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'display_resolved_action'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)

    def v2_playbook_on_task_start(self, task, is_conditional):
        if self.get_option("test_on_task_start"):
            self._display.display(f"v2_playbook_on_task_start: {task.action} == {task.resolved_action}")

    def v2_runner_item_on_ok(self, result):
        self._display.display(f"v2_runner_item_on_ok: {result.task.action} == {result.task.resolved_action}")

    def v2_runner_on_ok(self, result):
        if not result.task.loop:
            self._display.display(f"v2_runner_on_ok: {result.task.action} == {result.task.resolved_action}")
