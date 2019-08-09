# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils._text import to_native
from ansible.module_utils.common.validation import check_type_int


def test_check_type_int():
    test_cases = (
        ('1', 1),
        (u'1', 1),
        (1002, 1002),
    )
    for case in test_cases:
        assert case[1] == check_type_int(case[0])


def test_check_type_int_fail():
    test_cases = (
        {'k1': 'v1'},
        (b'1', 1),
        (3.14159, 3),
        'b',
    )
    for case in test_cases:
        with pytest.raises(TypeError) as e:
            check_type_int(case)
        assert 'cannot be converted to an int' in to_native(e.value)
