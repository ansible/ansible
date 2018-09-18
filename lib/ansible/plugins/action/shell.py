# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        # Shell module is implemented via command
        self._task.action = 'command'
        self._task.args['_uses_shell'] = True

        command_action = self._shared_loader_obj.action_loader.get('command',
                                                                   task=self._task,
                                                                   connection=self._connection,
                                                                   play_context=self._play_context,
                                                                   loader=self._loader,
                                                                   templar=self._templar,
                                                                   shared_loader_obj=self._shared_loader_obj)
        result = command_action.run(task_vars=task_vars)

        return result
