from __future__ import annotations

from ansible.plugins.action import ActionBase
from ansible.module_utils.formerly_core import thingtocall


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset()

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(None, task_vars)

        result = dict(changed=False, ttc_res=thingtocall())

        return result
