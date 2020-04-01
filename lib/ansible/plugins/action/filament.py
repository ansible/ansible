from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from datetime import datetime


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        module_args = self._task.args.copy()
        if int(module_args['num1']) > 10:
            module_args['num1'] = 9
        if int(module_args['num2']) > 10:
            module_args['num2'] = 9
        module_return = self._execute_module(module_args=module_args,
                                             task_vars=task_vars, tmp=tmp)
        return module_return
