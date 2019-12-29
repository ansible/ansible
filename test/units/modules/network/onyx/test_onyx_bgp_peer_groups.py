#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_bgp_peer_groups
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxBgpPeerGroupsModule(TestOnyxModule):

    module = onyx_bgp_peer_groups

    def setUp(self):
        super(TestOnyxBgpPeerGroupsModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_bgp_peer_groups.OnyxBgpPeerGroupsModule, "_show_bgp_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxBgpPeerGroupsModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_bgp_peer_groups.cfg'
        data = load_fixture(config_file)
        self.get_config.return_value = data
        self.load_config.return_value = None

    def test_bgp_group_creation_no_change(self):
        set_module_args(dict(peer_groups=[dict(name='group1',
                                               router_bgp=1)]))
        self.execute_module(changed=False)

    def test_bgp_group_creation_with_change(self):
        set_module_args(dict(peer_groups=[dict(name='group2',
                                               router_bgp=1)]))
        commands = ['router bgp 1 neighbor group2 peer-group']
        self.execute_module(changed=True, commands=commands)

    def test_bgp_neighbor_assignment_no_change(self):
        set_module_args(dict(neighbors=[dict(group_name='group1',
                                             router_bgp=1,
                                             ip_address='1.1.1.1')]))
        self.execute_module(changed=False)

    def test_bgp_neighbor_assignment_with_change(self):
        set_module_args(dict(neighbors=[dict(group_name='group2',
                                             router_bgp=1,
                                             ip_address='1.1.1.0')]))
        commands = ['router bgp 1 neighbor 1.1.1.0 peer-group group2']
        self.execute_module(changed=True, commands=commands)

    def test_bgp_next_hop_peer_no_change(self):
        set_module_args(dict(peer_groups=[dict(name='group1',
                                               router_bgp=1,
                                               next_hop_peer_enabled=False)]))
        self.execute_module(changed=False)

    def test_bgp_next_hop_peer_with_change(self):
        set_module_args(dict(peer_groups=[dict(name='group1',
                                               router_bgp=1,
                                               next_hop_peer_enabled=True)]))
        commands = ['router bgp 1 neighbor group1 next-hop-peer']
        self.execute_module(changed=True, commands=commands)

    def test_bgp_listen_range_peer_no_change(self):
        set_module_args(dict(peer_groups=[dict(name='group1',
                                               router_bgp=1,
                                               listen_range_ip_prefix='1.1.2.3',
                                               remote_as='3',
                                               mask_length='24')]))
        self.execute_module(changed=False)

    def test_bgp_listen_range_peer_with_change(self):
        set_module_args(dict(peer_groups=[dict(name='group1',
                                               router_bgp=1,
                                               next_hop_peer_enabled=True)]))
        commands = ['router bgp 1 neighbor group1 next-hop-peer']
        self.execute_module(changed=True, commands=commands)

    def test_bgp_delete_group_with_change(self):
        set_module_args(dict(peer_groups=[dict(name='group1',
                                               router_bgp=1,
                                               state='absent')]))
        commands = ['no router bgp 1 neighbor group1 peer-group']
        self.execute_module(changed=True, commands=commands)

    def test_bgp_delete_neighbor_with_change(self):
        set_module_args(dict(neighbors=[dict(group_name='group1',
                                             router_bgp=1,
                                             ip_address='1.1.1.1',
                                             state='absent')]))
        commands = ['no router bgp 1 neighbor 1.1.1.1 peer-group group1']
        self.execute_module(changed=True, commands=commands)
