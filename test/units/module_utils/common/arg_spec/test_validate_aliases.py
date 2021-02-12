# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator
from ansible.module_utils.common.warnings import get_deprecation_messages


def test_spec_with_aliases():
    arg_spec = {
        'path': {'aliases': ['dir', 'directory']}
    }

    parameters = {
        'dir': '/tmp',
        'directory': '/tmp',
    }

    expected = {
        'dir': '/tmp',
        'directory': '/tmp',
        'path': '/tmp',
    }

    v = ArgumentSpecValidator(arg_spec, parameters)
    passed = v.validate()

    assert passed is True
    assert v.validated_parameters == expected


def test_alias_deprecation():
    arg_spec = {
        'path': {
            'aliases': ['not_yo_path'],
            'deprecated_aliases': [{
                'name': 'not_yo_path',
                'version': '1.7',
            }]
        }
    }

    parameters = {
        'not_yo_path': '/tmp',
    }

    expected = {
        'path': '/tmp',
        'not_yo_path': '/tmp',
    }

    v = ArgumentSpecValidator(arg_spec, parameters)
    passed = v.validate()

    assert passed is True
    assert v.validated_parameters == expected
    assert v.error_messages == []
    assert "Alias 'not_yo_path' is deprecated." in get_deprecation_messages()[0]['msg']
