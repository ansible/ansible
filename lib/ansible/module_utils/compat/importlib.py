# Copyright (c) 2020 Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import sys

try:
    from importlib import import_module  # pylint: disable=unused-import
except ImportError:
    # importlib.import_module returns the tail
    # whereas __import__ returns the head
    # compat to work like importlib.import_module
    def import_module(name):  # type: ignore[misc]
        __import__(name)
        return sys.modules[name]
