# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import ansible.module_utils.common.warnings as warnings

from ansible.module_utils.common.arg_spec import ModuleArgumentSpecValidator, ValidationResult


def test_module_validate():
    arg_spec = {'name': {}}
    parameters = {'name': 'larry'}
    expected = {'name': 'larry'}

    v = ModuleArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    assert isinstance(result, ValidationResult)
    assert result.error_messages == []
    assert result.deprecations == []
    assert result.warnings == []
    assert result.validated_parameters == expected


def test_module_alias_deprecations_warnings():
    arg_spec = {
        'path': {
            'aliases': ['source', 'src', 'flamethrower'],
            'deprecated_aliases': [{'name': 'flamethrower', 'date': '2020-03-04'}],
        },
    }
    parameters = {'flamethrower': '/tmp', 'source': '/tmp'}
    expected = {
        'path': '/tmp',
        'flamethrower': '/tmp',
        'source': '/tmp',
    }

    v = ModuleArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    assert result.validated_parameters == expected
    assert result.deprecations == [
        {
            'collection_name': None,
            'date': '2020-03-04',
            'name': 'flamethrower',
            'version': None,
        }
    ]
    assert "Alias 'flamethrower' is deprecated" in warnings._global_deprecations[0]['msg']
    assert result.warnings == [{'alias': 'flamethrower', 'option': 'path'}]
    assert "Both option path and its alias flamethrower are set" in warnings._global_warnings[0]
