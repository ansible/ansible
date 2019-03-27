''' unit test template for ONTAP Ansible module '''

from __future__ import print_function
import json
import pytest

import time
from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_service_processor_network \
    import NetAppOntapServiceProcessorNetwork as sp_module  # module under test

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
        self.data = data
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.kind == 'sp-enabled':
            xml = self.build_sp_info(self.data)
        elif self.kind == 'sp-disabled':
            xml = self.build_sp_disabled_info(self.data)
        else:
            xml = self.build_info()
        self.xml_out = xml
        return xml

    @staticmethod
    def build_sp_info(sp):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list':
            {
                'service-processor-network-info':
                {
                    'node-name': sp['node'],
                    'is-enabled': 'true',
                    'address-type': sp['address_type'],
                    'dhcp': 'v4',
                    'gateway-ip-address': sp['gateway_ip_address'],
                    'netmask': sp['netmask'],
                    'ip-address': sp['ip_address'],
                    'setup-status': 'succeeded',
                }
            }
        }
        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_info():
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 0
        }
        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_sp_disabled_info(sp):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list':
            {
                'service-processor-network-info':
                {
                    'node-name': sp['node'],
                    'is-enabled': 'false',
                    'address-type': sp['address_type'],
                    'setup-status': 'not_setup',
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
        self.mock_sp = {
            'node': 'test-vsim1',
            'gateway_ip_address': '2.2.2.2',
            'address_type': 'ipv4',
            'ip_address': '1.1.1.1',
            'netmask': '255.255.248.0',
            'dhcp': 'v4'
        }

    def mock_args(self, enable=True):
        data = {
            'node': self.mock_sp['node'],
            'is_enabled': enable,
            'address_type': self.mock_sp['address_type'],
            'hostname': 'host',
            'username': 'admin',
            'password': 'password',
        }
        if enable is True:
            data['ip_address'] = self.mock_sp['ip_address']
            data['gateway_ip_address'] = self.mock_sp['gateway_ip_address']
            data['netmask'] = self.mock_sp['netmask']
            data['dhcp'] = 'v4'
        return data

    def get_sp_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_volume object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_volume object
        """
        sp_obj = sp_module()
        sp_obj.autosupport_log = Mock(return_value=None)
        if kind is None:
            sp_obj.server = MockONTAPConnection()
        else:
            sp_obj.server = MockONTAPConnection(kind=kind, data=self.mock_sp)
        return sp_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            sp_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_modify_error_on_disabled_sp(self):
        ''' a more interesting test '''
        data = self.mock_args(enable=False)
        data['ip_address'] = self.mock_sp['ip_address']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_sp_mock_object('sp-disabled').apply()
        assert 'Error: Cannot modify a service processor network if it is disabled.' in \
               exc.value.args[0]['msg']

    def test_modify_sp(self):
        ''' a more interesting test '''
        data = self.mock_args()
        data['ip_address'] = '3.3.3.3'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_sp_mock_object('sp-enabled').apply()
        assert exc.value.args[0]['changed']

    def test_modify_sp_wait(self):
        ''' a more interesting test '''
        data = self.mock_args()
        data['ip_address'] = '3.3.3.3'
        data['wait_for_completion'] = True
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_sp_mock_object('sp-enabled').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_service_processor_network.NetAppOntapServiceProcessorNetwork.'
           'get_service_processor_network')
    def test_non_existing_sp(self, get_sp):
        set_module_args(self.mock_args())
        get_sp.return_value = None
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_sp_mock_object().apply()
        assert 'Error No Service Processor for node: test-vsim1' in exc.value.args[0]['msg']

    @patch('ansible.modules.storage.netapp.na_ontap_service_processor_network.NetAppOntapServiceProcessorNetwork.'
           'get_sp_network_status')
    @patch('time.sleep')
    def test_wait_on_sp_status(self, get_sp, sleep):
        data = self.mock_args()
        data['gateway_ip_address'] = '4.4.4.4'
        data['wait_for_completion'] = True
        set_module_args(data)
        get_sp.side_effect = ['in_progress', 'done']
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_sp_mock_object('sp-enabled').apply()
        sleep.assert_called_once_with()
        assert exc.value.args[0]['changed']
