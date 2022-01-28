"""Read YAML from stdin and write JSON to stdout."""
from __future__ import annotations

import datetime
import json
import sys

from yaml import load

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

# unique ISO date marker matching the one present in importer.py
ISO_DATE_MARKER = 'isodate:f23983df-f3df-453c-9904-bcd08af468cc:'


def default(value):
    """Custom default serializer which supports datetime.date types."""
    if isinstance(value, datetime.date):
        return '%s%s' % (ISO_DATE_MARKER, value.isoformat())

    raise TypeError('cannot serialize type: %s' % type(value))


json.dump(load(sys.stdin, Loader=SafeLoader), sys.stdout, default=default)
