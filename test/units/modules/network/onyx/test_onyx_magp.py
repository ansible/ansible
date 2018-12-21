#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_magp
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxMagpModule(TestOnyxModule):

    module = onyx_magp

    def setUp(self):
        super(TestOnyxMagpModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_magp.OnyxMagpModule,
            "_get_magp_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_version = patch.object(onyx_magp.OnyxMagpModule,
                                             "_get_os_version")
        self.get_version = self.mock_get_version.start()

    def tearDown(self):
        super(TestOnyxMagpModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_get_version.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_magp_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None
        self.get_version.return_value = "3.6.5000"

    def test_magp_absent_no_change(self):
        set_module_args(dict(interface='Vlan 1002', magp_id=110,
                             state='absent'))
        self.execute_module(changed=False)

    def test_magp_no_change(self):
        set_module_args(dict(interface='Vlan 1200', magp_id=103,
                             state='disabled'))
        self.execute_module(changed=False)

    def test_magp_present_no_change(self):
        set_module_args(dict(interface='Vlan 1200', magp_id=103))
        self.execute_module(changed=False)

    def test_magp_enable(self):
        set_module_args(dict(interface='Vlan 1200', magp_id=103,
                             state='enabled'))
        commands = ['interface vlan 1200 magp 103 no shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_magp_disable(self):
        set_module_args(dict(interface='Vlan 1243', magp_id=102,
                             state='disabled', router_ip='10.0.0.43',
                             router_mac='01:02:03:04:05:06'))
        commands = ['interface vlan 1243 magp 102 shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_magp_change_address(self):
        set_module_args(dict(interface='Vlan 1243', magp_id=102,
                             router_ip='10.0.0.44',
                             router_mac='01:02:03:04:05:07'))
        commands = [
            'interface vlan 1243 magp 102 ip virtual-router address 10.0.0.44',
            'interface vlan 1243 magp 102 ip virtual-router mac-address 01:02:03:04:05:07']
        self.execute_module(changed=True, commands=commands)

    def test_magp_remove_address(self):
        set_module_args(dict(interface='Vlan 1243', magp_id=102))
        commands = [
            'interface vlan 1243 magp 102 no ip virtual-router address',
            'interface vlan 1243 magp 102 no ip virtual-router mac-address']
        self.execute_module(changed=True, commands=commands)

    def test_magp_add(self):
        set_module_args(dict(interface='Vlan 1244', magp_id=104,
                             router_ip='10.0.0.44',
                             router_mac='01:02:03:04:05:07'))
        commands = [
            'interface vlan 1244 magp 104',
            'exit',
            'interface vlan 1244 magp 104 ip virtual-router address 10.0.0.44',
            'interface vlan 1244 magp 104 ip virtual-router mac-address 01:02:03:04:05:07']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_magp_change_vlan(self):
        set_module_args(dict(interface='Vlan 1244', magp_id=102,
                             router_ip='10.0.0.43',
                             router_mac='01:02:03:04:05:06'))
        commands = [
            'interface vlan 1243 no magp 102',
            'interface vlan 1244 magp 102',
            'exit',
            'interface vlan 1244 magp 102 ip virtual-router address 10.0.0.43',
            'interface vlan 1244 magp 102 ip virtual-router mac-address 01:02:03:04:05:06']
        self.execute_module(changed=True, commands=commands)
