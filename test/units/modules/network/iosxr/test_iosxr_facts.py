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

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.errors import AnsibleModuleExit
from ansible.modules.network.iosxr import iosxr_facts
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


class TestIosxrFacts(unittest.TestCase):

    def setUp(self):
        self.mock_run_commands = patch(
            'ansible.modules.network.iosxr.iosxr_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        self.mock_run_commands.stop()

    def execute_module(self, failed=False, changed=False):

        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item)
                    command = obj['command']
                except ValueError:
                    command = item
                filename = str(command).replace(' ', '_')
                filename = filename.replace('/', '7')
                filename = filename.replace('|', '1')
                output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

        with self.assertRaises(AnsibleModuleExit) as exc:
            iosxr_facts.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result.get('failed'))
        else:
            self.assertEqual(result.get('changed'), changed, result)

        return result

    def test_iosxr_facts_gather_subset_default(self):
        set_module_args(dict())
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('hardware', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('interfaces', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals('iosxr01', ansible_facts['ansible_net_hostname'])
        self.assertEquals([], ansible_facts['ansible_net_filesystems'])
        self.assertIn('GigabitEthernet0/0/0/0',
            ansible_facts['ansible_net_interfaces'].keys())

    def test_iosxr_facts_gather_subset_config(self):
        set_module_args({'gather_subset': 'config'})
        result = self.execute_module()
        ansible_facts = result['ansible_facts']
        self.assertIn('default', ansible_facts['ansible_net_gather_subset'])
        self.assertIn('config', ansible_facts['ansible_net_gather_subset'])
        self.assertEquals('iosxr01', ansible_facts['ansible_net_hostname'])
        self.assertIn('ansible_net_config', ansible_facts)
