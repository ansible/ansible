from __future__ import annotations

from ansible.module_utils.datatag import deprecate_value
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        result.update(deprecated_thing=deprecate_value("deprecated thing", msg="Deprecated thing is deprecated.", removal_version='999.999'))

        self._display.deprecated("did a deprecated thing", version="999.999")

        return result
