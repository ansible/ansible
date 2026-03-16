# Copyright: 2017, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause )

from __future__ import annotations

import collections.abc as c

from ansible.module_utils._internal import _no_six
from ansible.module_utils.common.text.converters import to_text


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
    return _no_six.deprecate(importable_name, __name__, "binary_type", "text_type")
