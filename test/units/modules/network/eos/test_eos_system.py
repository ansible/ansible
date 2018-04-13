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
from ansible.modules.network.eos import eos_system
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosSystemModule(TestEosModule):

    module = eos_system

    def setUp(self):
        super(TestEosSystemModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.eos.eos_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_system.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestEosSystemModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('eos_system_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

    def test_eos_system_hostname_changed(self):
        set_module_args(dict(hostname='foo'))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_eos_system_domain_name(self):
        set_module_args(dict(domain_name='test.com'))
        commands = ['ip domain-name test.com']
        self.execute_module(changed=True, commands=commands)

    def test_eos_system_domain_list(self):
        set_module_args(dict(domain_list=['ansible.com', 'redhat.com']))
        commands = ['no ip domain-list ops.ansible.com',
                    'ip domain-list redhat.com']
        self.execute_module(changed=True, commands=commands)

    def test_eos_system_lookup_source(self):
        set_module_args(dict(lookup_source=['Ethernet1']))
        commands = ['no ip domain lookup source-interface Management1',
                    'ip domain lookup source-interface Ethernet1']
        self.execute_module(changed=True, commands=commands)

    def test_eos_system_lookup_source_complex(self):
        lookup_source = [{'interface': 'Management1', 'vrf': 'mgmt'},
                         {'interface': 'Ethernet1'}]
        set_module_args(dict(lookup_source=lookup_source))
        commands = ['no ip domain lookup source-interface Management1',
                    'ip domain lookup vrf mgmt source-interface Management1',
                    'ip domain lookup source-interface Ethernet1']
        self.execute_module(changed=True, commands=commands)

    # def test_eos_system_name_servers(self):
    #     name_servers = ['8.8.8.8', '8.8.4.4']
    #     set_module_args(dict(name_servers=name_servers))
    #     commands = ['ip name-server 8.8.4.4',
    #                 'no ip name-server vrf mgmt 8.8.4.4']
    #     self.execute_module(changed=True, commands=commands)

    # def rest_eos_system_name_servers_complex(self):
    #     name_servers = dict(server='8.8.8.8', vrf='test')
    #     set_module_args(dict(name_servers=name_servers))
    #     commands = ['ip name-server vrf test 8.8.8.8',
    #                 'no ip name-server vrf default 8.8.8.8',
    #                 'no ip name-server vrf mgmt 8.8.4.4']
    #     self.execute_module(changed=True, commands=commands)

    def test_eos_system_state_absent(self):
        set_module_args(dict(state='absent'))
        commands = ['no ip domain-name', 'no hostname']
        self.execute_module(changed=True, commands=commands)

    def test_eos_system_no_change(self):
        set_module_args(dict(hostname='switch01', domain_name='eng.ansible.com'))
        commands = []
        self.execute_module(commands=commands)

    def test_eos_system_missing_vrf(self):
        name_servers = dict(server='8.8.8.8', vrf='missing')
        set_module_args(dict(name_servers=name_servers))
        result = self.execute_module(failed=True)
