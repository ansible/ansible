from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        self._display.deprecated("a deprecation warning", version="2.99")
        self._display.warning("a warning")

        return dict(changed=False)
