# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests for Ansible module: na_ontap_object_store """

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_object_store \
    import NetAppOntapObjectStoreConfig as my_module  # module under test

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
        if self.type == 'object_store':
            xml = self.build_object_store_info()
        elif self.type == 'object_store_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_object_store_info():
        ''' build xml data for object store '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'attributes':
                {'aggr-object-store-config-info':
                    {'object-store-name': 'ansible'}
                 }
                }
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
        # whether to use a mock or a simulator
        self.onbox = False

    def set_default_args(self):
        if self.onbox:
            hostname = '10.10.10.10'
            username = 'admin'
            password = 'password'
            name = 'ansible'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            name = 'ansible'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'name': name
        })

    def call_command(self, module_args):
        ''' utility function to call apply '''
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            # mock the connection
            my_obj.server = MockONTAPConnection('object_store')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        return exc.value.args[0]['changed']

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_object_store_get_called(self):
        ''' fetching details of object store '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.get_aggr_object_store() is not None

    def test_ensure_get_called_existing(self):
        ''' test for existing object store'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='object_store')
        assert my_obj.get_aggr_object_store()

    def test_object_store_create(self):
        ''' test for creating object store'''
        module_args = {
            'provider_type': 'abc',
            'server': 'abc',
            'container': 'abc',
            'access_key': 'abc',
            'secret_password': 'abc'
        }
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            # mock the connection
            my_obj.server = MockONTAPConnection(kind='object_store')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_object_store_delete(self):
        ''' test for deleting object store'''
        module_args = {
            'state': 'absent',
        }
        changed = self.call_command(module_args)
        assert changed

    def test_if_all_methods_catch_exception(self):
        module_args = {
            'provider_type': 'abc',
            'server': 'abc',
            'container': 'abc',
            'access_key': 'abc',
            'secret_password': 'abc'
        }
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('object_store_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.get_aggr_object_store()
        assert '' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_aggr_object_store()
        assert 'Error provisioning object store config ' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.delete_aggr_object_store()
        assert 'Error removing object store config ' in exc.value.args[0]['msg']
