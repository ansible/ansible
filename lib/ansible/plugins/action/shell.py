# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        # Shell module is implemented via command with a special arg
        self._task.args['_uses_shell'] = True

        # Shell shares the same module code as command. Fail if command
        # specific options are set.
        if "expand_argument_vars" in self._task.args:
            raise AnsibleActionFail(f"Unsupported parameters for ({self._task.action}) module: expand_argument_vars")

        command_action = self._shared_loader_obj.action_loader.get('ansible.legacy.command',
                                                                   task=self._task,
                                                                   connection=self._connection,
                                                                   play_context=self._play_context,
                                                                   loader=self._loader,
                                                                   templar=self._templar,
                                                                   shared_loader_obj=self._shared_loader_obj)
        result = command_action.run(task_vars=task_vars)

        return result
