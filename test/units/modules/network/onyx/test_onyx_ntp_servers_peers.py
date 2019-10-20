#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_ntp_servers_peers
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxNtpServersPeersModule(TestOnyxModule):

    module = onyx_ntp_servers_peers
    enabled = False

    def setUp(self):
        self.enabled = False
        super(TestOnyxNtpServersPeersModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_ntp_servers_peers.OnyxNTPServersPeersModule, "_show_peers_servers_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxNtpServersPeersModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_ntp_servers_peers_show.cfg'
        data = load_fixture(config_file)
        self.get_config.return_value = data
        self.load_config.return_value = None

    def test_ntp_peer_state_no_change(self):
        set_module_args(dict(peer=[dict(ip_or_name='1.1.1.1',
                                        enabled='yes')]))
        self.execute_module(changed=False)

    def test_ntp_peer_state_with_change(self):
        set_module_args(dict(peer=[dict(ip_or_name='1.1.1.1',
                                        enabled='no')]))
        commands = ['ntp peer 1.1.1.1 disable']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_peer_version_no_change(self):
        set_module_args(dict(peer=[dict(ip_or_name='1.1.1.1',
                                        version='4')]))
        self.execute_module(changed=False)

    def test_ntp_peer_version_with_change(self):
        set_module_args(dict(peer=[dict(ip_or_name='1.1.1.1',
                                        version='3')]))
        commands = ['ntp peer 1.1.1.1 version 3']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_peer_key_id_no_change(self):
        set_module_args(dict(peer=[dict(ip_or_name='1.1.1.1',
                                        key_id='5')]))
        self.execute_module(changed=False)

    def test_ntp_peer_key_id_with_change(self):
        set_module_args(dict(peer=[dict(ip_or_name='1.1.1.1',
                                        key_id='6')]))
        commands = ['ntp peer 1.1.1.1 keyID 6']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_peer_delete_with_change(self):
        set_module_args(dict(peer=[dict(ip_or_name='1.1.1.1',
                                        state='absent')]))
        commands = ['no ntp peer 1.1.1.1']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_server_state_no_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          enabled='no')]))
        self.execute_module(changed=False)

    def test_ntp_server_state_with_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          enabled='yes')]))
        commands = ['no ntp server 2.2.2.2 disable']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_server_version_no_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          version='4')]))
        self.execute_module(changed=False)

    def test_ntp_server_version_with_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          version='3')]))
        commands = ['ntp server 2.2.2.2 version 3']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_server_keyID_no_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          key_id='99')]))
        self.execute_module(changed=False)

    def test_ntp_server_keyID_with_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          key_id='8')]))
        commands = ['ntp server 2.2.2.2 keyID 8']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_server_trusted_state_no_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          trusted_enable='yes')]))
        self.execute_module(changed=False)

    def test_ntp_server_trusted_state_with_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          trusted_enable='no')]))
        commands = ['no ntp server 2.2.2.2 trusted-enable']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_server_delete_with_change(self):
        set_module_args(dict(server=[dict(ip_or_name='2.2.2.2',
                                          state='absent')]))
        commands = ['no ntp server 2.2.2.2']
        self.execute_module(changed=True, commands=commands)

    def test_ntpdate_with_change(self):
        set_module_args(dict(ntpdate='192.22.1.66'))
        commands = ['ntpdate 192.22.1.66']
        self.execute_module(changed=True, commands=commands)
