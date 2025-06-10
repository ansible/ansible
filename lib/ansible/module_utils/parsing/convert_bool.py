# Copyright: 2017, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause )

from __future__ import annotations

import collections.abc as c

from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.common import warnings as _warnings


BOOLEANS_TRUE = frozenset(('y', 'yes', 'on', '1', 'true', 't', 1, 1.0, True))
BOOLEANS_FALSE = frozenset(('n', 'no', 'off', '0', 'false', 'f', 0, 0.0, False))
BOOLEANS = BOOLEANS_TRUE.union(BOOLEANS_FALSE)


def boolean(value, strict=True):
    if isinstance(value, bool):
        return value

    normalized_value = value

    if isinstance(value, (str, bytes)):
        normalized_value = to_text(value, errors='surrogate_or_strict').lower().strip()

    if not isinstance(value, c.Hashable):
        normalized_value = None  # prevent unhashable types from bombing, but keep the rest of the existing fallback/error behavior

    if normalized_value in BOOLEANS_TRUE:
        return True
    elif normalized_value in BOOLEANS_FALSE or not strict:
        return False

    raise TypeError("The value '%s' is not a valid boolean. Valid booleans include: %s" % (to_text(value), ', '.join(repr(i) for i in BOOLEANS)))


def __getattr__(importable_name):
    """Inject import-time deprecation warnings."""
    if importable_name in {"binary_type", "text_type"}:
        import importlib
        importable = getattr(
            importlib.import_module("ansible.module_utils.six"),
            importable_name
        )
    else:
        raise AttributeError(
            f"Cannot import name {importable_name!r} from {__name__!r} ({__file__!r})"
        )

    _warnings.deprecate(
        msg=f"Importing {importable_name!r} from {__name__!r} is deprecated.",
        version="2.23",
    )
    return importable
