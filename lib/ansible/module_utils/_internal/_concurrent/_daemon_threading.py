"""Proxy stdlib threading module that only supports non-joinable daemon threads."""
# NB: all new local module attrs are _ prefixed to ensure an identical public attribute surface area to the module we're proxying

from __future__ import annotations as _annotations

import threading as _threading
import typing as _t


class _DaemonThread(_threading.Thread):
    """
    Daemon-only Thread subclass; prevents running threads of this type from blocking interpreter shutdown and process exit.
    The join() method is a no-op.
    """

    def __init__(self, *args, daemon: bool | None = None, **kwargs) -> None:
        super().__init__(*args, daemon=daemon or True, **kwargs)

    def join(self, timeout=None) -> None:
        """ThreadPoolExecutor's atexit handler joins all queue threads before allowing shutdown; prevent them from blocking."""


Thread = _DaemonThread  # shadow the real Thread attr with our _DaemonThread


def __getattr__(name: str) -> _t.Any:
    """Delegate anything not defined locally to the real `threading` module."""
    return getattr(_threading, name)
