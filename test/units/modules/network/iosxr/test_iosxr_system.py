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

from units.compat.mock import patch
from units.modules.utils import set_module_args
from .iosxr_module import TestIosxrModule, load_fixture
from ansible.modules.network.iosxr import iosxr_system


class TestIosxrSystemModule(TestIosxrModule):

    module = iosxr_system

    def setUp(self):
        super(TestIosxrSystemModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.iosxr.iosxr_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.iosxr.iosxr_system.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_is_cliconf = patch('ansible.modules.network.iosxr.iosxr_system.is_cliconf')
        self.is_cliconf = self.mock_is_cliconf.start()

    def tearDown(self):
        super(TestIosxrSystemModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('iosxr_system_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')
        self.is_cliconf.return_value = True

    def test_iosxr_system_hostname_changed(self):
        set_module_args(dict(hostname='foo'))
        commands = ['hostname foo', 'no domain lookup disable']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_domain_name(self):
        set_module_args(dict(domain_name='test.com'))
        commands = ['domain name test.com', 'no domain lookup disable']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_domain_search(self):
        set_module_args(dict(domain_search=['ansible.com', 'redhat.com']))
        commands = ['domain list ansible.com', 'no domain list cisco.com', 'no domain lookup disable']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_lookup_source(self):
        set_module_args(dict(lookup_source='Ethernet1'))
        commands = ['domain lookup source-interface Ethernet1', 'no domain lookup disable']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_lookup_enabled(self):
        set_module_args(dict(lookup_enabled=True))
        commands = ['no domain lookup disable']
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_name_servers(self):
        name_servers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
        set_module_args(dict(name_servers=name_servers))
        commands = ['domain name-server 1.1.1.1', 'no domain name-server 8.8.4.4', 'no domain lookup disable']
        self.execute_module(changed=True)

    def test_iosxr_system_state_absent(self):
        set_module_args(dict(state='absent'))
        commands = [
            'no hostname',
            'no domain name',
            'no domain lookup disable',
            'no domain lookup source-interface MgmtEth0/0/CPU0/0',
            'no domain list redhat.com',
            'no domain list cisco.com',
            'no domain name-server 8.8.8.8',
            'no domain name-server 8.8.4.4'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_iosxr_system_no_change(self):
        set_module_args(dict(hostname='iosxr01', domain_name='eng.ansible.com', lookup_enabled=False))
        self.execute_module()
