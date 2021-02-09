# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator


def test_spec_with_aliases():
    arg_spec = {
        'path': {'aliases': ['dir', 'directory']}
    }

    parameters = {
        'dir': '/tmp',
        'directory': '/tmp',
    }

    passed = v.validate(arg_spec, parameters)

    assert passed is True
    assert v.validated_parameters == {'path': '/tmp'}
