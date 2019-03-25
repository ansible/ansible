#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_ospf
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxOspfModule(TestOnyxModule):

    module = onyx_ospf

    def setUp(self):
        super(TestOnyxOspfModule, self).setUp()
        self._ospf_exists = True
        self.mock_get_config = patch.object(
            onyx_ospf.OnyxOspfModule,
            "_get_ospf_config")
        self.get_config = self.mock_get_config.start()

        self.mock_get_interfaces_config = patch.object(
            onyx_ospf.OnyxOspfModule,
            "_get_ospf_interfaces_config")
        self.get_interfaces_config = self.mock_get_interfaces_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxOspfModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        if self._ospf_exists:
            config_file = 'onyx_ospf_show.cfg'
            self.get_config.return_value = load_fixture(config_file)
            config_file = 'onyx_ospf_interfaces_show.cfg'
            self.get_interfaces_config.return_value = load_fixture(config_file)
        else:
            self.get_config.return_value = None
            self.get_interfaces_config.return_value = None
        self.load_config.return_value = None

    def test_ospf_absent_no_change(self):
        set_module_args(dict(ospf=3, state='absent'))
        self.execute_module(changed=False)

    def test_ospf_present_no_change(self):
        interface = dict(name='Loopback 1', area='0.0.0.0')
        set_module_args(dict(ospf=2, router_id='10.2.3.4',
                             interfaces=[interface]))
        self.execute_module(changed=False)

    def test_ospf_present_remove(self):
        set_module_args(dict(ospf=2, state='absent'))
        commands = ['no router ospf 2']
        self.execute_module(changed=True, commands=commands)

    def test_ospf_change_router(self):
        interface = dict(name='Loopback 1', area='0.0.0.0')
        set_module_args(dict(ospf=2, router_id='10.2.3.5',
                             interfaces=[interface]))
        commands = ['router ospf 2', 'router-id 10.2.3.5', 'exit']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ospf_remove_router(self):
        interface = dict(name='Loopback 1', area='0.0.0.0')
        set_module_args(dict(ospf=2, interfaces=[interface]))
        commands = ['router ospf 2', 'no router-id', 'exit']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ospf_add_interface(self):
        interfaces = [dict(name='Loopback 1', area='0.0.0.0'),
                      dict(name='Loopback 2', area='0.0.0.0')]
        set_module_args(dict(ospf=2, router_id='10.2.3.4',
                             interfaces=interfaces))
        commands = ['interface loopback 2 ip ospf area 0.0.0.0']
        self.execute_module(changed=True, commands=commands)

    def test_ospf_remove_interface(self):
        set_module_args(dict(ospf=2, router_id='10.2.3.4'))
        commands = ['interface loopback 1 no ip ospf area']
        self.execute_module(changed=True, commands=commands)

    def test_ospf_add(self):
        self._ospf_exists = False
        interfaces = [dict(name='Loopback 1', area='0.0.0.0'),
                      dict(name='Vlan 210', area='0.0.0.0'),
                      dict(name='Eth1/1', area='0.0.0.0'),
                      dict(name='Po1', area='0.0.0.0')]
        set_module_args(dict(ospf=2, router_id='10.2.3.4',
                             interfaces=interfaces))
        commands = ['router ospf 2', 'router-id 10.2.3.4', 'exit',
                    'interface loopback 1 ip ospf area 0.0.0.0',
                    'interface vlan 210 ip ospf area 0.0.0.0',
                    'interface ethernet 1/1 ip ospf area 0.0.0.0',
                    'interface port-channel 1 ip ospf area 0.0.0.0']
        self.execute_module(changed=True, commands=commands)
