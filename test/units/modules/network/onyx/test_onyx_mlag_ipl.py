#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_mlag_ipl
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxMlagIplModule(TestOnyxModule):

    module = onyx_mlag_ipl

    def setUp(self):
        super(TestOnyxMlagIplModule, self).setUp()
        self._mlag_enabled = True
        self.mock_get_config = patch.object(
            onyx_mlag_ipl.OnyxMlagIplModule,
            "_show_mlag_data")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxMlagIplModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        if self._mlag_enabled:
            config_file = 'onyx_mlag_ipl_show.cfg'
            self.get_config.return_value = load_fixture(config_file)
        else:
            self.get_config.return_value = None
        self.load_config.return_value = None

    def test_no_ipl_no_change(self):
        self._mlag_enabled = False
        set_module_args(dict(name="Po1", state='absent'))
        self.execute_module(changed=False)

    def test_ipl_no_change(self):
        self._mlag_enabled = True
        set_module_args(dict(name="Po1", state='present',
                             vlan_interface='Vlan 1002',
                             peer_address='10.2.2.2'))
        self.execute_module(changed=False)

    def test_ipl_add(self):
        self._mlag_enabled = False
        set_module_args(dict(name="Po1", state='present',
                             vlan_interface='Vlan 1002',
                             peer_address='10.2.2.2'))
        commands = ['interface port-channel 1 ipl 1',
                    'interface vlan 1002 ipl 1 peer-address 10.2.2.2']
        self.execute_module(changed=True, commands=commands)

    def test_ipl_add_peer(self):
        self._mlag_enabled = True
        set_module_args(dict(name="Po1", state='present',
                             vlan_interface='Vlan 1002',
                             peer_address='10.2.2.4'))
        commands = ['interface vlan 1002 ipl 1 peer-address 10.2.2.4']
        self.execute_module(changed=True, commands=commands)

    def test_ipl_remove(self):
        self._mlag_enabled = True
        set_module_args(dict(name="Po1", state='absent'))
        commands = ['interface port-channel 1 no ipl 1']
        self.execute_module(changed=True, commands=commands)

    def test_ipl_change_vlan(self):
        self._mlag_enabled = True
        set_module_args(dict(name="Po1", state='present',
                             vlan_interface='Vlan 1003',
                             peer_address='10.2.2.4'))
        commands = ['interface vlan 1002 no ipl 1',
                    'interface vlan 1003 ipl 1 peer-address 10.2.2.4']
        self.execute_module(changed=True, commands=commands)
