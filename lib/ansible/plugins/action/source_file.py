from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Plugin to set facts from variables sourced in `source_file` module."""

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if self._task.args.get("path", None) is None:
            result["failed"] = True
            result["msg"] = "path arg needs to be provided"
            return result

        result.update(self._execute_module(task_vars=task_vars))

        return result
