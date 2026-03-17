from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    _supports_async = True

    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)

        return {}
