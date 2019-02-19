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

from ansible.modules.storage.netapp.na_ontap_volume \
    import NetAppOntapVolume as vol_module  # module under test

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
        if self.kind == 'volume':
            xml = self.build_volume_info(self.params)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_volume_info(vol_details):
        ''' build xml data for volume-attributes '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'volume-attributes': {
                    'volume-id-attributes': {
                        'containing-aggregate-name': vol_details['aggregate'],
                        'junction-path': vol_details['junction_path']
                    },
                    'volume-export-attributes': {
                        'policy': 'default'
                    },
                    'volume-state-attributes': {
                        'state': "online"
                    },
                    'volume-space-attributes': {
                        'space-guarantee': 'none',
                        'size': vol_details['size']
                    },
                    'volume-snapshot-attributes': {
                        'snapshot-policy': vol_details['snapshot_policy']
                    },
                    'volume-security-attributes': {
                        'volume-security-unix-attributes': {
                            'permissions': vol_details['unix_permissions']
                        }
                    }
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
        self.mock_vol = {
            'name': 'test_vol',
            'aggregate': 'test_aggr',
            'junction_path': '/test',
            'vserver': 'test_vserver',
            'size': 20,
            'unix_permissions': '755',
            'snapshot_policy': 'default'
        }

    def mock_args(self):
        return {
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'aggregate_name': self.mock_vol['aggregate'],
            'space_guarantee': 'none',
            'policy': 'default',
            'is_online': True,
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'unix_permissions': '---rwxr-xr-x',
            'snapshot_policy': 'default'
        }

    def get_volume_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_volume object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_volume object
        """
        vol_obj = vol_module()
        vol_obj.ems_log_event = Mock(return_value=None)
        vol_obj.cluster = Mock()
        vol_obj.cluster.invoke_successfully = Mock()
        if kind is None:
            vol_obj.server = MockONTAPConnection()
        else:
            vol_obj.server = MockONTAPConnection(kind='volume', data=self.mock_vol)
        return vol_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            vol_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_volume(self):
        ''' Test if get_volume returns None for non-existent volume '''
        set_module_args(self.mock_args())
        result = self.get_volume_mock_object().get_volume()
        assert result is None

    def test_get_existing_volume(self):
        ''' Test if get_volume returns details for existing volume '''
        set_module_args(self.mock_args())
        result = self.get_volume_mock_object('volume').get_volume()
        assert result['name'] == self.mock_vol['name']
        assert result['size'] == self.mock_vol['size']

    def test_create_error_missing_param(self):
        ''' Test if create throws an error if aggregate_name is not specified'''
        data = self.mock_args()
        del data['aggregate_name']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_volume_mock_object('volume').create_volume()
        msg = 'Error provisioning volume test_vol: aggregate_name is required'
        assert exc.value.args[0]['msg'] == msg

    def test_successful_create(self):
        ''' Test successful create '''
        data = self.mock_args()
        data['size'] = 20
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_create_idempotency(self):
        ''' Test create idempotency '''
        set_module_args(self.mock_args())
        obj = self.get_volume_mock_object('volume')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert not exc.value.args[0]['changed']

    def test_successful_delete(self):
        ''' Test delete existing volume '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    def test_delete_idempotency(self):
        ''' Test delete idempotency '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object().apply()
        assert not exc.value.args[0]['changed']

    def test_successful_modify_size(self):
        ''' Test successful modify size '''
        data = self.mock_args()
        data['size'] = 200
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    def test_modify_idempotency(self):
        ''' Test modify idempotency '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert not exc.value.args[0]['changed']

    def test_mount_volume(self):
        ''' Test mount volume '''
        data = self.mock_args()
        data['junction_path'] = "/test123"
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    def test_unmount_volume(self):
        ''' Test unmount volume '''
        data = self.mock_args()
        data['junction_path'] = ""
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    def test_successful_modify_space(self):
        ''' Test successful modify space '''
        data = self.mock_args()
        data['space_guarantee'] = 'volume'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    def test_successful_modify_state(self):
        ''' Test successful modify state '''
        data = self.mock_args()
        data['is_online'] = False
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    def test_successful_modify_unix_permissions(self):
        ''' Test successful modify unix_permissions '''
        data = self.mock_args()
        data['unix_permissions'] = '---rw-r-xr-x'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    def test_successful_modify_snapshot_policy(self):
        ''' Test successful modify snapshot_policy '''
        data = self.mock_args()
        data['snapshot_policy'] = 'default-1weekly'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    def test_successful_move(self):
        ''' Test successful modify aggregate '''
        data = self.mock_args()
        data['aggregate_name'] = 'different_aggr'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object('volume').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.change_volume_state')
    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.volume_mount')
    def test_modify_helper(self, mount_volume, change_state):
        data = self.mock_args()
        set_module_args(data)
        modify = {
            'is_online': False,
            'junction_path': 'something'
        }
        obj = self.get_volume_mock_object('volume')
        obj.modify_volume(modify)
        change_state.assert_called_with()
        mount_volume.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_true_1(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '------------'
        set_module_args(data)
        current = {
            'unix_permissions': '0'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert obj.compare_chmod_value(current)

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_true_2(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '---rwxrwxrwx'
        set_module_args(data)
        current = {
            'unix_permissions': '777'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert obj.compare_chmod_value(current)

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_true_3(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '---rwxr-xr-x'
        set_module_args(data)
        current = {
            'unix_permissions': '755'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert obj.compare_chmod_value(current)

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_true_3(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '755'
        set_module_args(data)
        current = {
            'unix_permissions': '755'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert obj.compare_chmod_value(current)

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_false_1(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '---rwxrwxrwx'
        set_module_args(data)
        current = {
            'unix_permissions': '0'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert not obj.compare_chmod_value(current)

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_false_2(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '---rwxrwxrwx'
        set_module_args(data)
        current = None
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert not obj.compare_chmod_value(current)

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_invalid_input_1(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '---xwrxwrxwr'
        set_module_args(data)
        current = {
            'unix_permissions': '777'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert not obj.compare_chmod_value(current)

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_invalid_input_2(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '---rwx-wx--a'
        set_module_args(data)
        current = {
            'unix_permissions': '0'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert not obj.compare_chmod_value(current)

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_compare_chmod_value_invalid_input_3(self, get_volume):
        data = self.mock_args()
        data['unix_permissions'] = '---'
        set_module_args(data)
        current = {
            'unix_permissions': '0'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object()
        assert not obj.compare_chmod_value(current)
