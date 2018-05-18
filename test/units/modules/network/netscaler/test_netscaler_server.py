
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


class TestNetscalerServerModule(TestModule):

    @classmethod
    def setUpClass(cls):
        class MockException(Exception):
            pass

        cls.MockException = MockException

        m = MagicMock()
        cls.server_mock = MagicMock()
        cls.server_mock.__class__ = MagicMock(add=Mock())
        nssrc_modules_mock = {
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic.server': m,
            'nssrc.com.citrix.netscaler.nitro.resource.config.basic.server.server': cls.server_mock,
        }

        cls.nitro_specific_patcher = patch.dict(sys.modules, nssrc_modules_mock)
        cls.nitro_base_patcher = nitro_base_patcher

    @classmethod
    def tearDownClass(cls):
        cls.nitro_base_patcher.stop()
        cls.nitro_specific_patcher.stop()

    def setUp(self):
        super(TestNetscalerServerModule, self).setUp()
        self.nitro_base_patcher.start()
        self.nitro_specific_patcher.start()

        # Setup minimal required arguments to pass AnsibleModule argument parsing

    def tearDown(self):
        super(TestNetscalerServerModule, self).tearDown()
        self.nitro_base_patcher.stop()
        self.nitro_specific_patcher.stop()

    def test_graceful_nitro_api_import_error(self):
        # Stop nitro api patching to cause ImportError
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        self.nitro_base_patcher.stop()
        self.nitro_specific_patcher.stop()
        from ansible.modules.network.netscaler import netscaler_server
        self.module = netscaler_server
        result = self.failed()
        self.assertEqual(result['msg'], 'Could not load nitro python sdk')

    def test_graceful_nitro_error_on_login(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        client_mock = Mock()
        client_mock.login = Mock(side_effect=MockException)
        m = Mock(return_value=client_mock)
        with patch('ansible.modules.network.netscaler.netscaler_server.get_nitro_client', m):
            with patch('ansible.modules.network.netscaler.netscaler_server.nitro_exception', MockException):
                self.module = netscaler_server
                result = self.failed()
                self.assertTrue(result['msg'].startswith('nitro exception'), msg='nitro exception during login not handled properly')

    def test_graceful_no_connection_error(self):

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.ConnectionError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertTrue(result['msg'].startswith('Connection error'), msg='Connection error was not handled gracefully')

    def test_graceful_login_error(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        if sys.version_info[:2] == (2, 6):
            self.skipTest('requests library not available under python2.6')

        class MockException(Exception):
            pass
        client_mock = Mock()
        attrs = {'login.side_effect': requests.exceptions.SSLError}
        client_mock.configure_mock(**attrs)
        m = Mock(return_value=client_mock)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            nitro_exception=MockException,
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertTrue(result['msg'].startswith('SSL Error'), msg='SSL Error was not handled gracefully')

    def test_save_config_called_on_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            server_exists=Mock(side_effect=[False, True]),
            ConfigProxy=Mock(return_value=server_proxy_mock),
            diff_list=Mock(return_value={}),
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            self.assertIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_called_on_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            server_exists=Mock(side_effect=[True, False]),
            ConfigProxy=Mock(return_value=server_proxy_mock),
            diff_list=Mock(return_value={}),
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            self.assertIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_not_called_on_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            server_exists=Mock(side_effect=[False, True]),
            ConfigProxy=Mock(return_value=server_proxy_mock),
            diff_list=Mock(return_value={}),
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            self.assertNotIn(call.save_config(), client_mock.mock_calls)

    def test_save_config_not_called_on_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='absent',
            save_config=False,
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            server_exists=Mock(side_effect=[True, False]),
            ConfigProxy=Mock(return_value=server_proxy_mock),
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            self.assertNotIn(call.save_config(), client_mock.mock_calls)

    def test_do_state_change_fail(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_mock = Mock()

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            server_exists=Mock(side_effect=[True, False]),
            ConfigProxy=Mock(return_value=server_proxy_mock),
            diff_list=Mock(return_value={}),
            do_state_change=Mock(return_value=Mock(errorcode=1, message='Failed on purpose'))
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertEqual(result['msg'], 'Error when setting disabled state. errorcode: 1 message: Failed on purpose')

    def test_disable_server_graceful(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
            disabled=True,
            graceful=True
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_mock = Mock()

        d = {
            'graceful': True,
            'delay': 20,
        }
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value=d),
            get_immutables_intersection=Mock(return_value=[]),
            server_exists=Mock(side_effect=[True, True]),
            ConfigProxy=Mock(return_value=server_proxy_mock),
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            result = self.exited()
            self.assertEqual(d, {}, 'Graceful disable options were not discarded from the diff_list with the actual object')

    def test_new_server_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            server_exists=Mock(side_effect=[False, True]),
            server_identical=Mock(side_effect=[True]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            server_proxy_mock.assert_has_calls([call.add()])

    def test_modified_server_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            server_exists=Mock(side_effect=[True, True]),
            server_identical=Mock(side_effect=[False, True]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            server_proxy_mock.assert_has_calls([call.update()])

    def test_absent_server_execution_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            server_exists=Mock(side_effect=[True, False]),
            server_identical=Mock(side_effect=[False, True]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            server_proxy_mock.assert_has_calls([call.delete()])

    def test_present_server_identical_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            server_exists=Mock(side_effect=[True, True]),
            server_identical=Mock(side_effect=[True, True]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            server_proxy_mock.assert_not_called()

    def test_absent_server_noop_flow(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            server_exists=Mock(side_effect=[False, False]),
            server_identical=Mock(side_effect=[False, False]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            self.exited()
            server_proxy_mock.assert_not_called()

    def test_present_server_failed_update(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            server_exists=Mock(side_effect=[True, True]),
            server_identical=Mock(side_effect=[False, False]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertEqual(result['msg'], 'Server is not configured according to parameters given')
            self.assertTrue(result['failed'])

    def test_present_server_failed_create(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            server_exists=Mock(side_effect=[False, False]),
            server_identical=Mock(side_effect=[False, False]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertEqual(result['msg'], 'Server does not seem to exist')
            self.assertTrue(result['failed'])

    def test_present_server_update_immutable_attribute(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=['domain']),
            server_exists=Mock(side_effect=[True, True]),
            server_identical=Mock(side_effect=[False, False]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertEqual(result['msg'], 'Cannot update immutable attributes [\'domain\']')
            self.assertTrue(result['failed'])

    def test_absent_server_failed_delete(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        client_mock = Mock()

        m = Mock(return_value=client_mock)

        server_proxy_attrs = {
            'diff_object.return_value': {},
        }
        server_proxy_mock = Mock()
        server_proxy_mock.configure_mock(**server_proxy_attrs)
        config_proxy_mock = Mock(return_value=server_proxy_mock)

        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            nitro_exception=self.MockException,
            get_nitro_client=m,
            diff_list=Mock(return_value={}),
            get_immutables_intersection=Mock(return_value=[]),
            server_exists=Mock(side_effect=[True, True]),
            server_identical=Mock(side_effect=[False, False]),
            ConfigProxy=config_proxy_mock,
            do_state_change=Mock(return_value=Mock(errorcode=0))
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertEqual(result['msg'], 'Server seems to be present')
            self.assertTrue(result['failed'])

    def test_graceful_nitro_exception_state_present(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='present',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            server_exists=m,
            nitro_exception=MockException
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation absent'
            )

    def test_graceful_nitro_exception_state_absent(self):
        set_module_args(dict(
            nitro_user='user',
            nitro_pass='pass',
            nsip='1.1.1.1',
            state='absent',
        ))
        from ansible.modules.network.netscaler import netscaler_server

        class MockException(Exception):
            def __init__(self, *args, **kwargs):
                self.errorcode = 0
                self.message = ''

        m = Mock(side_effect=MockException)
        with patch.multiple(
            'ansible.modules.network.netscaler.netscaler_server',
            server_exists=m,
            nitro_exception=MockException
        ):
            self.module = netscaler_server
            result = self.failed()
            self.assertTrue(
                result['msg'].startswith('nitro exception'),
                msg='Nitro exception not caught on operation absent'
            )
