''' unit tests ONTAP Ansible module: na_ontap_lun_map '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_lun_map \
    import NetAppOntapLUNMap as my_module

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

    def __init__(self, kind=None):
        ''' save arguments '''
        self.type = kind
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'lun_map':
            xml = self.build_lun_info()
        elif self.type == 'lun_map_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_lun_info():
        ''' build xml data for lun-map-entry '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'initiator-groups': [{'initiator-group-info': {'initiator-group-name': 'ansible', 'lun-id': 2}}]}
        xml.translate_struct(data)
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
        self.onbox = False

    def set_default_args(self):
        if self.onbox:
            hostname = '10.10.10.10'
            username = 'admin'
            password = 'password'
            initiator_group_name = 'ansible'
            vserver = 'ansible'
            path = '/vol/ansible/test'
            lun_id = 2
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            initiator_group_name = 'ansible'
            vserver = 'ansible'
            path = '/vol/ansible/test'
            lun_id = 2
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'initiator_group_name': initiator_group_name,
            'vserver': vserver,
            'path': path,
            'lun_id': lun_id
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_get_called(self):
        ''' test get_lun_map for non-existent lun'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.get_lun_map is not None

    def test_ensure_get_called_existing(self):
        ''' test get_lun_map for existing lun'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='lun_map')
        assert my_obj.get_lun_map()

    @patch('ansible.modules.storage.netapp.na_ontap_lun_map.NetAppOntapLUNMap.create_lun_map')
    def test_successful_create(self, create_lun_map):
        ''' mapping lun and testing idempotency '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        create_lun_map.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        set_module_args(self.set_default_args())
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('lun_map')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_lun_map.NetAppOntapLUNMap.delete_lun_map')
    def test_successful_delete(self, delete_lun_map):
        ''' unmapping lun and testing idempotency '''
        data = self.set_default_args()
        data['state'] = 'absent'
        set_module_args(data)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('lun_map')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        delete_lun_map.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_if_all_methods_catch_exception(self):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('lun_map_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_lun_map()
        assert 'Error mapping lun' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.delete_lun_map()
        assert 'Error unmapping lun' in exc.value.args[0]['msg']
