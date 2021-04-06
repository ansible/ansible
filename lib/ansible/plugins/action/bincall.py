from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError
from ansible.module_utils.json_utils import _filter_non_json_lines
from ansible.plugins.action import ActionBase

class BinaryModule(ActionBase):
    """
    Action plugin for calling binary modules.
    Required layout:

    +- action_plugins
    |  |
    |  +-- <name>.py
    |
    +- library
       |
       +-- <name>-<osname>-<arch>

    """
    NAME = ""

    def __init__(self, *args, **kwargs):
        ActionBase.__init__(self, *args, **kwargs)
        self._supports_async = True

        if not self.NAME:
            raise Exception("Module name was not yet set")

        # Determine what is the target platform and choose the binary module accordingly
        platform = self._low_level_execute_command("uname -sm")
        if platform["rc"]:
            raise Exception(platform["stderr"])
        sysarch = platform["stdout"].lower().strip().split(" ")
        if len(sysarch) == 2:
            system, arch = sysarch
        else:
            raise Exception("Unknown platform: {}".format(platform["stdout"]))

        self.module_name = "{}-{}-{}".format(self.NAME, system, arch)

    def run(self, tmp=None, task_vars=None):
        """
        Call a binary module according to the platform specifics.
        """
        if not task_vars:
            task_vars = {}

        result = ActionBase.run(self, tmp=tmp, task_vars=task_vars)
        result.update(
            self._execute_module(
                module_name=self.module_name,
                module_args=self._task.args,
                task_vars=task_vars,
                wrap_async=self._task.async_val
            )
        )

        return result
