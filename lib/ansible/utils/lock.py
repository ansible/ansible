# Copyright (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import wraps


def lock_decorator(attr='missing_lock_attr', lock=None):
    '''This decorator is a generic implementation that allows you
    to either use a pre-defined instance attribute as the location
    of the lock, or to explicitly pass a lock object.

    This code was implemented with ``threading.Lock`` in mind, but
    may work with other locks, assuming that they function as
    context managers.

    When using ``attr``, the assumption is the first argument to
    the wrapped method, is ``self`` or ``cls``.

    Examples:

        @lock_decorator(attr='_callback_lock')
        def send_callback(...):

        @lock_decorator(lock=threading.Lock())
        def some_method(...):
    '''
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # Python2 doesn't have ``nonlocal``
            # assign the actual lock to ``_lock``
            if lock is None:
                _lock = getattr(args[0], attr)
            else:
                _lock = lock
            with _lock:
                return func(*args, **kwargs)
        return inner
    return outer
