
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


class TestNetscalerServicegroupModule(TestModule):

    @classmethod
    def setUpClass(cls):
        class MockException(Exception):
            pass
        cls.MockException = MockException
        m = MagicMock()
        cls.servicegroup_mock = MagicMock()
        cls.servicegroup_mock.__class__ = MagicMock()
        nssrc_modules_mock = {
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup.servicegroup': cls.servicegroup_mock,
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup_servicegroupmember_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup_servicegroupmember_binding.servicegroup_servicegroupmember_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup_lbmonitor_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic.servicegroup_lbmonitor_binding.servicegroup_lbmonitor_binding': m,

            'nssrc.com.citrix.netscaler.nitro.resource.config.lb': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbmonitor_servicegroup_binding': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.lb.lbmonitor_servicegroup_binding.lbmonitor_servicegroup_binding': m
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

        # Setup minimal required arguments to pass AnsibleModule argument parsing

    def tearDown(self):
        self.nitro_base_patcher.stop()
        self.nitro_specific_patcher.stop()

    def test_graceful_nitro_api_import_error(self):
        # Stop nitro api patching to cause ImportError
        self.set_module_state('present')
        self.nitro_base_patcher.stop()
        self.nitro_specific_patcher.stop()
        from ansible.modules.network.netscaler import netscaler_servicegroup
        self.module = netscaler_servicegroup
        result = self.failed()
        self.assertEqual(result['msg'], 'Could not load nitro python sdk')

    def test_graceful_nitro_error_on_login(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        client_mock = Mock()
        client_mock.login = Mock(side_effect=MockException)
        m = Mock(return_value=client_mock)
        with patch('ansible.modules.network.netscaler.netscaler_servicegroup.get_nitro_client', m):
            with patch('ansible.modules.network.netscaler.netscaler_servicegroup.nitro_exception', MockException):
                self.module = netscaler_servicegroup
                result = self.failed()
                self.assertTrue(result['msg'].startswith('nitro exception'), msg='nitro exception during login not handled properly')

    def test_graceful_no_connection_error(self):

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup

        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.ConnectionError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            get_nitro_client=m,
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Connection error'), msg='Connection error was not handled gracefully')

    def test_graceful_login_error(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')

        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.SSLError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            get_nitro_client=m,
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertTrue(result['msg'].startswith('SSL Error'), msg='SSL Error was not handled gracefully')

    def test_create_non_existing_servicegroup(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        servicegroup_exists_mock = Mock(side_effect=[False, True])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=servicegroup_exists_mock,
            servicemembers_identical=Mock(side_effect=[False, True]),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_servicegroup
            result = self.exited()
            servicegroup_proxy_mock.assert_has_calls([call.add()])
            self.assertTrue(result['changed'], msg='Change not recorded')

    def test_update_servicegroup_when_servicegroup_differs(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        servicegroup_exists_mock = Mock(side_effect=[True, True])
        servicegroup_identical_mock = Mock(side_effect=[False, True])
        monitor_bindings_identical_mock = Mock(side_effect=[True, True])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=servicegroup_exists_mock,
            servicegroup_identical=servicegroup_identical_mock,
            monitor_bindings_identical=monitor_bindings_identical_mock,
            servicemembers_identical=Mock(side_effect=[True, True]),
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_servicegroup
            result = self.exited()
            servicegroup_proxy_mock.assert_has_calls([call.update()])
            self.assertTrue(result['changed'], msg='Change not recorded')

    def test_update_servicegroup_when_monitor_bindings_differ(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        servicegroup_exists_mock = Mock(side_effect=[True, True])
        servicegroup_identical_mock = Mock(side_effect=[True, True])
        monitor_bindings_identical_mock = Mock(side_effect=[False, True])
        sync_monitor_bindings_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=servicegroup_exists_mock,
            servicegroup_identical=servicegroup_identical_mock,
            monitor_bindings_identical=monitor_bindings_identical_mock,
            nitro_exception=self.MockException,
            servicemembers_identical=Mock(side_effect=[True, True]),
            sync_monitor_bindings=sync_monitor_bindings_mock,
        ):
            self.module = netscaler_servicegroup
            result = self.exited()
        # poor man's assert_called_once since python3.5 does not implement that mock method
        self.assertEqual(len(sync_monitor_bindings_mock.mock_calls), 1, msg='sync monitor bindings not called once')
        self.assertTrue(result['changed'], msg='Change not recorded')

    def test_update_servicegroup_when_service_members_differ(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        sync_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=Mock(side_effect=[True, True]),
            servicegroup_identical=Mock(side_effect=[True, True]),
            monitor_bindings_identical=Mock(side_effect=[True, True]),
            sync_monitor_bindings=Mock(),
            servicemembers_identical=Mock(side_effect=[False, True]),
            sync_service_members=sync_mock,

        ):
            self.module = netscaler_servicegroup
            result = self.exited()
        # poor man's assert_called_once since python3.5 does not implement that mock method
        self.assertEqual(len(sync_mock.mock_calls), 1, msg='sync monitor bindings not called once')
        self.assertTrue(result['changed'], msg='Change not recorded')

    def test_immutables_changed(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=Mock(side_effect=[True, True]),
            servicegroup_identical=Mock(side_effect=[False, True]),
            get_immutables_intersection=Mock(return_value=['some']),
            nitro_exception=self.MockException,

        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Cannot update immutable attributes'))

    def test_servicegroup_exists_sanity(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        sync_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=Mock(side_effect=[False, False]),
            servicegroup_identical=Mock(side_effect=[False, False]),
            monitor_bindings_identical=Mock(side_effect=[True, True]),
            sync_monitor_bindings=Mock(),
            servicemembers_identical=Mock(side_effect=[False, True]),
            nitro_exception=self.MockException,
            sync_service_members=sync_mock,

        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertEqual(result['msg'], 'Service group is not present')

    def test_servicegroup_differ_sanity(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        sync_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=Mock(side_effect=[True, True]),
            servicegroup_identical=Mock(side_effect=[False, False]),
            monitor_bindings_identical=Mock(side_effect=[True, True]),
            sync_monitor_bindings=Mock(),
            servicemembers_identical=Mock(side_effect=[False, True]),
            nitro_exception=self.MockException,
            sync_service_members=sync_mock,

        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertEqual(result['msg'], 'Service group is not identical to configuration')

    def test_servicegroup_servicemembers_differ_sanity(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        sync_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=Mock(side_effect=[True, True]),
            servicegroup_identical=Mock(side_effect=[True, True]),
            monitor_bindings_identical=Mock(side_effect=[True, True]),
            sync_monitor_bindings=Mock(),
            servicemembers_identical=Mock(side_effect=[False, False]),
            nitro_exception=self.MockException,
            sync_service_members=sync_mock,

        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertEqual(result['msg'], 'Service group members differ from configuration')

    def test_servicegroup_monitor_bindings_sanity(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        sync_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=Mock(side_effect=[True, True]),
            servicegroup_identical=Mock(side_effect=[True, True]),
            monitor_bindings_identical=Mock(side_effect=[False, False]),
            sync_monitor_bindings=Mock(),
            servicemembers_identical=Mock(side_effect=[True, True]),
            nitro_exception=self.MockException,
            sync_service_members=sync_mock,

        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertEqual(result['msg'], 'Monitor bindings are not identical')

    def test_no_change_to_module_when_all_identical(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        servicegroup_exists_mock = Mock(side_effect=[True, True])
        servicegroup_identical_mock = Mock(side_effect=[True, True])
        monitor_bindings_identical_mock = Mock(side_effect=[True, True])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=servicegroup_exists_mock,
            servicegroup_identical=servicegroup_identical_mock,
            servicemembers_identical=Mock(side_effect=[True, True]),
            monitor_bindings_identical=monitor_bindings_identical_mock,
            nitro_exception=self.MockException,
        ):
            self.module = netscaler_servicegroup
            result = self.exited()
            self.assertFalse(result['changed'], msg='Erroneous changed status update')

    def test_absent_operation(self):
        self.set_module_state('absent')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        servicegroup_exists_mock = Mock(side_effect=[True, False])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=servicegroup_exists_mock,

        ):
            self.module = netscaler_servicegroup
            result = self.exited()
            servicegroup_proxy_mock.assert_has_calls([call.delete()])
            self.assertTrue(result['changed'], msg='Changed status not set correctly')

    def test_absent_operation_no_change(self):
        self.set_module_state('absent')
        from ansible.modules.network.netscaler import netscaler_servicegroup
        servicegroup_proxy_mock = MagicMock()
        attrs = {
            'diff_object.return_value': {},
        }
        servicegroup_proxy_mock.configure_mock(**attrs)

        m = MagicMock(return_value=servicegroup_proxy_mock)
        servicegroup_exists_mock = Mock(side_effect=[False, False])

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=m,
            servicegroup_exists=servicegroup_exists_mock,

        ):
            self.module = netscaler_servicegroup
            result = self.exited()
            servicegroup_proxy_mock.assert_not_called()
            self.assertFalse(result['changed'], msg='Changed status not set correctly')

    def test_absent_operation_sanity(self):
        self.set_module_state('absent')
        from ansible.modules.network.netscaler import netscaler_servicegroup

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            ConfigProxy=MagicMock(),
            servicegroup_exists=Mock(side_effect=[True, True]),
            nitro_exception=self.MockException,

        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertEqual(result['msg'], 'Service group is present')

    def test_graceful_nitro_exception_operation_present(self):
        self.set_module_state('present')
        from ansible.modules.network.netscaler import netscaler_servicegroup

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            servicegroup_exists=m,
            nitro_exception=MockException
        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation present'
            )

    def test_graceful_nitro_exception_operation_absent(self):
        self.set_module_state('absent')
        from ansible.modules.network.netscaler import netscaler_servicegroup

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_servicegroup',
            servicegroup_exists=m,
            nitro_exception=MockException
        ):
            self.module = netscaler_servicegroup
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation absent'
            )
