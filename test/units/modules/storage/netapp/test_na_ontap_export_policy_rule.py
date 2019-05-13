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

from ansible.modules.storage.netapp.na_ontap_export_policy_rule \
    import NetAppontapExportRule as policy_rule  # module under test

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
        self.data = data
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.kind == 'rule':
            xml = self.build_policy_rule(self.data)
        if self.kind == 'rules':
            xml = self.build_policy_rule(self.data, multiple=True)
        if self.kind == 'policy':
            xml = self.build_policy()
        self.xml_out = xml
        return xml

    @staticmethod
    def build_policy_rule(policy, multiple=False):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {'attributes-list': {
            'export-rule-info': {
                'policy-name': policy['name'],
                'client-match': policy['client_match'],
                'ro-rule': {
                    'security-flavor': 'any'
                },
                'rw-rule': {
                    'security-flavor': 'any'
                },
                'protocol': {
                    'access-protocol': policy['protocol']
                },
                'super-user-security': {
                    'security-flavor': 'any'
                },
                'is-allow-set-uid-enabled': 'false',
                'rule-index': policy['rule_index']
            }
        }, 'num-records': 2 if multiple is True else 1}
        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_policy():
        ''' build xml data for export-policy-get-iter '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,

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
        self.mock_rule = {
            'name': 'test',
            'protocol': 'nfs',
            'client_match': '1.1.1.0',
            'rule_index': 10
        }

    def mock_rule_args(self):
        return {
            'name': self.mock_rule['name'],
            'client_match': self.mock_rule['client_match'],
            'vserver': 'test',
            'protocol': self.mock_rule['protocol'],
            'rule_index': self.mock_rule['rule_index'],
            'ro_rule': 'any',
            'rw_rule': 'any',
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_firewall_policy object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_firewall_policy object
        """
        obj = policy_rule()
        obj.autosupport_log = Mock(return_value=None)
        if kind is None:
            obj.server = MockONTAPConnection()
        else:
            obj.server = MockONTAPConnection(kind=kind, data=self.mock_rule_args())
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            policy_rule()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_rule(self):
        ''' Test if get_export_policy_rule returns None for non-existent policy '''
        set_module_args(self.mock_rule_args())
        result = self.get_mock_object().get_export_policy_rule()
        assert result is None

    def test_get_nonexistent_policy(self):
        ''' Test if get_export_policy returns None for non-existent policy '''
        set_module_args(self.mock_rule_args())
        result = self.get_mock_object().get_export_policy()
        assert result is None

    def test_get_existing_rule(self):
        ''' Test if get_export_policy_rule returns rule details for existing policy '''
        data = self.mock_rule_args()
        set_module_args(data)
        result = self.get_mock_object('rule').get_export_policy_rule()
        assert result['name'] == data['name']
        assert result['client_match'] == data['client_match']
        assert result['ro_rule'] == ['any']   # from build_rule()

    def test_get_existing_policy(self):
        ''' Test if get_export_policy returns policy details for existing policy '''
        data = self.mock_rule_args()
        set_module_args(data)
        result = self.get_mock_object('policy').get_export_policy()
        assert result is not None

    def test_create_missing_param_error(self):
        ''' Test validation error from create '''
        data = self.mock_rule_args()
        del data['ro_rule']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_mock_object().apply()
        msg = 'Error: Missing required param for creating export policy rule ro_rule'
        assert exc.value.args[0]['msg'] == msg

    def test_successful_create(self):
        ''' Test successful create '''
        set_module_args(self.mock_rule_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_create_idempotency(self):
        ''' Test create idempotency '''
        set_module_args(self.mock_rule_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object('rule').apply()
        assert not exc.value.args[0]['changed']

    def test_successful_delete_without_rule_index(self):
        ''' Test delete existing job '''
        data = self.mock_rule_args()
        data['state'] = 'absent'
        del data['rule_index']
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object('rule').apply()
        assert exc.value.args[0]['changed']

    def test_delete_idempotency(self):
        ''' Test delete idempotency '''
        data = self.mock_rule_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object().apply()
        assert not exc.value.args[0]['changed']

    def test_successful_modify(self):
        ''' Test successful modify protocol '''
        data = self.mock_rule_args()
        data['protocol'] = ['cifs']
        data['allow_suid'] = 'true'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_mock_object('rule').apply()
        assert exc.value.args[0]['changed']

    def test_error_on_ambiguous_delete(self):
        ''' Test error if multiple entries match for a delete '''
        data = self.mock_rule_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_mock_object('rules').apply()
        msg = "Multiple export policy rules exist.Please specify a rule_index to delete"
        assert exc.value.args[0]['msg'] == msg

    def test_helper_query_parameters(self):
        ''' Test helper method set_query_parameters() '''
        data = self.mock_rule_args()
        set_module_args(data)
        result = self.get_mock_object('rule').set_query_parameters()
        print(str(result))
        assert 'query' in result
        assert 'export-rule-info' in result['query']
        assert result['query']['export-rule-info']['rule-index'] == data['rule_index']
