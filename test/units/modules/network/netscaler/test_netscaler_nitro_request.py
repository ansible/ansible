
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

from units.compat.mock import patch, Mock, call
from .netscaler_module import TestModule
import copy
import tempfile
import json
import sys
import codecs

from ansible.modules.network.netscaler import netscaler_nitro_request

module_arguments = dict(
    nsip=None,
    nitro_user=None,
    nitro_pass=None,
    nitro_protocol=None,
    validate_certs=None,
    nitro_auth_token=None,
    resource=None,
    name=None,
    attributes=None,
    args=None,
    filter=None,
    operation=None,
    expected_nitro_errorcode=None,
    action=None,
    instance_ip=None,
    instance_name=None,
    instance_id=None,
)


class TestNetscalerNitroRequestModule(TestModule):

    @classmethod
    def setUpClass(cls):
        class MockException(Exception):
            pass

        cls.MockException = MockException

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fail_on_conflicting_authentication_methods(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_user='nsroot',
            nitro_pass='nsroot',
            nitro_auth_token='##DDASKLFDJ',
        ))
        mock_module_instance = Mock(params=args)
        expected_calls = [
            call.fail_json(
                changed=False,
                failed=True,
                msg='Cannot define both authentication token and username/password'
            )
        ]
        module_mock = Mock(return_value=mock_module_instance)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', module_mock):
            netscaler_nitro_request.NitroAPICaller()
            mock_module_instance.assert_has_calls(expected_calls)

    def test_nitro_user_pass_credentials(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_user='nsroot',
            nitro_pass='nsroot',
        ))
        mock_module_instance = Mock(params=args)
        expected_headers = {
            'Content-Type': 'application/json',
            'X-NITRO-USER': 'nsroot',
            'X-NITRO-PASS': 'nsroot',
        }
        module_mock = Mock(return_value=mock_module_instance)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', module_mock):
            instance = netscaler_nitro_request.NitroAPICaller()
            self.assertDictEqual(instance._headers, expected_headers)

    def test_mas_login_headers(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_user='nsroot',
            nitro_pass='nsroot',
            operation='mas_login',
        ))
        mock_module_instance = Mock(params=args)
        expected_headers = {
            'Content-Type': 'application/json',
        }
        module_mock = Mock(return_value=mock_module_instance)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', module_mock):
            instance = netscaler_nitro_request.NitroAPICaller()
            self.assertDictEqual(instance._headers, expected_headers)

    def test_mas_proxy_call_headers_instance_ip(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_auth_token='##ABDB',
            operation='add',
            instance_ip='192.168.1.1',
        ))
        mock_module_instance = Mock(params=args)
        expected_headers = {
            'Content-Type': 'application/json',
            '_MPS_API_PROXY_MANAGED_INSTANCE_IP': args['instance_ip'],
            'Cookie': 'NITRO_AUTH_TOKEN=%s' % args['nitro_auth_token'],
        }
        module_mock = Mock(return_value=mock_module_instance)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', module_mock):
            instance = netscaler_nitro_request.NitroAPICaller()
            self.assertDictEqual(instance._headers, expected_headers)

    def test_mas_proxy_call_headers_instance_id(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_auth_token='##ABDB',
            operation='add',
            instance_id='myid',
        ))
        mock_module_instance = Mock(params=args)
        expected_headers = {
            'Content-Type': 'application/json',
            '_MPS_API_PROXY_MANAGED_INSTANCE_ID': args['instance_id'],
            'Cookie': 'NITRO_AUTH_TOKEN=%s' % args['nitro_auth_token'],
        }
        module_mock = Mock(return_value=mock_module_instance)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', module_mock):
            instance = netscaler_nitro_request.NitroAPICaller()
            self.assertDictEqual(instance._headers, expected_headers)

    def test_mas_proxy_call_headers_instance_name(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_auth_token='##ABDB',
            operation='add',
            instance_name='myname',
        ))
        mock_module_instance = Mock(params=args)
        expected_headers = {
            'Content-Type': 'application/json',
            '_MPS_API_PROXY_MANAGED_INSTANCE_NAME': args['instance_name'],
            'Cookie': 'NITRO_AUTH_TOKEN=%s' % args['nitro_auth_token'],
        }
        module_mock = Mock(return_value=mock_module_instance)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', module_mock):
            instance = netscaler_nitro_request.NitroAPICaller()
            self.assertDictEqual(instance._headers, expected_headers)

    def test_edit_response_data_no_body_success_status(self):
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule'):
            instance = netscaler_nitro_request.NitroAPICaller()
            r = None
            info = {
                'status': 200,
            }
            result = {}
            success_status = 200

            expected_result = {
                'nitro_errorcode': 0,
                'nitro_message': 'Success',
                'nitro_severity': 'NONE',
                'http_response_body': '',
                'http_response_data': info,
            }
            instance.edit_response_data(r, info, result, success_status)
            self.assertDictEqual(result, expected_result)

    def test_edit_response_data_no_body_fail_status(self):
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule'):
            instance = netscaler_nitro_request.NitroAPICaller()
            r = None
            info = {
                'status': 201,
            }
            result = {}
            success_status = 200

            expected_result = {
                'nitro_errorcode': -1,
                'nitro_message': 'HTTP status %s' % info['status'],
                'nitro_severity': 'ERROR',
                'http_response_body': '',
                'http_response_data': info,
            }
            instance.edit_response_data(r, info, result, success_status)
            self.assertDictEqual(result, expected_result)

    def test_edit_response_data_actual_body_data(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_user='nsroot',
            nitro_pass='nsroot',
            nitro_auth_token='##DDASKLFDJ',
        ))
        module_mock = Mock(params=args, from_json=json.loads)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', Mock(return_value=module_mock)):
            with tempfile.TemporaryFile() as r:
                actual_body = {
                    'errorcode': 258,
                    'message': 'Some error',
                    'severity': 'ERROR',
                }
                r.write(codecs.encode(json.dumps(actual_body), 'utf-8'))
                r.seek(0)

                instance = netscaler_nitro_request.NitroAPICaller()
                info = {
                    'status': 200,
                }
                result = {}
                success_status = 200

                expected_result = {
                    'http_response_body': json.dumps(actual_body),
                    'http_response_data': info,
                }
                nitro_data = {}
                for key, value in actual_body.items():
                    nitro_data['nitro_%s' % key] = value
                expected_result.update(nitro_data)

                instance.edit_response_data(r, info, result, success_status)
                self.assertDictEqual(result, expected_result)

    def test_edit_response_data_actual_body_data_irrelevant(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_user='nsroot',
            nitro_pass='nsroot',
            nitro_auth_token='##DDASKLFDJ',
        ))
        module_mock = Mock(params=args, from_json=json.loads)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', Mock(return_value=module_mock)):
            with tempfile.TemporaryFile() as r:
                actual_body = {}
                r.write(codecs.encode(json.dumps(actual_body), 'utf-8'))
                r.seek(0)

                instance = netscaler_nitro_request.NitroAPICaller()
                info = {
                    'status': 200,
                }
                result = {}
                success_status = 200

                expected_result = {
                    'http_response_body': json.dumps(actual_body),
                    'http_response_data': info,
                    'nitro_errorcode': 0,
                    'nitro_message': 'Success',
                    'nitro_severity': 'NONE',
                }

                instance.edit_response_data(r, info, result, success_status)
                self.assertDictEqual(result, expected_result)

    def test_edit_response_data_body_in_info(self):
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_user='nsroot',
            nitro_pass='nsroot',
        ))
        module_mock = Mock(params=args, from_json=json.loads)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', Mock(return_value=module_mock)):
            body = {
                'errorcode': 258,
                'message': 'Numerical error 258',
                'severity': 'ERROR'
            }
            instance = netscaler_nitro_request.NitroAPICaller()
            r = None
            info = {
                'status': 200,
                'body': codecs.encode(json.dumps(body), 'utf-8'),
            }
            result = {}
            success_status = 200

            expected_result = {
                'http_response_body': json.dumps(body),
                'http_response_data': info,
            }

            nitro_data = {}
            for key, value in body.items():
                nitro_data['nitro_%s' % key] = value

            expected_result.update(nitro_data)
            instance.edit_response_data(r, info, result, success_status)
            self.assertDictEqual(result, expected_result)

    def test_handle_get_return_object(self):
        resource = 'lbvserver'
        args = copy.deepcopy(module_arguments)
        args.update(dict(
            nitro_user='nsroot',
            nitro_pass='nsroot',
            resource=resource,
        ))
        resource_data = {
            'property1': 'value1',
            'property2': 'value2',
        }
        module_mock = Mock(params=args, from_json=json.loads)
        with patch('ansible.modules.network.netscaler.netscaler_nitro_request.AnsibleModule', Mock(return_value=module_mock)):
            instance = netscaler_nitro_request.NitroAPICaller()

            data = {resource: resource_data}
            result = {
                'nitro_errorcode': 0,
                'http_response_body': json.dumps(data),
            }
            expected_result = {
                'nitro_object': resource_data
            }
            expected_result.update(result)
            instance.handle_get_return_object(result)
            self.assertDictEqual(result, expected_result)
