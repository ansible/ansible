# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re

from ansible.module_utils.six import iteritems

SIZE_RANGES = {
    'Y': 1 << 80,
    'Z': 1 << 70,
    'E': 1 << 60,
    'P': 1 << 50,
    'T': 1 << 40,
    'G': 1 << 30,
    'M': 1 << 20,
    'K': 1 << 10,
    'B': 1,
}


def lenient_lowercase(lst):
    """Lowercase elements of a list.

    If an element is not a string, pass it through untouched.
    """
    lowered = []
    for value in lst:
        try:
            lowered.append(value.lower())
        except AttributeError:
            lowered.append(value)
    return lowered


def human_to_bytes(number, default_unit=None, isbits=False):
    """Convert number in string format into bytes (ex: '2K' => 2048) or using unit argument.

    example: human_to_bytes('10M') <=> human_to_bytes(10, 'M').

    When isbits is False (default), converts bytes from a human-readable format to integer.
        example: human_to_bytes('1MB') returns 1048576 (int).
        The function expects 'B' (uppercase) as a byte identifier passed
        as a part of 'name' param string or 'unit', e.g. 'MB'/'KB'/etc.
        (except when the identifier is single 'b', it is perceived as a byte identifier too).
        if 'Mb'/'Kb'/... is passed, the ValueError will be rased.

    When isbits is True, converts bits from a human-readable format to integer.
        example: human_to_bytes('1Mb', isbits=True) returns 8388608 (int) -
        string bits representation was passed and return as a number or bits.
        The function expects 'b' (lowercase) as a bit identifier, e.g. 'Mb'/'Kb'/etc.
        if 'MB'/'KB'/... is passed, the ValueError will be rased.
    """
    m = re.search(r'^\s*(\d*\.?\d*)\s*([A-Za-z]+)?', str(number), flags=re.IGNORECASE)
    if m is None:
        raise ValueError("human_to_bytes() can't interpret following string: %s" % str(number))
    try:
        num = float(m.group(1))
    except Exception:
        raise ValueError("human_to_bytes() can't interpret following number: %s (original input string: %s)" % (m.group(1), number))

    unit = m.group(2)
    if unit is None:
        unit = default_unit

    if unit is None:
        ''' No unit given, returning raw number '''
        return int(round(num))
    range_key = unit[0].upper()
    try:
        limit = SIZE_RANGES[range_key]
    except Exception:
        raise ValueError("human_to_bytes() failed to convert %s (unit = %s). The suffix must be one of %s" % (number, unit, ", ".join(SIZE_RANGES.keys())))

    # default value
    unit_class = 'B'
    unit_class_name = 'byte'
    # handling bits case
    if isbits:
        unit_class = 'b'
        unit_class_name = 'bit'
    # check unit value if more than one character (KB, MB)
    if len(unit) > 1:
        expect_message = 'expect %s%s or %s' % (range_key, unit_class, range_key)
        if range_key == 'B':
            expect_message = 'expect %s or %s' % (unit_class, unit_class_name)

        if unit_class_name in unit.lower():
            pass
        elif unit[1] != unit_class:
            raise ValueError("human_to_bytes() failed to convert %s. Value is not a valid string (%s)" % (number, expect_message))

    return int(round(num * limit))


def bytes_to_human(size, isbits=False, unit=None):
    base = 'Bytes'
    if isbits:
        base = 'bits'
    suffix = ''

    for suffix, limit in sorted(iteritems(SIZE_RANGES), key=lambda item: -item[1]):
        if (unit is None and size >= limit) or unit is not None and unit.upper() == suffix[0]:
            break

    if limit != 1:
        suffix += base[0]
    else:
        suffix = base

    return '%.2f %s' % (size / limit, suffix)
