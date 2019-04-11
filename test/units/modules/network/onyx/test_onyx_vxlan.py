#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_vxlan
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxVxlanModule(TestOnyxModule):

    module = onyx_vxlan
    arp_suppression = True

    def setUp(self):
        super(TestOnyxVxlanModule, self).setUp()
        self.mock_get_vxlan_config = patch.object(
            onyx_vxlan.OnyxVxlanModule, "_show_vxlan_config")
        self.get_vxlan_config = self.mock_get_vxlan_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_nve_detail = patch.object(
            onyx_vxlan.OnyxVxlanModule, "_show_nve_detail")
        self.get_nve_detail = self.mock_get_nve_detail.start()

    def tearDown(self):
        super(TestOnyxVxlanModule, self).tearDown()
        self.mock_get_vxlan_config.stop()
        self.mock_load_config.stop()
        self.mock_get_nve_detail.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        interfaces_nve_config_file = 'onyx_show_interfaces_nve.cfg'
        interfaces_nve_detail_config_file = 'onyx_show_interfaces_nve_detail.cfg'
        self.get_nve_detail.return_value = None
        interfaces_nve_detail_data = load_fixture(interfaces_nve_detail_config_file)
        interfaces_nv_data = load_fixture(interfaces_nve_config_file)
        self.get_nve_detail.return_value = interfaces_nve_detail_data
        if self.arp_suppression is False:
            interfaces_nve_detail_data[0]["10"][0]["Neigh Suppression"] = "Disable"
            interfaces_nve_detail_data[0]["6"][0]["Neigh Suppression"] = "Disable"
            self.get_nve_detail.return_value = interfaces_nve_detail_data
        self.get_vxlan_config.return_value = interfaces_nv_data

        self.load_config.return_value = None

    def test_configure_vxlan_no_change(self):
        set_module_args(dict(nve_id=1, loopback_id=1, bgp=True, mlag_tunnel_ip='192.10.10.1',
                             vni_vlan_list=[dict(vlan_id=10, vni_id=10010), dict(vlan_id=6, vni_id=10060)],
                             arp_suppression=True))
        self.execute_module(changed=False)

    def test_configure_vxlan_with_change(self):
        set_module_args(dict(nve_id=2, loopback_id=1, bgp=True, mlag_tunnel_ip='192.10.10.1',
                             vni_vlan_list=[dict(vlan_id=10, vni_id=10010), dict(vlan_id=6, vni_id=10060)],
                             arp_suppression=True))
        commands = [
            "no interface nve 1", "interface nve 2", "exit",
            "interface nve 2 vxlan source interface loopback 1 ",
            "interface nve 2 nve controller bgp", "interface nve 2 vxlan mlag-tunnel-ip 192.10.10.1",
            "interface nve 2 nve neigh-suppression", "interface nve 2 nve vni 10010 vlan 10",
            "interface vlan 10", "exit", "interface nve 2 nve vni 10060 vlan 6", "interface vlan 6", "exit"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_loopback_id_with_change(self):
        set_module_args(dict(nve_id=1, loopback_id=2, bgp=True, mlag_tunnel_ip='192.10.10.1',
                             vni_vlan_list=[dict(vlan_id=10, vni_id=10010), dict(vlan_id=6, vni_id=10060)],
                             arp_suppression=True))
        commands = ["interface nve 1 vxlan source interface loopback 2 "]
        self.execute_module(changed=True, commands=commands)

    def test_mlag_tunnel_ip_with_change(self):
        set_module_args(dict(nve_id=1, loopback_id=1, bgp=True, mlag_tunnel_ip='192.10.10.10',
                             vni_vlan_list=[dict(vlan_id=10, vni_id=10010), dict(vlan_id=6, vni_id=10060)],
                             arp_suppression=True))
        commands = ["interface nve 1 vxlan mlag-tunnel-ip 192.10.10.10"]
        self.execute_module(changed=True, commands=commands)

    def test_vni_vlan_list_with_change(self):
        set_module_args(dict(nve_id=1, loopback_id=1, bgp=True, mlag_tunnel_ip='192.10.10.1',
                             vni_vlan_list=[dict(vlan_id=11, vni_id=10011), dict(vlan_id=7, vni_id=10061)],
                             arp_suppression=False))
        commands = ["interface nve 1 nve vni 10011 vlan 11", "interface nve 1 nve vni 10061 vlan 7"]
        self.execute_module(changed=True, commands=commands)

    def test_arp_suppression_with_change(self):
        self.arp_suppression = False
        set_module_args(dict(nve_id=1, loopback_id=1, bgp=True, mlag_tunnel_ip='192.10.10.1',
                             vni_vlan_list=[dict(vlan_id=10, vni_id=10010), dict(vlan_id=6, vni_id=10060)],
                             arp_suppression=True))
        commands = ["interface vlan 10", "exit", "interface vlan 6", "exit"]
        self.execute_module(changed=True, commands=commands)
