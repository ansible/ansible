#!/usr/bin/env python
#
# (c) 2016 Red Hat Inc.
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json

import ansible.module_utils.basic

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.errors import AnsibleModuleExit
from ansible.modules.network.iosxr import iosxr_system
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}

def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except:
        pass

    fixture_data[path] = data
    return data


class TestIosxrSystemModule(unittest.TestCase):

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.iosxr.iosxr_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.iosxr.iosxr_system.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def execute_module(self, failed=False, changed=False, commands=None, sort=True):

        self.get_config.return_value = load_fixture('iosxr_system_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

        with self.assertRaises(AnsibleModuleExit) as exc:
            iosxr_system.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result['failed'], result)
        else:
            self.assertEqual(result['changed'], changed, result)

        if commands:
            if sort:
                self.assertEqual(sorted(commands), sorted(result['commands']), result['commands'])
            else:
                self.assertEqual(commands, result['commands'])

        return result

    def test_iosxr_system_hostname_changed(self):
        set_module_args(dict(hostname='foo'))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_domain_name(self):
        set_module_args(dict(domain_name='test.com'))
        commands = ['domain name test.com']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_domain_search(self):
        set_module_args(dict(domain_search=['ansible.com', 'redhat.com']))
        commands=['domain list ansible.com', 'no domain list cisco.com']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_lookup_source(self):
        set_module_args(dict(lookup_source='Ethernet1'))
        commands = ['domain lookup source-interface Ethernet1']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_lookup_enabled(self):
        set_module_args(dict(lookup_enabled=True))
        commands = ['no domain lookup disable']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_name_servers(self):
        name_servers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
        set_module_args(dict(name_servers=name_servers))
        commands = ['domain name-server 1.1.1.1', 'no domain name-server 8.8.4.4']
        self.execute_module(changed=True)

    def test_iosxr_system_state_absent(self):
        set_module_args(dict(state='absent'))
        commands = ['no hostname', 'no domain name',
                             'no domain lookup disable',
                             'no domain lookup source-interface MgmtEth0/0/CPU0/0',
                             'no domain list redhat.com', 'no domain list cisco.com',
                             'no domain name-server 8.8.8.8', 'no domain name-server 8.8.4.4']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_no_change(self):
        set_module_args(dict(hostname='iosxr01', domain_name='eng.ansible.com'))
        self.execute_module()

