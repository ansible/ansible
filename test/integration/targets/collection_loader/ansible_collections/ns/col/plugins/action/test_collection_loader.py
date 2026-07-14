from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        import my_module

        result = super(ActionModule, self).run(tmp, task_vars)
        result['modules'] = my_module.run()

        return result
