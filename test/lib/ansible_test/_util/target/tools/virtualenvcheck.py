"""Detect the real python interpreter when running in a virtual environment created by the 'virtualenv' module."""

from __future__ import annotations

import json

try:
    # virtualenv <20
    from sys import real_prefix  # type: ignore[attr-defined]
except ImportError:
    real_prefix = None

try:
    # venv and virtualenv >= 20
    from sys import base_exec_prefix
except ImportError:
    base_exec_prefix = None

print(json.dumps(dict(
    real_prefix=real_prefix or base_exec_prefix,
)))
