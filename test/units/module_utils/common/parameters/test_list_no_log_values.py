# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.parameters import list_no_log_values


@pytest.fixture
def argument_spec():
    # Allow extra specs to be passed to the fixture, which will be added to the output
    def _argument_spec(extra_opts=None):
        spec = {
            'secret': {'type': 'str', 'no_log': True},
            'other_secret': {'type': 'str', 'no_log': True},
            'state': {'type': 'str'},
            'value': {'type': 'int'},
        }

        if extra_opts:
            spec.update(extra_opts)

        return spec

    return _argument_spec


@pytest.fixture
def module_parameters():
    # Allow extra parameters to be passed to the fixture, which will be added to the output
    def _module_parameters(extra_params=None):
        params = {
            'secret': 'undercookwovennativity',
            'other_secret': 'cautious-slate-makeshift',
            'state': 'present',
            'value': 5,
        }

        if extra_params:
            params.update(extra_params)

        return params

    return _module_parameters


def test_list_no_log_values_no_secrets(module_parameters):
    argument_spec = {
        'other_secret': {'type': 'str', 'no_log': False},
        'state': {'type': 'str'},
        'value': {'type': 'int'},
    }
    result = set()
    assert result == list_no_log_values(argument_spec, module_parameters)


def test_list_no_log_values(argument_spec, module_parameters):
    result = set(('undercookwovennativity', 'cautious-slate-makeshift'))
    assert result == list_no_log_values(argument_spec(), module_parameters())


def test_list_no_log_values_suboptions(argument_spec, module_parameters):
    extra_opts = {
        'subopt1': {
            'type': 'dict',
            'options': {
                'sub_1_1': {'no_log': True},
                'sub_1_2': {'type': 'list'},
            },
        },
    }

    extra_params = {
        'subopt1': {
            'sub_1_1': 'Precision-Bagel',
            'sub_1_2': ['Pebble-Slogan'],
        }
    }

    result = set(('undercookwovennativity', 'cautious-slate-makeshift', 'Precision-Bagel'))
    assert result == list_no_log_values(argument_spec(extra_opts), module_parameters(extra_params))


def test_list_no_log_values_recursive_suboptions(argument_spec, module_parameters):
    extra_opts = {
        'subopt1': {
            'type': 'dict',
            'options': {
                'sub_1_1': {'no_log': True},
                'subopt2': {
                    'type': 'dict',
                    'options': {
                        'sub_2_1': {'no_log': True},
                        'sub_2_2': {},
                    },
                },
            },
        },
    }

    extra_params = {
        'subopt1': {
            'sub_1_1': 'Precision-Bagel',
            'subopt2': {
                'sub_2_1': 'Sandstone-Unwrapped',
                'sub_2_2': 'Hamstring-Aged',
            },
        }
    }
    result = set(('undercookwovennativity', 'cautious-slate-makeshift', 'Precision-Bagel', 'Sandstone-Unwrapped'))
    assert result == list_no_log_values(argument_spec(extra_opts), module_parameters(extra_params))


