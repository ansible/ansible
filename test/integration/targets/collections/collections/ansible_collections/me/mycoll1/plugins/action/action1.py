from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        """ handler for file transfer operations """
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if result.get('skipped'):
            return result

        module_args = self._task.args.copy()

        result.update(
            self._execute_module(
                module_name='me.mycoll2.module1',
                module_args=module_args,
                task_vars=task_vars,
            )
        )

        return result
