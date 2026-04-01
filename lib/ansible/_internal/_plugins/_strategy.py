from __future__ import annotations

import contextlib
import dataclasses
import typing as t

if t.TYPE_CHECKING:
    from ansible.plugins.strategy import StrategyBase
    from ansible.executor.task_queue_manager import TaskQueueManager


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class StrategyContext:
    """Expose active strategy and TQM instances."""

    _current: t.ClassVar[t.Self | None] = None

    strategy: StrategyBase
    tqm: TaskQueueManager

    @contextlib.contextmanager
    def activate(self) -> t.Generator[None]:
        cls = type(self)

        try:
            cls._current = self
            yield
        finally:
            cls._current = None

    @classmethod
    def current(cls) -> StrategyContext:
        if not cls._current:
            raise ReferenceError(f"A required {cls.__name__} context is not active.") from None

        return cls._current
