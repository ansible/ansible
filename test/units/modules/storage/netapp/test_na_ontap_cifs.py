# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: na_ontap_cifs '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_cifs \
    import NetAppONTAPCifsShare as my_module  # module under test

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
        if self.type == 'cifs':
            xml = self.build_cifs_info()
        elif self.type == 'cifs_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_cifs_info():
        ''' build xml data for cifs-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1, 'attributes-list': {'cifs-share': {
            'share-name': 'test',
            'path': '/test',
            'share-properties': {'cifs-share-properties': 'browsable'},
            'symlink-properties': {'cifs-share-symlink-properties': 'enable'},
        }}}
        xml.translate_struct(data)
        print(xml.to_string())
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
            hostname = '10.193.77.37'
            username = 'admin'
            password = 'netapp1!'
            share_name = 'test'
            path = '/test'
            share_properties = 'browsable,oplocks'
            symlink_properties = 'disable'
            vserver = 'abc'
        else:
            hostname = '10.193.77.37'
            username = 'admin'
            password = 'netapp1!'
            share_name = 'test'
            path = '/test'
            share_properties = 'show_previous_versions'
            symlink_properties = 'disable'
            vserver = 'abc'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'share_name': share_name,
            'path': path,
            'share_properties': share_properties,
            'symlink_properties': symlink_properties,
            'vserver': vserver
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_cifs_get_called(self):
        ''' fetching details of cifs '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        cifs_get = my_obj.get_cifs_share()
        print('Info: test_cifs_share_get: %s' % repr(cifs_get))
        assert not bool(cifs_get)

    def test_ensure_apply_for_cifs_called(self):
        ''' creating cifs share and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
        if not self.onbox:
            my_obj.server = MockONTAPConnection('cifs')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_cifs.NetAppONTAPCifsShare.create_cifs_share')
    def test_cifs_create_called(self, create_cifs_share):
        ''' creating cifs'''
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_apply: %s' % repr(exc.value))
        create_cifs_share.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_cifs.NetAppONTAPCifsShare.delete_cifs_share')
    def test_cifs_delete_called(self, delete_cifs_share):
        ''' deleting cifs'''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args['state'] = 'absent'
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('cifs')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_apply: %s' % repr(exc.value))
        delete_cifs_share.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_cifs.NetAppONTAPCifsShare.modify_cifs_share')
    def test_cifs_modify_called(self, modify_cifs_share):
        ''' modifying cifs'''
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('cifs')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_apply: %s' % repr(exc.value))
        modify_cifs_share.assert_called_with()

    def test_if_all_methods_catch_exception(self):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('cifs_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_cifs_share()
        assert 'Error creating cifs-share' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.delete_cifs_share()
        assert 'Error deleting cifs-share' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.modify_cifs_share()
        assert 'Error modifying cifs-share' in exc.value.args[0]['msg']
