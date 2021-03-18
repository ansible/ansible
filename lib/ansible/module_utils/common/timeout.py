# Copyright (c) 2020, Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import signal
from functools import wraps

from ansible.module_utils.common.warnings import warn


def _raise_timeout(signum, frame):
    raise TimeoutError


@contextlib.contextmanager
def timeout(timeout, raising=False):
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(timeout)
    try:
        yield
    except TimeoutError:
        if raising:
            raise
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
