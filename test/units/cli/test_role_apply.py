# -*- coding: utf-8 -*-
# (c) 2015, Marc Abramowitz <msabramo@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import shlex
import sys
import yaml

from ansible.cli.role_apply import role_apply

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, mock_open, Mock


@patch('os.system')
def test_role_apply(mock_os_system):
    def os_system_side_effect(cmd):
        playbook_file = shlex.split(cmd)[-1]
        os_system_side_effect.playbook_text = open(playbook_file).read()

    mock_os_system.side_effect = os_system_side_effect
    role_apply(
        hosts=['somehost'], roles=['somerole'], show_playbook=False)
    cmd = mock_os_system.call_args[0][0]
    assert cmd.startswith('ansible-playbook')
    assert cmd.endswith('.yml')
    playbook_text = os_system_side_effect.playbook_text
    assert playbook_text.startswith('#!/usr/bin/env ansible-playbook')
    playbook = yaml.load(playbook_text)
    assert len(playbook) == 1
    assert playbook[0]['hosts'] == ['somehost']
    assert playbook[0]['roles'] == ['somerole']


@patch('ansible.cli.role_apply.Display')
@patch('os.system')
def test_role_apply_show_playbook(mock_os_system, mock_Display):
    def os_system_side_effect(cmd):
        playbook_file = shlex.split(cmd)[-1]
        os_system_side_effect.playbook_text = open(playbook_file).read()

    mock_os_system.side_effect = os_system_side_effect
    role_apply(
        hosts=['somehost'], roles=['somerole'], show_playbook=True)
    cmd = mock_os_system.call_args[0][0]
    assert cmd.startswith('ansible-playbook')
    assert cmd.endswith('.yml')
    playbook_text = os_system_side_effect.playbook_text
    assert playbook_text.startswith('#!/usr/bin/env ansible-playbook')
    playbook = yaml.load(playbook_text)
    assert len(playbook) == 1
    assert playbook[0]['hosts'] == ['somehost']
    assert playbook[0]['roles'] == ['somerole']
    mock_Display.return_value.display.assert_any_call(playbook_text)


@patch.object(sys, 'argv',
              ['ansible',
               '-r', 'somerole', '--timeout', '30', '-u', 'somueser'])
@patch('os.system')
def test_role_apply_options(mock_os_system):
    def os_system_side_effect(cmd):
        playbook_file = shlex.split(cmd)[-1]
        os_system_side_effect.playbook_text = open(playbook_file).read()

    mock_os_system.side_effect = os_system_side_effect
    role_apply(hosts=['somehost'], roles=['somerole'])
    cmd = mock_os_system.call_args[0][0]
    assert cmd.startswith('ansible-playbook')
    assert cmd.endswith('.yml')
    playbook_text = os_system_side_effect.playbook_text
    assert playbook_text.startswith('#!/usr/bin/env ansible-playbook')
    playbook = yaml.load(playbook_text)
    assert len(playbook) == 1
    assert playbook[0]['hosts'] == ['somehost']
    assert playbook[0]['roles'] == ['somerole']
