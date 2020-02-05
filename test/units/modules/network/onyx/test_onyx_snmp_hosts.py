#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_snmp_hosts
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxSNMPHostsModule(TestOnyxModule):

    module = onyx_snmp_hosts

    def setUp(self):
        self.enabled = False
        super(TestOnyxSNMPHostsModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_snmp_hosts.OnyxSNMPHostsModule, "_show_hosts_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxSNMPHostsModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_snmp_hosts.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_snmp_host_enabled_state_no_change(self):
        set_module_args(dict(hosts=[dict(name='1.1.1.1',
                                         enabled=True)]))
        self.execute_module(changed=False)

    def test_snmp_host_enabled_state_with_change(self):
        set_module_args(dict(hosts=[dict(name='1.1.1.1',
                                         enabled=False)]))
        commands = ['snmp-server host 1.1.1.1 disable']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_host_notification_type_no_change(self):
        set_module_args(dict(hosts=[dict(name='2.2.2.2',
                                         notification_type='trap',
                                         version='2c',
                                         port='5')]))
        self.execute_module(changed=False)

    def test_snmp_host_notification_type_with_change(self):
        set_module_args(dict(hosts=[dict(name='2.2.2.2',
                                         notification_type='inform',
                                         version='2c',
                                         port='5')]))
        commands = ['snmp-server host 2.2.2.2 informs port 5 version 2c']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_host_version_no_change(self):
        set_module_args(dict(hosts=[dict(name='2.2.2.2',
                                         notification_type='trap',
                                         version='2c',
                                         port='5')]))
        self.execute_module(changed=False)

    def test_snmp_host_version_with_change(self):
        set_module_args(dict(hosts=[dict(name='2.2.2.2',
                                         notification_type='trap',
                                         version='1',
                                         port='5')]))
        commands = ['snmp-server host 2.2.2.2 traps port 5 version 1']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_host_port_no_change(self):
        set_module_args(dict(hosts=[dict(name='2.2.2.2',
                                         notification_type='trap',
                                         version='2c',
                                         port='5')]))
        self.execute_module(changed=False)

    def test_snmp_host_port_with_change(self):
        set_module_args(dict(hosts=[dict(name='2.2.2.2',
                                         notification_type='trap',
                                         version='2c',
                                         port='3')]))
        commands = ['snmp-server host 2.2.2.2 traps port 3 version 2c']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_host_user_name_no_change(self):
        set_module_args(dict(hosts=[dict(name='1.1.1.1',
                                         notification_type='inform',
                                         version='3',
                                         port='3',
                                         user_name='sara',
                                         auth_type='md5',
                                         auth_password='sara123saea1234678')]))
        self.execute_module(changed=False)

    def test_snmp_host_user_name_with_change(self):
        set_module_args(dict(hosts=[dict(name='1.1.1.1',
                                         notification_type='inform',
                                         version='3',
                                         port='3',
                                         user_name='masa',
                                         auth_type='md5',
                                         auth_password='sara123saea1234678')]))
        commands = ['snmp-server host 1.1.1.1 informs port 3 version 3 user masa auth md5 sara123saea1234678']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_host_auth_type_no_change(self):
        set_module_args(dict(hosts=[dict(name='1.1.1.1',
                                         notification_type='inform',
                                         version='3',
                                         port='3',
                                         user_name='sara',
                                         auth_type='md5',
                                         auth_password='sara123saea1234678')]))
        self.execute_module(changed=False)

    def test_snmp_host_auth_type_with_change(self):
        set_module_args(dict(hosts=[dict(name='1.1.1.1',
                                         notification_type='inform',
                                         version='3',
                                         port='3',
                                         user_name='sara',
                                         auth_type='sha',
                                         auth_password='sara123saea1234678')]))
        commands = ['snmp-server host 1.1.1.1 informs port 3 version 3 user sara auth sha sara123saea1234678']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_host_privacy_type_no_change(self):
        set_module_args(dict(hosts=[dict(name='1.1.1.1',
                                         notification_type='inform',
                                         version='3',
                                         port='3',
                                         user_name='sara',
                                         auth_type='md5',
                                         auth_password='sara123saea1234678',
                                         privacy_type='3des',
                                         privacy_password='pjqriuewjhksjmdoiws')]))
        self.execute_module(changed=False)

    def test_snmp_host_privacy_type_with_change(self):
        set_module_args(dict(hosts=[dict(name='1.1.1.1',
                                         notification_type='inform',
                                         version='3',
                                         port='3',
                                         user_name='sara',
                                         auth_type='md5',
                                         auth_password='sara123saea1234678',
                                         privacy_type='aes-192',
                                         privacy_password='pjqriuewjhksjmdoiws')]))
        commands = ['snmp-server host 1.1.1.1 informs port 3 version 3 user sara auth md5 sara123saea1234678 priv aes-192 pjqriuewjhksjmdoiws']
        self.execute_module(changed=True, commands=commands)

    def test_snmp_host_state_with_change(self):
        set_module_args(dict(hosts=[dict(name='2.2.2.2',
                                         notification_type='trap',
                                         version='2c',
                                         port='5',
                                         state='absent')]))
        commands = ['no snmp-server host 2.2.2.2']
        self.execute_module(changed=True, commands=commands)
