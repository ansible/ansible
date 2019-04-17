# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import pytest

from ansible.module_utils.common.parameters import handle_aliases
from ansible.module_utils._text import to_native

DEFAULT_LEGAL_INPUTS = [
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
]


def test_handle_aliases_no_aliases():
    argument_spec = {
        'name': {'type': 'str'},
    }

    params = {
        'name': 'foo',
        'path': 'bar'
    }

    expected = (
        {},
        DEFAULT_LEGAL_INPUTS + ['name'],
    )
    expected[1].sort()

    result = handle_aliases(argument_spec, params)
    result[1].sort()
    assert expected == result


def test_handle_aliases_basic():
    argument_spec = {
        'name': {'type': 'str', 'aliases': ['surname', 'nick']},
    }

    params = {
        'name': 'foo',
        'path': 'bar',
        'surname': 'foo',
        'nick': 'foo',
    }

    expected = (
        {'surname': 'name', 'nick': 'name'},
        DEFAULT_LEGAL_INPUTS + ['name', 'surname', 'nick'],
    )
    expected[1].sort()

    result = handle_aliases(argument_spec, params)
    result[1].sort()
    assert expected == result


def test_handle_aliases_value_error():
    argument_spec = {
        'name': {'type': 'str', 'aliases': ['surname', 'nick'], 'default': 'bob', 'required': True},
    }

    params = {
        'name': 'foo',
    }

    with pytest.raises(ValueError) as ve:
        handle_aliases(argument_spec, params)
        assert 'internal error: aliases must be a list or tuple' == to_native(ve.error)


def test_handle_aliases_type_error():
    argument_spec = {
        'name': {'type': 'str', 'aliases': 'surname'},
    }

    params = {
        'name': 'foo',
    }

    with pytest.raises(TypeError) as te:
        handle_aliases(argument_spec, params)
        assert 'internal error: required and default are mutually exclusive' in to_native(te.error)
