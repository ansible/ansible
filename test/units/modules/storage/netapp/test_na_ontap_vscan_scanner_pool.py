# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests for Ansible module: na_ontap_vscan_scanner_pool '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_vscan_scanner_pool \
    import NetAppOntapVscanScannerPool as scanner_module  # module under test

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
        if self.kind == 'scanner':
            xml = self.build_scanner_pool_info(self.params)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_scanner_pool_info(sanner_details):
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'vscan-scanner-pool-info': {
                    'scanner-pool': sanner_details['scanner_pool'],
                    'scanner-policy': sanner_details['scanner_policy']
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
        self.mock_scanner = {
            'state': 'present',
            'scanner_pool': 'test_pool',
            'vserver': 'test_vserver',
            'hostnames': ['host1', 'host2'],
            'privileged_users': ['domain\\admin', 'domain\\carchi8py'],
            'scanner_policy': 'primary'
        }

    def mock_args(self):
        return {
            'state': self.mock_scanner['state'],
            'scanner_pool': self.mock_scanner['scanner_pool'],
            'vserver': self.mock_scanner['vserver'],
            'hostnames': self.mock_scanner['hostnames'],
            'privileged_users': self.mock_scanner['privileged_users'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'scanner_policy': self.mock_scanner['scanner_policy']
        }

    def get_scanner_mock_object(self, kind=None):
        scanner_obj = scanner_module()
        scanner_obj.asup_log_for_cserver = Mock(return_value=None)
        if kind is None:
            scanner_obj.server = MockONTAPConnection()
        else:
            scanner_obj.server = MockONTAPConnection(kind='scanner', data=self.mock_scanner)
        return scanner_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            scanner_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_scanner(self):
        ''' Test if get_scanner_pool returns None for non-existent job '''
        set_module_args(self.mock_args())
        result = self.get_scanner_mock_object().get_scanner_pool()
        assert not result

    def test_get_existing_scanner(self):
        ''' Test if get_scanner_pool returns None for non-existent job '''
        set_module_args(self.mock_args())
        result = self.get_scanner_mock_object('scanner').get_scanner_pool()
        assert result

    def test_successfully_create(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_scanner_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_create_idempotency(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_scanner_mock_object('scanner').apply()
        assert not exc.value.args[0]['changed']

    def test_apply_policy(self):
        data = self.mock_args()
        data['scanner_policy'] = 'secondary'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_scanner_mock_object('scanner').apply()
        assert exc.value.args[0]['changed']

    def test_successfully_delete(self):
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_scanner_mock_object('scanner').apply()
        assert exc.value.args[0]['changed']

    def test_delete_idempotency(self):
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_scanner_mock_object().apply()
        assert not exc.value.args[0]['changed']
