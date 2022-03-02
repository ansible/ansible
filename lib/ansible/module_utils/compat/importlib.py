# Copyright (c) 2020 Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

try:
    from importlib import import_module
except ImportError:
    # importlib.import_module returns the tail
    # whereas __import__ returns the head
    # compat to work like importlib.import_module
    def import_module(name):  # type: ignore[misc]
        __import__(name)
        return sys.modules[name]
