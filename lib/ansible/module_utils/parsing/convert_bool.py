# Copyright: 2017, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause )

from __future__ import annotations

from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils.common.text.converters import to_text


BOOLEANS_TRUE = frozenset(('y', 'yes', 'on', '1', 'true', 't', 1, 1.0, True))
BOOLEANS_FALSE = frozenset(('n', 'no', 'off', '0', 'false', 'f', 0, 0.0, False))
BOOLEANS = BOOLEANS_TRUE.union(BOOLEANS_FALSE)


def boolean(value, strict=True):
    if isinstance(value, bool):
        return value

    normalized_value = value
    if isinstance(value, (text_type, binary_type)):
        normalized_value = to_text(value, errors='surrogate_or_strict').lower().strip()

    if normalized_value in BOOLEANS_TRUE:
        return True
    elif normalized_value in BOOLEANS_FALSE or not strict:
        return False

    raise TypeError("The value '%s' is not a valid boolean.  Valid booleans include: %s" % (to_text(value), ', '.join(repr(i) for i in BOOLEANS)))
