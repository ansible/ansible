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

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.errors import AnsibleModuleExit
from ansible.modules.network.iosxr import _iosxr_template
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


class TestIosxrTemplateModule(unittest.TestCase):

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.iosxr._iosxr_template.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.iosxr._iosxr_template.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def execute_module(self, failed=False, changed=False, commands=None,
            sort=True):

        config_file = 'iosxr_template_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

        with self.assertRaises(AnsibleModuleExit) as exc:
            _iosxr_template.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result['failed'], result)
        else:
            self.assertEqual(result.get('changed'), changed, result)

        if commands:
            if sort:
                self.assertEqual(sorted(commands), sorted(result['updates']), result['updates'])
            else:
                self.assertEqual(commands, result['updates'], result['updates'])

        return result

    def test_iosxr_template_unchanged(self):
        src = load_fixture('iosxr_template_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_iosxr_template_simple(self):
        src = load_fixture('iosxr_template_src.cfg')
        set_module_args(dict(src=src))
        commands = ['hostname foo',
                    'interface GigabitEthernet0/0',
                    'no ip address']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_template_force(self):
        src = load_fixture('iosxr_template_config.cfg')
        set_module_args(dict(src=src, force=True))
        commands = [str(s).strip() for s in src.split('\n') if s and s != '!']
        self.execute_module(changed=True, commands=commands)
        self.assertFalse(self.get_config.called)

    def test_iosxr_template_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_iosxr_template_config(self):
        src = load_fixture('iosxr_template_config.cfg')
        config = 'hostname router'
        set_module_args(dict(src=src, config=config))
        commands = ['interface GigabitEthernet0/0',
                    'ip address 1.2.3.4 255.255.255.0',
                    'description test string',
                    'interface GigabitEthernet0/1',
                    'ip address 6.7.8.9 255.255.255.0',
                    'description test string',
                    'shutdown']
        self.execute_module(changed=False)
        self.assertTrue(self.get_config.called)
