# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.parameters import _list_deprecations


@pytest.fixture
def params():
    return {
        'name': 'bob',
        'dest': '/etc/hosts',
        'state': 'present',
        'value': 5,
    }


def test_list_deprecations():
    argument_spec = {
        'old': {'type': 'str', 'removed_in_version': '2.5'},
        'foo': {'type': 'dict', 'options': {'old': {'type': 'str', 'removed_in_version': 1.0}}},
        'bar': {'type': 'list', 'elements': 'dict', 'options': {'old': {'type': 'str', 'removed_in_version': '2.10'}}},
    }

    params = {
        'name': 'rod',
        'old': 'option',
        'foo': {'old': 'value'},
        'bar': [{'old': 'value'}, {}],
    }
    result = _list_deprecations(argument_spec, params)
    assert len(result) == 3
    result.sort(key=lambda entry: entry['msg'])
    assert result[0]['msg'] == """Param 'bar["old"]' is deprecated. See the module docs for more information"""
    assert result[0]['version'] == '2.10'
    assert result[1]['msg'] == """Param 'foo["old"]' is deprecated. See the module docs for more information"""
    assert result[1]['version'] == 1.0
    assert result[2]['msg'] == "Param 'old' is deprecated. See the module docs for more information"
    assert result[2]['version'] == '2.5'
