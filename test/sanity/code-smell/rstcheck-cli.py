"""Wrapper around rstcheck to provide Jinja2 compatibility for Sphinx."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import runpy
import sys

try:
    from jinja2.filters import pass_context as _passctx, pass_environment as _passenv
    _mod = sys.modules['jinja2']
    _mod.contextfunction = _passctx
    _mod.environmentfilter = _passenv
except ImportError:
    pass

sys.path.remove(os.path.dirname(__file__))  # avoid recursively running sanity test

runpy.run_module('rstcheck', run_name='__main__', alter_sys=True)
