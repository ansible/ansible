# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """
    Custom action plugin to test WinRM stdin failure recovery (lines 618-624).
    This patches the connection's _winrm_write_stdin to fail deterministically.
    """

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)

        # Get the connection object
        connection = self._connection

        # Save the original method
        original_write_stdin = connection._winrm_write_stdin

        def failing_write_stdin(_command_id, _stdin_iterator):
            """Replacement that always fails"""
            # Now raise the injected exception
            raise Exception("INJECTED TEST FAILURE: stdin write failed")

        try:
            # Patch the method to inject failure
            connection._winrm_write_stdin = failing_write_stdin

            # Execute a module that will use stdin (pipelining is on by default)
            # win_ping returns valid JSON: {"ping": "pong"}
            module_result = self._execute_module(
                module_name='ansible.windows.win_ping',
                module_args={},
                task_vars=task_vars,
            )

            # Merge the module result
            result.update(module_result)
        finally:
            # Always restore original method
            connection._winrm_write_stdin = original_write_stdin

        return result
