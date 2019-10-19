# (c) 2019 Red Hat Inc.
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
from ansible.modules.network.cloudengine import ce_lldp_interface
from units.modules.network.cloudengine.ce_module import TestCloudEngineModule, load_fixture
from units.modules.utils import set_module_args


class TestCloudEngineLacpModule(TestCloudEngineModule):
    module = ce_lldp_interface

    def setUp(self):
        super(TestCloudEngineLacpModule, self).setUp()

        # self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_lldp.get_nc_config')
        self.mock_get_resource_connection = patch('ansible.module_utils.network.common.cfg.base.get_resource_connection')
        self.get_resource_connection = patch('ansible.module_utils.network.common.facts.facts.get_resource_connection')
        self.mock_get_config = patch('ansible.module_utils.network.cloudengine.facts.lldp_interface.lldp_interface.get_nc_config')
        self.get_nc_config = self.mock_get_config.start()
        self.mock_get_resource_connection.start()
        self.get_resource_connection.start()

        self.mock_get_resource_connection = [None]*100
        self.get_resource_connection = [None]*100

        self.mock_set_config = patch('ansible.module_utils.network.cloudengine.config.lldp_interface.lldp_interface.set_nc_config')
        self.set_nc_config = self.mock_set_config.start()
        self.set_nc_config.return_value = None
        self.xml_absent = load_fixture('ce_lldp_interface', 'lldp_interface_existing.txt')
        self.xml_present = load_fixture('ce_lldp_interface', 'lldp_interface_changed.txt')
        self.result_ok = load_fixture('ce_lldp_interface', 'result_ok.txt')

    def tearDown(self):
        super(TestCloudEngineLacpModule, self).tearDown()
        self.mock_set_config.stop()
        self.mock_get_config.stop()

    def test_lldp_present(self):
        update = ['lldp transmit fast-mode interval 8',
                  'lldp admin-status txrx',
                  'undo lldp tlv-disable basic-tlv management-address',
                  'undo lldp tlv-disable basic-tlv port-description',
                  'undo lldp tlv-disable basic-tlv system-capability',
                  'undo lldp tlv-disable basic-tlv system-description',
                  'undo lldp tlv-disable basic-tlv system-name',
                  'undo lldp tlv-disable dot1-tlv port-vlan-id',
                  'undo lldp tlv-disable dot1-tlv protocol-vlan-id 112',
                  'undo lldp tlv-disable dot1-tlv vlan-name 32',
                  'undo lldp tlv-disable dot3-tlv link-aggregation',
                  'undo lldp tlv-disable dot3-tlv mac-physic',
                  'undo lldp tlv-disable dot3-tlv max-frame-size',
                  'undo lldp tlv-disable dot3-tlv eee']
        self.get_nc_config.side_effect = (self.xml_absent, self.xml_present)
        self.set_nc_config.side_effect = [self.result_ok]*11
        config = dict(
            ifname='10GE1/0/1',
            admin_status='rxonly',
            msg_interval=8,
            basic_tlv=dict(management_addr=True,
                           port_desc=True,
                           system_capability=True,
                           system_description=True,
                           system_name=True),
            dot1_tlv=dict(port_vlan_enable=True,
                          prot_vlan_enable=True,
                          prot_vlan_id=1,
                          vlan_name_enable=True,
                          vlan_name=1),
            dot3_tlv=dict(link_aggregation=True,
                          mac_physic=True,
                          max_frame_size=True,
                          eee=True)
          )
        set_module_args(dict(config=config))
        result = self.execute_module(changed=True)
        self.assertEquals(sorted(result['commands']), sorted(update))

    def repeat_config(self):
        update = ['lldp transmit fast-mode interval 8',
                  'lldp admin-status txrx',
                  'undo lldp tlv-disable basic-tlv management-address',
                  'undo lldp tlv-disable basic-tlv port-description',
                  'undo lldp tlv-disable basic-tlv system-capability',
                  'undo lldp tlv-disable basic-tlv system-description',
                  'undo lldp tlv-disable basic-tlv system-name',
                  'undo lldp tlv-disable dot1-tlv port-vlan-id',
                  'undo lldp tlv-disable dot1-tlv protocol-vlan-id 112',
                  'undo lldp tlv-disable dot1-tlv vlan-name 32',
                  'undo lldp tlv-disable dot3-tlv link-aggregation',
                  'undo lldp tlv-disable dot3-tlv mac-physic',
                  'undo lldp tlv-disable dot3-tlv max-frame-size',
                  'undo lldp tlv-disable dot3-tlv eee']
        self.get_nc_config.side_effect = (self.xml_present, self.xml_present)
        self.set_nc_config.side_effect = [self.result_ok]*11
        config = dict(
            ifname='10GE1/0/1',
            admin_status='rxonly',
            msg_interval=8,
            basic_tlv=dict(management_addr=True,
                           port_desc=True,
                           system_capability=True,
                           system_description=True,
                           system_name=True),
            dot1_tlv=dict(port_vlan_enable=True,
                          prot_vlan_enable=True,
                          prot_vlan_id=1,
                          vlan_name_enable=True,
                          vlan_name=1),
            dot3_tlv=dict(link_aggregation=True,
                          mac_physic=True,
                          max_frame_size=True,
                          eee=True)
          )
        set_module_args(dict(config=config))
        result = self.execute_module(changed=True)
        self.assertEquals(sorted(result['commands']), sorted(update))
