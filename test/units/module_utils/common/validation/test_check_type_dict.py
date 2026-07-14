# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.validation import check_type_dict


def test_check_type_dict():
    test_cases = (
        ({'k1': 'v1'}, {'k1': 'v1'}),
        ('k1=v1,k2=v2', {'k1': 'v1', 'k2': 'v2'}),
        ('k1=v1, k2=v2', {'k1': 'v1', 'k2': 'v2'}),
        ('k1=v1,     k2=v2,  k3=v3', {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}),
        ('{"key": "value", "list": ["one", "two"]}', {'key': 'value', 'list': ['one', 'two']}),
        ('k1=v1 k2=v2', {'k1': 'v1', 'k2': 'v2'}),
    )
    for case in test_cases:
        assert case[1] == check_type_dict(case[0])


def test_check_type_dict_fail():
    test_cases = (
        1,
        3.14159,
        [1, 2],
        'a',
        '{1}',
        'k1=v1 k2'
    )
    for case in test_cases:
        with pytest.raises(TypeError):
            check_type_dict(case)
