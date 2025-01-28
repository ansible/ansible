from __future__ import annotations

from jinja2 import __version__ as _jinja2_version

# DTFIX-FUTURE: sanity test to ensure this doesn't drift from requirements
_MINIMUM_JINJA_VERSION = (3, 1)

if tuple(map(int, _jinja2_version.split('.', maxsplit=2)[:2])) < _MINIMUM_JINJA_VERSION:
    raise RuntimeError(f'Jinja version {".".join(map(str, _MINIMUM_JINJA_VERSION))} or higher is required (current version {_jinja2_version}).')
