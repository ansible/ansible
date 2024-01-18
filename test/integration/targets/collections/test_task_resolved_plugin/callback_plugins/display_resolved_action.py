# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    name: display_resolved_action
    type: aggregate
    short_description: Displays the requested and resolved actions at the end of a playbook.
    description:
        - Displays the requested and resolved actions in the format "requested == resolved".
    requirements:
      - Enable in configuration.
'''

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'display_resolved_action'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)
        self.requested_to_resolved = {}

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.requested_to_resolved[task.action] = task.resolved_action

    def v2_playbook_on_stats(self, stats):
        for requested, resolved in self.requested_to_resolved.items():
            self._display.display("%s == %s" % (requested, resolved), screen_only=True)
