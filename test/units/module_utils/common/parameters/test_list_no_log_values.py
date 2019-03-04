# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.parameters import list_no_log_values


@pytest.fixture
def params():
    return {
        'secret': 'undercookwovennativity',
        'other_secret': 'cautious-slate-makeshift',
        'state': 'present',
        'value': 5,
    }


def test_list_no_log_values(params):
    argument_spec = {
        'secret': {'type': 'str', 'no_log': True},
        'other_secret': {'type': 'str', 'no_log': True},
        'state': {'type': 'str'},
        'value': {'type': 'int'},
    }
    result = set(('undercookwovennativity', 'cautious-slate-makeshift'))
    assert result == list_no_log_values(argument_spec, params)


def test_list_no_log_values_no_secrets(params):
    argument_spec = {
        'other_secret': {'type': 'str', 'no_log': False},
        'state': {'type': 'str'},
        'value': {'type': 'int'},
    }
    result = set()
    assert result == list_no_log_values(argument_spec, params)
