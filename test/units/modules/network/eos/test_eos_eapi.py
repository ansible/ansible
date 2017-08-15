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

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.eos import eos_eapi
from .eos_module import TestEosModule, load_fixture, set_module_args


class TestEosEapiModule(TestEosModule):

    module = eos_eapi

    def setUp(self):
        self.mock_run_commands = patch('ansible.modules.network.eos.eos_eapi.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_eapi.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_verify_state = patch('ansible.modules.network.eos.eos_eapi.verify_state')
        self.verify_state = self.mock_verify_state.start()

        self.command_fixtures = {}

    def tearDown(self):
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

        # hack for older version of mock
        # should be using patch.stopall() but CI is still failing
        try:
            self.mock_verify_state.stop()
        except RuntimeError:
            pass

    def load_fixtures(self, commands=None, transport='eapi'):
        def run_commands(module, commands, **kwargs):
            output = list()
            for cmd in commands:
                output.append(load_fixture(self.command_fixtures[cmd]))
            return output

        self.run_commands.side_effect = run_commands
        self.load_config.return_value = dict(diff=None, session='session')

    def start_configured(self, *args, **kwargs):
        self.command_fixtures = {
            'show vrf': 'eos_eapi_show_vrf.text',
            'show management api http-commands | json': 'eos_eapi_show_mgmt.json'
        }
        return self.execute_module(*args, **kwargs)

    def start_unconfigured(self, *args, **kwargs):
        self.command_fixtures = {
            'show vrf': 'eos_eapi_show_vrf.text',
            'show management api http-commands | json': 'eos_eapi_show_mgmt_unconfigured.json'
        }
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
        set_module_args(dict(http_port=80000))
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
        self.start_unconfigured(failed=True)

    def test_eos_eapi_state_absent(self):
        set_module_args(dict(state='stopped'))
        commands = ['management api http-commands', 'shutdown']
        self.start_configured(changed=True, commands=commands)

    def test_eos_eapi_state_failed(self):
        self.mock_verify_state.stop()
        set_module_args(dict(state='stopped', timeout=1))
        result = self.start_configured(failed=True)
        'timeout expired before eapi running state changed' in result['msg']

    def test_eos_eapi_state_failed(self):
        self.mock_verify_state.stop()
        set_module_args(dict(state='stopped', timeout=1))
        result = self.start_configured(failed=True)
        'timeout expired before eapi running state changed' in result['msg']
