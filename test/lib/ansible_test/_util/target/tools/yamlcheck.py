"""Show availability of PyYAML and libyaml support."""

from __future__ import annotations

import json

try:
    import yaml
except ImportError:
    yaml = None

try:
    from yaml import CLoader
except ImportError:
    CLoader = None  # type: ignore[misc]

print(json.dumps(dict(
    yaml=bool(yaml),
    cloader=bool(CLoader),
)))
