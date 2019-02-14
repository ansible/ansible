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

from ansible.modules.storage.netapp.na_ontap_net_port \
    import NetAppOntapNetPort as port_module  # module under test

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
        if self.type == 'port':
            xml = self.build_port_info(self.data)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_port_info(port_details):
        ''' build xml data for net-port-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'net-port-info': {
                    # 'port': port_details['port'],
                    'mtu': port_details['mtu'],
                    'is-administrative-auto-negotiate': 'true',
                    'ipspace': 'default',
                    'administrative-flowcontrol': port_details['flowcontrol_admin'],
                    'node': port_details['node']
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
        self.mock_port = {
            'node': 'test',
            'ports': 'a1',
            'flowcontrol_admin': 'something',
            'mtu': '1000'
        }

    def mock_args(self):
        return {
            'node': self.mock_port['node'],
            'flowcontrol_admin': self.mock_port['flowcontrol_admin'],
            'ports': [self.mock_port['ports']],
            'mtu': self.mock_port['mtu'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_port_mock_object(self, kind=None, data=None):
        """
        Helper method to return an na_ontap_net_port object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_net_port object
        """
        obj = port_module()
        obj.autosupport_log = Mock(return_value=None)
        if data is None:
            data = self.mock_port
        obj.server = MockONTAPConnection(kind=kind, data=data)
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            port_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_port(self):
        ''' Test if get_net_port returns None for non-existent port '''
        set_module_args(self.mock_args())
        result = self.get_port_mock_object().get_net_port('test')
        assert result is None

    def test_get_existing_port(self):
        ''' Test if get_net_port returns details for existing port '''
        set_module_args(self.mock_args())
        result = self.get_port_mock_object('port').get_net_port('test')
        assert result['mtu'] == self.mock_port['mtu']
        assert result['flowcontrol_admin'] == self.mock_port['flowcontrol_admin']

    def test_successful_modify(self):
        ''' Test modify_net_port '''
        data = self.mock_args()
        data['mtu'] = '2000'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object('port').apply()
        assert exc.value.args[0]['changed']

    def test_successful_modify_multiple_ports(self):
        ''' Test modify_net_port '''
        data = self.mock_args()
        data['ports'] = ['a1', 'a2']
        data['mtu'] = '2000'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object('port').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_net_port.NetAppOntapNetPort.get_net_port')
    def test_get_called(self, get_port):
        ''' Test get_net_port '''
        data = self.mock_args()
        data['ports'] = ['a1', 'a2']
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object('port').apply()
        assert get_port.call_count == 2
