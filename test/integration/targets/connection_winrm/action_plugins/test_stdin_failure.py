# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """
    Custom action plugin to trip a failure using the winrm connection plugin.
    This patches the connection's _winrm_write_stdin to fail deterministically.
    """

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)

        connection = self._connection
        original_write_stdin = connection._winrm_write_stdin

        def failing_write_stdin(_command_id, _stdin_iterator):
            raise Exception("INJECTED TEST FAILURE: stdin write failed")

        try:
            connection._winrm_write_stdin = failing_write_stdin

            # Execute a module that will use stdin (pipelining is on by default)
            module_result = self._execute_module(
                module_name='ansible.windows.win_ping',
                module_args={},
                task_vars=task_vars,
            )

            result.update(module_result)
        finally:
            connection._winrm_write_stdin = original_write_stdin

        return result
