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
from ansible.modules.network.vyos import vyos_config
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


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


class TestVyosConfigModule(unittest.TestCase):

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.vyos.vyos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.vyos.vyos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.vyos.vyos_config.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def execute_module(self, failed=False, changed=False, commands=None, sort=True, defaults=False):

        config_file = 'vyos_config_defaults.cfg' if defaults else 'vyos_config_config.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

        with self.assertRaises(AnsibleModuleExit) as exc:
            vyos_config.main()

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

    def test_vyos_config_unchanged(self):
        src = load_fixture('vyos_config_config.cfg')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_vyos_config_src(self):
        src = load_fixture('vyos_config_src.cfg')
        set_module_args(dict(src=src))
        commands = ['set system host-name foo', 'delete interfaces ethernet eth0 address']
        self.execute_module(changed=True, commands=commands)

    def test_vyos_config_src_brackets(self):
        src = load_fixture('vyos_config_src_brackets.cfg')
        set_module_args(dict(src=src))
        commands = ['set interfaces ethernet eth0 address 10.10.10.10/24', 'set system host-name foo']
        self.execute_module(changed=True, commands=commands)

    def test_vyos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_vyos_config_save(self):
        set_module_args(dict(save=True))
        self.execute_module(changed=True)
        self.assertEqual(self.run_commands.call_count, 1)
        self.assertEqual(self.get_config.call_count, 0)
        self.assertEqual(self.load_config.call_count, 0)
        args = self.run_commands.call_args[0][1]
        self.assertIn('save', args)

    def test_vyos_config_lines(self):
        commands = ['set system host-name foo']
        set_module_args(dict(lines=commands))
        self.execute_module(changed=True, commands=commands)

    def test_vyos_config_config(self):
        config = 'set system host-name localhost'
        new_config = ['set system host-name router']
        set_module_args(dict(lines=new_config, config=config))
        self.execute_module(changed=True, commands=new_config)

    def test_vyos_config_match_none(self):
        lines = ['set system interfaces ethernet eth0 address 1.2.3.4/24',
                 'set system interfaces ethernet eth0 description test string']
        set_module_args(dict(lines=lines, match='none'))
        self.execute_module(changed=True, commands=lines, sort=False)
