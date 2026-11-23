# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import json
import typing as t

from ansible.module_utils.connection import Connection
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Return state from the active persistent daemon without executing a module."""

    def run(self, tmp: str | None = None, task_vars: dict[str, t.Any] | None = None) -> dict[str, t.Any]:
        result = super().run(tmp, task_vars)
        result.update(json.loads(Connection(self._connection.socket_path).get_capabilities()))
        return result
