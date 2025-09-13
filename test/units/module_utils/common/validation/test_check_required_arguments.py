# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import sys

import pytest

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.validation import check_required_arguments


@pytest.fixture
def arguments_terms():
    return {
        'foo': {
            'required': True,
        },
        'bar': {
            'required': False,
        },
        'tomato': {
            'irrelevant': 72,
        },
    }


@pytest.fixture
def arguments_terms_multiple():
    return {
        'foo': {
            'required': True,
        },
        'bar': {
            'required': True,
        },
        'tomato': {
            'irrelevant': 72,
        },
    }


def test_check_required_arguments(arguments_terms):
    params = {
        'foo': 'hello',
        'bar': 'haha',
    }
    assert check_required_arguments(arguments_terms, params) == []


def test_check_required_arguments_missing(arguments_terms):
    params = {
        'apples': 'woohoo',
    }
    expected = "missing required arguments: foo"

    with pytest.raises(TypeError) as e:
        check_required_arguments(arguments_terms, params)

    assert to_native(e.value) == expected


def test_check_required_arguments_missing_multiple(arguments_terms_multiple):
    params = {
        'apples': 'woohoo',
    }
    expected = "missing required arguments: bar, foo"

    with pytest.raises(TypeError) as e:
        check_required_arguments(arguments_terms_multiple, params)

    assert to_native(e.value) == expected


def test_check_required_arguments_missing_none():
    terms = None
    params = {
        'foo': 'bar',
        'baz': 'buzz',
    }
    assert check_required_arguments(terms, params) == []


def test_check_required_arguments_no_params(arguments_terms):
    with pytest.raises(TypeError) as te:
        check_required_arguments(arguments_terms, None)
    expected = "argument of type 'NoneType' is not a container or iterable" if sys.version_info >= (3, 14) else "'NoneType' is not iterable"
    assert expected in to_native(te.value)
