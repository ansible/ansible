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

from ansible.modules.storage.netapp.na_ontap_interface \
    import NetAppOntapInterface as interface_module  # module under test

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
        if self.type == 'interface':
            xml = self.build_interface_info(self.params)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_interface_info(data):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'net-interface-info': {
                    'interface-name': data['name'],
                    'administrative-status': data['administrative-status'],
                    'failover-policy': data['failover-policy'],
                    'firewall-policy': data['firewall-policy'],
                    'is-auto-revert': data['is-auto-revert'],
                    'home-node': data['home_node'],
                    'home-port': data['home_port'],
                    'address': data['address'],
                    'netmask': data['netmask'],
                    'role': data['role'],
                    'protocols': data['protocols'] if data.get('protocols') else None,
                    'dns-domain-name': data['dns_domain_name'],
                    'listen-for-dns_query': data['listen_for_dns_query'],
                    'is-dns-update-enabled': data['is_dns_update_enabled']
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
        self.mock_interface = {
            'name': 'test_lif',
            'administrative-status': 'up',
            'failover-policy': 'up',
            'firewall-policy': 'up',
            'is-auto-revert': 'true',
            'home_node': 'node',
            'role': 'test',
            'home_port': 'e0c',
            'address': '2.2.2.2',
            'netmask': '1.1.1.1',
            'dns_domain_name': 'test.com',
            'listen_for_dns_query': True,
            'is_dns_update_enabled': True
        }

    def mock_args(self):
        return {
            'vserver': 'vserver',
            'interface_name': self.mock_interface['name'],
            'home_node': self.mock_interface['home_node'],
            'role': self.mock_interface['role'],
            'home_port': self.mock_interface['home_port'],
            'address': self.mock_interface['address'],
            'netmask': self.mock_interface['netmask'],
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
        }

    def get_interface_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_interface object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_interface object
        """
        interface_obj = interface_module()
        interface_obj.autosupport_log = Mock(return_value=None)
        if kind is None:
            interface_obj.server = MockONTAPConnection()
        else:
            interface_obj.server = MockONTAPConnection(kind=kind, data=self.mock_interface)
        return interface_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            interface_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_create_error_missing_param(self):
        ''' Test if create throws an error if required param 'role' is not specified'''
        data = self.mock_args()
        del data['role']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_interface_mock_object('interface').create_interface()
        msg = 'Error: Missing one or more required parameters for creating interface: ' \
              'home_port, netmask, role, home_node, address'
        expected = sorted(','.split(msg))
        received = sorted(','.split(exc.value.args[0]['msg']))
        assert expected == received

    def test_get_nonexistent_interface(self):
        ''' Test if get_interface returns None for non-existent interface '''
        set_module_args(self.mock_args())
        result = self.get_interface_mock_object().get_interface()
        assert result is None

    def test_get_existing_interface(self):
        ''' Test if get_interface returns None for existing interface '''
        set_module_args(self.mock_args())
        result = self.get_interface_mock_object(kind='interface').get_interface()
        assert result['interface_name'] == self.mock_interface['name']

    def test_successful_create(self):
        ''' Test successful create '''
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_interface_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_successful_create_for_NVMe(self):
        ''' Test successful create for NVMe protocol'''
        data = self.mock_args()
        data['protocols'] = 'fc-nvme'
        del data['address']
        del data['netmask']
        del data['home_port']
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_interface_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_create_idempotency_for_NVMe(self):
        ''' Test create idempotency for NVMe protocol '''
        data = self.mock_args()
        data['protocols'] = 'fc-nvme'
        del data['address']
        del data['netmask']
        del data['home_port']
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_interface_mock_object('interface').apply()
        assert not exc.value.args[0]['changed']

    def test_create_error_for_NVMe(self):
        ''' Test if create throws an error if required param 'protocols' uses NVMe'''
        data = self.mock_args()
        data['protocols'] = 'fc-nvme'
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_interface_mock_object('interface').create_interface()
        msg = 'Error: Following parameters for creating interface are not supported for data-protocol fc-nvme: ' \
              'netmask, firewall_policy, address'
        expected = sorted(','.split(msg))
        received = sorted(','.split(exc.value.args[0]['msg']))
        assert expected == received

    def test_create_idempotency(self):
        ''' Test create idempotency '''
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_interface_mock_object('interface').apply()
        assert not exc.value.args[0]['changed']

    def test_successful_delete(self):
        ''' Test delete existing interface '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_interface_mock_object('interface').apply()
        assert exc.value.args[0]['changed']

    def test_delete_idempotency(self):
        ''' Test delete idempotency '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_interface_mock_object().apply()
        assert not exc.value.args[0]['changed']

    def test_successful_modify(self):
        ''' Test successful modify interface_minutes '''
        data = self.mock_args()
        data['home_port'] = 'new_port'
        data['dns_domain_name'] = 'test2.com'
        data['listen_for_dns_query'] = False
        data['is_dns_update_enabled'] = False
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            interface_obj = self.get_interface_mock_object('interface')
            interface_obj.apply()
        assert exc.value.args[0]['changed']

    def test_modify_idempotency(self):
        ''' Test modify idempotency '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_interface_mock_object('interface').apply()
        assert not exc.value.args[0]['changed']
