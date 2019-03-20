#
# (c) 2016 Red Hat Inc.
# Copyright (C) 2017 Lenovo.
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
from ansible.modules.network.cnos import cnos_system
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosSystemModule(TestCnosModule):

    module = cnos_system

    def setUp(self):
        super(TestCnosSystemModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.cnos.cnos_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.cnos.cnos_system.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestCnosSystemModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('cnos_system_config.cfg')
        self.load_config.return_value = None

    def test_cnos_system_hostname_changed(self):
        set_module_args(dict(hostname='foo'))
        commands = ['hostname foo']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_system_domain_lookup(self):
        set_module_args(dict(lookup_enabled=False))
        commands = ['no ip domain-lookup']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_system_missing_vrf(self):
        domain_name = dict(name='example.com', vrf='example')
        set_module_args(dict(domain_name=domain_name))
        self.execute_module(failed=True)

    def test_cnos_system_domain_name(self):
        set_module_args(dict(domain_name=['example.net']))
        commands = ['ip domain-name example.net vrf default']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_system_domain_name_complex(self):
        domain_name = dict(name='example.net', vrf='management')
        set_module_args(dict(domain_name=[domain_name]))
        commands = ['ip domain-name example.net vrf management']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_system_domain_search(self):
        set_module_args(dict(domain_search=['example.net']))
        commands = ['ip domain-list example.net vrf default']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_system_domain_search_complex(self):
        domain_search = dict(name='example.net', vrf='management')
        set_module_args(dict(domain_search=[domain_search]))
        commands = ['ip domain-list example.net vrf management']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_system_name_servers(self):
        set_module_args(dict(name_servers=['1.2.3.4', '8.8.8.8']))
        commands = ['ip name-server 1.2.3.4 vrf default', 'ip name-server 8.8.8.8 vrf default']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_system_name_servers_complex(self):
        name_servers = dict(server='1.2.3.4', vrf='management')
        set_module_args(dict(name_servers=[name_servers]))
        commands = ['ip name-server 1.2.3.4 vrf management']
        self.execute_module(changed=True, commands=commands)

    def test_cnos_system_state_absent(self):
        set_module_args(dict(state='absent'))
        commands = ['no hostname']
        self.execute_module(changed=True, commands=commands)
