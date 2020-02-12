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
from ansible.modules.network.awplus import awplus_lag_interfaces
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusLagInterfacesModule(TestAwplusModule):

    module = awplus_lag_interfaces

    def setUp(self):
        super(TestAwplusLagInterfacesModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch(
            'ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch(
            'ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch(
            'ansible.module_utils.network.awplus.providers.providers.CliProvider.edit_config')
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.awplus.facts.lag_interfaces.lag_interfaces.Lag_interfacesFacts.get_device_data')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestAwplusLagInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        def load_from_file(*args, **kwargs):
            return load_fixture('awplus_lag_interfaces_config.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_awplus_lag_interfaces_default(self):
        set_module_args(dict(
            config=[dict(
                name='2',
                members=[dict(member='port1.0.4', mode='passive')]
            )]
        ))
        commands = ['interface port1.0.4', 'channel-group 2 mode passive']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_lag_interfaces_default_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name='1',
                members=[dict(member='port1.0.2', mode='active')]
            )]
        ))
        self.execute_module(changed=False, commands=[])

    def test_awplus_lag_interfaces_merged(self):
        set_module_args(dict(
            config=[dict(
                name='3',
                members=[dict(member='port1.0.4', mode='active')]
            )], state="merged"
        ))
        commands = ['interface port1.0.4', 'channel-group 3 mode active']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_lag_interfaces_merged_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="1",
                members=[dict(member='port1.0.2', mode='active')]
            )], state="merged"
        ))
        self.execute_module(changed=False, commands=[])

    def test_awplus_lag_interfaces_replaced(self):
        set_module_args(dict(
            config=[dict(
                name='4',
                members=[dict(member='port1.0.4', mode='active')]
            )], state="replaced"
        ))
        commands = ['interface port1.0.4', 'channel-group 4 mode active']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_lag_interfaces_replaced_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="1",
                members=[dict(member='port1.0.2', mode='active')]
            )], state="replaced"
        ))
        self.execute_module(changed=False, commands=[])

    def test_awplus_lag_interfaces_overridden(self):
        set_module_args(dict(
            config=[dict(
                name="3",
                members=[dict(member='port1.0.4', mode='passive')]
            )], state="overridden"
        ))
        commands = ['interface port1.0.2', 'no channel-group',
                    'interface port1.0.4', 'channel-group 3 mode passive']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_lag_interfaces_overridden_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="1",
                members=[dict(member='port1.0.2', mode='active')]
            )], state="overridden"
        ))
        self.execute_module(changed=False, commands=[])

    def test_awplus_lag_interfaces_deleted(self):
        set_module_args(dict(
            config=[dict(
                name="1"
            )], state="deleted"
        ))
        commands = ['interface port1.0.2', 'no channel-group']
        self.execute_module(changed=True, commands=commands)
