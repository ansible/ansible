from __future__ import annotations

import importlib.metadata

jinja2_version = importlib.metadata.version('jinja2')

# DTFIX-FUTURE: sanity test to ensure this doesn't drift from requirements
_MINIMUM_JINJA_VERSION = (3, 1)
_CURRENT_JINJA_VERSION = tuple(map(int, jinja2_version.split('.', maxsplit=2)[:2]))

if _CURRENT_JINJA_VERSION < _MINIMUM_JINJA_VERSION:
    raise RuntimeError(f'Jinja version {".".join(map(str, _MINIMUM_JINJA_VERSION))} or higher is required (current version {jinja2_version}).')
