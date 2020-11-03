# Copyright (c) 2020, Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import signal
from functools import wraps


def _raise_timeout(signum, frame):
    raise TimeoutError


def timeout(time):
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(time)
            try:
                return func(*args, **kwargs)
            except TimeoutError:
                return None
            finally:
                signal.signal(signal.SIGALRM, signal.SIG_IGN)
        return inner
    return outer
