# Copyright (c) 2020, Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import signal
from functools import wraps


def _raise_timeout(signum, frame):
    raise TimeoutError


class Timeout:
    def __init__(self, timeout):
        self._timeout = timeout

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(self._timeout)
            try:
                return func(*args, **kwargs)
            except TimeoutError:
                return None
            finally:
                signal.signal(signal.SIGALRM, signal.SIG_IGN)
        return inner

    def __enter__(self):
        signal.signal(signal.SIGALRM, _raise_timeout)
        signal.alarm(self._timeout)

    def __exit__(self, exc_type, exc_value, traceback):
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        if exc_type is TimeoutError:
            return True
