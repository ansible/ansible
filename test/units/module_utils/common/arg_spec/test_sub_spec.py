# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator, ValidationResult


def test_sub_spec():
    arg_spec = {
        'state': {},
        'user': {
            'type': 'dict',
            'options': {
                'first': {'no_log': True},
                'last': {},
                'age': {'type': 'int'},
            }
        }
    }

    parameters = {
        'state': 'present',
        'user': {
            'first': 'Rey',
            'last': 'Skywalker',
            'age': '19',
        }
    }

    expected = {
        'state': 'present',
        'user': {
            'first': 'Rey',
            'last': 'Skywalker',
            'age': 19,
        }
    }

    v = ArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    assert isinstance(result, ValidationResult)
    assert result.validated_parameters == expected
    assert result.error_messages == []


def test_nested_sub_spec():
    arg_spec = {
        'type': {},
        'car': {
            'type': 'dict',
            'options': {
                'make': {},
                'model': {},
                'customizations': {
                    'type': 'dict',
                    'options': {
                        'engine': {},
                        'transmission': {},
                        'color': {},
                        'max_rpm': {'type': 'int'},
                    }
                }
            }
        }
    }

    parameters = {
        'type': 'endurance',
        'car': {
            'make': 'Ford',
            'model': 'GT-40',
            'customizations': {
                'engine': '7.0 L',
                'transmission': '5-speed',
                'color': 'Ford blue',
                'max_rpm': '6000',
            }

        }
    }

    expected = {
        'type': 'endurance',
        'car': {
            'make': 'Ford',
            'model': 'GT-40',
            'customizations': {
                'engine': '7.0 L',
                'transmission': '5-speed',
                'color': 'Ford blue',
                'max_rpm': 6000,
            }

        }
    }

    v = ArgumentSpecValidator(arg_spec)
    result = v.validate(parameters)

    assert isinstance(result, ValidationResult)
    assert result.validated_parameters == expected
    assert result.error_messages == []
