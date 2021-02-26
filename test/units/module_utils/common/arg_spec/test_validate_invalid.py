# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator
from ansible.module_utils.six import PY2


# Each item is id, argument_spec, parameters, expected, error test string
INVALID_SPECS = [
    (
        'invalid-list',
        {'packages': {'type': 'list'}},
        {'packages': {'key': 'value'}},
        {'packages': {'key': 'value'}},
        "unable to convert to list: <class 'dict'> cannot be converted to a list",
    ),
    (
        'invalid-dict',
        {'users': {'type': 'dict'}},
        {'users': ['one', 'two']},
        {'users': ['one', 'two']},
        "unable to convert to dict: <class 'list'> cannot be converted to a dict",
    ),
    (
        'invalid-bool',
        {'bool': {'type': 'bool'}},
        {'bool': {'k': 'v'}},
        {'bool': {'k': 'v'}},
        "unable to convert to bool: <class 'dict'> cannot be converted to a bool",
    ),
    (
        'invalid-float',
        {'float': {'type': 'float'}},
        {'float': 'hello'},
        {'float': 'hello'},
        "unable to convert to float: <class 'str'> cannot be converted to a float",
    ),
    (
        'invalid-bytes',
        {'bytes': {'type': 'bytes'}},
        {'bytes': 'one'},
        {'bytes': 'one'},
        "unable to convert to bytes: <class 'str'> cannot be converted to a Byte value",
    ),
    (
        'invalid-bits',
        {'bits': {'type': 'bits'}},
        {'bits': 'one'},
        {'bits': 'one'},
        "unable to convert to bits: <class 'str'> cannot be converted to a Bit value",
    ),
    (
        'invalid-jsonargs',
        {'some_json': {'type': 'jsonarg'}},
        {'some_json': set()},
        {'some_json': set()},
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
        "Unsupported parameters: another, badparam",
    ),
    (
        'invalid-elements',
        {'numbers': {'type': 'list', 'elements': 'int'}},
        {'numbers': [55, 33, 34, {'key': 'value'}]},
        {'numbers': [55, 33, 34]},
        "Elements value for option 'numbers' is of type <class 'dict'> and we were unable to convert to int: <class 'dict'> cannot be converted to an int"
    ),
    (
        'required',
        {'req': {'required': True}},
        {},
        {'req': None},
        "missing required arguments: req"
    )
]


@pytest.mark.parametrize(
    ('arg_spec', 'parameters', 'expected', 'error'),
    ((i[1], i[2], i[3], i[4]) for i in INVALID_SPECS),
    ids=[i[0] for i in INVALID_SPECS]
)
def test_invalid_spec(arg_spec, parameters, expected, error):
    v = ArgumentSpecValidator(arg_spec, parameters)
    passed = v.validate()

    if PY2:
        error = error.replace('class', 'type')

    assert error in v.error_messages[0]
    assert v.validated_parameters == expected
    assert passed is False
