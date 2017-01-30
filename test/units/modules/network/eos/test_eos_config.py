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
import sys
import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.errors import AnsibleModuleExit
from ansible.modules.network.eos import eos_config
from ansible.module_utils.netcfg import NetworkConfig
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

PROVIDER_ARGS = {
    'host': 'localhost',
    'username': 'username',
    'password': 'password'
}

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


class TestEosConfigModule(unittest.TestCase):

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.eos.eos_config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_supports_sessions = patch('ansible.modules.network.eos.eos_config.supports_sessions')
        self.supports_sessions = self.mock_supports_sessions.start()
        self.supports_sessions.return_value = True

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def execute_module(self, failed=False, changed=False):

        self.get_config.return_value = load_fixture('eos_config_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

        with self.assertRaises(AnsibleModuleExit) as exc:
            eos_config.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result.get('failed'))
        else:
            self.assertEqual(result.get('changed'), changed, result)

        return result

    def test_eos_config_no_change(self):
        args = dict(lines=['hostname localhost'])
        args.update(PROVIDER_ARGS)
        set_module_args(args)
        result = self.execute_module()

    def test_eos_config_src(self):
        args = dict(src=load_fixture('eos_config_candidate.cfg'))
        args.update(PROVIDER_ARGS)
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['hostname switch01', 'interface Ethernet1',
                  'description test interface', 'no shutdown', 'ip routing']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])

    def test_eos_config_lines(self):
        args = dict(lines=['hostname switch01', 'ip domain-name eng.ansible.com'])
        args.update(PROVIDER_ARGS)
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])

    def test_eos_config_before(self):
        args = dict(lines=['hostname switch01', 'ip domain-name eng.ansible.com'],
                     before=['before command'])

        args.update(PROVIDER_ARGS)
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['before command', 'hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])
        self.assertEqual('before command', result['commands'][0])

    def test_eos_config_after(self):
        args = dict(lines=['hostname switch01', 'ip domain-name eng.ansible.com'],
                     after=['after command'])

        args.update(PROVIDER_ARGS)
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['after command', 'hostname switch01']

        self.assertEqual(sorted(config), sorted(result['commands']), result['commands'])
        self.assertEqual('after command', result['commands'][-1])

    def test_eos_config_parents(self):
        args = dict(lines=['ip address 1.2.3.4/5', 'no shutdown'], parents=['interface Ethernet10'])
        args.update(PROVIDER_ARGS)
        set_module_args(args)

        result = self.execute_module(changed=True)
        config = ['interface Ethernet10', 'ip address 1.2.3.4/5', 'no shutdown']

        self.assertEqual(config, result['commands'], result['commands'])

    def test_eos_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        args.update(PROVIDER_ARGS)
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_match_exact_requires_lines(self):
        args = dict(match='exact')
        args.update(PROVIDER_ARGS)
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_match_strict_requires_lines(self):
        args = dict(match='strict')
        args.update(PROVIDER_ARGS)
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_replace_block_requires_lines(self):
        args = dict(replace='block')
        args.update(PROVIDER_ARGS)
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_replace_config_requires_src(self):
        args = dict(replace='config')
        args.update(PROVIDER_ARGS)
        set_module_args(args)
        result = self.execute_module(failed=True)

    def test_eos_config_backup_returns__backup__(self):
        args = dict(backup=True)
        args.update(PROVIDER_ARGS)
        set_module_args(args)
        result = self.execute_module()
        self.assertIn('__backup__', result)



