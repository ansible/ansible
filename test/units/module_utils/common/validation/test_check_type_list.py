# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.validation import check_type_list


def test_check_type_list():
    test_cases = (
        ([1, 2], [1, 2]),
        (1, ['1']),
        (['a', 'b'], ['a', 'b']),
        ('a', ['a']),
        (3.14159, ['3.14159']),
        ('a,b,1,2', ['a', 'b', '1', '2'])
    )
    for case in test_cases:
        assert case[1] == check_type_list(case[0])


def test_check_type_list_failure():
    test_cases = (
        {'k1': 'v1'},
    )
    for case in test_cases:
        with pytest.raises(TypeError):
            check_type_list(case)
