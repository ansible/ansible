# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        self._supports_async = True
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        wrap_async = self._task.async_val and not self._connection.has_native_async
        # explicitly call `ansible.legacy.command` for backcompat to allow library/ override of `command` while not allowing
        # collections search for an unqualified `command` module
        results = merge_hash(results, self._execute_module(module_name='ansible.legacy.command', task_vars=task_vars, wrap_async=wrap_async))

        if not wrap_async:
            # remove a temporary path we created
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return results
