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

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_igmp_interface
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxIgmpInterfaceModule(TestOnyxModule):

    module = onyx_igmp_interface

    def setUp(self):
        super(TestOnyxIgmpInterfaceModule, self).setUp()

        self.mock_get_config = patch.object(onyx_igmp_interface.OnyxIgmpInterfaceModule, "_show_igmp_interfaces")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxIgmpInterfaceModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_igmp_interfaces.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_igmp_interface_enabled_no_change(self):
        set_module_args(dict(state='enabled', name='Eth1/3'))
        self.execute_module(changed=False)

    def test_igmp_interface_enabled_change(self):
        set_module_args(dict(state='enabled', name='Eth1/1'))
        commands = ['interface ethernet 1/1 ip igmp snooping fast-leave']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_interface_disabled_no_change(self):
        set_module_args(dict(state='disabled', name='Eth1/1'))
        self.execute_module(changed=False)

    def test_igmp_interface_disabled_change(self):
        set_module_args(dict(state='disabled', name='Eth1/3'))
        commands = ['interface ethernet 1/3 no ip igmp snooping fast-leave']
        self.execute_module(changed=True, commands=commands)
