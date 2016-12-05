from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
           task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        result['changed'] = False
        result['add_extra_var'] = (self._task.args['name'], self._task.args['value'])
        return result
