# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.validation import check_type_dict


@pytest.mark.parametrize('value, expected', [
    ({'k1': 'v1'}, {'k1': 'v1'}),
    ('k1=v1,k2=v2', {'k1': 'v1', 'k2': 'v2'}),
    ('k1=v1, k2=v2', {'k1': 'v1', 'k2': 'v2'}),
    ('k1=v1,     k2=v2,  k3=v3', {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}),
    ('{"key": "value", "list": ["one", "two"]}', {'key': 'value', 'list': ['one', 'two']}),
    ('k1=v1 k2=v2', {'k1': 'v1', 'k2': 'v2'}),
    ('k1="v1,v2",k2=v3', {'k1': 'v1,v2', 'k2': 'v3'}),
    ("k1='v1 v2'", {'k1': 'v1 v2'}),
    ('k1=a\\,b', {'k1': 'a,b'}),
    ('k1=a\\ b', {'k1': 'a b'}),
    ('k1=v1,', {'k1': 'v1'}),
    ("{'k1': 'v1'}", {'k1': 'v1'}),
])
def test_check_type_dict(value, expected):
    assert expected == check_type_dict(value)


@pytest.mark.parametrize('value', [
    1,
    3.14159,
    [1, 2],
    'a',
    '{',
    '{1}',
    'k1=v1 k2',
])
def test_check_type_dict_fail(value):
    with pytest.raises(TypeError):
        check_type_dict(value)
