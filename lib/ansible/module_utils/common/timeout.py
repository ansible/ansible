# Copyright (c) 2020, Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import signal
from functools import wraps

from ansible.module_utils.common.warnings import warn


def _raise_timeout(signum, frame):
    raise TimeoutError


class Timeout:
    def __init__(self, timeout):
        self._timeout = timeout
        self.timed_out = False

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            func_name = getattr(func, '__qualname__', func.__name__)
            signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(self._timeout)
            try:
                return func(*args, **kwargs)
            except TimeoutError:
                warn('Function call to %s timed out after %d seconds.' % (func_name, self._timeout)
                return None
            finally:
                signal.signal(signal.SIGALRM, signal.SIG_IGN)
        return inner

    def __enter__(self):
        signal.signal(signal.SIGALRM, _raise_timeout)
        signal.alarm(self._timeout)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        if exc_type is TimeoutError:
            self.timed_out = True
            return True
