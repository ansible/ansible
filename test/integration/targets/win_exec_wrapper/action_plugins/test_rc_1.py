# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import json

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        super().run(tmp, task_vars)
        del tmp

        exec_command = self._connection.exec_command

        def patched_exec_command(*args, **kwargs):
            rc, stdout, stderr = exec_command(*args, **kwargs)

            new_stdout = json.dumps({
                "rc": rc,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "failed": False,
                "changed": False,
            }).encode()

            return (0, new_stdout, b"")

        try:
            # This is done to capture the raw rc/stdio from the module exec
            self._connection.exec_command = patched_exec_command
            return self._execute_module(task_vars=task_vars)
        finally:
            self._connection.exec_command = exec_command
