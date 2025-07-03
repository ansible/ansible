from __future__ import annotations

import threading

from ansible.module_utils._internal._concurrent import _daemon_threading


def test_daemon_thread_getattr() -> None:
    """Ensure that the threading module proxy delegates properly to the real module."""
    assert _daemon_threading.current_thread is threading.current_thread


def test_daemon_threading_thread_override() -> None:
    """Ensure that the proxy module's Thread attribute is different from the real module's."""
    assert _daemon_threading.Thread is not threading.Thread
