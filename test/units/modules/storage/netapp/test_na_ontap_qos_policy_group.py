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

from ansible.modules.storage.netapp.na_ontap_qos_policy_group \
    import NetAppOntapQosPolicyGroup as qos_policy_group_module  # module under test

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
                'qos-policy-group-info': {
                    'is-shared': 'true',
                    'max-throughput': '800KB/s,800IOPS',
                    'min-throughput': '100IOPS',
                    'num-workloads': 0,
                    'pgid': 8690,
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
            'max_throughput': '800KB/s,800IOPS',
            'min_throughput': '100IOPS'
        }

    def mock_args(self):
        return {
            'name': self.mock_policy_group['name'],
            'vserver': self.mock_policy_group['vserver'],
            'max_throughput': '800KB/s,800IOPS',
            'min_throughput': '100IOPS',
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
        policy_obj.asup_log_for_cserver = Mock(return_value=None)
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

    @patch('ansible.modules.storage.netapp.na_ontap_qos_policy_group.NetAppOntapQosPolicyGroup.get_policy_group')
    def test_create_error(self, get_policy_group):
        ''' Test create error '''
        set_module_args(self.mock_args())
        get_policy_group.side_effect = [
            None
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error creating qos policy group policy_1: NetApp API failed. Reason - test:error'

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

    @patch('ansible.modules.storage.netapp.na_ontap_qos_policy_group.NetAppOntapQosPolicyGroup.get_policy_group')
    def test_delete_error(self, get_policy_group):
        ''' Test create idempotency '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        current = {
            'max_throughput': '800KB/s,800IOPS',
            'min_throughput': '100IOPS',
            'name': 'policy_1',
            'vserver': 'policy_vserver'
        }
        get_policy_group.side_effect = [
            current
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error deleting qos policy group policy_1: NetApp API failed. Reason - test:error'

    def test_successful_modify_max_throughput(self):
        ''' Test successful modify max throughput '''
        data = self.mock_args()
        data['max_throughput'] = '900KB/s,800iops'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object('policy').apply()
        assert exc.value.args[0]['changed']

    def test_modify_max_throughput_idempotency(self):
        ''' Test modify idempotency '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_policy_group_mock_object('policy').apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_qos_policy_group.NetAppOntapQosPolicyGroup.get_policy_group')
    def test_modify_error(self, get_policy_group):
        ''' Test create idempotency '''
        data = self.mock_args()
        data['max_throughput'] = '900KB/s,900IOPS'
        set_module_args(data)
        current = {
            'max_throughput': '800KB/s,800IOPS',
            'min_throughput': '100IOPS',
            'name': 'policy_1',
            'vserver': 'policy_vserver'
        }
        get_policy_group.side_effect = [
            current
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error modifying qos policy group policy_1: NetApp API failed. Reason - test:error'

    @patch('ansible.modules.storage.netapp.na_ontap_qos_policy_group.NetAppOntapQosPolicyGroup.get_policy_group')
    def test_rename(self, get_policy_group):
        ''' Test rename idempotency '''
        data = self.mock_args()
        data['name'] = 'policy_2'
        data['from_name'] = 'policy_1'
        set_module_args(data)
        current = {
            'max_throughput': '800KB/s,800IOPS',
            'min_throughput': '100IOPS',
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

    @patch('ansible.modules.storage.netapp.na_ontap_qos_policy_group.NetAppOntapQosPolicyGroup.get_policy_group')
    def test_rename_idempotency(self, get_policy_group):
        ''' Test rename idempotency '''
        data = self.mock_args()
        data['name'] = 'policy_1'
        data['from_name'] = 'policy_1'
        current = {
            'max_throughput': '800KB/s,800IOPS',
            'min_throughput': '100IOPS',
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

    @patch('ansible.modules.storage.netapp.na_ontap_qos_policy_group.NetAppOntapQosPolicyGroup.get_policy_group')
    def test_rename_error(self, get_policy_group):
        ''' Test create idempotency '''
        data = self.mock_args()
        data['from_name'] = 'policy_1'
        data['name'] = 'policy_2'
        set_module_args(data)
        current = {
            'is_shared': 'true',
            'max_throughput': '800KB/s,800IOPS',
            'min_throughput': '100IOPS',
            'name': 'policy_1',
            'vserver': 'policy_vserver'
        }
        get_policy_group.side_effect = [
            None,
            current
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_policy_group_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error renaming qos policy group policy_1: NetApp API failed. Reason - test:error'
