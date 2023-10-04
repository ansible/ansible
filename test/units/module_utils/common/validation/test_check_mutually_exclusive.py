# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.validation import check_mutually_exclusive


@pytest.fixture
def mutually_exclusive_terms():
    return [
        ('string1', 'string2',),
        ('box', 'fox', 'socks'),
    ]


def test_check_mutually_exclusive(mutually_exclusive_terms):
    params = {
        'string1': 'cat',
        'fox': 'hat',
    }
    assert check_mutually_exclusive(mutually_exclusive_terms, params) == []


def test_check_mutually_exclusive_found(mutually_exclusive_terms):
    params = {
        'string1': 'cat',
        'string2': 'hat',
        'fox': 'red',
        'socks': 'blue',
    }
    expected = "parameters are mutually exclusive: string1|string2, box|fox|socks"

    with pytest.raises(TypeError) as e:
        check_mutually_exclusive(mutually_exclusive_terms, params)

    assert to_native(e.value) == expected


def test_check_mutually_exclusive_none():
    terms = None
    params = {
        'string1': 'cat',
        'fox': 'hat',
    }
    assert check_mutually_exclusive(terms, params) == []


def test_check_mutually_exclusive_no_params(mutually_exclusive_terms):
    with pytest.raises(TypeError) as te:
        check_mutually_exclusive(mutually_exclusive_terms, None)
    assert "'NoneType' object is not iterable" in to_native(te.value)
