# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        self._supports_async = True
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Command module has a special config option to turn off the command nanny warnings
        if 'warn' not in self._task.args:
            self._task.args['warn'] = C.COMMAND_WARNINGS

        wrap_async = self._task.async_val and not self._connection.has_native_async
        results = merge_hash(results, self._execute_module(task_vars=task_vars, wrap_async=wrap_async))

        if not wrap_async:
            # remove a temporary path we created
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return results
