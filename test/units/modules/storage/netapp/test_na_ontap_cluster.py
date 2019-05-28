# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: na_ontap_cluster '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_cluster \
    import NetAppONTAPCluster as my_module  # module under test

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
        if self.type == 'cluster':
            xml = self.build_cluster_info()
        elif self.type == 'cluster_fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    def autosupport_log(self):
        ''' mock autosupport log'''
        return None

    @staticmethod
    def build_cluster_info():
        ''' build xml data for cluster-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'license-v2-status': {'package': 'cifs', 'method': 'site'}}
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
        self.use_vsim = False

    def set_default_args(self):
        if self.use_vsim:
            hostname = '10.193.77.37'
            username = 'admin'
            password = 'netapp1!'
            license_package = 'CIFS'
            node_serial_number = '123'
            license_code = 'AAA'
            cluster_name = 'abc'
        else:
            hostname = '10.193.77.37'
            username = 'admin'
            password = 'netapp1!'
            license_package = 'CIFS'
            node_serial_number = '123'
            cluster_ip_address = '0.0.0.0'
            license_code = 'AAA'
            cluster_name = 'abc'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'license_package': license_package,
            'node_serial_number': node_serial_number,
            'license_code': license_code,
            'cluster_name': cluster_name,
            'cluster_ip_address': cluster_ip_address
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_license_get_called(self):
        ''' fetching details of license '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        license_get = my_obj.get_licensing_status()
        print('Info: test_license_get: %s' % repr(license_get))
        assert not bool(license_get)

    def test_ensure_apply_for_cluster_called(self):
        ''' creating license and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.autosupport_log = Mock(return_value=None)
        if not self.use_vsim:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cluster_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cluster')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cluster_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_cluster.NetAppONTAPCluster.create_cluster')
    def test_cluster_create_called(self, cluster_create):
        ''' creating cluster'''
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.autosupport_log = Mock(return_value=None)
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cluster')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cluster_apply: %s' % repr(exc.value))
        cluster_create.assert_called_with()

    def test_if_all_methods_catch_exception(self):
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cluster_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.get_licensing_status()
        assert 'Error checking license status' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_cluster()
        assert 'Error creating cluster' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.cluster_join()
        assert 'Error adding node to cluster' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.license_v2_add()
        assert 'Error adding license' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.license_v2_delete()
            assert 'Error deleting license' in exc.value.args[0]['msg']
