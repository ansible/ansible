''' unit tests for Ansible module: na_ontap_vscan_on_demand_task '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_vscan_on_demand_task \
    import NetAppOntapVscanOnDemandTask as onDemand_module  # module under test

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
        if self.kind == 'task':
            xml = self.build_onDemand_pool_info(self.params)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_onDemand_pool_info(onDemand_details):
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'vscan-on-demand-task-info': {
                    'task-name': onDemand_details['task_name'],
                    'report-directory': onDemand_details['report_directory'],
                    'scan-paths': {
                        'string': onDemand_details['scan_paths']
                    }
                }
            }
        }
        xml.translate_struct(attributes)
        return xml


class TestMyModule(unittest.TestCase):
    ''' Unit tests for na_ontap_job_schedule '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        self.mock_onDemand = {
            'state': 'present',
            'vserver': 'test_vserver',
            'report_directory': '/',
            'task_name': '/',
            'scan_paths': '/'
        }

    def mock_args(self):
        return {
            'state': self.mock_onDemand['state'],
            'vserver': self.mock_onDemand['vserver'],
            'report_directory': self.mock_onDemand['report_directory'],
            'task_name': self.mock_onDemand['task_name'],
            'scan_paths': self.mock_onDemand['scan_paths'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_demand_mock_object(self, kind=None):
        scanner_obj = onDemand_module()
        scanner_obj.asup_log_for_cserver = Mock(return_value=None)
        if kind is None:
            scanner_obj.server = MockONTAPConnection()
        else:
            scanner_obj.server = MockONTAPConnection(kind='task', data=self.mock_onDemand)
        return scanner_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            onDemand_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_demand_task(self):
        set_module_args(self.mock_args())
        result = self.get_demand_mock_object().get_demand_task()
        assert not result

    def test_get_existing_demand_task(self):
        set_module_args(self.mock_args())
        result = self.get_demand_mock_object('task').get_demand_task()
        assert result

    def test_successfully_create(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_demand_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_create_idempotency(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_demand_mock_object('task').apply()
        assert not exc.value.args[0]['changed']

    def test_successfully_delete(self):
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_demand_mock_object('task').apply()
        assert exc.value.args[0]['changed']

    def test_delete_idempotency(self):
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_demand_mock_object().apply()
        assert not exc.value.args[0]['changed']
