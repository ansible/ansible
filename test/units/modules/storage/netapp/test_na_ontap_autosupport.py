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

from ansible.modules.storage.netapp.na_ontap_autosupport \
    import NetAppONTAPasup as asup_module  # module under test

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
        if self.kind == 'asup':
            xml = self.build_asup_config_info(self.params)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_asup_config_info(asup_data):
        ''' build xml data for asup-config '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {'attributes': {'autosupport-config-info': {
            'node-name': asup_data['node_name'],
            'is-enabled': asup_data['is_enabled'],
            'is-support-enabled': asup_data['support'],
            'proxy-url': asup_data['proxy_url'],
            'post-url': asup_data['post_url'],
            'transport': asup_data['transport'],
            'is-node-in-subject': 'false',
            'from': 'test',
            'mail-hosts': [{'string': '1.2.3.4'}, {'string': '4.5.6.8'}],
            'noteto': [{'mail-address': 'abc@test.com'},
                       {'mail-address': 'def@test.com'}],
        }}}
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
        self.mock_asup = {
            'node_name': 'test-vsim1',
            'transport': 'https',
            'support': 'false',
            'post_url': 'testbed.netapp.com/asupprod/post/1.0/postAsup',
            'proxy_url': 'something.com',
        }

    def mock_args(self):
        return {
            'node_name': self.mock_asup['node_name'],
            'transport': self.mock_asup['transport'],
            'support': self.mock_asup['support'],
            'post_url': self.mock_asup['post_url'],
            'proxy_url': self.mock_asup['proxy_url'],
            'hostname': 'host',
            'username': 'admin',
            'password': 'password',
        }

    def get_asup_mock_object(self, kind=None, enabled='false'):
        """
        Helper method to return an na_ontap_volume object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_volume object
        """
        asup_obj = asup_module()
        asup_obj.autosupport_log = Mock(return_value=None)
        if kind is None:
            asup_obj.server = MockONTAPConnection()
        else:
            data = self.mock_asup
            data['is_enabled'] = enabled
            asup_obj.server = MockONTAPConnection(kind='asup', data=data)
        return asup_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            asup_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_enable_asup(self):
        ''' a more interesting test '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_asup_mock_object('asup').apply()
        assert exc.value.args[0]['changed']

    def test_disable_asup(self):
        ''' a more interesting test '''
        # enable asup
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_asup_mock_object(kind='asup', enabled='true').apply()
        assert exc.value.args[0]['changed']

    def test_result_from_get(self):
        ''' Check boolean and service_state conversion from get '''
        data = self.mock_args()
        set_module_args(data)
        obj = self.get_asup_mock_object(kind='asup', enabled='true')
        # constructed based on valued passed in self.mock_asup and build_asup_config_info()
        expected_dict = {
            'node_name': 'test-vsim1',
            'service_state': 'started',
            'support': False,
            'hostname_in_subject': False,
            'transport': self.mock_asup['transport'],
            'post_url': self.mock_asup['post_url'],
            'proxy_url': self.mock_asup['proxy_url'],
            'from_address': 'test',
            'mail_hosts': ['1.2.3.4', '4.5.6.8'],
            'partner_addresses': [],
            'to_addresses': [],
            'noteto': ['abc@test.com', 'def@test.com']
        }
        result = obj.get_autosupport_config()
        assert result == expected_dict

    def test_modify_config(self):
        ''' Check boolean and service_state conversion from get '''
        data = self.mock_args()
        data['transport'] = 'http'
        data['post_url'] = 'somethingelse.com'
        data['proxy_url'] = 'somethingelse.com'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_asup_mock_object('asup').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_autosupport.NetAppONTAPasup.get_autosupport_config')
    def test_get_called(self, get_asup):
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_asup_mock_object('asup').apply()
        get_asup.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_autosupport.NetAppONTAPasup.modify_autosupport_config')
    def test_modify_called(self, modify_asup):
        data = self.mock_args()
        data['transport'] = 'http'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_asup_mock_object('asup').apply()
        modify_asup.assert_called_with({'transport': 'http', 'service_state': 'started'})

    @patch('ansible.modules.storage.netapp.na_ontap_autosupport.NetAppONTAPasup.modify_autosupport_config')
    @patch('ansible.modules.storage.netapp.na_ontap_autosupport.NetAppONTAPasup.get_autosupport_config')
    def test_modify_not_called(self, get_asup, modify_asup):
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_asup_mock_object('asup').apply()
        get_asup.assert_called_with()
        modify_asup.assert_not_called()

    def test_modify_packet(self):
        '''check XML construction for nested attributes like mail-hosts, noteto, partner-address, and to'''
        data = self.mock_args()
        set_module_args(data)
        obj = self.get_asup_mock_object(kind='asup', enabled='true')
        modify_dict = {
            'noteto': ['one@test.com'],
            'partner_addresses': ['firstpartner@test.com'],
            'mail_hosts': ['1.1.1.1'],
            'to_addresses': ['first@test.com']
        }
        obj.modify_autosupport_config(modify_dict)
        xml = obj.server.xml_in
        for key in ['noteto', 'to', 'partner-address']:
            assert xml[key] is not None
            assert xml[key]['mail-address'] is not None
        assert xml['noteto']['mail-address'] == modify_dict['noteto'][0]
        assert xml['to']['mail-address'] == modify_dict['to_addresses'][0]
        assert xml['partner-address']['mail-address'] == modify_dict['partner_addresses'][0]
        assert xml['mail-hosts'] is not None
        assert xml['mail-hosts']['string'] is not None
        assert xml['mail-hosts']['string'] == modify_dict['mail_hosts'][0]
