from __future__ import annotations

import dataclasses
import typing as t

from ansible.module_utils._internal._ambient_context import AmbientContextBase

if t.TYPE_CHECKING:
    from ansible.playbook.task import Task


@dataclasses.dataclass
class TaskContext(AmbientContextBase):
    """Ambient context that wraps task execution on workers. It provides access to the currently executing task."""

    task: Task
