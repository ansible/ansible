#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests.mock import patch
from ansible.modules.network.onyx import onyx_linkagg
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxLinkaggModule(TestOnyxModule):

    module = onyx_linkagg

    def setUp(self):
        super(TestOnyxLinkaggModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_linkagg.OnyxLinkAggModule,
            "_get_port_channels")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()
        self.mock_get_version = patch.object(
            onyx_linkagg.OnyxLinkAggModule, "_get_os_version")
        self.get_version = self.mock_get_version.start()

    def tearDown(self):
        super(TestOnyxLinkaggModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_get_version.stop()

    def load_fixture(self, config_file):
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None
        self.get_version.return_value = "3.6.5000"

    def load_port_channel_fixture(self):
        config_file = 'onyx_port_channel_show.cfg'
        self.load_fixture(config_file)

    def load_mlag_port_channel_fixture(self):
        config_file = 'onyx_mlag_port_channel_show.cfg'
        self.load_fixture(config_file)

    def test_port_channel_no_change(self):
        set_module_args(dict(name='Po22', state='present',
                             members=['Eth1/7']))
        self.load_port_channel_fixture()
        self.execute_module(changed=False)

    def test_port_channel_remove(self):
        set_module_args(dict(name='Po22', state='absent'))
        self.load_port_channel_fixture()
        commands = ['no interface port-channel 22']
        self.execute_module(changed=True, commands=commands)

    def test_port_channel_add(self):
        set_module_args(dict(name='Po23', state='present',
                             members=['Eth1/8']))
        self.load_port_channel_fixture()
        commands = ['interface port-channel 23', 'exit',
                    'interface ethernet 1/8 channel-group 23 mode on']
        self.execute_module(changed=True, commands=commands)

    def test_port_channel_add_member(self):
        set_module_args(dict(name='Po22', state='present',
                             members=['Eth1/7', 'Eth1/8']))
        self.load_port_channel_fixture()
        commands = ['interface ethernet 1/8 channel-group 22 mode on']
        self.execute_module(changed=True, commands=commands)

    def test_port_channel_remove_member(self):
        set_module_args(dict(name='Po22', state='present'))
        self.load_port_channel_fixture()
        commands = ['interface ethernet 1/7 no channel-group']
        self.execute_module(changed=True, commands=commands)

    def test_mlag_port_channel_no_change(self):
        set_module_args(dict(name='Mpo33', state='present',
                             members=['Eth1/8']))
        self.load_mlag_port_channel_fixture()
        self.execute_module(changed=False)

    def test_mlag_port_channel_remove(self):
        set_module_args(dict(name='Mpo33', state='absent'))
        self.load_mlag_port_channel_fixture()
        commands = ['no interface mlag-port-channel 33']
        self.execute_module(changed=True, commands=commands)

    def test_mlag_port_channel_add(self):
        set_module_args(dict(name='Mpo34', state='present',
                             members=['Eth1/9']))
        self.load_mlag_port_channel_fixture()
        commands = ['interface mlag-port-channel 34', 'exit',
                    'interface ethernet 1/9 mlag-channel-group 34 mode on']
        self.execute_module(changed=True, commands=commands)

    def test_mlag_port_channel_add_member(self):
        set_module_args(dict(name='Mpo33', state='present',
                             members=['Eth1/8', 'Eth1/9']))
        self.load_mlag_port_channel_fixture()
        commands = ['interface ethernet 1/9 mlag-channel-group 33 mode on']
        self.execute_module(changed=True, commands=commands)

    def test_mlag_port_channel_remove_member(self):
        set_module_args(dict(name='Mpo33', state='present'))
        self.load_mlag_port_channel_fixture()
        commands = ['interface ethernet 1/8 no mlag-channel-group']
        self.execute_module(changed=True, commands=commands)
