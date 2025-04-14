from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        args = self.validate_argument_spec(argument_spec=dict(
            fail_mode=dict(default='raise', choices=['raise', 'result_dict'], type='str')
        ))
        if args[0].validated_parameters['fail_mode'] == 'raise':
            raise Exception("I am an exception from an action.")

        return dict(exception="I am a captured traceback from an action", failed=True, msg="sorry, it broke")
