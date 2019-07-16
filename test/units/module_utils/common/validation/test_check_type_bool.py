# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils._text import to_native
from ansible.module_utils.common.validation import check_type_bool


def test_check_type_bool():
    test_cases = (
        (True, True),
        (False, False),
        ('1', True),
        ('on', True),
        (1, True),
        ('0', False),
        (0, False),
        ('n', False),
        ('f', False),
        ('false', False),
        ('true', True),
        ('y', True),
        ('t', True),
        ('yes', True),
        ('no', False),
        ('off', False),
    )
    for case in test_cases:
        assert case[1] == check_type_bool(case[0])


def test_check_type_bool_fail():
    default_test_msg = 'cannot be converted to a bool'
    test_cases = (
        ({'k1': 'v1'}, 'is not a valid bool'),
        (3.14159, default_test_msg),
        (-1, default_test_msg),
        (-90810398401982340981023948192349081, default_test_msg),
        (90810398401982340981023948192349081, default_test_msg),
    )
    for case in test_cases:
        with pytest.raises(TypeError) as e:
            check_type_bool(case)
        assert 'cannot be converted to a bool' in to_native(e.value)
