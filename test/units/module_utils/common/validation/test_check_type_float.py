# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils._text import to_native
from ansible.module_utils.common.validation import check_type_float


def test_check_type_float():
    test_cases = (
        ('1.5', 1.5),
        ('''1.5''', 1.5),
        (u'1.5', 1.5),
        (1002, 1002.0),
        (1.0, 1.0),
        (3.141592653589793, 3.141592653589793),
        ('3.141592653589793', 3.141592653589793),
        (b'3.141592653589793', 3.141592653589793),
    )
    for case in test_cases:
        assert case[1] == check_type_float(case[0])


def test_check_type_float_fail():
    test_cases = (
        {'k1': 'v1'},
        ['a', 'b'],
        'b',
    )
    for case in test_cases:
        with pytest.raises(TypeError) as e:
            check_type_float(case)
        assert 'cannot be converted to a float' in to_native(e.value)
