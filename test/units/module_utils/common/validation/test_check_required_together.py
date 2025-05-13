# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.validation import check_required_together


@pytest.fixture
def together_terms():
    return [
        ['bananas', 'potatoes'],
        ['cats', 'wolves']
    ]


def test_check_required_together(together_terms):
    params = {
        'bananas': 'hello',
        'potatoes': 'this is here too',
        'dogs': 'haha',
    }
    assert check_required_together(together_terms, params) == []


def test_check_required_together_missing(together_terms):
    params = {
        'bananas': 'woohoo',
        'wolves': 'uh oh',
    }
    expected = "parameters are required together: bananas, potatoes"

    with pytest.raises(TypeError) as e:
        check_required_together(together_terms, params)

    assert to_native(e.value) == expected


def test_check_required_together_missing_none():
    terms = None
    params = {
        'foo': 'bar',
        'baz': 'buzz',
    }
    assert check_required_together(terms, params) == []


def test_check_required_together_no_params(together_terms):
    with pytest.raises(TypeError) as te:
        check_required_together(together_terms, None)

    assert "'NoneType' object is not iterable" in to_native(te.value)
