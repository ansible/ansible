# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: na_ontap_nvme_subsystem '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_nvme_subsystem \
    import NetAppONTAPNVMESubsystem as my_module

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

    def __init__(self, kind=None, parm1=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'subsystem':
            xml = self.build_subsystem_info(self.parm1)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_subsystem_info(vserver):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 2,
                'attributes-list': [{'nvme-target-subsystem-map-info': {'path': 'abcd/vol'}},
                                    {'nvme-target-subsystem-map-info': {'path': 'xyz/vol'}}]}
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
            hostname = '10.193.75.3'
            username = 'admin'
            password = 'netapp1!'
            subsystem = 'test'
            vserver = 'ansible'
            ostype = 'linux'
            paths = ['abcd/vol', 'xyz/vol']
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            subsystem = 'test'
            vserver = 'vserver'
            ostype = 'linux'
            paths = ['abcd/vol', 'xyz/vol']
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'subsystem': subsystem,
            'ostype': ostype,
            'vserver': vserver,
            'paths': paths
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_get_called(self):
        ''' test get_subsystem()  for non-existent subsystem'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.get_subsystem() is None

    def test_ensure_get_called_existing(self):
        ''' test get_subsystem()  for existing subsystem'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subsystem')
        assert my_obj.get_subsystem()

    @patch('ansible.modules.storage.netapp.na_ontap_nvme_subsystem.NetAppONTAPNVMESubsystem.create_subsystem')
    def test_successful_create(self, create_subsystem):
        ''' creating subsystem and testing idempotency '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        create_subsystem.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('subsystem')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_nvme_subsystem.NetAppONTAPNVMESubsystem.delete_subsystem')
    def test_successful_delete(self, delete_subsystem):
        ''' deleting subsystem and testing idempotency '''
        data = self.set_default_args()
        data['state'] = 'absent'
        set_module_args(data)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('subsystem')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        delete_subsystem.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_ensure_get_called(self):
        ''' test get_subsystem_host_map()  for non-existent subsystem'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.get_subsystem_host_map('paths') is None

    def test_ensure_get_called_existing(self):
        ''' test get_subsystem_host_map()  for existing subsystem'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subsystem')
        assert my_obj.get_subsystem_host_map('paths')

    @patch('ansible.modules.storage.netapp.na_ontap_nvme_subsystem.NetAppONTAPNVMESubsystem.add_subsystem_host_map')
    def test_successful_add_mock(self, add_subsystem_host_map):
        ''' adding subsystem host/map and testing idempotency '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        add_subsystem_host_map.assert_called_with(['abcd/vol', 'xyz/vol'], 'paths')

    @patch('ansible.modules.storage.netapp.na_ontap_nvme_subsystem.NetAppONTAPNVMESubsystem.remove_subsystem_host_map')
    def test_successful_remove_mock(self, remove_subsystem_host_map):
        ''' removing subsystem host/map and testing idempotency '''
        data = self.set_default_args()
        data['paths'] = ['abcd/vol']
        set_module_args(data)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('subsystem')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        remove_subsystem_host_map.assert_called_with(['xyz/vol'], 'paths')

    def test_successful_add(self):
        ''' adding subsystem host/map and testing idempotency '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    def test_successful_remove(self):
        ''' removing subsystem host/map and testing idempotency '''
        data = self.set_default_args()
        data['paths'] = ['abcd/vol']
        set_module_args(data)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('subsystem')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
