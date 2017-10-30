# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import wraps

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def renamed_deprecation(func, new, version):
    @wraps(func)
    def wrapper(*args, **kwargs):
        display.deprecated(
            'The `%s` test was renamed to fit better gramatically with the switch to proper test syntax. '
            'Please use `%s` as a replacement' % (func.__name__, new),
            version=version
        )
        return func(*args, **kwargs)
    return wrapper
