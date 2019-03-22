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

from ansible.modules.storage.netapp.na_ontap_unix_group \
    import NetAppOntapUnixGroup as group_module  # module under test

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
        if self.kind == 'group':
            xml = self.build_group_info(self.params)
        elif self.kind == 'group-fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_group_info(data):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = \
            {'attributes-list': {'unix-group-info': {'group-name': data['name'],
                                                     'group-id': data['id']}},
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
        self.mock_group = {
            'name': 'test',
            'id': '11',
            'vserver': 'something',
        }

    def mock_args(self):
        return {
            'name': self.mock_group['name'],
            'id': self.mock_group['id'],
            'vserver': self.mock_group['vserver'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_group_mock_object(self, kind=None, data=None):
        """
        Helper method to return an na_ontap_unix_group object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_unix_group object
        """
        obj = group_module()
        obj.autosupport_log = Mock(return_value=None)
        if data is None:
            data = self.mock_group
        obj.server = MockONTAPConnection(kind=kind, data=data)
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            group_module()

    def test_get_nonexistent_group(self):
        ''' Test if get_unix_group returns None for non-existent group '''
        set_module_args(self.mock_args())
        result = self.get_group_mock_object().get_unix_group()
        assert result is None

    def test_get_existing_group(self):
        ''' Test if get_unix_group returns details for existing group '''
        set_module_args(self.mock_args())
        result = self.get_group_mock_object('group').get_unix_group()
        assert result['name'] == self.mock_group['name']

    def test_get_xml(self):
        set_module_args(self.mock_args())
        obj = self.get_group_mock_object('group')
        result = obj.get_unix_group()
        assert obj.server.xml_in['query']
        assert obj.server.xml_in['query']['unix-group-info']
        group_info = obj.server.xml_in['query']['unix-group-info']
        assert group_info['group-name'] == self.mock_group['name']
        assert group_info['vserver'] == self.mock_group['vserver']

    def test_create_error_missing_params(self):
        data = self.mock_args()
        del data['id']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_group_mock_object('group').create_unix_group()
        assert 'Error: Missing a required parameter for create: (id)' == exc.value.args[0]['msg']

    @patch('ansible.modules.storage.netapp.na_ontap_unix_group.NetAppOntapUnixGroup.create_unix_group')
    def test_create_called(self, create_group):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_group_mock_object().apply()
        assert exc.value.args[0]['changed']
        create_group.assert_called_with()

    def test_create_xml(self):
        '''Test create ZAPI element'''
        set_module_args(self.mock_args())
        create = self.get_group_mock_object()
        with pytest.raises(AnsibleExitJson) as exc:
            create.apply()
        mock_key = {
            'group-name': 'name',
            'group-id': 'id',
        }
        for key in ['group-name', 'group-id']:
            assert create.server.xml_in[key] == self.mock_group[mock_key[key]]

    @patch('ansible.modules.storage.netapp.na_ontap_unix_group.NetAppOntapUnixGroup.modify_unix_group')
    @patch('ansible.modules.storage.netapp.na_ontap_unix_group.NetAppOntapUnixGroup.delete_unix_group')
    def test_delete_called(self, delete_group, modify_group):
        ''' Test delete existing group '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_group_mock_object('group').apply()
        assert exc.value.args[0]['changed']
        delete_group.assert_called_with()
        assert modify_group.call_count == 0

    @patch('ansible.modules.storage.netapp.na_ontap_unix_group.NetAppOntapUnixGroup.get_unix_group')
    @patch('ansible.modules.storage.netapp.na_ontap_unix_group.NetAppOntapUnixGroup.modify_unix_group')
    def test_modify_called(self, modify_group, get_group):
        ''' Test modify group group_id '''
        data = self.mock_args()
        data['id'] = 20
        set_module_args(data)
        get_group.return_value = {'id': 10}
        obj = self.get_group_mock_object('group')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        get_group.assert_called_with()
        modify_group.assert_called_with({'id': 20})

    def test_modify_only_id(self):
        ''' Test modify group id '''
        set_module_args(self.mock_args())
        modify = self.get_group_mock_object('group')
        modify.modify_unix_group({'id': 123})
        print(modify.server.xml_in.to_string())
        assert modify.server.xml_in['group-id'] == '123'
        with pytest.raises(KeyError):
            modify.server.xml_in['id']

    def test_modify_xml(self):
        ''' Test modify group full_name '''
        set_module_args(self.mock_args())
        modify = self.get_group_mock_object('group')
        modify.modify_unix_group({'id': 25})
        assert modify.server.xml_in['group-name'] == self.mock_group['name']
        assert modify.server.xml_in['group-id'] == '25'

    @patch('ansible.modules.storage.netapp.na_ontap_unix_group.NetAppOntapUnixGroup.create_unix_group')
    @patch('ansible.modules.storage.netapp.na_ontap_unix_group.NetAppOntapUnixGroup.delete_unix_group')
    @patch('ansible.modules.storage.netapp.na_ontap_unix_group.NetAppOntapUnixGroup.modify_unix_group')
    def test_do_nothing(self, modify, delete, create):
        ''' changed is False and none of the opetaion methods are called'''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        obj = self.get_group_mock_object()
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        create.assert_not_called()
        delete.assert_not_called()
        modify.assert_not_called()

    def test_get_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_group_mock_object('group-fail').get_unix_group()
        assert 'Error getting UNIX group' in exc.value.args[0]['msg']

    def test_create_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_group_mock_object('group-fail').create_unix_group()
        assert 'Error creating UNIX group' in exc.value.args[0]['msg']

    def test_modify_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_group_mock_object('group-fail').modify_unix_group({'id': '123'})
        assert 'Error modifying UNIX group' in exc.value.args[0]['msg']

    def test_delete_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_group_mock_object('group-fail').delete_unix_group()
        assert 'Error removing UNIX group' in exc.value.args[0]['msg']
