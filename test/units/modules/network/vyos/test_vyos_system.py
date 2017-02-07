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
from ansible.modules.network.vyos import vyos_system
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def set_module_args(args):
    json_args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(json_args)


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


class TestVyosSystemModule(unittest.TestCase):

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.vyos.vyos_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.vyos.vyos_system.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def execute_module(self, failed=False, changed=False, commands=None, sort=True):
        self.get_config.return_value = load_fixture('vyos_config_config.cfg')

        with self.assertRaises(AnsibleModuleExit) as exc:
            vyos_system.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result['failed'], result)
        else:
            self.assertEqual(result.get('changed'), changed, result)

        if commands:
            if sort:
                self.assertEqual(sorted(commands), sorted(result['commands']), result['commands'])
            else:
                self.assertEqual(commands, result['commands'], result['commands'])

        return result

    def test_vyos_system_hostname(self):
        set_module_args(dict(host_name='foo'))
        result = self.execute_module(changed=True)
        self.assertIn("set system host-name 'foo'", result['commands'])
        self.assertEqual(1, len(result['commands']))

    def test_vyos_system_clear_hostname(self):
        set_module_args(dict(host_name='foo', state='absent'))
        result = self.execute_module(changed=True)
        self.assertIn('delete system host-name', result['commands'])
        self.assertEqual(1, len(result['commands']))

    def test_vyos_remove_single_name_server(self):
        set_module_args(dict(name_server=['8.8.4.4'], state='absent'))
        result = self.execute_module(changed=True)
        self.assertIn("delete system name-server '8.8.4.4'", result['commands'])
        self.assertEqual(1, len(result['commands']))

    def test_vyos_system_domain_name(self):
        set_module_args(dict(domain_name='example2.com'))
        result = self.execute_module(changed=True)
        self.assertIn("set system domain-name 'example2.com'", result['commands'])
        self.assertEqual(1, len(result['commands']))

    def test_vyos_system_clear_domain_name(self):
        set_module_args(dict(domain_name='example.com', state='absent'))
        result = self.execute_module(changed=True)
        self.assertIn('delete system domain-name', result['commands'])
        self.assertEqual(1, len(result['commands']))

    def test_vyos_system_domain_search(self):
        set_module_args(dict(domain_search=['foo.example.com', 'bar.example.com']))
        result = self.execute_module(changed=True)
        self.assertIn("set system domain-search domain 'foo.example.com'", result['commands'])
        self.assertIn("set system domain-search domain 'bar.example.com'", result['commands'])
        self.assertEqual(2, len(result['commands']))

    def test_vyos_system_clear_domain_search(self):
        set_module_args(dict(domain_search=[]))
        result = self.execute_module(changed=True)
        self.assertIn('delete system domain-search domain', result['commands'])
        self.assertEqual(1, len(result['commands']))

    def test_vyos_system_no_change(self):
        set_module_args(dict(host_name='router', domain_name='example.com', name_server=['8.8.8.8', '8.8.4.4']))
        result = self.execute_module()
        self.assertEqual([], result['commands'])

    def test_vyos_system_clear_all(self):
        set_module_args(dict(state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(4, len(result['commands']))
