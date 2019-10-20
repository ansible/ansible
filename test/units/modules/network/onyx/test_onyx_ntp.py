#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_ntp
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxNTP(TestOnyxModule):

    module = onyx_ntp
    enabled = False

    def setUp(self):
        self.enabled = False
        super(TestOnyxNTP, self).setUp()
        self.mock_get_config = patch.object(
            onyx_ntp.OnyxNTPModule, "_show_ntp_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxNTP, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_ntp_show.cfg'
        data = load_fixture(config_file)
        self.get_config.return_value = data
        self.load_config.return_value = None

    def test_ntp_state_no_change(self):
        set_module_args(dict(state='enabled'))
        self.execute_module(changed=False)

    def test_ntp_state_with_change(self):
        set_module_args(dict(state='disabled'))
        commands = ['no ntp enable']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_authenticate_state_no_change(self):
        set_module_args(dict(authenticate_state='disabled'))
        self.execute_module(changed=False)

    def test_ntp_authenticate_state_with_change(self):
        set_module_args(dict(authenticate_state='enabled'))
        commands = ['ntp authenticate']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_authentication_key_no_change(self):
        set_module_args(dict(ntp_authentication_keys=[dict(auth_key_id='22',
                                                           auth_key_encrypt_type='sha1',
                                                           auth_key_password='12345')]))
        self.execute_module(changed=False)

    def test_ntp_authentication_key_with_change(self):
        set_module_args(dict(ntp_authentication_keys=[dict(auth_key_id='22',
                                                           auth_key_encrypt_type='md5',
                                                           auth_key_password='12345')]))
        commands = ['ntp authentication-key 22 md5 12345']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_trusted_keys_with_change(self):
        set_module_args(dict(trusted_keys='22'))
        commands = ['ntp trusted-key 22']
        self.execute_module(changed=True, commands=commands)
