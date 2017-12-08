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

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_system
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosSystemModule(TestNxosModule):

    module = nxos_system

    def setUp(self):
        super(TestNxosSystemModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_system.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestNxosSystemModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('', 'nxos_system_config.cfg')
        self.load_config.return_value = None

    def test_nxos_system_hostname_changed(self):
        set_module_args(dict(hostname='foo'))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_domain_lookup(self):
        set_module_args(dict(domain_lookup=True))
        commands = ['ip domain-lookup']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_missing_vrf(self):
        domain_name = dict(name='example.com', vrf='example')
        set_module_args(dict(domain_name=domain_name))
        self.execute_module(failed=True)

    def test_nxos_system_domain_name(self):
        set_module_args(dict(domain_name=['example.net']))
        commands = ['no ip domain-name ansible.com',
                    'vrf context management', 'no ip domain-name eng.ansible.com', 'exit',
                    'ip domain-name example.net']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_domain_name_complex(self):
        domain_name = dict(name='example.net', vrf='management')
        set_module_args(dict(domain_name=[domain_name]))
        commands = ['no ip domain-name ansible.com',
                    'vrf context management', 'no ip domain-name eng.ansible.com', 'exit',
                    'vrf context management', 'ip domain-name example.net', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_domain_search(self):
        set_module_args(dict(domain_search=['example.net']))
        commands = ['vrf context management', 'no ip domain-list ansible.com', 'exit',
                    'vrf context management', 'no ip domain-list redhat.com', 'exit',
                    'no ip domain-list ansible.com', 'no ip domain-list redhat.com',
                    'ip domain-list example.net']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_domain_search_complex(self):
        domain_search = dict(name='example.net', vrf='management')
        set_module_args(dict(domain_search=[domain_search]))
        commands = ['vrf context management', 'no ip domain-list ansible.com', 'exit',
                    'vrf context management', 'no ip domain-list redhat.com', 'exit',
                    'no ip domain-list ansible.com', 'no ip domain-list redhat.com',
                    'vrf context management', 'ip domain-list example.net', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_name_servers(self):
        set_module_args(dict(name_servers=['1.2.3.4', '8.8.8.8']))
        commands = ['no ip name-server 172.26.1.1',
                    'vrf context management', 'no ip name-server 8.8.8.8', 'exit',
                    'vrf context management', 'no ip name-server 172.26.1.1', 'exit',
                    'ip name-server 1.2.3.4']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_name_servers_complex(self):
        name_servers = dict(server='1.2.3.4', vrf='management')
        set_module_args(dict(name_servers=[name_servers]))
        commands = ['no ip name-server 8.8.8.8', 'no ip name-server 172.26.1.1',
                    'vrf context management', 'no ip name-server 8.8.8.8', 'exit',
                    'vrf context management', 'no ip name-server 172.26.1.1', 'exit',
                    'vrf context management', 'ip name-server 1.2.3.4', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_system_mtu(self):
        set_module_args(dict(system_mtu=2000))
        commands = ['system jumbomtu 2000']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_system_state_absent(self):
        set_module_args(dict(state='absent'))
        commands = ['no hostname', 'no ip domain-name ansible.com',
                    'vrf context management', 'no ip domain-name eng.ansible.com', 'exit',
                    'no ip domain-list ansible.com', 'no ip domain-list redhat.com',
                    'vrf context management', 'no ip domain-list ansible.com', 'exit',
                    'vrf context management', 'no ip domain-list redhat.com', 'exit',
                    'no ip name-server 8.8.8.8', 'no ip name-server 172.26.1.1',
                    'vrf context management', 'no ip name-server 8.8.8.8', 'exit',
                    'vrf context management', 'no ip name-server 172.26.1.1', 'exit',
                    'no system jumbomtu']
        self.execute_module(changed=True, commands=commands)
