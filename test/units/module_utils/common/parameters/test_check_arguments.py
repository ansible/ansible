# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from ansible.module_utils.common.parameters import get_unsupported_parameters


@pytest.fixture
def argument_spec():
    return {
        'state': {'aliases': ['status']},
        'enabled': {},
    }


def mock_handle_aliases(*args):
    aliases = {}
    legal_inputs = [
        '_ansible_check_mode',
        '_ansible_debug',
        '_ansible_diff',
        '_ansible_keep_remote_files',
        '_ansible_module_name',
        '_ansible_no_log',
        '_ansible_remote_tmp',
        '_ansible_selinux_special_fs',
        '_ansible_shell_executable',
        '_ansible_socket',
        '_ansible_string_conversion_action',
        '_ansible_syslog_facility',
        '_ansible_tmpdir',
        '_ansible_verbosity',
        '_ansible_version',
        'state',
        'status',
        'enabled',
    ]

    return aliases, legal_inputs


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
    mocker.patch('ansible.module_utils.common.parameters.handle_aliases', side_effect=mock_handle_aliases)
    result = get_unsupported_parameters(argument_spec, module_parameters, legal_inputs)

    assert result == expected
