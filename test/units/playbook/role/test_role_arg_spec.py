# -*- coding: utf-8 -*-
# (c) 2020 Ansible Project
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.playbook.role import Role


def test_Role__create_validation_task():
    """Test that we properly create task data from a role entry point's arg spec."""
    role = Role()
    entrypoint = "main"
    argspec = {
        'short_description': 'foo',
        'options': {
            'param1': {
                'type': 'str',
                'required': 'true'
            }
        }
    }
    expected = {
        'name': "Validating arguments against arg spec '%s' - %s" % (entrypoint, argspec['short_description']),
        'action': {
            'module': 'validate_arg_spec',
            'argument_spec': argspec['options'],
            'provided_arguments': {},
            'validate_args_context': {
                'argument_spec_name': 'main',
                'name': None,
                'path': None,
                'type': 'role'
            }
        }
    }

    actual = role._create_validation_task(argspec, entrypoint)
    assert expected == actual


def test_Role__prepend_validation_task():
    """Test that we properly insert task data at the front of an existing task list."""
    role = Role()
    metadata = {
        'main': {
            'options': {
                'param1': {
                    'type': 'str',
                    'required': 'true'
                }
            }
        }
    }
    expected = {
        'name': "Validating arguments against arg spec 'main'",
        'action': {
            'module': 'validate_arg_spec',
            'argument_spec': metadata['main']['options'],
            'provided_arguments': {},
            'validate_args_context': {
                'argument_spec_name': 'main',
                'name': None,
                'path': None,
                'type': 'role'
            }
        }
    }
    task_data = ['first', 'second']

    role._prepend_validation_task(task_data, metadata)
    assert task_data == [expected, 'first', 'second']
