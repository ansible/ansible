# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from ansible.module_utils.common.parameters import _get_unsupported_parameters


@pytest.fixture
def argument_spec():
    return {
        'state': {'aliases': ['status']},
        'enabled': {},
    }


@pytest.mark.parametrize(
    ('module_parameters', 'legal_inputs', 'expected'),
    (
        ({'fish': 'food'}, ['state', 'enabled'], set(['fish'])),
        ({'state': 'enabled', 'path': '/var/lib/path'}, None, set(['path'])),
        ({'state': 'enabled', 'path': '/var/lib/path'}, ['state', 'path'], set()),
        ({'state': 'enabled', 'path': '/var/lib/path'}, ['state'], set(['path'])),
        ({}, None, set()),
        ({'state': 'enabled'}, None, set()),
        ({'status': 'enabled', 'enabled': True, 'path': '/var/lib/path'}, None, set(['path'])),
        ({'status': 'enabled', 'enabled': True}, None, set()),
    )
)
def test_check_arguments(argument_spec, module_parameters, legal_inputs, expected, mocker):
    result = _get_unsupported_parameters(argument_spec, module_parameters, legal_inputs)

    assert result == expected
