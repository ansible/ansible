
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


class TestNetscalerGSLBVserverModule(TestModule):

    @classmethod
    def setUpClass(cls):
        class MockException(Exception):
            pass

        cls.MockException = MockException

        m = MagicMock()
        nssrc_modules_mock = {
            'nssrc.com.citrix.netscaler.nitro.resource.config.gslb': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver.gslbvserver': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver_gslbservice_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver_gslbservice_binding.gslbvserver_gslbservice_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver_domain_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbvserver_domain_binding.gslbvserver_domain_binding': m,
        }

        cls.nitro_specific_patcher = patch.dict(sys.modules, nssrc_modules_mock)
        cls.nitro_base_patcher = nitro_base_patcher

    @classmethod
    def tearDownClass(cls):
        cls.nitro_base_patcher.stop()
        cls.nitro_specific_patcher.stop()

    def setUp(self):
        super(TestNetscalerGSLBVserverModule, self).setUp()

        self.nitro_base_patcher.start()
        self.nitro_specific_patcher.start()

        # Setup minimal required arguments to pass AnsibleModule argument parsing

    def tearDown(self):
        super(TestNetscalerGSLBVserverModule, self).tearDown()

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
        from ansible.modules.network.netscaler import netscaler_gslb_vserver
        self.module = netscaler_gslb_vserver
        result = self.failed()
        self.assertEqual(result['msg'], 'Could not load nitro python sdk')

    def test_graceful_nitro_error_on_login(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        client_mock = Mock()
        client_mock.login = Mock(side_effect=MockException)
        m = Mock(return_value=client_mock)
        with patch('ansible.modules.network.netscaler.netscaler_gslb_vserver.get_nitro_client', m):
            with patch('ansible.modules.network.netscaler.netscaler_gslb_vserver.nitro_exception', MockException):
                self.module = netscaler_gslb_vserver
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
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.ConnectionError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Connection error'), msg='Connection error was not handled gracefully')

    def test_graceful_login_error(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.SSLError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertTrue(result['msg'].startswith('SSL Error'), msg='SSL Error was not handled gracefully')

    def test_ensure_feature_is_enabled_called(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        gslb_service_proxy_mock = Mock()
        ensure_feature_is_enabled_mock = Mock()
        client_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=Mock(return_value=client_mock),
            gslb_vserver_exists=Mock(side_effect=[False, True]),
            gslb_vserver_identical=Mock(side_effect=[True]),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=ensure_feature_is_enabled_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            ConfigProxy=Mock(return_value=gslb_service_proxy_mock),
        ):
            self.module = netscaler_gslb_vserver
            self.exited()
            ensure_feature_is_enabled_mock.assert_called_with(client_mock, 'GSLB')

    def test_save_config_called_on_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        gslb_service_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            gslb_vserver_exists=Mock(side_effect=[False, True]),
            gslb_vserver_identical=Mock(side_effect=[True]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=Mock(return_value=gslb_service_proxy_mock),
        ):
            self.module = netscaler_gslb_vserver
            self.exited()
            self.assertIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_called_on_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        gslb_service_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            gslb_vserver_exists=Mock(side_effect=[True, False]),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=Mock(return_value=gslb_service_proxy_mock),
        ):
            self.module = netscaler_gslb_vserver
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
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        gslb_service_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            gslb_vserver_exists=Mock(side_effect=[False, True]),
            gslb_vserver_identical=Mock(side_effect=[True]),
            nitro_exception=self.MockException,
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=Mock(return_value=gslb_service_proxy_mock),
        ):
            self.module = netscaler_gslb_vserver
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
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        gslb_service_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            gslb_vserver_exists=Mock(side_effect=[True, False]),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=Mock(return_value=gslb_service_proxy_mock),
        ):
            self.module = netscaler_gslb_vserver
            self.exited()
            self.assertNotIn(call.save_config(), client_mock.mock_calls)

    def test_new_gslb_vserver_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            gslb_vserver_exists=Mock(side_effect=[False, True]),
            gslb_vserver_identical=Mock(side_effect=[True]),
            nitro_exception=self.MockException,
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            self.exited()
            gslb_service_proxy_mock.assert_has_calls([call.add()])

    def test_modified_gslb_vserver_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            gslb_vserver_exists=Mock(side_effect=[True, True]),
            gslb_vserver_identical=Mock(side_effect=[False, False, True]),
            ensure_feature_is_enabled=Mock(),
            domain_bindings_identical=Mock(side_effect=[True, True, True]),
            service_bindings_identical=Mock(side_effect=[True, True, True]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            nitro_exception=self.MockException,
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            self.exited()
            gslb_service_proxy_mock.assert_has_calls([call.update()])

    def test_absent_gslb_vserver_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            gslb_vserver_exists=Mock(side_effect=[True, False]),
            gslb_vserver_identical=Mock(side_effect=[False, True]),
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            self.exited()
            gslb_service_proxy_mock.assert_has_calls([call.delete()])

    def test_present_gslb_vserver_identical_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            gslb_vserver_exists=Mock(side_effect=[True, True]),
            gslb_vserver_identical=Mock(side_effect=[True, True]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            self.exited()
            gslb_service_proxy_mock.assert_not_called()

    def test_present_gslb_vserver_domain_bindings_error_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            gslb_vserver_exists=Mock(side_effect=[True, True]),
            gslb_vserver_identical=Mock(side_effect=[True, True, True]),
            domain_bindings_identical=Mock(side_effect=[False, False, False]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'Domain bindings differ from configured')
            self.assertTrue(result['failed'])

    def test_present_gslb_vserver_service_bindings_error_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            gslb_vserver_exists=Mock(side_effect=[True, True]),
            gslb_vserver_identical=Mock(side_effect=[True, True, True]),
            service_bindings_identical=Mock(side_effect=[False, False, False]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'Service bindings differ from configured')
            self.assertTrue(result['failed'])

    def test_absent_gslb_vserver_noop_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            gslb_vserver_exists=Mock(side_effect=[False, False]),
            gslb_vserver_identical=Mock(side_effect=[False, False]),
            nitro_exception=self.MockException,
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            self.exited()
            gslb_service_proxy_mock.assert_not_called()

    def test_present_gslb_vserver_failed_update(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            gslb_vserver_exists=Mock(side_effect=[True, True]),
            gslb_vserver_identical=Mock(side_effect=[False, False, False]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'GSLB Vserver differs from configured')
            self.assertTrue(result['failed'])

    def test_present_gslb_vserver_failed_create(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            do_state_change=Mock(return_value=Mock(errorcode=0)),
            gslb_vserver_exists=Mock(side_effect=[False, False]),
            gslb_vserver_identical=Mock(side_effect=[False, False]),
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'GSLB Vserver does not exist')
            self.assertTrue(result['failed'])

    def test_present_gslb_vserver_update_immutable_attribute(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=['domain']),
            gslb_vserver_exists=Mock(side_effect=[True, True]),
            gslb_vserver_identical=Mock(side_effect=[False, False]),
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'Cannot update immutable attributes [\'domain\']')
            self.assertTrue(result['failed'])

    def test_absent_gslb_vserver_failed_delete(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        glsb_service_proxy_attrs = {
            'diff_object.return_value': {},
        }
        gslb_service_proxy_mock = Mock()
        gslb_service_proxy_mock.configure_mock(**glsb_service_proxy_attrs)
        config_proxy_mock = Mock(return_value=gslb_service_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            gslb_vserver_exists=Mock(side_effect=[True, True]),
            gslb_vserver_identical=Mock(side_effect=[False, False]),
            ensure_feature_is_enabled=Mock(),
            ConfigProxy=config_proxy_mock,
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertEqual(result['msg'], 'GSLB Vserver still exists')
            self.assertTrue(result['failed'])

    def test_graceful_nitro_exception_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='192.0.2.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            gslb_vserver_exists=m,
            ensure_feature_is_enabled=Mock(),
            nitro_exception=MockException
        ):
            self.module = netscaler_gslb_vserver
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
        from ansible.modules.network.netscaler import netscaler_gslb_vserver

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_gslb_vserver',
            gslb_vserver_exists=m,
            ensure_feature_is_enabled=Mock(),
            nitro_exception=MockException
        ):
            self.module = netscaler_gslb_vserver
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation absent'
            )
