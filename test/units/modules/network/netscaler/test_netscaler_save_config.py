
#  Copyright (c) 2017 Citrix Systems
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from ansible.compat.tests.mock import patch, Mock, MagicMock, call
from units.modules.utils import set_module_args
from .netscaler_module import TestModule, nitro_base_patcher

import sys

if sys.version_info[:2] != (2, 6):
    import requests


class TestNetscalerSaveConfigModule(TestModule):

    @classmethod
    def setUpClass(cls):
        class MockException(Exception):
            pass

        cls.MockException = MockException

        cls.nitro_base_patcher = nitro_base_patcher

    @classmethod
    def tearDownClass(cls):
        cls.nitro_base_patcher.stop()

    def setUp(self):
        super(TestNetscalerSaveConfigModule, self).setUp()
        self.nitro_base_patcher.start()

    def tearDown(self):
        super(TestNetscalerSaveConfigModule, self).tearDown()
        self.nitro_base_patcher.stop()

    def test_graceful_nitro_error_on_login(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
        ))
        from ansible.modules.network.netscaler import netscaler_save_config

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        client_mock = Mock()
        client_mock.login = Mock(side_effect=MockException)
        m = Mock(return_value=client_mock)
        with patch('ansible.modules.network.netscaler.netscaler_save_config.get_nitro_client', m):
            with patch('ansible.modules.network.netscaler.netscaler_save_config.nitro_exception', MockException):
                self.module = netscaler_save_config
                result = self.failed()
                self.assertTrue(result['msg'].startswith('nitro exception'), msg='nitro exception during login not handled properly')

    def test_graceful_no_connection_error(self):

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
        ))
        from ansible.modules.network.netscaler import netscaler_save_config

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.ConnectionError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_save_config',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_save_config
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Connection error'), msg='Connection error was not handled gracefully')

    def test_graceful_login_error(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
        ))
        from ansible.modules.network.netscaler import netscaler_save_config

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.SSLError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_save_config',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_save_config
            result = self.failed()
            self.assertTrue(result['msg'].startswith('SSL Error'), msg='SSL Error was not handled gracefully')

    def test_save_config_called(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
        ))

        class MockException(Exception):
            pass

        from ansible.modules.network.netscaler import netscaler_save_config
        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_save_config',
            get_nitro_client=Mock(return_value=client_mock),
            nitro_exception=MockException,
        ):
            self.module = netscaler_save_config
            self.exited()
            call_sequence = [call.login(), call.save_config(), call.logout()]
            client_mock.assert_has_calls(call_sequence)
