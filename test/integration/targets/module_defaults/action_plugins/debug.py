from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)

        if self._task.args and 'msg' in self._task.args:
            msg = self._task.args.get('msg')
        else:
            msg = "Hello overridden world!"

        result['changes'] = False
        result['msg'] = msg
        return result
