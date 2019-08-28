# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test template for ONTAP Ansible module '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_net_subnet \
    import NetAppOntapSubnet as my_module  # module under test

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
        self.type = kind
        self.params = data
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if xml.get_child_by_name('query') is not None and \
           xml.get_child_by_name('query').get_child_by_name('vserver-info') is not None:
            # assume this a a cserver request
            xml = self.build_cserver_info()
        elif self.type == 'subnet':
            if xml.get_child_by_name('query'):
                name_obj = xml.get_child_by_name('query').get_child_by_name('net-subnet-info').get_child_by_name('subnet-name')
                xml_name = name_obj.get_content()
                if xml_name == self.params.get('name'):
                    xml = self.build_subnet_info(self.params)
        elif self.type == 'subnet_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_cserver_info():
        ''' build xml data for vserver-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'vserver-info': {
                    'vserver-name': 'cserver',
                }
            }
        }
        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_subnet_info(data):
        ''' build xml data for subnet-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        ip_ranges = []
        for elem in data['ip_ranges']:
            ip_ranges.append({'ip-range': elem})
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'net-subnet-info': {
                    'broadcast-domain': data['broadcast_domain'],
                    'gateway': data['gateway'],
                    'ip-ranges': ip_ranges,
                    'ipspace': data['ipspace'],
                    'subnet': data['subnet'],
                    'subnet-name': data['name'],
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
        self.server = MockONTAPConnection()

    def set_default_args(self):
        return dict({
            'name': 'test_subnet',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'broadcast_domain': 'Default',
            'gateway': '10.0.0.1',
            'ipspace': 'Default',
            'subnet': '10.0.0.0/24',
            'ip_ranges': ['10.0.0.10-10.0.0.20', '10.0.0.30']
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_get_called(self):
        ''' test get_subnet for non-existent subnet'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.get_subnet() is None

    def test_ensure_get_called_existing(self):
        ''' test get_subnet for existing subnet'''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subnet', data=data)
        assert my_obj.get_subnet() is not None

    @patch('ansible.module_utils.netapp.ems_log_event')
    def test_fail_broadcast_domain_modify(self, mock_ems_log):
        ''' test that boradcast_domain is not alterable '''
        data = self.set_default_args()
        data.update({'broadcast_domain': 'Test'})
        set_module_args(data)
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subnet', data=self.set_default_args())
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        assert 'cannot modify broadcast_domain parameter' in exc.value.args[0]['msg']

    @patch('ansible.module_utils.netapp.ems_log_event')
    @patch('ansible.modules.storage.netapp.na_ontap_net_subnet.NetAppOntapSubnet.create_subnet')
    def test_successful_create(self, create_subnet, mock_ems_log):
        ''' creating subnet and testing idempotency '''
        print("Create:")
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        create_subnet.assert_called_with()

        # to reset na_helper from remembering the previous 'changed' value
        print("reset:")
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subnet', data=data)
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.ems_log_event')
    @patch('ansible.modules.storage.netapp.na_ontap_net_subnet.NetAppOntapSubnet.rename_subnet')
    def test_successful_rename(self, rename_subnet, mock_ems_log):
        ''' renaming subnet '''
        data = self.set_default_args()
        data.update({'from_name': data['name'], 'name': 'new_test_subnet'})
        set_module_args(data)
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subnet', data=self.set_default_args())
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.ems_log_event')
    @patch('ansible.modules.storage.netapp.na_ontap_net_subnet.NetAppOntapSubnet.delete_subnet')
    def test_successful_delete(self, delete_subnet, mock_ems_log):
        ''' deleting subnet and testing idempotency '''
        data = self.set_default_args()
        data['state'] = 'absent'
        set_module_args(data)
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subnet', data=data)
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        delete_subnet.assert_called_with()

        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.ems_log_event')
    def test_successful_modify(self, mock_ems_log):
        ''' modifying subnet and testing idempotency '''
        data = self.set_default_args()
        data.update({'ip_ranges': ['10.0.0.10-10.0.0.25', '10.0.0.30']})
        set_module_args(data)
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subnet', data=self.set_default_args())
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.ems_log_event')
    def test_if_all_methods_catch_exception(self, mock_ems_log):
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='subnet_fail', data=data)
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_subnet()
        assert 'Error creating subnet' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.delete_subnet()
        assert 'Error deleting subnet' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.modify_subnet()
        assert 'Error modifying subnet' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.rename_subnet()
        assert 'Error renaming subnet' in exc.value.args[0]['msg']
