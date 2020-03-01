#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.modules.network.nxos import nxos_lldp_interfaces
from units.compat.mock import patch, MagicMock
from units.modules.utils import set_module_args
from .nxos_module import TestNxosModule, load_fixture


class TestNxosLldpInterfacesModule(TestNxosModule):

    module = nxos_lldp_interfaces

    def setUp(self):
        super(TestNxosLldpInterfacesModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.module_utils.network.common.network.Config.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.common.network.Config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_resource_connection_config = patch(
            'ansible.module_utils.network.common.cfg.base.get_resource_connection'
        )
        self.get_resource_connection_config = self.mock_get_resource_connection_config.start(
        )

        self.mock_get_resource_connection_facts = patch(
            'ansible.module_utils.network.common.facts.facts.get_resource_connection'
        )
        self.get_resource_connection_facts = self.mock_get_resource_connection_facts.start()

        self.mock_edit_config = patch(
            'ansible.module_utils.network.nxos.config.lldp_interfaces.lldp_interfaces.Lldp_interfaces.edit_config'
        )
        self.edit_config = self.mock_edit_config.start()

        self.mock_execute_show_command = patch(
            'ansible.module_utils.network.nxos.facts.lldp_interfaces.lldp_interfaces.Lldp_interfacesFacts.get_device_data'
        )
        self.execute_show_command = self.mock_execute_show_command.start()

    def tearDown(self):
        super(TestNxosLldpInterfacesModule, self).tearDown()
        self.mock_get_resource_connection_config.stop()
        self.mock_get_resource_connection_facts.stop()
        self.mock_edit_config.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_execute_show_command.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            output = '''interface Ethernet1/1
            lldp receive
            no lldp transmit
          interface Ethernet1/2
            no lldp receive
            lldp tlv-set vlan 12'''
            return output

        self.execute_show_command.side_effect = load_from_file

    def test_nxos_lldp_interfaces_merged(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/3",
                     receive=False,
                     tlv_set=dict(
                         vlan=123
                     )
                     )
            ], state="merged"))
        commands = ['interface Ethernet1/3',
                    'no lldp receive',
                    'lldp tlv-set vlan 123']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_lldp_interfaces_merged_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     receive=False,
                     tlv_set=dict(
                         vlan=12
                     )
                     ),
                dict(name="Ethernet1/1",
                          receive=True,
                          transmit=False)
            ], state="merged"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_lldp_interfaces_replaced(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     receive=True,
                     transmit=False,
                     tlv_set=dict(
                         management_address='192.0.2.123'
                     )
                     )
            ], state="replaced"))
        commands = ['interface Ethernet1/2',
                    'lldp receive',
                    'no lldp transmit',
                    'no lldp tlv-set vlan 12',
                    'lldp tlv-set management-address 192.0.2.123']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_lldp_interfaces_replaced_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     receive=False,
                     tlv_set=dict(
                         vlan=12
                     )
                     ),
                dict(name="Ethernet1/1",
                          receive=True,
                          transmit=False)
            ], state="replaced"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_lldp_interfaces_overridden(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/4",
                     receive=True,
                     transmit=False
                     )
            ], state="overridden"))
        commands = ['interface Ethernet1/4',
                    'lldp receive',
                    'no lldp transmit',
                    'interface Ethernet1/1',
                    'lldp receive',
                    'lldp transmit',
                    'interface Ethernet1/2',
                    'lldp receive',
                    'no lldp tlv-set vlan 12']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_lldp_interfaces_overridden_idempotent(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     receive=False,
                     tlv_set=dict(
                         vlan=12
                     )
                     ),
                dict(name="Ethernet1/1",
                          receive=True,
                          transmit=False)
            ], state="overridden"))
        self.execute_module(changed=False, commands=[])

    def test_nxos_lldp_interfaces_deleted_intf(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2")
            ], state="deleted"))
        commands = ['interface Ethernet1/2',
                    'lldp receive',
                    'no lldp tlv-set vlan 12']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_lldp_interfaces_deleted_all(self):
        set_module_args(
            dict(state="deleted"))
        commands = ['interface Ethernet1/2',
                    'lldp receive',
                    'no lldp tlv-set vlan 12',
                    'interface Ethernet1/1',
                    'lldp receive',
                    'lldp transmit']
        self.execute_module(changed=True, commands=commands)

    def test_nxos_lldp_interfaces_rendered(self):
        set_module_args(
            dict(config=[
                dict(name="Ethernet1/2",
                     receive=False,
                     tlv_set=dict(
                         vlan=12
                     )
                     ),
                dict(name="Ethernet1/1",
                     receive=True,
                     transmit=False)
            ], state="rendered"))
        commands = ['interface Ethernet1/1',
                    'lldp receive',
                    'no lldp transmit',
                    'interface Ethernet1/2',
                    'no lldp receive',
                    'lldp tlv-set vlan 12']
        result = self.execute_module(changed=False)
        self.assertEqual(sorted(result['rendered']), sorted(
            commands), result['rendered'])

    def test_nxos_lldp_interfaces_parsed(self):
        set_module_args(dict(running_config='''interface Ethernet1/1
            lldp receive
            no lldp transmit
          interface Ethernet1/2
            no lldp receive
            lldp tlv-set vlan 12''', state="parsed"))
        result = self.execute_module(changed=False)
        compare_list = [{'name': 'Ethernet1/1', 'receive': True, 'transmit': False},
                        {'name': 'Ethernet1/2', 'receive': False, 'tlv_set': {
                            'vlan': 12
                        }}]
        self.assertEqual(result['parsed'],
                         compare_list, result['parsed'])

    def test_nxos_lldp_interfaces_gathered(self):
        set_module_args(dict(state="gathered"))
        result = self.execute_module(changed=False)
        compare_list = [{'name': 'Ethernet1/1', 'receive': True, 'transmit': False},
                        {'name': 'Ethernet1/2', 'receive': False, 'tlv_set': {
                            'vlan': 12
                        }}]
        self.assertEqual(result['gathered'],
                         compare_list, result['gathered'])
