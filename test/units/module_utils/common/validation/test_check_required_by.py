# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils._text import to_native
from ansible.module_utils.common.validation import check_required_by


@pytest.fixture
def required_by_terms():
    return {
        'fruit': ['name', 'flavor'],
        'car': ['color', 'doors'],
    }


def test_check_required_by(required_by_terms):
    params = {
        'fruit': 'hello',
        'flavor': 'sweet',
        'name': 'banana',
    }

    assert check_required_by(required_by_terms, params) == {}


def test_check_required_by_missing(required_by_terms):
    params = {
        'fruit': 'hello',
        'flavor': 'sweet',
    }

    expected = "missing parameter(s) required by 'fruit': name"

    with pytest.raises(TypeError) as e:
        check_required_by(required_by_terms, params)

    assert to_native(e.value) == expected


def test_check_required_by_multiple_same_missing(required_by_terms):
    params = {
        'fruit': 'hello',
    }

    expected = "missing parameter(s) required by 'fruit': name, flavor"

    with pytest.raises(TypeError) as e:
        check_required_by(required_by_terms, params)

    assert to_native(e.value) == expected


def test_check_required_by_multiple_different_missing(required_by_terms):
    params = {
        'fruit': 'hello',
        'car': 'goodbye',
    }

    expected = "missing parameter(s) required by 'car': color, doors"

    with pytest.raises(TypeError) as e:
        check_required_by(required_by_terms, params)

    assert to_native(e.value) == expected


def test_check_required_by_multiple_different_second_missing(required_by_terms):
    params = {
        'fruit': 'hello',
        'flavor': 'sour',
        'name': 'apple',
        'car': 'goodbye',
    }

    expected = "missing parameter(s) required by 'car': color, doors"

    with pytest.raises(TypeError) as e:
        check_required_by(required_by_terms, params)

    assert to_native(e.value) == expected


def test_check_required_required_by_missing_none():
    terms = None
    params = {
        'foo': 'bar',
        'baz': 'buzz',
    }
    assert check_required_by(terms, params) == {}


def test_check_required_by_no_params(required_by_terms):
    with pytest.raises(TypeError) as te:
        check_required_by(required_by_terms, None)
    assert "'NoneType' is not iterable" in to_native(te.value)
