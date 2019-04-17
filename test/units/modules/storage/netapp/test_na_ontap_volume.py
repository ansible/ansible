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

    def __init__(self, kind=None, data=None, job_error=None):
        ''' save arguments '''
        self.kind = kind
        self.params = data
        self.xml_in = None
        self.xml_out = None
        self.job_error = job_error

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.kind == 'volume':
            xml = self.build_volume_info(self.params)
        elif self.kind == 'job_info':
            xml = self.build_job_info(self.job_error)
        elif self.kind == 'error_modify':
            xml = self.build_modify_error()
        elif self.kind == 'failure_modify_async':
            xml = self.build_failure_modify_async()
        elif self.kind == 'success_modify_async':
            xml = self.build_success_modify_async()
        elif self.kind == 'zapi_error':
            error = netapp_utils.zapi.NaApiError('test', 'error')
            raise error
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
                        'junction-path': vol_details['junction_path'],
                        'style-extended': 'flexvol'
                    },
                    'volume-language-attributes': {
                        'language-code': 'en'
                    },
                    'volume-export-attributes': {
                        'policy': 'default'
                    },
                    'volume-performance-attributes': {
                        'is-atime-update-enabled': 'true'
                    },
                    'volume-state-attributes': {
                        'state': "online"
                    },
                    'volume-space-attributes': {
                        'space-guarantee': 'none',
                        'size': vol_details['size'],
                        'percentage-snapshot-reserve': vol_details['percent_snapshot_space']
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

    @staticmethod
    def build_flex_group_info(vol_details):
        ''' build xml data for flexGroup volume-attributes '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'volume-attributes': {
                    'volume-id-attributes': {
                        'aggr-list': vol_details['aggregate'],
                        'junction-path': vol_details['junction_path'],
                        'style-extended': 'flexgroup'
                    },
                    'volume-language-attributes': {
                        'language-code': 'en'
                    },
                    'volume-export-attributes': {
                        'policy': 'default'
                    },
                    'volume-performance-attributes': {
                        'is-atime-update-enabled': 'true'
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

    @staticmethod
    def build_job_info(error):
        ''' build xml data for a job '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = netapp_utils.zapi.NaElement('attributes')
        if error is None:
            state = 'success'
        elif error == 'time_out':
            state = 'running'
        elif error == 'failure':
            state = 'failure'
        else:
            state = 'other'
        attributes.add_node_with_children('job-info', **{
            'job-state': state,
            'job-progress': 'dummy',
            'job-completion': error,
        })
        xml.add_child_elem(attributes)
        xml.add_new_child('result-status', 'in_progress')
        xml.add_new_child('result-jobid', '1234')
        return xml

    @staticmethod
    def build_modify_error():
        ''' build xml data for modify error '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = netapp_utils.zapi.NaElement('failure-list')
        info_list_obj = netapp_utils.zapi.NaElement('volume-modify-iter-info')
        info_list_obj.add_new_child('error-message', 'modify error message')
        attributes.add_child_elem(info_list_obj)
        xml.add_child_elem(attributes)
        return xml

    @staticmethod
    def build_success_modify_async():
        ''' build xml data for success modify async '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = netapp_utils.zapi.NaElement('success-list')
        info_list_obj = netapp_utils.zapi.NaElement('volume-modify-iter-async-info')
        info_list_obj.add_new_child('status', 'in_progress')
        info_list_obj.add_new_child('jobid', '1234')
        attributes.add_child_elem(info_list_obj)
        xml.add_child_elem(attributes)
        return xml

    @staticmethod
    def build_failure_modify_async():
        ''' build xml data for failure modify async '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = netapp_utils.zapi.NaElement('failure-list')
        info_list_obj = netapp_utils.zapi.NaElement('volume-modify-iter-async-info')
        info_list_obj.add_new_child('status', 'failed')
        info_list_obj.add_new_child('jobid', '1234')
        info_list_obj.add_new_child('error-message', 'modify error message')
        attributes.add_child_elem(info_list_obj)
        xml.add_child_elem(attributes)
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
            'size': 20971520,
            'unix_permissions': '755',
            'snapshot_policy': 'default',
            'percent_snapshot_space': 60,
            'language': 'en'
        }

    def mock_args(self, tag=None):
        args = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'space_guarantee': 'none',
            'policy': 'default',
            'language': self.mock_vol['language'],
            'is_online': True,
            'unix_permissions': '---rwxr-xr-x',
            'snapshot_policy': 'default',
            'size': 20,
            'size_unit': 'mb',
            'junction_path': '/test',
            'percent_snapshot_space': 60,
            'type': 'type'
        }
        if tag is None:
            args['aggregate_name'] = self.mock_vol['aggregate']
            return args

        elif tag == 'flexGroup_manual':
            args['aggr_list'] = 'aggr_0,aggr_1'
            args['aggr_list_multiplier'] = 2
            return args

        elif tag == 'flexGroup_auto':
            args['auto_provision_as'] = 'flexgroup'
            return args

    def get_volume_mock_object(self, kind=None, job_error=None):
        """
        Helper method to return an na_ontap_volume object
        :param kind: passes this param to MockONTAPConnection().
        :param job_error: error message when getting job status.
        :return: na_ontap_volume object
        """
        vol_obj = vol_module()
        vol_obj.ems_log_event = Mock(return_value=None)
        vol_obj.cluster = Mock()
        vol_obj.cluster.invoke_successfully = Mock()
        vol_obj.volume_style = None
        if kind is None:
            vol_obj.server = MockONTAPConnection()
        elif kind == 'volume':
            vol_obj.server = MockONTAPConnection(kind='volume', data=self.mock_vol)
        elif kind == 'job_info':
            vol_obj.server = MockONTAPConnection(kind='job_info', data=self.mock_vol, job_error=job_error)
        elif kind == 'error_modify':
            vol_obj.server = MockONTAPConnection(kind='error_modify', data=self.mock_vol)
        elif kind == 'failure_modify_async':
            vol_obj.server = MockONTAPConnection(kind='failure_modify_async', data=self.mock_vol)
        elif kind == 'success_modify_async':
            vol_obj.server = MockONTAPConnection(kind='success_modify_async', data=self.mock_vol)
        elif kind == 'zapi_error':
            vol_obj.server = MockONTAPConnection(kind='zapi_error', data=self.mock_vol)
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

    def test_modify_error(self):
        ''' Test modify idempotency '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_volume_mock_object('error_modify').volume_modify_attributes()
        assert exc.value.args[0]['msg'] == 'Error modifying volume test_vol: modify error message'

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

    def test_successful_modify_percent_snapshot_space(self):
        ''' Test successful modify snapshot_policy '''
        data = self.mock_args()
        data['percent_snapshot_space'] = '90'
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

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_successful_rename(self, get_volume):
        ''' Test successful rename volume '''
        data = self.mock_args()
        data['from_name'] = self.mock_vol['name']
        data['name'] = 'new_name'
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
        }
        get_volume.side_effect = [
            None,
            current
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_volume_mock_object().apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_successful_rename_async(self, get_volume):
        ''' Test successful rename volume '''
        data = self.mock_args()
        data['from_name'] = self.mock_vol['name']
        data['name'] = 'new_name'
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'is_infinite': True
        }
        get_volume.side_effect = [
            None,
            current
        ]
        obj = self.get_volume_mock_object('job_info')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
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

    def test_successful_create_flex_group_manually(self):
        ''' Test successful create flexGroup manually '''
        data = self.mock_args('flexGroup_manual')
        data['time_out'] = 20
        set_module_args(data)
        obj = self.get_volume_mock_object('job_info')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    def test_successful_create_flex_group_auto_provision(self):
        ''' Test successful create flexGroup auto provision '''
        data = self.mock_args('flexGroup_auto')
        data['time_out'] = 20
        set_module_args(data)
        obj = self.get_volume_mock_object('job_info')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_successful_delete_flex_group(self, get_volume):
        ''' Test successful delete felxGroup '''
        data = self.mock_args('flexGroup_manual')
        data['state'] = 'absent'
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'style_extended': 'flexgroup',
            'unix_permissions': '755'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object('job_info')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_successful_resize_flex_group(self, get_volume):
        ''' Test successful reszie flexGroup '''
        data = self.mock_args('flexGroup_manual')
        data['size'] = 400
        data['size_unit'] = 'mb'
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'style_extended': 'flexgroup',
            'size': 20971520,
            'unix_permissions': '755'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object('job_info')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.check_job_status')
    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_successful_modify_unix_permissions_flex_group(self, get_volume, check_job_status):
        ''' Test successful modify unix permissions flexGroup '''
        data = self.mock_args('flexGroup_manual')
        data['time_out'] = 20
        data['unix_permissions'] = '---rw-r-xr-x'
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'style_extended': 'flexgroup',
            'unix_permissions': '777'
        }
        get_volume.side_effect = [
            current
        ]
        check_job_status.side_effect = [
            None
        ]
        obj = self.get_volume_mock_object('success_modify_async')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_successful_modify_unix_permissions_flex_group_0_time_out(self, get_volume):
        ''' Test successful modify unix permissions flexGroup '''
        data = self.mock_args('flexGroup_manual')
        data['time_out'] = 0
        data['unix_permissions'] = '---rw-r-xr-x'
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'style_extended': 'flexgroup',
            'unix_permissions': '777'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object('success_modify_async')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.check_job_status')
    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_error_modify_unix_permissions_flex_group(self, get_volume, check_job_status):
        ''' Test error modify unix permissions flexGroup '''
        data = self.mock_args('flexGroup_manual')
        data['time_out'] = 20
        data['unix_permissions'] = '---rw-r-xr-x'
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'style_extended': 'flexgroup',
            'unix_permissions': '777'
        }
        get_volume.side_effect = [
            current
        ]
        check_job_status.side_effect = ['error']
        obj = self.get_volume_mock_object('success_modify_async')
        with pytest.raises(AnsibleFailJson) as exc:
            obj.apply()
        assert exc.value.args[0]['msg'] == 'Error when modify volume: error'

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_failure_modify_unix_permissions_flex_group(self, get_volume):
        ''' Test failure modify unix permissions flexGroup '''
        data = self.mock_args('flexGroup_manual')
        data['unix_permissions'] = '---rw-r-xr-x'
        data['time_out'] = 20
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'style_extended': 'flexvol',
            'unix_permissions': '777'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object('failure_modify_async')
        with pytest.raises(AnsibleFailJson) as exc:
            obj.apply()
        assert exc.value.args[0]['msg'] == 'Error modifying volume test_vol: modify error message'

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_successful_offline_state_flex_group(self, get_volume):
        ''' Test successful offline flexGroup state '''
        data = self.mock_args('flexGroup_manual')
        data['is_online'] = False
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'style_extended': 'flexgroup',
            'is_online': True,
            'junction_path': 'anything',
            'unix_permissions': '755'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object('job_info')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_volume.NetAppOntapVolume.get_volume')
    def test_successful_online_state_flex_group(self, get_volume):
        ''' Test successful online flexGroup state '''
        data = self.mock_args('flexGroup_manual')
        set_module_args(data)
        current = {
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'name': self.mock_vol['name'],
            'vserver': self.mock_vol['vserver'],
            'style_extended': 'flexgroup',
            'is_online': False,
            'junction_path': 'anything',
            'unix_permissions': '755'
        }
        get_volume.side_effect = [
            current
        ]
        obj = self.get_volume_mock_object('job_info')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']

    def test_check_job_status_error(self):
        ''' Test check job status error '''
        data = self.mock_args('flexGroup_manual')
        data['time_out'] = 0
        set_module_args(data)
        obj = self.get_volume_mock_object('job_info', job_error='failure')
        result = obj.check_job_status('123')
        assert result == 'failure'

    def test_check_job_status_time_out_is_0(self):
        ''' Test check job status time out is 0'''
        data = self.mock_args('flexGroup_manual')
        data['time_out'] = 0
        set_module_args(data)
        obj = self.get_volume_mock_object('job_info', job_error='time_out')
        result = obj.check_job_status('123')
        assert result == 'job completion exceeded expected timer of: 0 seconds'

    def test_check_job_status_unexpected(self):
        ''' Test check job status unexpected state '''
        data = self.mock_args('flexGroup_manual')
        data['time_out'] = 20
        set_module_args(data)
        obj = self.get_volume_mock_object('job_info', job_error='other')
        with pytest.raises(AnsibleFailJson) as exc:
            obj.check_job_status('123')
        assert exc.value.args[0]['failed']

    def test_error_assign_efficiency_policy(self):
        data = self.mock_args()
        data['efficiency_policy'] = 'test_policy'
        set_module_args(data)
        obj = self.get_volume_mock_object('zapi_error')
        with pytest.raises(AnsibleFailJson) as exc:
            obj.assign_efficiency_policy()
        assert exc.value.args[0]['msg'] == 'Error enable efficiency on volume test_vol: NetApp API failed. Reason - test:error'

    def test_error_assign_efficiency_policy_async(self):
        data = self.mock_args()
        data['efficiency_policy'] = 'test_policy'
        set_module_args(data)
        obj = self.get_volume_mock_object('zapi_error')
        with pytest.raises(AnsibleFailJson) as exc:
            obj.assign_efficiency_policy_async()
        assert exc.value.args[0]['msg'] == 'Error enable efficiency on volume test_vol: NetApp API failed. Reason - test:error'
