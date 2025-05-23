from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    supports_raw_params = True

    def run(self, tmp=None, task_vars=None):
        action_args = self._task.args
        return dict(action_args=action_args)
