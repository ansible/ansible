# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.parameters import list_deprecations


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
        'old': {'type': 'str', 'removed_in_version': '2.5'}
    }

    params = {
        'name': 'rod',
        'old': 'option',
    }
    result = list_deprecations(argument_spec, params)
    for item in result:
        assert item['msg'] == "Param 'old' is deprecated. See the module docs for more information"
        assert item['version'] == '2.5'
