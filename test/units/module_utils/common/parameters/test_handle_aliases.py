# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import pytest

from ansible.module_utils.common.parameters import _handle_aliases
from ansible.module_utils.common.text.converters import to_native


def test_handle_aliases_no_aliases():
    argument_spec = {
        'name': {'type': 'str'},
    }

    params = {
        'name': 'foo',
        'path': 'bar'
    }

    expected = {}
    result = _handle_aliases(argument_spec, params)

    assert expected == result


def test_handle_aliases_basic():
    argument_spec = {
        'name': {'type': 'str', 'aliases': ['surname', 'nick']},
    }

    params = {
        'name': 'foo',
        'path': 'bar',
        'surname': 'foo',
        'nick': 'foo',
    }

    expected = {'surname': 'name', 'nick': 'name'}
    result = _handle_aliases(argument_spec, params)

    assert expected == result


def test_handle_aliases_value_error():
    argument_spec = {
        'name': {'type': 'str', 'aliases': ['surname', 'nick'], 'default': 'bob', 'required': True},
    }

    params = {
        'name': 'foo',
    }

    with pytest.raises(ValueError) as ve:
        _handle_aliases(argument_spec, params)
        assert 'internal error: aliases must be a list or tuple' == to_native(ve.error)


def test_handle_aliases_type_error():
    argument_spec = {
        'name': {'type': 'str', 'aliases': 'surname'},
    }

    params = {
        'name': 'foo',
    }

    with pytest.raises(TypeError) as te:
        _handle_aliases(argument_spec, params)
        assert 'internal error: required and default are mutually exclusive' in to_native(te.error)
