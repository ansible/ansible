# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test template for ONTAP Ansible module '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_net_routes \
    import NetAppOntapNetRoutes as net_route_module  # module under test

if not netapp_utils.has_netapp_lib():
    pytestmark = pytest.mark.skip('skipping as missing required netapp_lib')


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class MockONTAPConnection(object):
    ''' mock server connection to ONTAP host '''

    def __init__(self, kind=None, data=None):
        ''' save arguments '''
        self.kind = kind
        self.params = data
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.kind == 'net_route':
            xml = self.build_net_route_info(self.params)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_net_route_info(net_route_details):
        ''' build xml data for net_route-attributes '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'attributes': {
                'net-vs-routes-info': {
                    'address-family': 'ipv4',
                    'destination': net_route_details['destination'],
                    'gateway': net_route_details['gateway'],
                    'metric': net_route_details['metric'],
                    'vserver': net_route_details['vserver']
                }
            }
        }
        xml.translate_struct(attributes)
        return xml


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        self.server = MockONTAPConnection()
        self.mock_net_route = {
            'destination': '176.0.0.0/24',
            'gateway': '10.193.72.1',
            'vserver': 'test_vserver',
            'metric': '70'
        }

    def mock_args(self):
        return {
            'vserver': self.mock_net_route['vserver'],
            'destination': self.mock_net_route['destination'],
            'gateway': self.mock_net_route['gateway'],
            'metric': self.mock_net_route['metric'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_net_route_mock_object(self, kind=None, data=None):
        """
        Helper method to return an na_ontap_net_route object
        :param kind: passes this param to MockONTAPConnection()
        :param data: passes this data to  MockONTAPConnection()
        :return: na_ontap_net_route object
        """
        net_route_obj = net_route_module()
        net_route_obj.ems_log_event = Mock(return_value=None)
        net_route_obj.cluster = Mock()
        net_route_obj.cluster.invoke_successfully = Mock()
        if kind is None:
            net_route_obj.server = MockONTAPConnection()
        else:
            if data is None:
                net_route_obj.server = MockONTAPConnection(kind='net_route', data=self.mock_net_route)
            else:
                net_route_obj.server = MockONTAPConnection(kind='net_route', data=data)
        return net_route_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            net_route_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_net_route(self):
        ''' Test if get_net_route returns None for non-existent net_route '''
        set_module_args(self.mock_args())
        result = self.get_net_route_mock_object().get_net_route()
        assert result is None

    def test_get_existing_job(self):
        ''' Test if get_net_route returns details for existing net_route '''
        set_module_args(self.mock_args())
        result = self.get_net_route_mock_object('net_route').get_net_route()
        assert result['destination'] == self.mock_net_route['destination']
        assert result['gateway'] == self.mock_net_route['gateway']

    def test_create_error_missing_param(self):
        ''' Test if create throws an error if destination is not specified'''
        data = self.mock_args()
        del data['destination']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_net_route_mock_object('net_route').create_net_route()
        msg = 'missing required arguments: destination'
        assert exc.value.args[0]['msg'] == msg

    @patch('ansible.modules.storage.netapp.na_ontap_net_routes.NetAppOntapNetRoutes.create_net_route')
    def test_successful_create(self, create_net_route):
        ''' Test successful create '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object().apply()
        assert exc.value.args[0]['changed']
        create_net_route.assert_called_with()

    def test_create_idempotency(self):
        ''' Test create idempotency '''
        set_module_args(self.mock_args())
        obj = self.get_net_route_mock_object('net_route')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert not exc.value.args[0]['changed']

    def test_successful_delete(self):
        ''' Test successful delete '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object('net_route').apply()
        assert exc.value.args[0]['changed']

    def test_delete_idempotency(self):
        ''' Test delete idempotency '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object().apply()
        assert not exc.value.args[0]['changed']

    def test_successful_modify_metric(self):
        ''' Test successful modify metric '''
        data = self.mock_args()
        del data['metric']
        data['from_metric'] = '70'
        data['metric'] = '40'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object('net_route').apply()
        assert exc.value.args[0]['changed']

    def test_modify_metric_idempotency(self):
        ''' Test modify metric idempotency'''
        data = self.mock_args()
        data['metric'] = '70'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object('net_route').apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_net_routes.NetAppOntapNetRoutes.get_net_route')
    def test_successful_modify_gateway(self, get_net_route):
        ''' Test successful modify gateway '''
        data = self.mock_args()
        del data['gateway']
        data['from_gateway'] = '10.193.72.1'
        data['gateway'] = '10.193.0.1'
        set_module_args(data)
        current = {
            'destination': '176.0.0.0/24',
            'gateway': '10.193.72.1',
            'metric': '70',
            'vserver': 'test_server'
        }
        get_net_route.side_effect = [
            None,
            current
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object().apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_net_routes.NetAppOntapNetRoutes.get_net_route')
    def test__modify_gateway_idempotency(self, get_net_route):
        ''' Test modify gateway idempotency '''
        data = self.mock_args()
        del data['gateway']
        data['from_gateway'] = '10.193.72.1'
        data['gateway'] = '10.193.0.1'
        set_module_args(data)
        current = {
            'destination': '178.0.0.1/24',
            'gateway': '10.193.72.1',
            'metric': '70',
            'vserver': 'test_server'
        }
        get_net_route.side_effect = [
            current,
            None
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object('net_route', current).apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_net_routes.NetAppOntapNetRoutes.get_net_route')
    def test_successful_modify_destination(self, get_net_route):
        ''' Test successful modify destination '''
        data = self.mock_args()
        del data['destination']
        data['from_destination'] = '176.0.0.0/24'
        data['destination'] = '178.0.0.1/24'
        set_module_args(data)
        current = {
            'destination': '176.0.0.0/24',
            'gateway': '10.193.72.1',
            'metric': '70',
            'vserver': 'test_server'
        }
        get_net_route.side_effect = [
            None,
            current
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object().apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_net_routes.NetAppOntapNetRoutes.get_net_route')
    def test__modify_destination_idempotency(self, get_net_route):
        ''' Test modify destination idempotency'''
        data = self.mock_args()
        del data['destination']
        data['from_destination'] = '176.0.0.0/24'
        data['destination'] = '178.0.0.1/24'
        set_module_args(data)
        current = {
            'destination': '178.0.0.1/24',
            'gateway': '10.193.72.1',
            'metric': '70',
            'vserver': 'test_server'
        }
        get_net_route.side_effect = [
            current,
            None
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_net_route_mock_object('net_route', current).apply()
        assert not exc.value.args[0]['changed']
