#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_igmp_vlan
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxIgmpVlan(TestOnyxModule):

    module = onyx_igmp_vlan
    enabled = False
    mrouter_state = False
    querier_state = False
    static_groups_enabled = False

    def setUp(self):
        self.enabled = False
        super(TestOnyxIgmpVlan, self).setUp()
        self.mock_get_igmp_config = patch.object(
            onyx_igmp_vlan.OnyxIgmpVlanModule, "_show_igmp_vlan")
        self.get_igmp_config = self.mock_get_igmp_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_igmp_guerier_config = patch.object(
            onyx_igmp_vlan.OnyxIgmpVlanModule, "_show_igmp_querier_config")
        self.get_igmp_guerier_config = self.mock_get_igmp_guerier_config.start()

        self.mock_get_igmp_static_groups_config = patch.object(
            onyx_igmp_vlan.OnyxIgmpVlanModule, "_show_igmp_snooping_groups_config")
        self.get_igmp_static_groups_config = self.mock_get_igmp_static_groups_config.start()

    def tearDown(self):
        super(TestOnyxIgmpVlan, self).tearDown()
        self.mock_get_igmp_config.stop()
        self.mock_load_config.stop()
        self.mock_get_igmp_guerier_config.stop()
        self.mock_get_igmp_static_groups_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        igmp_vlan_config_file = 'onyx_show_ip_igmp_snooping.cfg'
        igmp_querier_config_file = 'onyx_show_ip_igmp_snooping_querier.cfg'
        igmp_static_groups_file = 'onyx_show_ip_igmp_snooping_groups.cfg'
        igmp_vlan_data = load_fixture(igmp_vlan_config_file)
        igmp_querier_data = load_fixture(igmp_querier_config_file)
        igmp_static_groups_data = None
        if self.enabled:
            igmp_vlan_data[0]['message 1'] = 'IGMP snooping is enabled'

        if self.querier_state:
            igmp_vlan_data[0]['message 3'] = 'Snooping switch is acting as Querier'

        if self.mrouter_state:
            igmp_vlan_data[0]['mrouter static port list'] = 'Eth1/1'

        if self.static_groups_enabled:
            igmp_static_groups_data = load_fixture(igmp_static_groups_file)

        self.get_igmp_config.return_value = igmp_vlan_data
        self.get_igmp_guerier_config = igmp_querier_data
        self.get_igmp_static_groups_config = igmp_static_groups_data
        self.load_config.return_value = None

    def test_igmp_disabled_no_change(self):
        set_module_args(dict(state='disabled', vlan_id=10))
        self.execute_module(changed=False)

    def test_igmp_disabled_with_change(self):
        self.enabled = True
        set_module_args(dict(state='disabled', vlan_id=10))
        commands = ['vlan 10 no ip igmp snooping']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_enabled_no_change(self):
        self.enabled = True
        set_module_args(dict(state='enabled', vlan_id=10))
        self.execute_module(changed=False)

    def test_igmp_enabled_with_change(self):
        set_module_args(dict(state='enabled', vlan_id=10))
        commands = ['vlan 10 ip igmp snooping']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_mrouter_disabled_no_change(self):
        self.enabled = True
        set_module_args(dict(vlan_id=10, mrouter=dict(state='disabled', name='Eth1/1')))
        self.execute_module(changed=False)

    def test_igmp_mrouter_disabled_with_change(self):
        self.enabled = True
        self.mrouter_state = True
        set_module_args(dict(vlan_id=10, mrouter=dict(state='disabled', name='Eth1/1')))
        commands = ['vlan 10 no ip igmp snooping mrouter interface ethernet 1/1']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_mrouter_enabled_no_change(self):
        self.enabled = True
        self.mrouter_state = True
        set_module_args(dict(vlan_id=10, mrouter=dict(state='enabled', name='Eth1/1')))
        self.execute_module(changed=False)

    def test_igmp_mrouter_enabled_with_change(self):
        self.enabled = True
        set_module_args(dict(vlan_id=10, mrouter=dict(state='enabled', name='Eth1/1')))
        commands = ['vlan 10 ip igmp snooping mrouter interface ethernet 1/1']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_mrouter_enabled_withinterface_change(self):
        self.enabled = True
        self.mrouter_state = True
        set_module_args(dict(vlan_id=10, mrouter=dict(state='enabled', name='Eth1/2')))
        commands = ['vlan 10 ip igmp snooping mrouter interface ethernet 1/2']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_querier_disabled_no_change(self):
        self.enabled = True
        set_module_args(dict(vlan_id=10, querier=dict(state='disabled')))
        self.execute_module(changed=False)

    def test_igmp_querier_disabled_with_change(self):
        self.enabled = True
        self.querier_state = True
        set_module_args(dict(vlan_id=10, querier=dict(state='disabled')))
        commands = ['vlan 10 no ip igmp snooping querier']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_querier_enabled_no_change(self):
        self.enabled = True
        self.querier_state = True
        set_module_args(dict(vlan_id=10, querier=dict(state='enabled')))
        self.execute_module(changed=False)

    def test_igmp_querier_enabled_with_change(self):
        self.enabled = True
        set_module_args(dict(vlan_id=10, querier=dict(state='enabled')))
        commands = ['vlan 10 ip igmp snooping querier']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_querier_attr_no_change(self):
        self.enabled = True
        self.querier_state = True
        set_module_args(dict(vlan_id=10, querier=dict(state='enabled', interval=125, address='-')))
        self.execute_module(changed=True)

    def test_igmp_querier_attr_with_change(self):
        self.enabled = True
        self.querier_state = True
        set_module_args(dict(vlan_id=10, querier=dict(state='enabled', interval=127, address='10.10.10.1')))
        commands = ['vlan 10 ip igmp snooping querier query-interval 127',
                    'vlan 10 ip igmp snooping querier address 10.10.10.1']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_version_no_change(self):
        self.enabled = True
        set_module_args(dict(vlan_id=10, version='V3'))
        self.execute_module(changed=False)

    def test_igmp_version_with_change(self):
        self.enabled = True
        set_module_args(dict(vlan_id=10, version='V2'))
        commands = ['vlan 10 ip igmp snooping version 2']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_static_groups_multicast_ip_address_not_configured(self):
        self.enabled = True
        set_module_args(dict(vlan_id=10, static_groups=[dict(multicast_ip_address='224.5.5.2', name='Eth1/1',
                                                             sources=["1.1.1.2", "1.1.1.3"])]))
        commands = ['vlan 10 ip igmp snooping static-group 224.5.5.2 interface ethernet 1/1',
                    'vlan 10 ip igmp snooping static-group 224.5.5.2 interface ethernet 1/1 source 1.1.1.2',
                    'vlan 10 ip igmp snooping static-group 224.5.5.2 interface ethernet 1/1 source 1.1.1.3']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_static_groups_multicast_ip_address_configured_with_change(self):
        self.enabled = True
        self.static_groups_enabled = True
        set_module_args(dict(vlan_id=10, static_groups=[dict(multicast_ip_address='224.5.5.1', name='Eth1/3',
                                                             sources=["1.1.1.1", "1.1.1.2"])]))
        commands = ['vlan 10 ip igmp snooping static-group 224.5.5.1 interface ethernet 1/3',
                    'vlan 10 ip igmp snooping static-group 224.5.5.1 interface ethernet 1/3 source 1.1.1.1',
                    'vlan 10 ip igmp snooping static-group 224.5.5.1 interface ethernet 1/3 source 1.1.1.2']
        self.execute_module(changed=True, commands=commands)
