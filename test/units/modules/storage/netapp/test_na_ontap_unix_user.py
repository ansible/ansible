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

from ansible.modules.storage.netapp.na_ontap_unix_user \
    import NetAppOntapUnixUser as user_module  # module under test

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
        if self.kind == 'user':
            xml = self.build_user_info(self.params)
        elif self.kind == 'user-fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_user_info(data):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = \
            {'attributes-list': {'unix-user-info': {'user-id': data['id'],
                                                    'group-id': data['group_id'], 'full-name': data['full_name']}},
             'num-records': 1}
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
        self.mock_user = {
            'name': 'test',
            'id': '11',
            'group_id': '12',
            'vserver': 'something',
            'full_name': 'Test User'
        }

    def mock_args(self):
        return {
            'name': self.mock_user['name'],
            'group_id': self.mock_user['group_id'],
            'id': self.mock_user['id'],
            'vserver': self.mock_user['vserver'],
            'full_name': self.mock_user['full_name'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_user_mock_object(self, kind=None, data=None):
        """
        Helper method to return an na_ontap_unix_user object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_unix_user object
        """
        obj = user_module()
        obj.autosupport_log = Mock(return_value=None)
        if data is None:
            data = self.mock_user
        obj.server = MockONTAPConnection(kind=kind, data=data)
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            user_module()

    def test_get_nonexistent_user(self):
        ''' Test if get_unix_user returns None for non-existent user '''
        set_module_args(self.mock_args())
        result = self.get_user_mock_object().get_unix_user()
        assert result is None

    def test_get_existing_user(self):
        ''' Test if get_unix_user returns details for existing user '''
        set_module_args(self.mock_args())
        result = self.get_user_mock_object('user').get_unix_user()
        assert result['full_name'] == self.mock_user['full_name']

    def test_get_xml(self):
        set_module_args(self.mock_args())
        obj = self.get_user_mock_object('user')
        result = obj.get_unix_user()
        assert obj.server.xml_in['query']
        assert obj.server.xml_in['query']['unix-user-info']
        user_info = obj.server.xml_in['query']['unix-user-info']
        assert user_info['user-name'] == self.mock_user['name']
        assert user_info['vserver'] == self.mock_user['vserver']

    def test_create_error_missing_params(self):
        data = self.mock_args()
        del data['group_id']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_user_mock_object('user').create_unix_user()
        assert 'Error: Missing one or more required parameters for create: (group_id, id)' == exc.value.args[0]['msg']

    @patch('ansible.modules.storage.netapp.na_ontap_unix_user.NetAppOntapUnixUser.create_unix_user')
    def test_create_called(self, create_user):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_user_mock_object().apply()
        assert exc.value.args[0]['changed']
        create_user.assert_called_with()

    def test_create_xml(self):
        '''Test create ZAPI element'''
        set_module_args(self.mock_args())
        create = self.get_user_mock_object()
        with pytest.raises(AnsibleExitJson) as exc:
            create.apply()
        mock_key = {
            'user-name': 'name',
            'group-id': 'group_id',
            'user-id': 'id',
            'full-name': 'full_name'
        }
        for key in ['user-name', 'user-id', 'group-id', 'full-name']:
            assert create.server.xml_in[key] == self.mock_user[mock_key[key]]

    def test_create_wihtout_full_name(self):
        '''Test create ZAPI element'''
        data = self.mock_args()
        del data['full_name']
        set_module_args(data)
        create = self.get_user_mock_object()
        with pytest.raises(AnsibleExitJson) as exc:
            create.apply()
        with pytest.raises(KeyError):
            create.server.xml_in['full-name']

    @patch('ansible.modules.storage.netapp.na_ontap_unix_user.NetAppOntapUnixUser.modify_unix_user')
    @patch('ansible.modules.storage.netapp.na_ontap_unix_user.NetAppOntapUnixUser.delete_unix_user')
    def test_delete_called(self, delete_user, modify_user):
        ''' Test delete existing user '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_user_mock_object('user').apply()
        assert exc.value.args[0]['changed']
        delete_user.assert_called_with()
        assert modify_user.call_count == 0

    @patch('ansible.modules.storage.netapp.na_ontap_unix_user.NetAppOntapUnixUser.get_unix_user')
    @patch('ansible.modules.storage.netapp.na_ontap_unix_user.NetAppOntapUnixUser.modify_unix_user')
    def test_modify_called(self, modify_user, get_user):
        ''' Test modify user group_id '''
        data = self.mock_args()
        data['group_id'] = 20
        set_module_args(data)
        get_user.return_value = {'group_id': 10}
        obj = self.get_user_mock_object('user')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        get_user.assert_called_with()
        modify_user.assert_called_with({'group_id': 20})

    def test_modify_only_id(self):
        ''' Test modify user id '''
        set_module_args(self.mock_args())
        modify = self.get_user_mock_object('user')
        modify.modify_unix_user({'id': 123})
        assert modify.server.xml_in['user-id'] == '123'
        with pytest.raises(KeyError):
            modify.server.xml_in['group-id']
        with pytest.raises(KeyError):
            modify.server.xml_in['full-name']

    def test_modify_xml(self):
        ''' Test modify user full_name '''
        set_module_args(self.mock_args())
        modify = self.get_user_mock_object('user')
        modify.modify_unix_user({'full_name': 'New Name',
                                 'group_id': '25'})
        assert modify.server.xml_in['user-name'] == self.mock_user['name']
        assert modify.server.xml_in['full-name'] == 'New Name'
        assert modify.server.xml_in['group-id'] == '25'

    @patch('ansible.modules.storage.netapp.na_ontap_unix_user.NetAppOntapUnixUser.create_unix_user')
    @patch('ansible.modules.storage.netapp.na_ontap_unix_user.NetAppOntapUnixUser.delete_unix_user')
    @patch('ansible.modules.storage.netapp.na_ontap_unix_user.NetAppOntapUnixUser.modify_unix_user')
    def test_do_nothing(self, modify, delete, create):
        ''' changed is False and none of the opetaion methods are called'''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        obj = self.get_user_mock_object()
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        create.assert_not_called()
        delete.assert_not_called()
        modify.assert_not_called()

    def test_get_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_user_mock_object('user-fail').get_unix_user()
        assert 'Error getting UNIX user' in exc.value.args[0]['msg']

    def test_create_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_user_mock_object('user-fail').create_unix_user()
        assert 'Error creating UNIX user' in exc.value.args[0]['msg']

    def test_modify_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_user_mock_object('user-fail').modify_unix_user({'id': '123'})
        assert 'Error modifying UNIX user' in exc.value.args[0]['msg']

    def test_delete_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_user_mock_object('user-fail').delete_unix_user()
        assert 'Error removing UNIX user' in exc.value.args[0]['msg']
