#
# (c) 2016 Red Hat Inc.
# (c) 2017 Paul Neumann
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

from units.compat.mock import patch
from ansible.modules.network.icx import icx_system
from units.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXSystemModule(TestICXModule):

    module = icx_system

    def setUp(self):
        super(TestICXSystemModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.icx.icx_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.icx.icx_system.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_exec_command = patch('ansible.modules.network.icx.icx_system.exec_command')
        self.exec_command = self.mock_exec_command.start()
        self.set_running_config()

    def tearDown(self):
        super(TestICXSystemModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_exec_command.stop()

    def load_fixtures(self, commands=None):
        compares = None

        def load_file(*args, **kwargs):
            module = args
            for arg in args:
                if arg is not None:
                    if arg.params['check_running_config'] is not None:
                        compares = arg.params['check_running_config']
                        break
                    else:
                        compares = None

            env = self.get_running_config(compares)
            if env is True:
                return load_fixture('icx_system.txt').strip()
            else:
                return ''

        self.get_config.side_effect = load_file
        self.load_config.return_value = None

    def test_icx_system_set_config(self):
        set_module_args(dict(hostname='ruckus', name_servers=['172.16.10.2', '11.22.22.4'], domain_search=['ansible.com', 'redhat.com']))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'hostname ruckus',
                'ip dns domain-list ansible.com',
                'ip dns domain-list redhat.com',
                'ip dns server-address 11.22.22.4',
                'ip dns server-address 172.16.10.2'
            ]
            self.execute_module(changed=True, commands=commands)

        else:
            commands = [
                'hostname ruckus',
                'ip dns domain-list ansible.com',
                'ip dns domain-list redhat.com',
                'ip dns server-address 11.22.22.4',
                'ip dns server-address 172.16.10.2',
                'no ip dns domain-list ansib.eg.com',
                'no ip dns domain-list red.com',
                'no ip dns domain-list test1.com',
                'no ip dns server-address 10.22.22.64',
                'no ip dns server-address 172.22.22.64'
            ]
            self.execute_module(changed=True, commands=commands)

    def test_icx_system_remove_config(self):
        set_module_args(dict(name_servers=['10.22.22.64', '11.22.22.4'], domain_search=['ansib.eg.com', 'redhat.com'], state='absent'))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'no ip dns domain-list ansib.eg.com',
                'no ip dns domain-list redhat.com',
                'no ip dns server-address 10.22.22.64',
                'no ip dns server-address 11.22.22.4'
            ]
            self.execute_module(changed=True, commands=commands)

        else:
            commands = [
                'no ip dns domain-list ansib.eg.com',
                'no ip dns server-address 10.22.22.64',
            ]
            self.execute_module(changed=True, commands=commands)

    def test_icx_system_remove_config_compare(self):
        set_module_args(
            dict(
                name_servers=[
                    '10.22.22.64',
                    '11.22.22.4'],
                domain_search=[
                    'ansib.eg.com',
                    'redhat.com'],
                state='absent',
                check_running_config=True))
        if self.get_running_config(compare=True):
            if not self.ENV_ICX_USE_DIFF:
                commands = [
                    'no ip dns domain-list ansib.eg.com',
                    'no ip dns server-address 10.22.22.64',
                ]
                self.execute_module(changed=True, commands=commands)
            else:
                commands = [
                    'no ip dns domain-list ansib.eg.com',
                    'no ip dns server-address 10.22.22.64',
                ]
                self.execute_module(changed=True, commands=commands)

    def test_icx_aaa_servers_radius_set(self):
        radius = [
            dict(
                type='radius',
                hostname='2001:db8::1',
                auth_port_type='auth-port',
                auth_port_num='1821',
                acct_port_num='1321',
                acct_type='accounting-only',
                auth_key='radius',
                auth_key_type=[
                    'dot1x',
                    'mac-auth']),
            dict(
                type='radius',
                hostname='172.16.10.24',
                auth_port_type='auth-port',
                auth_port_num='2001',
                acct_port_num='5000',
                acct_type='authentication-only',
                auth_key='radius-server'),
            dict(
                type='tacacs',
                hostname='ansible.com')]
        set_module_args(dict(hostname='ruckus', aaa_servers=radius))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'hostname ruckus',
                'radius-server host 172.16.10.24 auth-port 2001 acct-port 5000 authentication-only key radius-server',
                'radius-server host ipv6 2001:db8::1 auth-port 1821 acct-port 1321 accounting-only key radius mac-auth dot1x',
                'tacacs-server host ansible.com'
            ]
            self.execute_module(changed=True, commands=commands)

        else:
            commands = [
                'hostname ruckus',
                'no radius-server host 172.16.20.14',
                'no tacacs-server host 182.16.10.20',
                'radius-server host 172.16.10.24 auth-port 2001 acct-port 5000 authentication-only key radius-server',
                'radius-server host ipv6 2001:db8::1 auth-port 1821 acct-port 1321 accounting-only key radius mac-auth dot1x',
                'tacacs-server host ansible.com'
            ]
            self.execute_module(changed=True, commands=commands)
