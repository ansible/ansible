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

from ansible.modules.storage.netapp.na_ontap_broadcast_domain \
    import NetAppOntapBroadcastDomain as broadcast_domain_module  # module under test

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
        self.type = kind
        self.params = data
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'broadcast_domain':
            xml = self.build_broadcast_domain_info(self.params)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_broadcast_domain_info(broadcast_domain_details):
        ''' build xml data for broadcast_domain info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'net-port-broadcast-domain-info': {
                    'broadcast-domain': broadcast_domain_details['name'],
                    'ipspace': broadcast_domain_details['ipspace'],
                    'mtu': broadcast_domain_details['mtu'],
                    'ports': {
                        'port-info': {
                            'port': 'test_port_1'
                        }
                    }
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
        self.mock_broadcast_domain = {
            'name': 'test_broadcast_domain',
            'mtu': '1000',
            'ipspace': 'Default',
            'ports': 'test_port_1'
        }

    def mock_args(self):
        return {
            'name': self.mock_broadcast_domain['name'],
            'ipspace': self.mock_broadcast_domain['ipspace'],
            'mtu': self.mock_broadcast_domain['mtu'],
            'ports': self.mock_broadcast_domain['ports'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_broadcast_domain_mock_object(self, kind=None, data=None):
        """
        Helper method to return an na_ontap_volume object
        :param kind: passes this param to MockONTAPConnection()
        :param data: passes this param to MockONTAPConnection()
        :return: na_ontap_volume object
        """
        broadcast_domain_obj = broadcast_domain_module()
        broadcast_domain_obj.asup_log_for_cserver = Mock(return_value=None)
        broadcast_domain_obj.cluster = Mock()
        broadcast_domain_obj.cluster.invoke_successfully = Mock()
        if kind is None:
            broadcast_domain_obj.server = MockONTAPConnection()
        else:
            if data is None:
                broadcast_domain_obj.server = MockONTAPConnection(kind='broadcast_domain', data=self.mock_broadcast_domain)
            else:
                broadcast_domain_obj.server = MockONTAPConnection(kind='broadcast_domain', data=data)
        return broadcast_domain_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            broadcast_domain_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_net_route(self):
        ''' Test if get_broadcast_domain returns None for non-existent broadcast_domain '''
        set_module_args(self.mock_args())
        result = self.get_broadcast_domain_mock_object().get_broadcast_domain()
        assert result is None

    def test_create_error_missing_broadcast_domain(self):
        ''' Test if create throws an error if broadcast_domain is not specified'''
        data = self.mock_args()
        del data['name']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_broadcast_domain_mock_object('broadcast_domain').create_broadcast_domain()
        msg = 'missing required arguments: name'
        assert exc.value.args[0]['msg'] == msg

    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.create_broadcast_domain')
    def test_successful_create(self, create_broadcast_domain):
        ''' Test successful create '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_broadcast_domain_mock_object().apply()
        assert exc.value.args[0]['changed']
        create_broadcast_domain.assert_called_with()

    def test_create_idempotency(self):
        ''' Test create idempotency '''
        set_module_args(self.mock_args())
        obj = self.get_broadcast_domain_mock_object('broadcast_domain')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert not exc.value.args[0]['changed']

    def test_modify_mtu(self):
        ''' Test successful modify mtu '''
        data = self.mock_args()
        data['mtu'] = '1200'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_broadcast_domain_mock_object('broadcast_domain').apply()
        assert exc.value.args[0]['changed']

    def test_modify_ipspace_idempotency(self):
        ''' Test modify ipsapce idempotency'''
        data = self.mock_args()
        data['ipspace'] = 'Cluster'
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_broadcast_domain_mock_object('broadcast_domain').apply()
        msg = 'A domain ipspace can not be modified after the domain has been created.'
        assert exc.value.args[0]['msg'] == msg

    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.add_broadcast_domain_ports')
    def test_add_ports(self, add_broadcast_domain_ports):
        ''' Test successful modify ports '''
        data = self.mock_args()
        data['ports'] = 'test_port_1,test_port_2'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_broadcast_domain_mock_object('broadcast_domain').apply()
        assert exc.value.args[0]['changed']
        add_broadcast_domain_ports.assert_called_with(['test_port_2'])

    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.delete_broadcast_domain_ports')
    def test_delete_ports(self, delete_broadcast_domain_ports):
        ''' Test successful modify ports '''
        data = self.mock_args()
        data['ports'] = ''
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_broadcast_domain_mock_object('broadcast_domain').apply()
        assert exc.value.args[0]['changed']
        delete_broadcast_domain_ports.assert_called_with(['test_port_1'])

    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.modify_broadcast_domain')
    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.split_broadcast_domain')
    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.get_broadcast_domain')
    def test_split_broadcast_domain(self, get_broadcast_domain, split_broadcast_domain, modify_broadcast_domain):
        ''' Test successful split broadcast domain '''
        data = self.mock_args()
        data['from_name'] = 'test_broadcast_domain'
        data['name'] = 'test_broadcast_domain_2'
        data['ports'] = 'test_port_2'
        set_module_args(data)
        current = {
            'name': 'test_broadcast_domain',
            'mtu': '1000',
            'ipspace': 'Default',
            'ports': ['test_port_1,test_port2']
        }
        get_broadcast_domain.side_effect = [
            None,
            current,
            current
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_broadcast_domain_mock_object().apply()
        assert exc.value.args[0]['changed']
        modify_broadcast_domain.assert_not_called()
        split_broadcast_domain.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.delete_broadcast_domain')
    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.modify_broadcast_domain')
    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.get_broadcast_domain')
    def test_split_broadcast_domain_modify_delete(self, get_broadcast_domain, modify_broadcast_domain, delete_broadcast_domain):
        ''' Test successful split broadcast domain '''
        data = self.mock_args()
        data['from_name'] = 'test_broadcast_domain'
        data['name'] = 'test_broadcast_domain_2'
        data['ports'] = 'test_port_1,test_port_2'
        data['mtu'] = '1200'
        set_module_args(data)

        current = {
            'name': 'test_broadcast_domain',
            'mtu': '1000',
            'ipspace': 'Default',
            'ports': ['test_port_1,test_port2']
        }
        get_broadcast_domain.side_effect = [
            None,
            current,
            current
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_broadcast_domain_mock_object().apply()
        assert exc.value.args[0]['changed']
        delete_broadcast_domain.assert_called_with('test_broadcast_domain')
        modify_broadcast_domain.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.get_broadcast_domain')
    def test_split_broadcast_domain_not_exist(self, get_broadcast_domain):
        ''' Test successful split broadcast domain '''
        data = self.mock_args()
        data['from_name'] = 'test_broadcast_domain'
        data['name'] = 'test_broadcast_domain_2'
        data['ports'] = 'test_port_2'
        set_module_args(data)

        get_broadcast_domain.side_effect = [
            None,
            None,
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_broadcast_domain_mock_object().apply()
        msg = 'A domain can not be split if it does not exist.'
        assert exc.value.args[0]['msg'], msg

    @patch('ansible.modules.storage.netapp.na_ontap_broadcast_domain.NetAppOntapBroadcastDomain.split_broadcast_domain')
    def test_split_broadcast_domain_idempotency(self, split_broadcast_domain):
        ''' Test successful split broadcast domain '''
        data = self.mock_args()
        data['from_name'] = 'test_broadcast_domain'
        data['ports'] = 'test_port_1'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_broadcast_domain_mock_object('broadcast_domain').apply()
        assert exc.value.args[0]['changed'] is False
        split_broadcast_domain.assert_not_called()
