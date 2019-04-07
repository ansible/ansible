
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
        cls.server_mock = MagicMock()
        cls.server_mock.__class__ = MagicMock(add=Mock())
        nssrc_modules_mock = {
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver.lbvserver': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver_service_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver_service_binding.lbvserver_service_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver_servicegroup_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbvserver_servicegroup_binding.lbvserver_servicegroup_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.ssl': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.ssl.sslvserver_sslcertkey_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.ssl.sslvserver_sslcertkey_binding.sslvserver_sslcertkey_binding': m,
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
        from ansible.modules.network.netscaler import netscaler_lb_vserver
        self.module = netscaler_lb_vserver
        result = self.failed()
        self.assertEqual(result['msg'], 'Could not load nitro python sdk')

    def test_graceful_nitro_error_on_login(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        client_mock = Mock()
        client_mock.login = Mock(side_effect=MockException)
        m = Mock(return_value=client_mock)
        with patch('ansible.modules.network.netscaler.netscaler_lb_vserver.get_nitro_client', m):
            with patch('ansible.modules.network.netscaler.netscaler_lb_vserver.nitro_exception', MockException):
                self.module = netscaler_lb_vserver
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
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.ConnectionError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=m,
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Connection error'), msg='Connection error was not handled gracefully')

    def test_graceful_login_error(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')

        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.SSLError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=m,
            nitro_exception=self.MockException,
            do_state_change=Mock(return_value=Mock(errorcode=0)),
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            self.assertTrue(result['msg'].startswith('SSL Error'), msg='SSL Error was not handled gracefully')

    def test_save_config_called_on_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        lb_vserver_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=m,
            lb_vserver_exists=Mock(side_effect=[False, True]),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
        ):
            self.module = netscaler_lb_vserver
            self.exited()
            self.assertIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_called_on_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        lb_vserver_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=m,
            lb_vserver_exists=Mock(side_effect=[True, False]),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
        ):
            self.module = netscaler_lb_vserver
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
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        lb_vserver_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=m,
            lb_vserver_exists=Mock(side_effect=[False, True]),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
        ):
            self.module = netscaler_lb_vserver
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
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        lb_vserver_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=m,
            lb_vserver_exists=Mock(side_effect=[True, False]),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
        ):
            self.module = netscaler_lb_vserver
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
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        client_mock = Mock()

        lb_vserver_proxy_mock = Mock()
        feature_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[True, True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),

            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=feature_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0)),
        ):
            self.module = netscaler_lb_vserver
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
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        client_mock = Mock()

        lb_vserver_proxy_mock = Mock()
        errorcode = 10
        message = 'mock error'

        class MockException(Exception):
            def __init__(self):
                self.errorcode = errorcode
                self.message = message

        feature_mock = Mock(side_effect=MockException)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[True, True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),

            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=feature_mock,
            nitro_exception=MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            expected_msg = 'nitro exception errorcode=%s, message=%s' % (errorcode, message)
            self.assertEqual(result['msg'], expected_msg, 'Failed to handle nitro exception')

    def test_create_new_lb_vserver_workflow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=Mock()),
            lb_vserver_exists=Mock(side_effect=[False, True]),
            lb_vserver_identical=Mock(side_effect=[True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),

            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
        ):
            self.module = netscaler_lb_vserver
            result = self.exited()
            lb_vserver_proxy_mock.assert_has_calls([call.add()])
            self.assertTrue(result['changed'])

    def test_update_lb_vserver_workflow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=Mock()),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),

            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=Mock(return_value=[]),
        ):
            self.module = netscaler_lb_vserver
            result = self.exited()
            lb_vserver_proxy_mock.assert_has_calls([call.update()])
            self.assertTrue(result['changed'])

    def test_service_bindings_handling(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()
        configured_dict = {
            'first': Mock(),
            'second': Mock(has_equal_attributes=Mock(return_value=False)),
        }

        actual_dict = {
            'second': Mock(),
            'third': Mock(),
        }

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[False, True]),
            get_configured_service_bindings=Mock(return_value=configured_dict),
            get_actual_service_bindings=Mock(return_value=actual_dict),

            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=(Mock(return_value=[])),
        ):
            self.module = netscaler_lb_vserver
            result = self.exited()
            configured_dict['first'].assert_has_calls([call.add()])

            configured_dict['second'].assert_has_calls([call.has_equal_attributes(actual_dict['second']), call.add()])

            actual_dict['second'].assert_has_calls([call.delete(client_mock, actual_dict['second'])])

            actual_dict['third'].assert_has_calls([call.delete(client_mock, actual_dict['third'])])

            self.assertTrue(result['changed'])

    def test_servicegroup_bindings_handling(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()
        configured_dict = {
            'first': Mock(),
            'second': Mock(has_equal_attributes=Mock(return_value=False)),
        }

        actual_dict = {
            'second': Mock(),
            'third': Mock(),
        }

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[False, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),
            get_configured_servicegroup_bindings=Mock(return_value=configured_dict),
            get_actual_servicegroup_bindings=Mock(return_value=actual_dict),

            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=(Mock(return_value=[])),
        ):
            self.module = netscaler_lb_vserver
            result = self.exited()
            configured_dict['first'].assert_has_calls([call.add()])

            configured_dict['second'].assert_has_calls([call.has_equal_attributes(actual_dict['second']), call.add()])

            actual_dict['second'].assert_has_calls([call.delete(client_mock, actual_dict['second'])])

            actual_dict['third'].assert_has_calls([call.delete(client_mock, actual_dict['third'])])

            self.assertTrue(result['changed'])

    def test_ssl_bindings_handling(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
            servicetype='SSL',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()
        ssl_sync_mock = Mock()

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),
            ssl_certkey_bindings_identical=Mock(side_effect=[False, True]),
            ssl_certkey_bindings_sync=ssl_sync_mock,
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=(Mock(return_value=[])),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.exited()
            self.assertTrue(len(ssl_sync_mock.mock_calls) > 0, msg='ssl cert_key bindings not called')
            self.assertTrue(result['changed'])

    def test_ssl_bindings_not_called_for_non_ssl_service(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
            save_config=False,
            servicetype='HTTP',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()
        ssl_sync_mock = Mock()

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),
            ssl_certkey_bindings_identical=Mock(side_effect=[False, True]),
            ssl_certkey_bindings_sync=ssl_sync_mock,
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=(Mock(return_value=[])),
        ):
            self.module = netscaler_lb_vserver
            result = self.exited()
            ssl_sync_mock.assert_not_called()
            self.assertTrue(result['changed'])

    def test_server_exists_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()
        ssl_sync_mock = Mock()

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[False, False]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),
            ssl_certkey_bindings_identical=Mock(side_effect=[False, True]),
            ssl_certkey_bindings_sync=ssl_sync_mock,
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'Did not create lb vserver')

    def test_server_identical_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()
        ssl_sync_mock = Mock()

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, False]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[True, True]),
            ssl_certkey_bindings_identical=Mock(side_effect=[False, True]),
            ssl_certkey_bindings_sync=ssl_sync_mock,
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=(Mock(return_value=[])),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'lb vserver is not configured correctly')

    def test_service_bindings_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[True, True]),
            service_bindings_identical=Mock(side_effect=[False, False]),
            ssl_certkey_bindings_identical=Mock(side_effect=[False, False]),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=(Mock(return_value=[])),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'service bindings are not identical')

    def test_servicegroup_bindings_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[False, False]),
            service_bindings_identical=Mock(side_effect=[True, True]),
            ssl_certkey_bindings_identical=Mock(side_effect=[False, False]),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=(Mock(return_value=[])),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'servicegroup bindings are not identical')

    def test_server_servicegroup_bindings_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False, True]),
            servicegroup_bindings_identical=Mock(side_effect=[False, False]),
            service_bindings_identical=Mock(side_effect=[True, True]),
            ssl_certkey_bindings_identical=Mock(side_effect=[False, False]),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=(Mock(return_value=[])),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'servicegroup bindings are not identical')

    def test_absent_state_workflow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        client_mock = Mock()
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            lb_vserver_exists=Mock(side_effect=[True, False]),
        ):
            self.module = netscaler_lb_vserver
            result = self.exited()
            lb_vserver_proxy_mock.assert_has_calls([call.delete()])
            self.assertTrue(result['changed'])

    def test_absent_state_sanity_check(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        client_mock = Mock()
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            lb_vserver_proxy_mock.assert_has_calls([call.delete()])
            self.assertEqual(result['msg'], 'lb vserver still exists')

    def test_disabled_state_change_called(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))

        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        do_state_change_mock = Mock(return_value=Mock(errorcode=0))
        client_mock = Mock()
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(return_value=True),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            nitro_exception=self.MockException,
            do_state_change=do_state_change_mock,
        ):
            self.module = netscaler_lb_vserver
            self.exited()
            self.assertTrue(len(do_state_change_mock.mock_calls) > 0, msg='Did not call state change')

    def test_get_immutables_failure(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))

        from ansible.modules.network.netscaler import netscaler_lb_vserver

        lb_vserver_proxy_mock = Mock()

        client_mock = Mock()
        m = Mock(return_value=['some'])
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_lb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            ConfigProxy=Mock(return_value=lb_vserver_proxy_mock),
            ensure_feature_is_enabled=Mock(),
            lb_vserver_exists=Mock(side_effect=[True, True]),
            lb_vserver_identical=Mock(side_effect=[False]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            get_immutables_intersection=m,
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_lb_vserver
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('Cannot update immutable attributes'),
                msg='Did not handle immutables error correctly',
            )
