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

from ansible.modules.storage.netapp.na_ontap_user_role \
    import NetAppOntapUserRole as role_module  # module under test

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
        if self.kind == 'role':
            xml = self.build_role_info(self.params)
        if self.kind == 'error':
            error = netapp_utils.zapi.NaApiError('test', 'error')
            raise error
        self.xml_out = xml
        return xml

    @staticmethod
    def build_role_info(vol_details):
        ''' build xml data for role-attributes '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'security-login-role-info': {
                    'access-level': 'all',
                    'command-directory-name': 'volume',
                    'role-name': 'testrole',
                    'role-query': 'show',
                    'vserver': 'ansible'
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
        self.mock_role = {
            'name': 'testrole',
            'access_level': 'all',
            'command_directory_name': 'volume',
            'vserver': 'ansible'
        }

    def mock_args(self):
        return {
            'name': self.mock_role['name'],
            'vserver': self.mock_role['vserver'],
            'command_directory_name': self.mock_role['command_directory_name'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'https': 'False'
        }

    def get_role_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_user_role object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_user_role object
        """
        role_obj = role_module()
        role_obj.asup_log_for_cserver = Mock(return_value=None)
        role_obj.cluster = Mock()
        role_obj.cluster.invoke_successfully = Mock()
        if kind is None:
            role_obj.server = MockONTAPConnection()
        else:
            role_obj.server = MockONTAPConnection(kind=kind, data=self.mock_role)
        return role_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            role_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_policy(self):
        ''' Test if get_role returns None for non-existent role '''
        set_module_args(self.mock_args())
        result = self.get_role_mock_object().get_role()
        assert result is None

    def test_get_existing_role(self):
        ''' Test if get_role returns details for existing role '''
        set_module_args(self.mock_args())
        result = self.get_role_mock_object('role').get_role()
        assert result['name'] == self.mock_role['name']

    def test_successful_create(self):
        ''' Test successful create '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_role_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_create_idempotency(self):
        ''' Test create idempotency '''
        data = self.mock_args()
        data['query'] = 'show'
        set_module_args(data)
        obj = self.get_role_mock_object('role')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_user_role.NetAppOntapUserRole.get_role')
    def test_create_error(self, get_role):
        ''' Test create error '''
        set_module_args(self.mock_args())
        get_role.side_effect = [
            None
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_role_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error creating role testrole: NetApp API failed. Reason - test:error'

    @patch('ansible.modules.storage.netapp.na_ontap_user_role.NetAppOntapUserRole.get_role')
    def test_successful_modify(self, get_role):
        ''' Test successful modify '''
        data = self.mock_args()
        data['query'] = 'show'
        set_module_args(data)
        current = self.mock_role
        current['query'] = 'show-space'
        get_role.side_effect = [
            current
        ]
        obj = self.get_role_mock_object()
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_user_role.NetAppOntapUserRole.get_role')
    def test_modify_idempotency(self, get_role):
        ''' Test modify idempotency '''
        data = self.mock_args()
        data['query'] = 'show'
        set_module_args(data)
        current = self.mock_role
        current['query'] = 'show'
        get_role.side_effect = [
            current
        ]
        obj = self.get_role_mock_object()
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_user_role.NetAppOntapUserRole.get_role')
    def test_modify_error(self, get_role):
        ''' Test modify error '''
        data = self.mock_args()
        data['query'] = 'show'
        set_module_args(data)
        current = self.mock_role
        current['query'] = 'show-space'
        get_role.side_effect = [
            current
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_role_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error modifying role testrole: NetApp API failed. Reason - test:error'

    def test_successful_delete(self):
        ''' Test delete existing role '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_role_mock_object('role').apply()
        assert exc.value.args[0]['changed']
