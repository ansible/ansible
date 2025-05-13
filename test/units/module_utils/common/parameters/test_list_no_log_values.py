# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.common.parameters import _list_no_log_values


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
            'secret': 'under',
            'other_secret': 'makeshift',
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
    expected = set()
    assert expected == _list_no_log_values(argument_spec, module_parameters)


def test_list_no_log_values(argument_spec, module_parameters):
    expected = set(('under', 'makeshift'))
    assert expected == _list_no_log_values(argument_spec(), module_parameters())


@pytest.mark.parametrize('extra_params', [
    {'subopt1': 1},
    {'subopt1': 3.14159},
    {'subopt1': ['one', 'two']},
    {'subopt1': ('one', 'two')},
])
def test_list_no_log_values_invalid_suboptions(argument_spec, module_parameters, extra_params):
    extra_opts = {
        'subopt1': {
            'type': 'dict',
            'options': {
                'sub_1_1': {},
            }
        }
    }

    with pytest.raises(TypeError, match=r"(Value '.*?' in the sub parameter field '.*?' must be a dict, not '.*?')"
                                        r"|(dictionary requested, could not parse JSON or key=value)"):
        _list_no_log_values(argument_spec(extra_opts), module_parameters(extra_params))


def test_list_no_log_values_suboptions(argument_spec, module_parameters):
    extra_opts = {
        'subopt1': {
            'type': 'dict',
            'options': {
                'sub_1_1': {'no_log': True},
                'sub_1_2': {'type': 'list'},
            }
        }
    }

    extra_params = {
        'subopt1': {
            'sub_1_1': 'bagel',
            'sub_1_2': ['pebble'],
        }
    }

    expected = set(('under', 'makeshift', 'bagel'))
    assert expected == _list_no_log_values(argument_spec(extra_opts), module_parameters(extra_params))


def test_list_no_log_values_sub_suboptions(argument_spec, module_parameters):
    extra_opts = {
        'sub_level_1': {
            'type': 'dict',
            'options': {
                'l1_1': {'no_log': True},
                'l1_2': {},
                'l1_3': {
                    'type': 'dict',
                    'options': {
                        'l2_1': {'no_log': True},
                        'l2_2': {},
                    }
                }
            }
        }
    }

    extra_params = {
        'sub_level_1': {
            'l1_1': 'saucy',
            'l1_2': 'napped',
            'l1_3': {
                'l2_1': 'corporate',
                'l2_2': 'tinsmith',
            }
        }
    }

    expected = set(('under', 'makeshift', 'saucy', 'corporate'))
    assert expected == _list_no_log_values(argument_spec(extra_opts), module_parameters(extra_params))


def test_list_no_log_values_suboptions_list(argument_spec, module_parameters):
    extra_opts = {
        'subopt1': {
            'type': 'list',
            'elements': 'dict',
            'options': {
                'sub_1_1': {'no_log': True},
                'sub_1_2': {},
            }
        }
    }

    extra_params = {
        'subopt1': [
            {
                'sub_1_1': ['playroom', 'luxury'],
                'sub_1_2': 'deuce',
            },
            {
                'sub_1_2': ['squishier', 'finished'],
            }
        ]
    }

    expected = set(('under', 'makeshift', 'playroom', 'luxury'))
    assert expected == _list_no_log_values(argument_spec(extra_opts), module_parameters(extra_params))


def test_list_no_log_values_sub_suboptions_list(argument_spec, module_parameters):
    extra_opts = {
        'subopt1': {
            'type': 'list',
            'elements': 'dict',
            'options': {
                'sub_1_1': {'no_log': True},
                'sub_1_2': {},
                'subopt2': {
                    'type': 'list',
                    'elements': 'dict',
                    'options': {
                        'sub_2_1': {'no_log': True, 'type': 'list'},
                        'sub_2_2': {},
                    }
                }
            }
        }
    }

    extra_params = {
        'subopt1': {
            'sub_1_1': ['playroom', 'luxury'],
            'sub_1_2': 'deuce',
            'subopt2': [
                {
                    'sub_2_1': ['basis', 'gave'],
                    'sub_2_2': 'liquid',
                },
                {
                    'sub_2_1': ['composure', 'thumping']
                },
            ]
        }
    }

    expected = set(('under', 'makeshift', 'playroom', 'luxury', 'basis', 'gave', 'composure', 'thumping'))
    assert expected == _list_no_log_values(argument_spec(extra_opts), module_parameters(extra_params))


@pytest.mark.parametrize('extra_params, expected', (
    ({'subopt_dict': 'dict_subopt1=rekindle-scandal,dict_subopt2=subgroupavenge'}, ('rekindle-scandal',)),
    ({'subopt_dict': 'dict_subopt1=aversion-mutable dict_subopt2=subgroupavenge'}, ('aversion-mutable',)),
    ({'subopt_dict': ['dict_subopt1=blip-marine,dict_subopt2=subgroupavenge', 'dict_subopt1=tipping,dict_subopt2=hardening']}, ('blip-marine', 'tipping')),
))
def test_string_suboptions_as_string(argument_spec, module_parameters, extra_params, expected):
    extra_opts = {
        'subopt_dict': {
            'type': 'dict',
            'options': {
                'dict_subopt1': {'no_log': True},
                'dict_subopt2': {},
            },
        },
    }

    result = set(('under', 'makeshift'))
    result.update(expected)
    assert result == _list_no_log_values(argument_spec(extra_opts), module_parameters(extra_params))
