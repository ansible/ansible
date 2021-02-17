# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator

# Each item is id, argument_spec, parameters, expected
VALID_SPECS = [
    [
        'basic',
        {
            'param_str': {'type': 'str'},
            'param_list': {'type': 'list'},
            'param_dict': {'type': 'dict'},
            'param_bool': {'type': 'bool'},
            'param_int': {'type': 'int'},
            'param_float': {'type': 'float'},
            'param_path': {'type': 'path'},
            'param_raw': {'type': 'raw'},
            'param_bytes': {'type': 'bytes'},
            'param_bits': {'type': 'bits'},

        },
        {
            'param_str': 22,
            'param_list': 'one,two,three',
            'param_dict': 'first=star,last=lord',
            'param_bool': True,
            'param_int': 22,
            'param_float': 1.5,
            'param_path': '/tmp',
            'param_raw': 'raw',
            'param_bytes': '2K',
            'param_bits': '1Mb',
        },
        {
            'param_str': '22',
            'param_list': ['one', 'two', 'three'],
            'param_dict': {'first': 'star', 'last': 'lord'},
            'param_bool': True,
            'param_float': 1.5,
            'param_int': 22,
            'param_path': '/tmp',
            'param_raw': 'raw',
            'param_bits': 1048576,
            'param_bytes': 2048,
        },
    ],
    [
        'defaults',
        {
            'param_str': {'type': 'str', 'default': 'DEFAULT'},
        },
        {},
        {
            'param_str': 'DEFAULT',
        },
    ],
    [
        'elements',
        {
            'param_list': {
                'type': 'list',
                'elements': 'int',
            }
        },
        {
            'param_list': [55, 33, 34, '22'],
        },
        {
            'param_list': [55, 33, 34, 22],
        },
    ],
]


@pytest.mark.parametrize(
    ('arg_spec', 'parameters', 'expected'),
    ((i[1], i[2], i[3]) for i in VALID_SPECS),
    ids=[i[0] for i in VALID_SPECS]
)
def test_valid_spec(arg_spec, parameters, expected):

    v = ArgumentSpecValidator(arg_spec, parameters)
    passed = v.validate()

    assert passed is True
    assert v.validated_parameters == expected
    assert v.error_messages == []
