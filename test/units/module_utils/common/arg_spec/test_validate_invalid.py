# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator, ValidationResult
from ansible.module_utils.errors import AnsibleValidationErrorMultiple


# Each item is id, argument_spec, parameters, expected, unsupported parameters, error test string
INVALID_SPECS = [
    (
        'invalid-list',
        {'packages': {'type': 'list'}},
        {'packages': {'key': 'value'}},
        {'packages': {'key': 'value'}},
        set(),
        "unable to convert to list: <class 'dict'> cannot be converted to a list",
    ),
    (
        'invalid-dict',
        {'users': {'type': 'dict'}},
        {'users': ['one', 'two']},
        {'users': ['one', 'two']},
        set(),
        "unable to convert to dict: <class 'list'> cannot be converted to a dict",
    ),
    (
        'invalid-bool',
        {'bool': {'type': 'bool'}},
        {'bool': {'k': 'v'}},
        {'bool': {'k': 'v'}},
        set(),
        "unable to convert to bool: <class 'dict'> cannot be converted to a bool",
    ),
    (
        'invalid-float',
        {'float': {'type': 'float'}},
        {'float': 'hello'},
        {'float': 'hello'},
        set(),
        "unable to convert to float: <class 'str'> cannot be converted to a float",
    ),
    (
        'invalid-bytes',
        {'bytes': {'type': 'bytes'}},
        {'bytes': 'one'},
        {'bytes': 'one'},
        set(),
        "unable to convert to bytes: <class 'str'> cannot be converted to a Byte value",
    ),
    (
        'invalid-bits',
        {'bits': {'type': 'bits'}},
        {'bits': 'one'},
        {'bits': 'one'},
        set(),
        "unable to convert to bits: <class 'str'> cannot be converted to a Bit value",
    ),
    (
        'invalid-jsonargs',
        {'some_json': {'type': 'jsonarg'}},
        {'some_json': set()},
        {'some_json': set()},
        set(),
        "unable to convert to jsonarg: <class 'set'> cannot be converted to a json string",
    ),
    (
        'invalid-parameter',
        {'name': {}},
        {
            'badparam': '',
            'another': '',
        },
        {
            'name': None,
            'badparam': '',
            'another': '',
        },
        set(('another', 'badparam')),
        "another, badparam. Supported parameters include: name.",
    ),
    (
        'invalid-elements',
        {'numbers': {'type': 'list', 'elements': 'int'}},
        {'numbers': [55, 33, 34, {'key': 'value'}]},
        {'numbers': [55, 33, 34]},
        set(),
        "Elements value for option 'numbers' is of type <class 'dict'> and we were unable to convert to int:"
    ),
    (
        'required',
        {'req': {'required': True}},
        {},
        {'req': None},
        set(),
        "missing required arguments: req"
    ),
    (
        'blank_values',
        {'ch_param': {'elements': 'str', 'type': 'list', 'choices': ['a', 'b']}},
        {'ch_param': ['']},
        {'ch_param': ['']},
        set(),
        "value of ch_param must be one or more of"
    )
]


@pytest.mark.parametrize(
    ('arg_spec', 'parameters', 'expected', 'unsupported', 'error'),
    (i[1:] for i in INVALID_SPECS),
    ids=[i[0] for i in INVALID_SPECS]
)
def test_invalid_spec(arg_spec, parameters, expected, unsupported, error):
    v = ArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    with pytest.raises(AnsibleValidationErrorMultiple) as exc_info:
        raise result.errors

    assert isinstance(result, ValidationResult)
    assert error in exc_info.value.msg
    assert error in result.error_messages[0]
    assert result.unsupported_parameters == unsupported
    assert result.validated_parameters == expected
