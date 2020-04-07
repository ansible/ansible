#!/usr/bin/env python
"""Show pyyaml version."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

try:
    import pytest
except ImportError:
    pytest = None

print(json.dumps(dict(
    pytest_version=pytest.__version__ if pytest else None,
)))
