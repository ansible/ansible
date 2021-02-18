# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator

# Each item is id, argument_spec, parameters, expected
VALID_SPECS = [
    (
        'str-no-type-specified',
        {'name': {}},
        {'name': 'rey'},
        {'name': 'rey'},
    ),
    (
        'str',
        {'name': {'type': 'str'}},
        {'name': 'rey'},
        {'name': 'rey'},
    ),
    (
        'str-convert',
        {'name': {'type': 'str'}},
        {'name': 5},
        {'name': '5'},
    ),
    (
        'list',
        {'packages': {'type': 'list'}},
        {'packages': ['vim', 'python']},
        {'packages': ['vim', 'python']},
    ),
    (
        'list-comma-string',
        {'packages': {'type': 'list'}},
        {'packages': 'vim,python'},
        {'packages': ['vim', 'python']},
    ),
    (
        'list-comma-string-space',
        {'packages': {'type': 'list'}},
        {'packages': 'vim, python'},
        {'packages': ['vim', ' python']},
    ),
    (
        'dict',
        {'user': {'type': 'dict'}},
        {
            'user':
            {
                'first': 'rey',
                'last': 'skywalker',
            }
        },
        {
            'user':
            {
                'first': 'rey',
                'last': 'skywalker',
            }
        },
    ),
    (
        'dict-k=v',
        {'user': {'type': 'dict'}},
        {'user': 'first=rey,last=skywalker'},
        {
            'user':
            {
                'first': 'rey',
                'last': 'skywalker',
            }
        },
    ),
    (
        'dict-k=v-spaces',
        {'user': {'type': 'dict'}},
        {'user': 'first=rey,   last=skywalker'},
        {
            'user':
            {
                'first': 'rey',
                'last': 'skywalker',
            }
        },
    ),
    (
        'bool',
        {
            'enabled': {'type': 'bool'},
            'disabled': {'type': 'bool'},
        },
        {
            'enabled': True,
            'disabled': False,
        },
        {
            'enabled': True,
            'disabled': False,
        },
    ),
    (
        'bool-ints',
        {
            'enabled': {'type': 'bool'},
            'disabled': {'type': 'bool'},
        },
        {
            'enabled': 1,
            'disabled': 0,
        },
        {
            'enabled': True,
            'disabled': False,
        },
    ),
    (
        'bool-true-false',
        {
            'enabled': {'type': 'bool'},
            'disabled': {'type': 'bool'},
        },
        {
            'enabled': 'true',
            'disabled': 'false',
        },
        {
            'enabled': True,
            'disabled': False,
        },
    ),
    (
        'bool-yes-no',
        {
            'enabled': {'type': 'bool'},
            'disabled': {'type': 'bool'},
        },
        {
            'enabled': 'yes',
            'disabled': 'no',
        },
        {
            'enabled': True,
            'disabled': False,
        },
    ),
    (
        'bool-y-n',
        {
            'enabled': {'type': 'bool'},
            'disabled': {'type': 'bool'},
        },
        {
            'enabled': 'y',
            'disabled': 'n',
        },
        {
            'enabled': True,
            'disabled': False,
        },
    ),
    (
        'bool-on-off',
        {
            'enabled': {'type': 'bool'},
            'disabled': {'type': 'bool'},
        },
        {
            'enabled': 'on',
            'disabled': 'off',
        },
        {
            'enabled': True,
            'disabled': False,
        },
    ),
    (
        'bool-1-0',
        {
            'enabled': {'type': 'bool'},
            'disabled': {'type': 'bool'},
        },
        {
            'enabled': '1',
            'disabled': '0',
        },
        {
            'enabled': True,
            'disabled': False,
        },
    ),
    (
        'bool-float',
        {
            'enabled': {'type': 'bool'},
            'disabled': {'type': 'bool'},
        },
        {
            'enabled': 1.0,
            'disabled': 0.0,
        },
        {
            'enabled': True,
            'disabled': False,
        },
    ),
    (
        'float',
        {'digit': {'type': 'float'}},
        {'digit': 3.14159},
        {'digit': 3.14159},
    ),
    (
        'float-str',
        {'digit': {'type': 'float'}},
        {'digit': '3.14159'},
        {'digit': 3.14159},
    ),
    (
        'path',
        {'path': {'type': 'path'}},
        {'path': '~/bin'},
        {'path': '/home/ansible/bin'},
    ),
    (
        'raw',
        {'raw': {'type': 'raw'}},
        {'raw': 0x644},
        {'raw': 0x644},
    ),
    (
        'bytes',
        {'bytes': {'type': 'bytes'}},
        {'bytes': '2K'},
        {'bytes': 2048},
    ),
    (
        'bits',
        {'bits': {'type': 'bits'}},
        {'bits': '1Mb'},
        {'bits': 1048576},
    ),
    (
        'jsonarg',
        {'some_json': {'type': 'jsonarg'}},
        {'some_json': '{"users": {"bob": {"role": "accountant"}}}'},
        {'some_json': '{"users": {"bob": {"role": "accountant"}}}'},
    ),
    (
        'jsonarg-list',
        {'some_json': {'type': 'jsonarg'}},
        {'some_json': ['one', 'two']},
        {'some_json': '["one", "two"]'},
    ),
    (
        'jsonarg-dict',
        {'some_json': {'type': 'jsonarg'}},
        {'some_json': {"users": {"bob": {"role": "accountant"}}}},
        {'some_json': '{"users": {"bob": {"role": "accountant"}}}'},
    ),
    (
        'defaults',
        {'param': {'default': 'DEFAULT'}},
        {},
        {'param': 'DEFAULT'},
    ),
    (
        'elements',
        {'numbers': {'type': 'list', 'elements': 'int'}},
        {'numbers': [55, 33, 34, '22']},
        {'numbers': [55, 33, 34, 22]},
    ),
]


@pytest.mark.parametrize(
    ('arg_spec', 'parameters', 'expected'),
    ((i[1], i[2], i[3]) for i in VALID_SPECS),
    ids=[i[0] for i in VALID_SPECS]
)
def test_valid_spec(arg_spec, parameters, expected, mocker):

    mocker.patch('ansible.module_utils.common.validation.os.path.expanduser', return_value='/home/ansible/bin')
    mocker.patch('ansible.module_utils.common.validation.os.path.expandvars', return_value='/home/ansible/bin')

    v = ArgumentSpecValidator(arg_spec, parameters)
    passed = v.validate()

    assert v.validated_parameters == expected
    assert v.error_messages == []
    assert passed is True
