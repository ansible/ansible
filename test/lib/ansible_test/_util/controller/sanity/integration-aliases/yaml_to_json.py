"""Read YAML from stdin and write JSON to stdout."""
from __future__ import annotations

import json
import sys

from yaml import load

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

json.dump(load(sys.stdin, Loader=SafeLoader), sys.stdout)
