"""Utilities for concurrent code execution using futures."""

from __future__ import annotations

import concurrent.futures
import types

from . import _daemon_threading


class DaemonThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    """ThreadPoolExecutor subclass that creates non-joinable daemon threads for non-blocking pool and process shutdown with abandoned threads."""

    atc = concurrent.futures.ThreadPoolExecutor._adjust_thread_count

    # clone the base class `_adjust_thread_count` method with a copy of its globals dict
    _adjust_thread_count = types.FunctionType(atc.__code__, atc.__globals__.copy(), name=atc.__name__, argdefs=atc.__defaults__, closure=atc.__closure__)
    # patch the method closure's `threading` module import to use our daemon-only thread factory instead
    _adjust_thread_count.__globals__.update(threading=_daemon_threading)

    del atc  # don't expose this as a class attribute
