
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

import sys

if sys.version_info[:2] != (2, 6):
    import requests


from .netscaler_module import TestModule, nitro_base_patcher, set_module_args


class TestNetscalerCSPolicyModule(TestModule):

    @classmethod
    def setUpClass(cls):
        class MockException(Exception):
            pass
        cls.MockException = MockException
        m = MagicMock()
        nssrc_modules_mock = {
            'nssrc.com.citrix.netscaler.nitro.resource.config.cs': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.cs.cspolicy': m,
        }

        cls.nitro_specific_patcher = patch.dict(sys.modules, nssrc_modules_mock)
        cls.nitro_base_patcher = nitro_base_patcher

    @classmethod
    def tearDownClass(cls):
        cls.nitro_base_patcher.stop()
        cls.nitro_specific_patcher.stop()

    def set_module_state(self, state):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state=state,
        ))

    def setUp(self):
        self.nitro_base_patcher.start()
        self.nitro_specific_patcher.start()

    def tearDown(self):
        self.nitro_base_patcher.stop()
        self.nitro_specific_patcher.stop()

    def test_graceful_nitro_api_import_error(self):
        # Stop nitro api patching to cause ImportError
        self.set_module_state('present')
        self.nitro_base_patcher.stop()
        self.nitro_specific_patcher.stop()
        from ansible.modules.network.netscaler import netscaler_cs_policy
        self.module = netscaler_cs_policy
        result = self.failed()
        self.assertEqual(result['msg'], 'Could not load nitro python sdk')

    def test_graceful_nitro_error_on_login(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_cs_policy

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        client_mock = Mock()
        client_mock.login = Mock(side_effect=MockException)
        m = Mock(return_value=client_mock)
        with patch('ansible.modules.network.netscaler.netscaler_cs_policy.get_nitro_client', m):
            with patch('ansible.modules.network.netscaler.netscaler_cs_policy.nitro_exception', MockException):
                self.module = netscaler_cs_policy
                result = self.failed()
                self.assertTrue(result['msg'].startswith('nitro exception'), msg='nitro exception during login not handled properly')

    def test_graceful_no_connection_error(self):

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_cs_policy

        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.ConnectionError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            get_nitro_client=m,
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_cs_policy
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Connection error'), msg='Connection error was not handled gracefully')

    def test_graceful_login_error(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_cs_policy

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.SSLError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_cs_policy
            result = self.failed()
            self.assertTrue(result['msg'].startswith('SSL Error'), msg='SSL Error was not handled gracefully')

    def test_create_non_existing_cs_policy(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_cs_policy
        cs_policy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        cs_policy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=cs_policy_mock)
        policy_exists_mock = Mock(side_effect=[False, True])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            ConfigProxy=m,
            policy_exists=policy_exists_mock,
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),
        ):
            self.module = netscaler_cs_policy
            result = self.exited()
            cs_policy_mock.assert_has_calls([call.add()])
            self.assertTrue(result['changed'], msg='Change not recorded')

    def test_update_cs_policy_when_cs_policy_differs(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_cs_policy
        cs_policy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        cs_policy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=cs_policy_mock)
        policy_exists_mock = Mock(side_effect=[True, True])
        policy_identical_mock = Mock(side_effect=[False, True])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            ConfigProxy=m,
            policy_exists=policy_exists_mock,
            policy_identical=policy_identical_mock,
            ensure_feature_is_enabled=Mock(),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_cs_policy
            result = self.exited()
            cs_policy_mock.assert_has_calls([call.update()])
            self.assertTrue(result['changed'], msg='Change not recorded')

    def test_no_change_to_module_when_all_identical(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_cs_policy
        cs_policy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        cs_policy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=cs_policy_mock)
        policy_exists_mock = Mock(side_effect=[True, True])
        policy_identical_mock = Mock(side_effect=[True, True])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            ConfigProxy=m,
            policy_exists=policy_exists_mock,
            policy_identical=policy_identical_mock,
            ensure_feature_is_enabled=Mock(),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_cs_policy
            result = self.exited()
            self.assertFalse(result['changed'], msg='Erroneous changed status update')

    def test_absent_operation(self):
        self.set_module_state('absent')
        from ansible.modules.network.netscaler import netscaler_cs_policy
        cs_policy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        cs_policy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=cs_policy_mock)
        policy_exists_mock = Mock(side_effect=[True, False])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            ConfigProxy=m,
            policy_exists=policy_exists_mock,
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),

        ):
            self.module = netscaler_cs_policy
            result = self.exited()
            cs_policy_mock.assert_has_calls([call.delete()])
            self.assertTrue(result['changed'], msg='Changed status not set correctly')

    def test_absent_operation_no_change(self):
        self.set_module_state('absent')
        from ansible.modules.network.netscaler import netscaler_cs_policy
        cs_policy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        cs_policy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=cs_policy_mock)
        policy_exists_mock = Mock(side_effect=[False, False])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            ConfigProxy=m,
            policy_exists=policy_exists_mock,
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),

        ):
            self.module = netscaler_cs_policy
            result = self.exited()
            cs_policy_mock.assert_not_called()
            self.assertFalse(result['changed'], msg='Changed status not set correctly')

    def test_graceful_nitro_exception_operation_present(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_cs_policy

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            policy_exists=m,
            ensure_feature_is_enabled=Mock(),
            nitro_exception=MockException
        ):
            self.module = netscaler_cs_policy
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation present'
            )

    def test_graceful_nitro_exception_operation_absent(self):
        self.set_module_state('absent')
        from ansible.modules.network.netscaler import netscaler_cs_policy

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            policy_exists=m,
            nitro_exception=MockException,
            ensure_feature_is_enabled=Mock(),
        ):
            self.module = netscaler_cs_policy
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation absent'
            )

    def test_ensure_feature_is_enabled_called(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_cs_policy

        client_mock = Mock()
        ensure_feature_is_enabled_mock = Mock()
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_policy',
            get_nitro_client=Mock(return_value=client_mock),
            policy_exists=Mock(side_effect=[True, True]),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=ensure_feature_is_enabled_mock,
        ):
            self.module = netscaler_cs_policy
            result = self.exited()
            ensure_feature_is_enabled_mock.assert_has_calls([call(client_mock, 'CS')])
