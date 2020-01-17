# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.eos import eos_lacp_interfaces
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosLacpInterfacesModule(TestEosModule):
    module = eos_lacp_interfaces

    def setUp(self):
        super(TestEosLacpInterfacesModule, self).setUp()

        self.mock_get_config = patch('ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch('ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start()

        self.mock_get_resource_connection_facts = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch('ansible.module_utils.network.eos.providers.providers.CliProvider.edit_config')
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.eos.facts.lacp_interfaces.lacp_interfaces.Lacp_interfacesFacts.get_device_data')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestEosLacpInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        def load_from_file(*args, **kwargs):
            return load_fixture('eos_lacp_interfaces_config.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_eos_lacp_interfaces_default(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                port_priority=45,
                rate="normal"
            )]
        ))
        commands = ['interface Ethernet1', 'lacp port-priority 45', 'lacp rate normal']
        self.execute_module(changed=True, commands=commands)

    def test_eos_lacp_interfaces_default_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet2",
                rate="fast"
            )]
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_lacp_interfaces_merged(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                port_priority=45,
                rate="normal"
            ), dict(
                name="Ethernet2",
                rate="normal"
            )], state="merged"
        ))
        commands = ['interface Ethernet1', 'lacp port-priority 45', 'lacp rate normal',
                    'interface Ethernet2', 'lacp rate normal']
        self.execute_module(changed=True, commands=commands)

    def test_eos_lacp_interfaces_merged_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet2",
                rate="fast"
            )], state="merged"
        ))
        self.execute_module(changed=False, commands=[])

    # Bug #64453
    # def test_eos_lacp_interfaces_replaced(self):
    #    set_module_args(dict(
    #        config=[dict(
    #            name="Ethernet1",
    #            port_priority=45,
    #            rate="normal"
    #        )], state="replaced"
    #    ))
    #    commands = ['interface Ethernet1', 'lacp port-priority 45', 'lacp rate normal']
    #    self.execute_module(changed=True, commands=commands)

    def test_eos_lacp_interfaces_replaced_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet2",
                rate="fast"
            )], state="replaced"
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_lacp_interfaces_overridden(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                port_priority=45,
                rate="normal"
            )], state="overridden"
        ))
        commands = ['interface Ethernet1', 'lacp port-priority 45', 'lacp rate normal',
                    'interface Ethernet2', 'no lacp port-priority', 'no lacp rate']
        self.execute_module(changed=True, commands=commands)

    def test_eos_lacp_interfaces_overridden_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                port_priority=30
            ), dict(
                name="Ethernet2",
                rate="fast"
            )], state="overridden"
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_lacp_interfaces_deleted(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet2",
            )], state="deleted"
        ))
        commands = ['interface Ethernet2', 'no lacp rate']
        self.execute_module(changed=True, commands=commands)
