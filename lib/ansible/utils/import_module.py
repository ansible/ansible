# Copyright (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


# HACK: keep Python 2.6 controller tests happy in CI until they're properly split
try:
    from importlib import import_module
except ImportError:
    # importlib.import_module returns the tail
    # whereas __import__ returns the head
    # compat to work like importlib.import_module
    def import_module(name):
        module = __import__(name)
        for part in name.split('.')[1:]:
            module = getattr(module, part)
        return module
