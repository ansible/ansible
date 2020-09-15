# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests for Ansible module: na_ontap_vscan'''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_vscan \
    import NetAppOntapVscan as vscan_module  # module under test

if not netapp_utils.has_netapp_lib():
    pytestmark = pytest.mark.skip('skipping as missing required netapp_lib')
HAS_NETAPP_ZAPI_MSG = "pip install netapp_lib is required"


# REST API canned responses when mocking send_request
SRR = {
    # common responses
    'is_rest': (200, None),
    'is_zapi': (400, "Unreachable"),
    'empty_good': ({}, None),
    'end_of_sequence': (None, "Ooops, the UT needs one more SRR response"),
    'generic_error': (None, "Expected error"),
    # module specific responses
    'enabled': ({'records': [{'enabled': True, 'svm': {'uuid': 'testuuid'}}]}, None),
    'disabled': ({'records': [{'enabled': False, 'svm': {'uuid': 'testuuid'}}]}, None),
}


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
        if self.kind == 'enable':
            xml = self.build_vscan_status_info(self.params)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_vscan_status_info(status):
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {'num-records': 1,
                      'attributes-list': {'vscan-status-info': {'is-vscan-enabled': status}}}
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

    def mock_args(self):
        return {
            'enable': False,
            'vserver': 'vserver',
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_vscan_mock_object(self, type='zapi', kind=None, status=None):
        vscan_obj = vscan_module()
        if type == 'zapi':
            if kind is None:
                vscan_obj.server = MockONTAPConnection()
            else:
                vscan_obj.server = MockONTAPConnection(kind=kind, data=status)
        # For rest, mocking is achieved through side_effect
        return vscan_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            vscan_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_successfully_enable(self):
        data = self.mock_args()
        data['enable'] = True
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_vscan_mock_object('zapi', 'enable', 'false').apply()
        assert exc.value.args[0]['changed']

    def test_idempotently_enable(self):
        data = self.mock_args()
        data['enable'] = True
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_vscan_mock_object('zapi', 'enable', 'true').apply()
        assert not exc.value.args[0]['changed']

    def test_successfully_disable(self):
        data = self.mock_args()
        data['enable'] = False
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_vscan_mock_object('zapi', 'enable', 'true').apply()
        assert exc.value.args[0]['changed']

    def test_idempotently_disable(self):
        data = self.mock_args()
        data['enable'] = False
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_vscan_mock_object('zapi', 'enable', 'false').apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.OntapRestAPI.send_request')
    def test_rest_error(self, mock_request):
        data = self.mock_args()
        set_module_args(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['generic_error'],
            SRR['end_of_sequence']
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_vscan_mock_object(type='rest').apply()
        assert exc.value.args[0]['msg'] == SRR['generic_error'][1]

    @patch('ansible.module_utils.netapp.OntapRestAPI.send_request')
    def test_rest_successly_enable(self, mock_request):
        data = self.mock_args()
        data['enable'] = True
        set_module_args(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['disabled'],
            SRR['empty_good'],
            SRR['end_of_sequence']
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_vscan_mock_object(type='rest').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.OntapRestAPI.send_request')
    def test_rest_idempotently_enable(self, mock_request):
        data = self.mock_args()
        data['enable'] = True
        set_module_args(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['enabled'],
            SRR['end_of_sequence']
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_vscan_mock_object(type='rest').apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.OntapRestAPI.send_request')
    def test_rest_successly_disable(self, mock_request):
        data = self.mock_args()
        data['enable'] = False
        set_module_args(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['enabled'],
            SRR['empty_good'],
            SRR['end_of_sequence']
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_vscan_mock_object(type='rest').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.OntapRestAPI.send_request')
    def test_rest_idempotently_disable(self, mock_request):
        data = self.mock_args()
        data['enable'] = False
        set_module_args(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['disabled'],
            SRR['end_of_sequence']
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_vscan_mock_object(type='rest').apply()
        assert not exc.value.args[0]['changed']
