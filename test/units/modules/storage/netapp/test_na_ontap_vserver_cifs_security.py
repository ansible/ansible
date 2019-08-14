# (c) 2019, NetApp, Inc
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

from ansible.modules.storage.netapp.na_ontap_vserver_cifs_security \
    import NetAppONTAPCifsSecurity as cifs_security_module  # module under test

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
        self.type = kind
        self.data = data
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'cifs_security':
            xml = self.build_port_info(self.data)
        if self.type == 'error':
            error = netapp_utils.zapi.NaApiError('test', 'error')
            raise error
        self.xml_out = xml
        return xml

    @staticmethod
    def build_port_info(cifs_security_details):
        ''' build xml data for cifs-security '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'cifs-security': {
                    'is_aes_encryption_enabled': cifs_security_details['is_aes_encryption_enabled'],
                    'lm_compatibility_level': cifs_security_details['lm_compatibility_level']
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
        self.mock_cifs_security = {
            'is_aes_encryption_enabled': 'true',
            'lm_compatibility_level': 'krb'
        }

    def mock_args(self):
        return {
            'is_aes_encryption_enabled': self.mock_cifs_security['is_aes_encryption_enabled'],
            'lm_compatibility_level': self.mock_cifs_security['lm_compatibility_level'],
            'vserver': 'ansible',
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'https': 'False'
        }

    def get_cifs_security_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_vserver_cifs_security object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_vserver_cifs_security object
        """
        obj = cifs_security_module()
        obj.asup_log_for_cserver = Mock(return_value=None)
        obj.server = Mock()
        obj.server.invoke_successfully = Mock()
        if kind is None:
            obj.server = MockONTAPConnection()
        else:
            obj.server = MockONTAPConnection(kind=kind, data=self.mock_cifs_security)
        return obj

    @patch('ansible.modules.storage.netapp.na_ontap_vserver_cifs_security.NetAppONTAPCifsSecurity.cifs_security_get_iter')
    def test_successful_modify(self, get_cifs_security):
        ''' Test successful modify max throughput '''
        data = self.mock_args()
        set_module_args(data)
        current = {
            'is_aes_encryption_enabled': False,
            'lm_compatibility_level': 'lm_ntlm_ntlmv2_krb'
        }
        get_cifs_security.side_effect = [
            current
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_cifs_security_mock_object('cifs_security').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_vserver_cifs_security.NetAppONTAPCifsSecurity.cifs_security_get_iter')
    def test_modify_error(self, get_cifs_security):
        ''' Test create idempotency '''
        data = self.mock_args()
        set_module_args(data)
        current = {
            'is_aes_encryption_enabled': False
        }
        get_cifs_security.side_effect = [
            current
        ]
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_cifs_security_mock_object('error').apply()
        assert exc.value.args[0]['msg'] == 'Error modifying cifs security on ansible: NetApp API failed. Reason - test:error'
