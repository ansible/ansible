# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test template for ONTAP Ansible module '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_qos_adaptive_policy_group \
    import NetAppOntapAdaptiveQosPolicyGroup as qos_policy_group_module  # module under test

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
        if self.kind == 'policy':
            xml = self.build_policy_group_info(self.params)
        if self.kind == 'error':
            error = netapp_utils.zapi.NaApiError('test', 'error')
            raise error
        self.xml_out = xml
        return xml

    @staticmethod
    def build_policy_group_info(vol_details):
        ''' build xml data for volume-attributes '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'qos-adaptive-policy-group-info': {
                    'absolute-min-iops': '50IOPS',
                    'expected-iops': '150IOPS/TB',
                    'peak-iops': '220IOPS/TB',
                    'peak-iops-allocation': 'used_space',
                    'num-workloads': 0,
                    'pgid': 6941,
                    'policy-group': vol_details['name'],
                    'vserver': vol_details['vserver']
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
        self.mock_policy_group = {
            'name': 'policy_1',
            'vserver': 'policy_vserver',
            'absolute_min_iops': '50IOPS',
            'expected_iops': '150IOPS/TB',
            'peak_iops': '220IOPS/TB',
            'peak_iops_allocation': 'used_space'
        }

    def mock_args(self):
        return {
            'name': self.mock_policy_group['name'],
            'vserver': self.mock_policy_group['vserver'],
            'absolute_min_iops': '50IOPS',
            'expected_iops': '150IOPS/TB',
            'peak_iops': '220IOPS/TB',
            'peak_iops_allocation': 'used_space',
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'https': 'False'
        }

    def get_policy_group_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_volume object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_volume object
        """
        policy_obj = qos_policy_group_module()
        policy_obj.autosupport_log = Mock(return_value=None)
        policy_obj.cluster = Mock()
        policy_obj.cluster.invoke_successfully = Mock()
        if kind is None:
            policy_obj.server = MockONTAPConnection()
        else:
            policy_obj.server = MockONTAPConnection(kind=kind, data=self.mock_policy_group)
        return policy_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            qos_policy_group_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_policy(self):
        ''' Test if get_policy_group returns None for non-existent policy_group '''
        set_module_args(self.mock_args())
        result = self.get_policy_group_mock_object().get_policy_group()
        assert result is None

    def test_get_existing_policy_group(self):
        ''' Test if get_policy_group returns details for existing policy_group '''
        set_module_args(self.mock_args())
        result = self.get_policy_group_mock_object('policy').get_policy_group()
        assert result['name'] == self.mock_policy_group['name']
        assert result['vserver'] == self.mock_policy_group['vserver']

    def test_create_error_missing_param(self):
        ''' Test if create throws an error if name is not specified'''
        data = self.mock_args()
        del data['name']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('policy').create_policy_group()
        msg = 'missing required arguments: name'
        assert exc.value.args[0]['msg'] == msg

    def test_successful_create(self):
        ''' Test successful create '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_create_idempotency(self):
        ''' Test create idempotency '''
        set_module_args(self.mock_args())
        obj = self.get_policy_group_mock_object('policy')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_qos_adaptive_policy_group.NetAppOntapAdaptiveQosPolicyGroup.get_policy_group')
    def test_create_error(self, get_policy_group):
        ''' Test create error '''
        set_module_args(self.mock_args())
        get_policy_group.side_effect = [
            None
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error creating adaptive qos policy group policy_1: NetApp API failed. Reason - test:error'

    def test_successful_delete(self):
        ''' Test delete existing volume '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object('policy').apply()
        assert exc.value.args[0]['changed']

    def test_delete_idempotency(self):
        ''' Test delete idempotency '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object().apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_qos_adaptive_policy_group.NetAppOntapAdaptiveQosPolicyGroup.get_policy_group')
    def test_delete_error(self, get_policy_group):
        ''' Test create idempotency'''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        current = {
            'absolute_min_iops': '50IOPS',
            'expected_iops': '150IOPS/TB',
            'peak_iops': '220IOPS/TB',
            'peak_iops_allocation': 'used_space',
            'name': 'policy_1',
            'vserver': 'policy_vserver'
        }
        get_policy_group.side_effect = [
            current
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error deleting adaptive qos policy group policy_1: NetApp API failed. Reason - test:error'

    def test_successful_modify_expected_iops(self):
        ''' Test successful modify expected iops '''
        data = self.mock_args()
        data['expected_iops'] = '175IOPS'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object('policy').apply()
        assert exc.value.args[0]['changed']

    def test_modify_expected_iops_idempotency(self):
        ''' Test modify idempotency '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object('policy').apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_qos_adaptive_policy_group.NetAppOntapAdaptiveQosPolicyGroup.get_policy_group')
    def test_modify_error(self, get_policy_group):
        ''' Test create idempotency '''
        data = self.mock_args()
        data['expected_iops'] = '175IOPS'
        set_module_args(data)
        current = {
            'absolute_min_iops': '50IOPS',
            'expected_iops': '150IOPS/TB',
            'peak_iops': '220IOPS/TB',
            'peak_iops_allocation': 'used_space',
            'name': 'policy_1',
            'vserver': 'policy_vserver'
        }
        get_policy_group.side_effect = [
            current
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error modifying adaptive qos policy group policy_1: NetApp API failed. Reason - test:error'

    @patch('ansible.modules.storage.netapp.na_ontap_qos_adaptive_policy_group.NetAppOntapAdaptiveQosPolicyGroup.get_policy_group')
    def test_rename(self, get_policy_group):
        ''' Test rename idempotency '''
        data = self.mock_args()
        data['name'] = 'policy_2'
        data['from_name'] = 'policy_1'
        set_module_args(data)
        current = {
            'absolute_min_iops': '50IOPS',
            'expected_iops': '150IOPS/TB',
            'peak_iops': '220IOPS/TB',
            'peak_iops_allocation': 'used_space',
            'name': 'policy_1',
            'vserver': 'policy_vserver'
        }
        get_policy_group.side_effect = [
            None,
            current
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object('policy').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_qos_adaptive_policy_group.NetAppOntapAdaptiveQosPolicyGroup.get_policy_group')
    def test_rename_idempotency(self, get_policy_group):
        ''' Test rename idempotency '''
        data = self.mock_args()
        data['name'] = 'policy_1'
        data['from_name'] = 'policy_1'
        current = {
            'absolute_min_iops': '50IOPS',
            'expected_iops': '150IOPS/TB',
            'peak_iops': '220IOPS/TB',
            'peak_iops_allocation': 'used_space',
            'name': 'policy_1',
            'vserver': 'policy_vserver'
        }
        get_policy_group.side_effect = [
            current,
            current
        ]
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object('policy').apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_qos_adaptive_policy_group.NetAppOntapAdaptiveQosPolicyGroup.get_policy_group')
    def test_rename_error(self, get_policy_group):
        ''' Test create idempotency '''
        data = self.mock_args()
        data['from_name'] = 'policy_1'
        data['name'] = 'policy_2'
        set_module_args(data)
        current = {
            'absolute_min_iops': '50IOPS',
            'expected_iops': '150IOPS/TB',
            'peak_iops': '220IOPS/TB',
            'peak_iops_allocation': 'used_space',
            'is_shared': 'true',
            'name': 'policy_1',
            'vserver': 'policy_vserver'
        }
        get_policy_group.side_effect = [
            None,
            current
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error renaming adaptive qos policy group policy_1: NetApp API failed. Reason - test:error'
