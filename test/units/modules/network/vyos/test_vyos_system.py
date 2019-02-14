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
from ansible.modules.network.vyos import vyos_system
from units.modules.utils import set_module_args
from .vyos_module import TestVyosModule, load_fixture


class TestVyosSystemModule(TestVyosModule):

    module = vyos_system

    def setUp(self):
        super(TestVyosSystemModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.vyos.vyos_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.vyos.vyos_system.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestVyosSystemModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('vyos_config_config.cfg')

    def test_vyos_system_hostname(self):
        set_module_args(dict(host_name='foo'))
        commands = ["set system host-name 'foo'"]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_system_clear_hostname(self):
        set_module_args(dict(host_name='foo', state='absent'))
        commands = ["delete system host-name"]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_remove_single_name_server(self):
        set_module_args(dict(name_server=['8.8.4.4'], state='absent'))
        commands = ["delete system name-server '8.8.4.4'"]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_system_domain_name(self):
        set_module_args(dict(domain_name='example2.com'))
        commands = ["set system domain-name 'example2.com'"]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_system_clear_domain_name(self):
        set_module_args(dict(domain_name='example.com', state='absent'))
        commands = ['delete system domain-name']
        self.execute_module(changed=True, commands=commands)

    def test_vyos_system_domain_search(self):
        set_module_args(dict(domain_search=['foo.example.com', 'bar.example.com']))
        commands = ["set system domain-search domain 'foo.example.com'",
                    "set system domain-search domain 'bar.example.com'"]
        self.execute_module(changed=True, commands=commands)

    def test_vyos_system_clear_domain_search(self):
        set_module_args(dict(domain_search=[]))
        commands = ['delete system domain-search domain']
        self.execute_module(changed=True, commands=commands)

    def test_vyos_system_no_change(self):
        set_module_args(dict(host_name='router', domain_name='example.com', name_server=['8.8.8.8', '8.8.4.4']))
        result = self.execute_module()
        self.assertEqual([], result['commands'])

    def test_vyos_system_clear_all(self):
        set_module_args(dict(state='absent'))
        commands = ['delete system host-name',
                    'delete system domain-search domain',
                    'delete system domain-name',
                    'delete system name-server']
        self.execute_module(changed=True, commands=commands)
