# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

import ansible.module_utils.common.warnings as warnings

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator, ValidationResult

# Each item is id, argument_spec, parameters, expected, valid parameter names
VALID_SPECS = [
    (
        'str-no-type-specified',
        {'name': {}},
        {'name': 'rey'},
        {'name': 'rey'},
        set(('name',)),
    ),
    (
        'str',
        {'name': {'type': 'str'}},
        {'name': 'rey'},
        {'name': 'rey'},
        set(('name',)),
    ),
    (
        'str-convert',
        {'name': {'type': 'str'}},
        {'name': 5},
        {'name': '5'},
        set(('name',)),
    ),
    (
        'list',
        {'packages': {'type': 'list'}},
        {'packages': ['vim', 'python']},
        {'packages': ['vim', 'python']},
        set(('packages',)),
    ),
    (
        'list-comma-string',
        {'packages': {'type': 'list'}},
        {'packages': 'vim,python'},
        {'packages': ['vim', 'python']},
        set(('packages',)),
    ),
    (
        'list-comma-string-space',
        {'packages': {'type': 'list'}},
        {'packages': 'vim, python'},
        {'packages': ['vim', ' python']},
        set(('packages',)),
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
        set(('user',)),
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
        set(('user',)),
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
        set(('user',)),
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
        set(('enabled', 'disabled')),
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
        set(('enabled', 'disabled')),
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
        set(('enabled', 'disabled')),
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
        set(('enabled', 'disabled')),
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
        set(('enabled', 'disabled')),
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
        set(('enabled', 'disabled')),
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
        set(('enabled', 'disabled')),
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
        set(('enabled', 'disabled')),
    ),
    (
        'float',
        {'digit': {'type': 'float'}},
        {'digit': 3.14159},
        {'digit': 3.14159},
        set(('digit',)),
    ),
    (
        'float-str',
        {'digit': {'type': 'float'}},
        {'digit': '3.14159'},
        {'digit': 3.14159},
        set(('digit',)),
    ),
    (
        'path',
        {'path': {'type': 'path'}},
        {'path': '~/bin'},
        {'path': '/home/ansible/bin'},
        set(('path',)),
    ),
    (
        'raw',
        {'raw': {'type': 'raw'}},
        {'raw': 0x644},
        {'raw': 0x644},
        set(('raw',)),
    ),
    (
        'bytes',
        {'bytes': {'type': 'bytes'}},
        {'bytes': '2K'},
        {'bytes': 2048},
        set(('bytes',)),
    ),
    (
        'bits',
        {'bits': {'type': 'bits'}},
        {'bits': '1Mb'},
        {'bits': 1048576},
        set(('bits',)),
    ),
    (
        'jsonarg',
        {'some_json': {'type': 'jsonarg'}},
        {'some_json': '{"users": {"bob": {"role": "accountant"}}}'},
        {'some_json': '{"users": {"bob": {"role": "accountant"}}}'},
        set(('some_json',)),
    ),
    (
        'jsonarg-list',
        {'some_json': {'type': 'jsonarg'}},
        {'some_json': ['one', 'two']},
        {'some_json': '["one", "two"]'},
        set(('some_json',)),
    ),
    (
        'jsonarg-dict',
        {'some_json': {'type': 'jsonarg'}},
        {'some_json': {"users": {"bob": {"role": "accountant"}}}},
        {'some_json': '{"users": {"bob": {"role": "accountant"}}}'},
        set(('some_json',)),
    ),
    (
        'defaults',
        {'param': {'default': 'DEFAULT'}},
        {},
        {'param': 'DEFAULT'},
        set(('param',)),
    ),
    (
        'elements',
        {'numbers': {'type': 'list', 'elements': 'int'}},
        {'numbers': [55, 33, 34, '22']},
        {'numbers': [55, 33, 34, 22]},
        set(('numbers',)),
    ),
    (
        'aliases',
        {'src': {'aliases': ['path', 'source']}},
        {'src': '/tmp'},
        {'src': '/tmp'},
        set(('src (path, source)',)),
    )
]


@pytest.mark.parametrize(
    ('arg_spec', 'parameters', 'expected', 'valid_params'),
    (i[1:] for i in VALID_SPECS),
    ids=[i[0] for i in VALID_SPECS]
)
def test_valid_spec(arg_spec, parameters, expected, valid_params, mocker):
    mocker.patch('ansible.module_utils.common.validation.os.path.expanduser', return_value='/home/ansible/bin')
    mocker.patch('ansible.module_utils.common.validation.os.path.expandvars', return_value='/home/ansible/bin')

    v = ArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    assert isinstance(result, ValidationResult)
    assert result.validated_parameters == expected
    assert result.unsupported_parameters == set()
    assert result.error_messages == []
    assert v._valid_parameter_names == valid_params

    # Again to check caching
    assert v._valid_parameter_names == valid_params
