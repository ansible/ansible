#!/usr/bin/env python
"""Detect the real python interpreter when running in a virtual environment created by the 'virtualenv' module."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

try:
    from sys import real_prefix
except ImportError:
    real_prefix = None

print(json.dumps(dict(
    real_prefix=real_prefix,
)))
