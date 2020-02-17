#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.eos import eos_interfaces
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosInterfacesModule(TestEosModule):
    module = eos_interfaces

    def setUp(self):
        super(TestEosInterfacesModule, self).setUp()

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

        self.mock_execute_show_command = patch('ansible.module_utils.network.eos.facts.interfaces.interfaces.InterfacesFacts.get_device_data')
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestEosInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        def load_from_file(*args, **kwargs):
            return load_fixture('eos_interfaces_config.cfg')
        self.execute_show_command.side_effect = load_from_file

    def test_eos_interfaces_merged(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet3",
                description="Ethernet_3"
            )], state="merged"
        ))
        commands = ['interface Ethernet3', 'description Ethernet_3']
        self.execute_module(changed=True, commands=commands)

    def test_eos_interfaces_merged_idempotent(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                description="Interface 1"
            )], state="merged"
        ))
        self.execute_module(changed=False, commands=[])

    def test_eos_interfaces_replaced(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet3",
                description="Ethernet_3",
                mtu=1000
            )], state="replaced"
        ))
        commands = ['interface Ethernet3', 'description Ethernet_3', 'mtu 1000']
        self.execute_module(changed=True, commands=commands)

    # Bug : 63805
    # def test_eos_interfaces_replaced_idempotent(self):
    #    set_module_args(dict(
    #        config=[dict(
    #            name="Ethernet1",
    #            description="Interface 1"
    #        )], state="replaced"
    #    ))
    #    self.execute_module(changed=False, commands=[])

    def test_eos_interfaces_delete(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
            )], state="deleted"
        ))
        commands = ['interface Ethernet1', 'no description', 'no shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_eos_interfaces_speed_forced(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                description="Interface_1",
                speed="forced 40g",
                duplex="full"
            )], state="replaced"
        ))
        commands = ['interface Ethernet1', 'description Interface_1', 'speed forced 40gfull', 'no shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_eos_interfaces_speed_full(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                description="Interface_1",
                speed="1000g",
                duplex="full"
            )], state="replaced"
        ))
        commands = ['interface Ethernet1', 'description Interface_1', 'speed 1000gfull', 'no shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_eos_interfaces_speed_auto(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                description="Interface_1",
                speed="auto",
                duplex="full"
            )], state="replaced"
        ))
        commands = ['interface Ethernet1', 'description Interface_1', 'speed auto', 'no shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_eos_interfaces_speed_half(self):
        set_module_args(dict(
            config=[dict(
                name="Ethernet1",
                description="Interface_1",
                speed="1000g",
                duplex="half"
            )], state="replaced"
        ))
        commands = ['interface Ethernet1', 'description Interface_1', 'speed 1000ghalf', 'no shutdown']
        self.execute_module(changed=True, commands=commands)

    # Bug # 63760
    # def test_eos_interfaces_overridden(self):
    #    set_module_args(dict(
    #        config=[dict(
    #            name="Ethernet3",
    #            description="Ethernet_3",
    #            mtu=1000
    #        ),
    #        dict(
    #        name="Ethernet1",
    #        description="Ethernet 1"
    #        )], state="overridden"
    #    ))
    #    commands = ['interface Ethernet3', 'description Ethernet_3', 'mtu 1000', 'interface Ethernet1',
    #                  'description Ethernet 1', 'interface Management1', 'no description', 'no ip address']
    #    self.execute_module(changed=True, commands=commands)

    # def test_eos_interfaces_overridden_idempotent(self):
    #    set_module_args(dict(
    #        config=[dict(
    #            name="Ethernet1",
    #            description="Interface 1"
    #        ),
    #        dict(
    #        name="Ethernet2",
    #        ),
    #        dict(
    #        name="Management 1",
    #        description="Management interface"
    #        )], state="overridden"
    #    ))
    #    self.execute_module(changed=False, commands=[])
