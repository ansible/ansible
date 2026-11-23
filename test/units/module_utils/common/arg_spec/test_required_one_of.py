# -*- coding: utf-8 -*-
# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from copy import deepcopy

import pytest

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator


@pytest.mark.parametrize(('option_spec', 'parameters', 'expected_errors'), [
    pytest.param({'type': 'raw'}, {'path': None}, ['one of the following is required: path, owner'], id='null-sentinel'),
    pytest.param({'type': 'raw', 'choices': None}, {'path': None}, ['one of the following is required: path, owner'], id='no-choices'),
    pytest.param({'type': 'raw', 'choices': [None, '/foo']}, {'path': None}, [], id='null-choice'),
    pytest.param({'type': 'raw', 'default': None}, {'path': None}, [], id='explicit-null-default'),
    pytest.param({'type': 'raw', 'default': '/foo'}, {'path': None}, [], id='default-defined'),
    pytest.param({'type': 'raw', 'default': False}, {'path': None}, [], id='false-default-defined'),
    pytest.param({'type': 'raw', 'default': '/foo'}, {}, [], id='default-populated'),
    pytest.param({'type': 'raw', 'default': None}, {}, ['one of the following is required: path, owner'], id='null-default-omitted'),
    pytest.param({'type': 'raw', 'choices': [None, '/foo']}, {}, ['one of the following is required: path, owner'], id='null-choice-omitted'),
    pytest.param({'type': 'raw'}, {'owner': False, 'path': None}, [], id='alternative-false'),
])
@pytest.mark.parametrize('container_type', ['top-level', 'dict', 'list'])
def test_required_one_of_null_definitions(
    option_spec: dict[str, object], parameters: dict[str, object], expected_errors: list[str], container_type: str,
) -> None:
    argument_spec = {'path': option_spec, 'owner': {'type': 'raw'}}
    required_one_of = [['path', 'owner']]
    original_parameters = deepcopy(parameters)

    if container_type == 'top-level':
        validator = ArgumentSpecValidator(argument_spec, required_one_of=required_one_of)
        result = validator.validate(parameters)
    else:
        nested_spec = {'type': container_type, 'options': argument_spec, 'required_one_of': required_one_of}
        nested_parameters: dict[str, object] | list[dict[str, object]] = parameters
        if container_type == 'list':
            nested_spec['elements'] = 'dict'
            nested_parameters = [parameters]
        validator = ArgumentSpecValidator({'user': nested_spec})
        result = validator.validate({'user': nested_parameters})
        expected_errors = [f'{error} found in user' for error in expected_errors]

    assert result.error_messages == expected_errors
    assert parameters == original_parameters


@pytest.mark.parametrize(('option_spec', 'value', 'expected_errors'), [
    ({'type': 'raw'}, None, ['one of the following is required: alias']),
    ({'type': 'raw', 'default': None}, None, []),
    ({'type': 'raw', 'choices': [None]}, None, []),
    ({'type': 'raw'}, False, []),
])
def test_required_one_of_alias_definition(option_spec: dict[str, object], value: object, expected_errors: list[str]) -> None:
    validator = ArgumentSpecValidator({'path': dict(option_spec, aliases=['alias'])}, required_one_of=[['alias']])

    result = validator.validate({'alias': value})

    assert result.error_messages == expected_errors


@pytest.mark.parametrize(('option_spec', 'expected_errors'), [
    ({'type': 'raw'}, ['one of the following is required: path, owner found in account -> user']),
    ({'type': 'raw', 'default': None}, []),
    ({'type': 'raw', 'choices': [None]}, []),
])
def test_required_one_of_uses_nested_definitions(option_spec: dict[str, object], expected_errors: list[str]) -> None:
    validator = ArgumentSpecValidator({
        'path': {'type': 'raw', 'default': None},
        'account': {
            'type': 'dict',
            'options': {
                'path': {'type': 'raw'},
                'user': {
                    'type': 'dict',
                    'options': {'path': option_spec, 'owner': {'type': 'raw'}},
                    'required_one_of': [['path', 'owner']],
                },
            },
        },
    })

    result = validator.validate({'account': {'user': {'path': None}}})

    assert result.error_messages == expected_errors
