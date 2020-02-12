#
# (c) 2020 Allied Telesis
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

from units.compat.mock import patch
from ansible.modules.network.awplus import awplus_system
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusSystemModule(TestAwplusModule):

    module = awplus_system

    def setUp(self):
        super(TestAwplusSystemModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_system.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestAwplusSystemModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('awplus_system_config.cfg')
        self.load_config.return_value = None

    def test_awplus_system_hostname_changed(self):
        set_module_args(dict(hostname='foo'))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_system_domain_name(self):
        set_module_args(dict(domain_name='test.com'))
        commands = ['ip domain-name test.com']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_system_domain_list(self):
        set_module_args(dict(domain_list=['ansible.com', 'redhat.com']))
        commands = ['no ip domain-list example.net',
                    'ip domain-list ansible.com',
                    'ip domain-list redhat.com']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_system_domain_list_complex(self):
        set_module_args(dict(domain_list=['ansible.com']))
        commands = ['no ip domain-list example.net',
                    'ip domain-list ansible.com']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_system_name_servers(self):
        name_servers = ['8.8.8.8', '8.8.4.4']
        set_module_args(dict(name_servers=name_servers))
        commands = ['no ip name-server vrf management 8.8.8.8 ',
                    'ip name-server 8.8.4.4']
        self.execute_module(changed=True, commands=commands, sort=False)

    def rest_awplus_system_name_servers_complex(self):
        name_servers = dict(server='8.8.8.8', vrf='test')
        set_module_args(dict(name_servers=name_servers))
        commands = ['no name-server 8.8.8.8',
                    'no name-server vrf management 8.8.8.8',
                    'ip name-server vrf test 8.8.8.8']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_system_state_absent(self):
        set_module_args(dict(state='absent'))
        commands = ['no hostname',
                    'no ip domain-name example.com',
                    'no ip domain-list example.net',
                    'no ip name-server 8.8.8.8',
                    'no ip name-server vrf management 8.8.8.8']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_system_no_change(self):
        set_module_args(dict(hostname='awplus'))
        self.execute_module(commands=[])

    def test_awplus_system_missing_vrf(self):
        name_servers = dict(server='8.8.8.8')
        set_module_args(dict(name_servers=name_servers))
        self.execute_module(failed=True)
