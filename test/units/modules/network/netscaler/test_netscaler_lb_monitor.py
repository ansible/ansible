
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


class TestNetscalerLBVServerModule(TestModule):

    @classmethod
    def setUpClass(cls):
        class MockException(Exception):
            pass

        cls.MockException = MockException

        m = MagicMock()
        nssrc_modules_mock = {
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbmonitor': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbmonitor.lbvmonitor': m,
        }

        cls.nitro_specific_patcher = patch.dict(sys.modules, nssrc_modules_mock)
        cls.nitro_base_patcher = nitro_base_patcher

    @classmethod
    def tearDownClass(cls):
        cls.nitro_base_patcher.stop()
        cls.nitro_specific_patcher.stop()

    def setUp(self):
        super(TestNetscalerLBVServerModule, self).setUp()

        self.nitro_base_patcher.start()
        self.nitro_specific_patcher.start()

        # Setup minimal required arguments to pass AnsibleModule argument parsing

    def tearDown(self):
        super(TestNetscalerLBVServerModule, self).tearDown()

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
        from ansible.modules.network.netscaler import netscaler_lb_monitor
        self.module = netscaler_lb_monitor
        result = self.failed()
        self.assertEqual(result['msg'], 'Could not load nitro python sdk')

    def test_graceful_nitro_error_on_login(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        client_mock = Mock()
        client_mock.login = Mock(side_effect=MockException)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_lb_monitor
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
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.ConnectionError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=m,
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_monitor
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Connection error'), msg='Connection error was not handled gracefully')

    def test_graceful_login_error(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')

        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.SSLError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=m,
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_monitor
            result = self.failed()
            self.assertTrue(result['msg'].startswith('SSL Error'), msg='SSL Error was not handled gracefully')

    def test_save_config_called_on_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=m,
            lbmonitor_exists=Mock(side_effect=[False, True]),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
        ):
            self.module = netscaler_lb_monitor
            self.exited()
            self.assertIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_called_on_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=m,
            lbmonitor_exists=Mock(side_effect=[True, False]),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
        ):
            self.module = netscaler_lb_monitor
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
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=m,
            lbmonitor_exists=Mock(side_effect=[False, True]),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
        ):
            self.module = netscaler_lb_monitor
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
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=m,
            lbmonitor_exists=Mock(side_effect=[True, False]),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
        ):
            self.module = netscaler_lb_monitor
            self.exited()
            self.assertNotIn(call.save_config(), client_mock.mock_calls)

    def test_ensure_feature_is_enabled_called(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        client_mock = Mock()

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))
        feature_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=client_mock),
            lbmonitor_exists=Mock(side_effect=[True, True]),
            lbmonitor_identical=Mock(side_effect=[True, True]),

            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=feature_mock,
        ):
            self.module = netscaler_lb_monitor
            self.exited()
            feature_mock.assert_called_with(client_mock, 'LB')

    def test_ensure_feature_is_enabled_nitro_exception_caught(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        client_mock = Mock()

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))
        errorcode = 10
        message = 'mock error'

        class MockException(Exception):
            def __init__(self):
                self.errorcode = errorcode
                self.message = message

        feature_mock = Mock(side_effect=MockException)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=client_mock),
            lbmonitor_exists=Mock(side_effect=[True, True]),
            lbmonitor_identical=Mock(side_effect=[True, True]),

            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=feature_mock,
            nitro_exception=MockException,
        ):
            self.module = netscaler_lb_monitor
            result = self.failed()
            expected_msg = 'nitro exception errorcode=%s, message=%s' % (errorcode, message)
            self.assertEqual(result['msg'], expected_msg, 'Failed to handle nitro exception')

    def test_create_new_lb_monitor_workflow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=Mock()),
            lbmonitor_exists=Mock(side_effect=[False, True]),
            lbmonitor_identical=Mock(side_effect=[True]),

            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
        ):
            self.module = netscaler_lb_monitor
            result = self.exited()
            lb_monitor_proxy_mock.assert_has_calls([call.add()])
            self.assertTrue(result['changed'])

    def test_update_lb_monitor_workflow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=Mock()),
            lbmonitor_exists=Mock(side_effect=[True, True]),
            lbmonitor_identical=Mock(side_effect=[False, True]),

            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            get_immutables_intersection=Mock(return_value=[]),
            diff_list=Mock(return_value={}),
        ):
            self.module = netscaler_lb_monitor
            result = self.exited()
            lb_monitor_proxy_mock.assert_has_calls([call.update()])
            self.assertTrue(result['changed'])

    def test_lb_monitor_exists_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=client_mock),
            lbmonitor_exists=Mock(side_effect=[False, False]),
            lbmonitor_identical=Mock(side_effect=[False, True]),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_monitor
            result = self.failed()
            self.assertEqual(result['msg'], 'lb monitor does not exist')

    def test_lb_monitor_identical_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=client_mock),
            lbmonitor_exists=Mock(side_effect=[True, True]),
            lbmonitor_identical=Mock(side_effect=[False, False]),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            get_immutables_intersection=(Mock(return_value=[])),
            nitro_exception=self.MockException,
            diff_list=Mock(return_value={}),
        ):
            self.module = netscaler_lb_monitor
            result = self.failed()
            self.assertEqual(result['msg'], 'lb monitor is not configured correctly')

    def test_absent_state_workflow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        client_mock = Mock()
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=client_mock),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            lbmonitor_exists=Mock(side_effect=[True, False]),
        ):
            self.module = netscaler_lb_monitor
            result = self.exited()
            lb_monitor_proxy_mock.assert_has_calls([call.delete()])
            self.assertTrue(result['changed'])

    def test_absent_state_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_monitor

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        client_mock = Mock()
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=client_mock),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            lbmonitor_exists=Mock(side_effect=[True, True]),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_monitor
            result = self.failed()
            lb_monitor_proxy_mock.assert_has_calls([call.delete()])
            self.assertEqual(result['msg'], 'lb monitor still exists')

    def test_get_immutables_failure(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))

        from ansible.modules.network.netscaler import netscaler_lb_monitor

        lb_monitor_proxy_mock = Mock(diff_object=Mock(return_value={}))

        client_mock = Mock()
        m = Mock(return_value=['some'])
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_monitor',
            get_nitro_client=Mock(return_value=client_mock),
            ConfigProxy=Mock(return_value=lb_monitor_proxy_mock),
            ensure_feature_is_enabled=Mock(),
            lbmonitor_exists=Mock(side_effect=[True, True]),
            lbmonitor_identical=Mock(side_effect=[False, True]),
            get_immutables_intersection=m,
            diff_list=Mock(return_value={}),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_monitor
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('Cannot update immutable attributes'),
                msg='Did not handle immutables error correctly',
            )
