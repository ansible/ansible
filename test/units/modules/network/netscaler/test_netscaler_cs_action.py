
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

from units.compat.mock import patch, Mock, MagicMock, call
from units.modules.utils import set_module_args
from .netscaler_module import TestModule, nitro_base_patcher

import sys

if sys.version_info[:2] != (2, 6):
    import requests


class TestNetscalerCSActionModule(TestModule):

    @classmethod
    def setUpClass(cls):
        class MockException(Exception):
            pass

        cls.MockException = MockException

        m = MagicMock()
        cls.cs_action_mock = MagicMock()
        cls.cs_action_mock.__class__ = MagicMock(add=Mock())
        nssrc_modules_mock = {
            'nssrc.com.citrix.netscaler.nitro.resource.config.cs': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.cs.csaction': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.cs.csaction.csaction': cls.cs_action_mock,
        }

        cls.nitro_specific_patcher = patch.dict(sys.modules, nssrc_modules_mock)
        cls.nitro_base_patcher = nitro_base_patcher

    @classmethod
    def tearDownClass(cls):
        cls.nitro_base_patcher.stop()
        cls.nitro_specific_patcher.stop()

    def setUp(self):
        super(TestNetscalerCSActionModule, self).setUp()

        self.nitro_base_patcher.start()
        self.nitro_specific_patcher.start()

        # Setup minimal required arguments to pass AnsibleModule argument parsing

    def tearDown(self):
        super(TestNetscalerCSActionModule, self).tearDown()

        self.nitro_base_patcher.stop()
        self.nitro_specific_patcher.stop()

    def test_graceful_nitro_api_import_error(self):
        # Stop nitro api patching to cause ImportError
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        self.nitro_base_patcher.stop()
        self.nitro_specific_patcher.stop()
        from ansible.modules.network.netscaler import netscaler_cs_action
        self.module = netscaler_cs_action
        result = self.failed()
        self.assertEqual(result['msg'], 'Could not load nitro python sdk')

    def test_graceful_nitro_error_on_login(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        client_mock = Mock()
        client_mock.login = Mock(side_effect=MockException)
        m = Mock(return_value=client_mock)
        with patch('ansible.modules.network.netscaler.netscaler_cs_action.get_nitro_client', m):
            with patch('ansible.modules.network.netscaler.netscaler_cs_action.nitro_exception', MockException):
                self.module = netscaler_cs_action
                result = self.failed()
                self.assertTrue(result['msg'].startswith('nitro exception'), msg='nitro exception during login not handled properly')

    def test_graceful_no_connection_error(self):

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.ConnectionError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_cs_action
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Connection error'), msg='Connection error was not handled gracefully')

    def test_graceful_login_error(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.SSLError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_cs_action
            result = self.failed()
            self.assertTrue(result['msg'].startswith('SSL Error'), msg='SSL Error was not handled gracefully')

    def test_save_config_called_on_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        cs_action_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            action_exists=Mock(side_effect=[False, True]),
            ensure_feature_is_enabled=Mock(return_value=True),
            diff_list=Mock(return_value={}),
            ConfigProxy=Mock(return_value=cs_action_proxy_mock),
        ):
            self.module = netscaler_cs_action
            self.exited()
            self.assertIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_called_on_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        cs_action_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            action_exists=Mock(side_effect=[True, False]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=Mock(return_value=cs_action_proxy_mock),
        ):
            self.module = netscaler_cs_action
            self.exited()
            self.assertIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_not_called_on_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        cs_action_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            action_exists=Mock(side_effect=[False, True]),
            diff_list=Mock(return_value={}),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=Mock(return_value=cs_action_proxy_mock),
        ):
            self.module = netscaler_cs_action
            self.exited()
            self.assertNotIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_not_called_on_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        cs_action_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            action_exists=Mock(side_effect=[True, False]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=Mock(return_value=cs_action_proxy_mock),
        ):
            self.module = netscaler_cs_action
            self.exited()
            self.assertNotIn(call.save_config(), client_mock.mock_calls)

    def test_new_cs_action_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            action_exists=Mock(side_effect=[False, True]),
            action_identical=Mock(side_effect=[True]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            self.exited()
            cs_action_proxy_mock.assert_has_calls([call.add()])

    def test_modified_cs_action_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            action_exists=Mock(side_effect=[True, True]),
            action_identical=Mock(side_effect=[False, True]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            self.exited()
            cs_action_proxy_mock.assert_has_calls([call.update()])

    def test_absent_cs_action_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            action_exists=Mock(side_effect=[True, False]),
            action_identical=Mock(side_effect=[False, True]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            self.exited()
            cs_action_proxy_mock.assert_has_calls([call.delete()])

    def test_present_cs_action_identical_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            action_exists=Mock(side_effect=[True, True]),
            action_identical=Mock(side_effect=[True, True]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            self.exited()
            cs_action_proxy_mock.assert_not_called()

    def test_absent_cs_action_noop_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            action_exists=Mock(side_effect=[False, False]),
            action_identical=Mock(side_effect=[False, False]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            self.exited()
            cs_action_proxy_mock.assert_not_called()

    def test_present_cs_action_failed_update(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            action_exists=Mock(side_effect=[True, True]),
            action_identical=Mock(side_effect=[False, False]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            result = self.failed()
            self.assertEqual(result['msg'], 'Content switching action differs from configured')
            self.assertTrue(result['failed'])

    def test_present_cs_action_failed_create(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            action_exists=Mock(side_effect=[False, False]),
            action_identical=Mock(side_effect=[False, False]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            result = self.failed()
            self.assertEqual(result['msg'], 'Content switching action does not exist')
            self.assertTrue(result['failed'])

    def test_present_cs_action_update_immutable_attribute(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=['domain']),
            action_exists=Mock(side_effect=[True, True]),
            action_identical=Mock(side_effect=[False, False]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            result = self.failed()
            self.assertEqual(result['msg'], 'Cannot update immutable attributes [\'domain\']')
            self.assertTrue(result['failed'])

    def test_absent_cs_action_failed_delete(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        cs_action_proxy_mock = Mock()
        cs_action_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=cs_action_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            action_exists=Mock(side_effect=[True, True]),
            action_identical=Mock(side_effect=[False, False]),
            ensure_feature_is_enabled=Mock(return_value=True),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_cs_action
            result = self.failed()
            self.assertEqual(result['msg'], 'Content switching action still exists')
            self.assertTrue(result['failed'])

    def test_graceful_nitro_exception_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            action_exists=m,
            ensure_feature_is_enabled=Mock(return_value=True),
            nitro_exception=MockException
        ):
            self.module = netscaler_cs_action
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation absent'
            )

    def test_graceful_nitro_exception_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_cs_action

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_cs_action',
            action_exists=m,
            ensure_feature_is_enabled=Mock(return_value=True),
            nitro_exception=MockException
        ):
            self.module = netscaler_cs_action
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation absent'
            )
