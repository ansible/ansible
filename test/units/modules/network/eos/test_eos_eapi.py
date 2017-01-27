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
from ansible.modules.network.eos import eos_eapi
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


class TestEosEapiModule(unittest.TestCase):

    def setUp(self):
        self.mock_run_commands = patch('ansible.modules.network.eos.eos_eapi.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_eapi.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def execute_module(self, failed=False, changed=False, commands=None,
            sort=True, command_fixtures={}):

        def run_commands(module, commands, **kwargs):
            output = list()
            for cmd in commands:
                output.append(load_fixture(command_fixtures[cmd]))
            return (0, output, '')

        self.run_commands.side_effect = run_commands
        self.load_config.return_value = dict(diff=None, session='session')

        with self.assertRaises(AnsibleModuleExit) as exc:
            eos_eapi.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result.get('failed'), result)
        else:
            self.assertEqual(result.get('changed'), changed, result)

        if commands:
            if sort:
                self.assertEqual(sorted(commands), sorted(result['commands']), result['commands'])
            else:
                self.assertEqual(commands, result['commands'])

        return result

    def start_configured(self, *args, **kwargs):
        command_fixtures = {
            'show vrf': 'eos_eapi_show_vrf.text',
            'show management api http-commands | json': 'eos_eapi_show_mgmt.json'
        }
        kwargs['command_fixtures'] = command_fixtures
        return self.execute_module(*args, **kwargs)

    def start_unconfigured(self, *args, **kwargs):
        command_fixtures = {
            'show vrf': 'eos_eapi_show_vrf.text',
            'show management api http-commands | json': 'eos_eapi_show_mgmt_unconfigured.json'
        }
        kwargs['command_fixtures'] = command_fixtures
        return self.execute_module(*args, **kwargs)

    def test_eos_eapi_http_enable(self):
        set_module_args(dict(http=True))
        commands = ['management api http-commands', 'protocol http port 80',
                    'no shutdown']
        self.start_unconfigured(changed=True, commands=commands)

    def test_eos_eapi_http_disable(self):
        set_module_args(dict(http=False))
        commands = ['management api http-commands', 'no protocol http']
        self.start_configured(changed=True, commands=commands)

    def test_eos_eapi_http_port(self):
        set_module_args(dict(http_port=81))
        commands = ['management api http-commands', 'protocol http port 81']
        self.start_configured(changed=True, commands=commands)

    def test_eos_eapi_http_invalid(self):
        set_module_args(dict(port=80000))
        commands = []
        self.start_unconfigured(failed=True)

    def test_eos_eapi_https_enable(self):
        set_module_args(dict(https=True))
        commands = ['management api http-commands', 'protocol https port 443',
                    'no shutdown']
        self.start_unconfigured(changed=True, commands=commands)

    def test_eos_eapi_https_disable(self):
        set_module_args(dict(https=False))
        commands = ['management api http-commands', 'no protocol https']
        self.start_configured(changed=True, commands=commands)

    def test_eos_eapi_https_port(self):
        set_module_args(dict(https_port=8443))
        commands = ['management api http-commands', 'protocol https port 8443']
        self.start_configured(changed=True, commands=commands)

    def test_eos_eapi_local_http_enable(self):
        set_module_args(dict(local_http=True))
        commands = ['management api http-commands', 'protocol http localhost port 8080',
                    'no shutdown']
        self.start_unconfigured(changed=True, commands=commands)

    def test_eos_eapi_local_http_disable(self):
        set_module_args(dict(local_http=False))
        commands = ['management api http-commands', 'no protocol http localhost']
        self.start_configured(changed=True, commands=commands)

    def test_eos_eapi_local_http_port(self):
        set_module_args(dict(local_http_port=81))
        commands = ['management api http-commands', 'protocol http localhost port 81']
        self.start_configured(changed=True, commands=commands)

    def test_eos_eapi_vrf(self):
        set_module_args(dict(vrf='test'))
        commands = ['management api http-commands', 'vrf test', 'no shutdown']
        self.start_unconfigured(changed=True, commands=commands)

    def test_eos_eapi_vrf_missing(self):
        set_module_args(dict(vrf='missing'))
        commands = []
        self.start_unconfigured(failed=True, commands=commands)

    def test_eos_eapi_state_absent(self):
        set_module_args(dict(state='stopped'))
        commands = ['management api http-commands', 'shutdown']
        self.start_configured(changed=True, commands=commands)

