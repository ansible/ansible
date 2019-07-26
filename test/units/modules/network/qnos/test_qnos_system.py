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

from units.compat.mock import patch, MagicMock
from ansible.modules.network.qnos import qnos_system
from ansible.plugins.cliconf.qnos import Cliconf
from units.modules.utils import set_module_args
from .qnos_module import TestQnosModule, load_fixture


class TestQnosSystemModule(TestQnosModule):

    module = qnos_system

    def setUp(self):
        super(TestQnosSystemModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.qnos.qnos_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.qnos.qnos_system.load_config')
        self.load_config = self.mock_load_config.start()

        self.cliconf_obj = Cliconf(MagicMock())
        self.running_config = load_fixture('qnos_system_config.cfg')

    def tearDown(self):
        super(TestQnosSystemModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('qnos_system_config.cfg')
        self.load_config.return_value = None

    def test_qnos_system_hostname_changed(self):
        set_module_args(dict(hostname='foo'))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_qnos_system_domain_name(self):
        set_module_args(dict(domain_name=['test.com']))

        commands = ['ip domain-name test.com',
                    'no ip domain-name eng.example.net',
                    'no ip domain-name vrf management eng.example.net']
        self.execute_module(changed=True, commands=commands)

    def test_qnos_system_domain_name_complex(self):
        set_module_args(dict(domain_name=[{'name': 'test.com', 'vrf': 'test'},
                                          {'name': 'eng.example.net'}]))
        commands = ['ip domain-name vrf test test.com',
                    'no ip domain-name vrf management eng.example.net']
        self.execute_module(changed=True, commands=commands)

    def test_qnos_system_domain_search(self):
        set_module_args(dict(domain_search=['ansible.com', 'redhat.com']))

        commands = ['no ip domain-list vrf management example.net',
                    'no ip domain-list example.net',
                    'no ip domain-list example.com',
                    'ip domain-list ansible.com',
                    'ip domain-list redhat.com']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_qnos_system_domain_search_complex(self):
        set_module_args(dict(domain_search=[{'name': 'ansible.com', 'vrf': 'test'}]))
        commands = ['no ip domain-list vrf management example.net',
                    'no ip domain-list example.net',
                    'no ip domain-list example.com',
                    'ip domain-list vrf test ansible.com']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_qnos_system_name_servers(self):
        name_servers = ['8.8.8.8', '8.8.4.4']
        set_module_args(dict(name_servers=name_servers))
        commands = ['no ip name-server vrf management 8.8.8.8',
                    'ip name-server 8.8.4.4']
        self.execute_module(changed=True, commands=commands, sort=False)

    def rest_qnos_system_name_servers_complex(self):
        name_servers = dict(server='8.8.8.8', vrf='test')
        set_module_args(dict(name_servers=name_servers))
        commands = ['no name-server 8.8.8.8',
                    'no name-server vrf management 8.8.8.8',
                    'ip name-server vrf test 8.8.8.8']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_qnos_system_state_absent(self):
        set_module_args(dict(state='absent'))
        commands = ['no hostname',
                    'ip domain-lookup',
                    'no ip domain-list vrf management', 'no ip domain-list',
                    'no ip domain-name vrf management', 'no ip domain-name',
                    'no ip name-server vrf management', 'no ip name-server']
        self.execute_module(changed=True, commands=commands)

    def test_qnos_system_no_change(self):
        set_module_args(dict(hostname='qnos01'))
        self.execute_module(commands=[])

    def test_qnos_system_missing_vrf(self):
        name_servers = dict(server='8.8.8.8', vrf='missing')
        set_module_args(dict(name_servers=name_servers))
        self.execute_module(failed=True)
