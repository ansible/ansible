#!/usr/bin/env python
"""Show python and pip versions."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

try:
    import yaml
except ImportError:
    yaml = None

try:
    from yaml import CLoader
except ImportError:
    CLoader = None

print(json.dumps(dict(
    yaml=bool(yaml),
    cloader=bool(CLoader),
)))
