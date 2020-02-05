# (c) 2019, NetApp, Inc
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

from ansible.modules.storage.netapp.na_ontap_security_key_manager \
    import NetAppOntapSecurityKeyManager as key_manager_module  # module under test

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
        self.data = data
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'key_manager':
            xml = self.build_port_info(self.data)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_port_info(key_manager_details):
        ''' build xml data for-key-manager-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'key-manager-info': {
                    'key-manager-ip-address': '0.0.0.0',
                    'key-manager-server-status': 'available',
                    'key-manager-tcp-port': '5696',
                    'node-name': 'test_node'
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
        self.mock_key_manager = {
            'node_name': 'test_node',
            'tcp_port': 5696,
            'ip_address': '0.0.0.0',
            'server_status': 'available'
        }

    def mock_args(self):
        return {
            'node': self.mock_key_manager['node_name'],
            'tcp_port': self.mock_key_manager['tcp_port'],
            'ip_address': self.mock_key_manager['ip_address'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'https': 'False'
        }

    def get_key_manager_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_security_key_manager object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_security_key_manager object
        """
        obj = key_manager_module()
        obj.asup_log_for_cserver = Mock(return_value=None)
        obj.cluster = Mock()
        obj.cluster.invoke_successfully = Mock()
        if kind is None:
            obj.cluster = MockONTAPConnection()
        else:
            obj.cluster = MockONTAPConnection(kind=kind, data=self.mock_key_manager)
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            key_manager_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_key_manager(self):
        ''' Test if get_key_manager() returns None for non-existent key manager '''
        set_module_args(self.mock_args())
        result = self.get_key_manager_mock_object().get_key_manager()
        assert result is None

    def test_get_existing_key_manager(self):
        ''' Test if get_key_manager() returns details for existing key manager '''
        set_module_args(self.mock_args())
        result = self.get_key_manager_mock_object('key_manager').get_key_manager()
        assert result['ip_address'] == self.mock_key_manager['ip_address']

    @patch('ansible.modules.storage.netapp.na_ontap_security_key_manager.NetAppOntapSecurityKeyManager.get_key_manager')
    def test_successfully_add_key_manager(self, get_key_manager):
        ''' Test successfully add key manager'''
        data = self.mock_args()
        data['state'] = 'present'
        set_module_args(data)
        get_key_manager.side_effect = [
            None
        ]
        obj = self.get_key_manager_mock_object('key_manager')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    def test_successfully_delete_key_manager(self):
        ''' Test successfully delete key manager'''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        obj = self.get_key_manager_mock_object('key_manager')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']
