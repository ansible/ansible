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

from ansible.modules.storage.netapp.na_ontap_firewall_policy \
    import NetAppONTAPFirewallPolicy as fp_module  # module under test

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
        if self.kind == 'policy':
            xml = self.build_policy_info(self.data)
        if self.kind == 'config':
            xml = self.build_firewall_config_info(self.data)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_policy_info(data):
        ''' build xml data for net-firewall-policy-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'net-firewall-policy-info': {
                    'policy': data['policy'],
                    'service': data['service'],
                    'allow-list': [
                        {'ip-and-mask': '1.2.3.0/24'}
                    ]
                }
            }
        }

        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_firewall_config_info(data):
        ''' build xml data for net-firewall-config-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'attributes': {
                'net-firewall-config-info': {
                    'is-enabled': 'true',
                    'is-logging': 'false'
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
        self.mock_policy = {
            'policy': 'test',
            'service': 'http',
            'vserver': 'my_vserver',
            'allow_list': '1.2.3.0/24'
        }
        self.mock_config = {
            'node': 'test',
            'enable': 'enable',
            'logging': 'enable'
        }

    def mock_policy_args(self):
        return {
            'policy': self.mock_policy['policy'],
            'service': self.mock_policy['service'],
            'vserver': self.mock_policy['vserver'],
            'allow_list': [self.mock_policy['allow_list']],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def mock_config_args(self):
        return {
            'node': self.mock_config['node'],
            'enable': self.mock_config['enable'],
            'logging': self.mock_config['logging'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_firewall_policy object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_firewall_policy object
        """
        obj = fp_module()
        obj.autosupport_log = Mock(return_value=None)
        if kind is None:
            obj.server = MockONTAPConnection()
        else:
            mock_data = self.mock_config if kind == 'config' else self.mock_policy
            obj.server = MockONTAPConnection(kind=kind, data=mock_data)
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            fp_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_helper_firewall_policy_attributes(self):
        ''' helper returns dictionary with vserver, service and policy details '''
        data = self.mock_policy
        set_module_args(self.mock_policy_args())
        result = self.get_mock_object('policy').firewall_policy_attributes()
        del data['allow_list']
        assert data == result

    def test_helper_validate_ip_addresses_positive(self):
        ''' test if helper validates if IP is a network address '''
        data = self.mock_policy_args()
        data['allow_list'] = ['1.2.0.0/16', '1.2.3.0/24']
        set_module_args(data)
        result = self.get_mock_object().validate_ip_addresses()
        assert result is None

    def test_helper_validate_ip_addresses_negative(self):
        ''' test if helper validates if IP is a network address '''
        data = self.mock_policy_args()
        data['allow_list'] = ['1.2.0.10/16', '1.2.3.0/24']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_mock_object().validate_ip_addresses()
        msg = 'Error: Invalid IP address value for allow_list parameter.' \
              'Please specify a network address without host bits set: ' \
              '1.2.0.10/16 has host bits set'
        assert exc.value.args[0]['msg'] == msg

    def test_get_nonexistent_policy(self):
        ''' Test if get_firewall_policy returns None for non-existent policy '''
        set_module_args(self.mock_policy_args())
        result = self.get_mock_object().get_firewall_policy()
        assert result is None

    def test_get_existing_policy(self):
        ''' Test if get_firewall_policy returns policy details for existing policy '''
        data = self.mock_policy_args()
        set_module_args(data)
        result = self.get_mock_object('policy').get_firewall_policy()
        assert result['service'] == data['service']
        assert result['allow_list'] == ['1.2.3.0/24']  # from build_policy_info()

    def test_successful_create(self):
        ''' Test successful create '''
        set_module_args(self.mock_policy_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_create_idempotency(self):
        ''' Test create idempotency '''
        set_module_args(self.mock_policy_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object('policy').apply()
        assert not exc.value.args[0]['changed']

    def test_successful_delete(self):
        ''' Test delete existing job '''
        data = self.mock_policy_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object('policy').apply()
        assert exc.value.args[0]['changed']

    def test_delete_idempotency(self):
        ''' Test delete idempotency '''
        data = self.mock_policy_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object().apply()
        assert not exc.value.args[0]['changed']

    def test_successful_modify(self):
        ''' Test successful modify allow_list '''
        data = self.mock_policy_args()
        data['allow_list'] = ['1.2.0.0/16']
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object('policy').apply()
        assert exc.value.args[0]['changed']

    def test_successful_modify_mutiple_ips(self):
        ''' Test successful modify allow_list '''
        data = self.mock_policy_args()
        data['allow_list'] = ['1.2.0.0/16', '1.0.0.0/8']
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object('policy').apply()
        assert exc.value.args[0]['changed']

    def test_get_nonexistent_config(self):
        ''' Test if get_firewall_config returns None for non-existent node '''
        set_module_args(self.mock_config_args())
        result = self.get_mock_object().get_firewall_config_for_node()
        assert result is None

    def test_get_existing_config(self):
        ''' Test if get_firewall_config returns policy details for existing node '''
        data = self.mock_config_args()
        set_module_args(data)
        result = self.get_mock_object('config').get_firewall_config_for_node()
        assert result['enable'] == 'enable'  # from build_config_info()
        assert result['logging'] == 'disable'  # from build_config_info()

    def test_successful_modify_config(self):
        ''' Test successful modify allow_list '''
        data = self.mock_config_args()
        data['enable'] = 'disable'
        data['logging'] = 'enable'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object('config').apply()
        assert exc.value.args[0]['changed']
