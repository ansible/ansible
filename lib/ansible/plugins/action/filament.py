from ansible.utils import *
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        # in case there is no task vars
        if task_vars is None:
            task_vars = dict()
        
        # run code from parent class
        result = super(ActionModule, self).run(tmp, task_vars)
        # run filament module
        module_return = self._execute_module(module_name='filament',task_vars=task_vars)
        # cat the result
        result.update(module_return)
        # change something
        result["foo"] = "!"+result["foo"]

        return result
        
        
