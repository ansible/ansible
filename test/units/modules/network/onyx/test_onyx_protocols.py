#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_protocol
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxProtocolModule(TestOnyxModule):

    module = onyx_protocol

    def setUp(self):
        super(TestOnyxProtocolModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_protocol.OnyxProtocolModule,
            "_get_protocols")
        self.get_config = self.mock_get_config.start()

        self.mock_get_ip_config = patch.object(
            onyx_protocol.OnyxProtocolModule,
            "_get_ip_routing")
        self.get_ip_config = self.mock_get_ip_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxProtocolModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_protocols_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None
        self.get_ip_config.return_value = "IP routing: enabled"

    def test_mlag_enable(self):
        set_module_args(dict(mlag='enabled'))
        commands = ['protocol mlag']
        self.execute_module(changed=True, commands=commands)

    def test_mlag_disable(self):
        set_module_args(dict(mlag='disabled'))
        self.execute_module(changed=False)

    def test_magp_enable(self):
        set_module_args(dict(magp='enabled'))
        commands = ['protocol magp']
        self.execute_module(changed=True, commands=commands)

    def test_magp_disable(self):
        set_module_args(dict(magp='disabled'))
        self.execute_module(changed=False)

    def test_spanning_tree_enable(self):
        set_module_args(dict(spanning_tree='enabled'))
        self.execute_module(changed=False)

    def test_spanning_tree_disable(self):
        set_module_args(dict(spanning_tree='disabled'))
        commands = ['no spanning-tree']
        self.execute_module(changed=True, commands=commands)

    def test_dcb_pfc_enable(self):
        set_module_args(dict(dcb_pfc='enabled'))
        commands = ['dcb priority-flow-control enable force']
        self.execute_module(changed=True, commands=commands)

    def test_dcb_pfc_disable(self):
        set_module_args(dict(dcb_pfc='disabled'))
        self.execute_module(changed=False)

    def test_igmp_snooping_enable(self):
        set_module_args(dict(igmp_snooping='enabled'))
        commands = ['ip igmp snooping']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_snooping_disable(self):
        set_module_args(dict(igmp_snooping='disabled'))
        self.execute_module(changed=False)

    def test_lacp_enable(self):
        set_module_args(dict(lacp='enabled'))
        commands = ['lacp']
        self.execute_module(changed=True, commands=commands)

    def test_lacp_disable(self):
        set_module_args(dict(lacp='disabled'))
        self.execute_module(changed=False)

    def test_ip_routing_enable(self):
        set_module_args(dict(ip_routing='enabled'))
        self.execute_module(changed=False)

    def test_ip_routing_disable(self):
        set_module_args(dict(ip_routing='disabled'))
        commands = ['no ip routing']
        self.execute_module(changed=True, commands=commands)

    def test_lldp_enable(self):
        set_module_args(dict(lldp='enabled'))
        commands = ['lldp']
        self.execute_module(changed=True, commands=commands)

    def test_lldp_disable(self):
        set_module_args(dict(lldp='disabled'))
        self.execute_module(changed=False)

    def test_bgp_enable(self):
        set_module_args(dict(bgp='enabled'))
        commands = ['protocol bgp']
        self.execute_module(changed=True, commands=commands)

    def test_bgp_disable(self):
        set_module_args(dict(bgp='disabled'))
        self.execute_module(changed=False)

    def test_ospf_enable(self):
        set_module_args(dict(ospf='enabled'))
        commands = ['protocol ospf']
        self.execute_module(changed=True, commands=commands)

    def test_ospf_disable(self):
        set_module_args(dict(ospf='disabled'))
        self.execute_module(changed=False)

    def test_nve_enable(self):
        set_module_args(dict(nve='enabled'))
        commands = ['protocol nve']
        self.execute_module(changed=True, commands=commands)

    def test_nve_disabled(self):
        set_module_args(dict(nve='disabled'))
        self.execute_module(changed=False)
