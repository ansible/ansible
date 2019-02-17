#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_mlag_vip
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxMlagVipModule(TestOnyxModule):

    module = onyx_mlag_vip

    def setUp(self):
        super(TestOnyxMlagVipModule, self).setUp()
        self._mlag_enabled = True
        self.mock_show_mlag = patch.object(
            onyx_mlag_vip.OnyxMLagVipModule,
            "_show_mlag")
        self.show_mlag = self.mock_show_mlag.start()
        self.mock_show_mlag_vip = patch.object(
            onyx_mlag_vip.OnyxMLagVipModule,
            "_show_mlag_vip")
        self.show_mlag_vip = self.mock_show_mlag_vip.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxMlagVipModule, self).tearDown()
        self.mock_show_mlag.stop()
        self.mock_show_mlag_vip.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        if self._mlag_enabled:
            config_file = 'onyx_mlag_vip_show.cfg'
            self.show_mlag_vip.return_value = load_fixture(config_file)
            config_file = 'onyx_mlag_show.cfg'
            self.show_mlag.return_value = load_fixture(config_file)
        else:
            self.show_mlag_vip.return_value = None
            self.show_mlag.return_value = None
        self.load_config.return_value = None

    def test_mlag_no_change(self):
        set_module_args(dict(ipaddress='10.209.25.107/24',
                             group_name='neo-mlag-vip-500',
                             mac_address='00:00:5E:00:01:4E'))
        self.execute_module(changed=False)

    def test_mlag_change(self):
        self._mlag_enabled = False
        set_module_args(dict(ipaddress='10.209.25.107/24',
                             group_name='neo-mlag-vip-500',
                             mac_address='00:00:5E:00:01:4E',
                             delay=0))
        commands = ['mlag-vip neo-mlag-vip-500 ip 10.209.25.107 /24 force',
                    'mlag system-mac 00:00:5e:00:01:4e', 'no mlag shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_mlag_send_group_name_only_change(self):
        self._mlag_enabled = False
        set_module_args(dict(group_name='neo-mlag-vip-500',
                             delay=0))
        commands = ['mlag-vip neo-mlag-vip-500',
                    'no mlag shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_mlag_absent_no_change(self):
        self._mlag_enabled = False
        set_module_args(dict(state='absent'))
        self.execute_module(changed=False)

    def test_mlag_absent_change(self):
        set_module_args(dict(state='absent', delay=0))
        commands = ['no mlag-vip']
        self.execute_module(changed=True, commands=commands)
