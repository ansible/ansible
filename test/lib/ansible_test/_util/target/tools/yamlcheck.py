"""Show availability of PyYAML and libyaml support."""
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
