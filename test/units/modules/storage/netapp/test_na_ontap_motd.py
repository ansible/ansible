# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit tests for Ansible module: na_ontap_motd """

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_motd \
    import NetAppONTAPMotd as my_module  # module under test

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
        if self.type == 'motd':
            xml = self.build_motd_info()
        elif self.type == 'motd_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_motd_info():
        ''' build xml data for motd '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {'vserver-motd-info': {'message': 'ansible',
                                                          'vserver': 'ansible',
                                                          'is-cluster-message-enabled': 'true'}}}
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
            message = 'ansible'
            vserver = 'ansible'
            show_cluster_motd = 'true'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            message = 'ansible'
            vserver = 'ansible'
            show_cluster_motd = 'true'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'message': message,
            'vserver': vserver,
            'show_cluster_motd': show_cluster_motd
        })

    def call_command(self, module_args):
        ''' utility function to call apply '''
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('motd')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        return exc.value.args[0]['changed']

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_motd_get_called(self):
        ''' fetching details of motd '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.motd_get() is None

    def test_ensure_get_called_existing(self):
        ''' test for existing motd'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='motd')
        assert my_obj.motd_get()

    def test_motd_create(self):
        ''' test for creating motd'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection(kind='motd')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_motd_delete(self):
        ''' test for deleting motd'''
        module_args = {
            'state': 'absent',
        }
        changed = self.call_command(module_args)
        assert changed

    def test_if_all_methods_catch_exception(self):
        set_module_args(self.set_default_args())
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('motd_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.motd_get()
        assert '' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.modify_motd()
        assert 'Error creating motd: ' in exc.value.args[0]['msg']
