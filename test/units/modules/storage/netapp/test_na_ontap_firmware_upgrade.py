# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: na_ontap_firmware_upgrade '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_firmware_upgrade\
    import NetAppONTAPFirmwareUpgrade as my_module  # module under test

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

    def __init__(self, kind=None, parm1=None, parm2=None, parm3=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.parm2 = parm2
        # self.parm3 = parm3
        self.xml_in = None
        self.xml_out = None
        self.firmware_type = 'None'

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'firmware_upgrade':
            xml = self.build_firmware_upgrade_info(self.parm1, self.parm2)
        if self.type == 'acp':
            xml = self.build_acp_firmware_info(self.firmware_type)
        self.xml_out = xml
        return xml

    def autosupport_log(self):
        ''' mock autosupport log'''
        return None

    @staticmethod
    def build_firmware_upgrade_info(version, node):
        ''' build xml data for service-processor firmware info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {
            'num-records': 1,
            'attributes-list': {'service-processor-info': {'firmware-version': '3.4'}}
        }
        xml.translate_struct(data)
        print(xml.to_string())
        return xml

    @staticmethod
    def build_acp_firmware_info(firmware_type):
        ''' build xml data for acp firmware info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {
            # 'num-records': 1,
            'attributes-list': {'storage-shelf-acp-module': {'state': 'firmware_update_required'}}
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
        self.use_vsim = False

    def set_default_args(self):
        if self.use_vsim:
            hostname = '10.10.10.10'
            username = 'admin'
            password = 'admin'
            node = 'vsim1'
            clear_logs = True
            package = 'test1.zip'
            install_baseline_image = False
            update_type = 'serial_full'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            node = 'abc'
            package = 'test1.zip'
            clear_logs = True
            install_baseline_image = False
            update_type = 'serial_full'

        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'node': node,
            'package': package,
            'clear_logs': clear_logs,
            'install_baseline_image': install_baseline_image,
            'update_type': update_type,
            'https': 'true'
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_missing_parameters(self):
        ''' fail if firmware_type is missing '''
        module_args = {}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(module_args)
            my_module()
        msg = 'missing required arguments: firmware_type'
        print('Info: %s' % exc.value.args[0]['msg'])
        assert exc.value.args[0]['msg'] == msg

    def test_invalid_firmware_type_parameters(self):
        ''' fail if firmware_type is missing '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'firmware_type': 'service_test'})
        set_module_args(module_args)
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(module_args)
            my_module()
        msg = 'value of firmware_type must be one of: service-processor, shelf, acp, disk, got: %s' % module_args['firmware_type']
        print('Info: %s' % exc.value.args[0]['msg'])
        assert exc.value.args[0]['msg'] == msg

    def test_ensure_sp_firmware_get_called(self):
        ''' a more interesting test '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'firmware_type': 'service-processor'})
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.server = self.server
        firmware_image_get = my_obj.firmware_image_get('node')
        print('Info: test_firmware_upgrade_get: %s' % repr(firmware_image_get))
        assert firmware_image_get is None

    def test_ensure_firmware_get_with_package_baseline_called(self):
        ''' a more interesting test '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'firmware_type': 'service-processor'})
        module_args.update({'package': 'test1.zip'})
        module_args.update({'install_baseline_image': True})
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(module_args)
            my_module()
        msg = 'Do not specify both package and install_baseline_image: true'
        print('info: ' + exc.value.args[0]['msg'])
        assert exc.value.args[0]['msg'] == msg

    def test_ensure_acp_firmware_required_get_called(self):
        ''' a test tp verify acp firmware upgrade is required or not  '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'firmware_type': 'acp'})
        set_module_args(module_args)
        my_obj = my_module()
        # my_obj.server = self.server
        my_obj.server = MockONTAPConnection(kind='acp')
        acp_firmware_required_get = my_obj.acp_firmware_required_get()
        print('Info: test_acp_firmware_upgrade_required_get: %s' % repr(acp_firmware_required_get))
        assert acp_firmware_required_get is True

    @patch('ansible.modules.storage.netapp.na_ontap_firmware_upgrade.NetAppONTAPFirmwareUpgrade.sp_firmware_image_update')
    @patch('ansible.modules.storage.netapp.na_ontap_firmware_upgrade.NetAppONTAPFirmwareUpgrade.sp_firmware_image_update_progress_get')
    def test_ensure_apply_for_firmware_upgrade_called(self, get_mock, update_mock):
        ''' updgrading firmware and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'package': 'test1.zip'})
        module_args.update({'firmware_type': 'service-processor'})
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.autosupport_log = Mock(return_value=None)
        if not self.use_vsim:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_firmware_upgrade_apply: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('firmware_upgrade', '3.5', 'true')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_firmware_upgrade_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
        update_mock.assert_called_with()

    def test_shelf_firmware_upgrade(self):
        ''' Test shelf firmware upgrade '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'firmware_type': 'shelf'})
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.autosupport_log = Mock(return_value=None)
        if not self.use_vsim:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_firmware_upgrade_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_firmware_upgrade.NetAppONTAPFirmwareUpgrade.acp_firmware_upgrade')
    @patch('ansible.modules.storage.netapp.na_ontap_firmware_upgrade.NetAppONTAPFirmwareUpgrade.acp_firmware_required_get')
    def test_acp_firmware_upgrade(self, get_mock, update_mock):
        ''' Test ACP firmware upgrade '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'firmware_type': 'acp'})
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.autosupport_log = Mock(return_value=None)
        if not self.use_vsim:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_firmware_upgrade_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_firmware_upgrade.NetAppONTAPFirmwareUpgrade.disk_firmware_upgrade')
    def test_disk_firmware_upgrade(self, get_mock):
        ''' Test disk firmware upgrade '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'firmware_type': 'disk'})
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.autosupport_log = Mock(return_value=None)
        if not self.use_vsim:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_firmware_upgrade_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
