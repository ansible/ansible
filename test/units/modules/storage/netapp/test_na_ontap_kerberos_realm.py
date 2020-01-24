# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test for ONTAP Kerberos Realm module '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import pytest
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.modules.storage.netapp.na_ontap_kerberos_realm \
    import NetAppOntapKerberosRealm as my_module  # module under test
from units.compat import unittest
from units.compat.mock import patch
from units.compat.mock import Mock


if not netapp_utils.has_netapp_lib():
    pytestmark = pytest.mark.skip('skipping as missing required netapp_lib')


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    print(Exception)
    # pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    print(Exception)
    # pass


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

    def __init__(self, kind=None):
        ''' save arguments '''
        self.type = kind
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml

        if self.type == 'present_realm':
            xml = self.build_realm()
        else:
            xml = self.build_empty_realm()

        self.xml_out = xml
        return xml

    @staticmethod
    def build_realm():
        ''' build xml data for kerberos realm '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': "1",
            'attributes-list': {
                'kerberos-realm': {
                    'admin-server-ip': "192.168.0.1",
                    'admin-server-port': "749",
                    'clock-skew': "5",
                    'kdc-ip': "192.168.0.1",
                    'kdc-port': "88",
                    'kdc-vendor': "other",
                    'password-server-ip': "192.168.0.1",
                    'password-server-port': "464",
                    "permitted-enc-types": {
                        "string": ["des", "des3", "aes_128", "aes_256"]
                    },
                    'realm': "EXAMPLE.COM",
                    'vserver-name': "vserver0"
                }
            }
        }
        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_empty_realm():
        ''' build xml data for kerberos realm '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': "0",
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
        self.server = MockONTAPConnection(kind='present_realm')

    @staticmethod
    def get_kerberos_realm_mock_object(kind=None):
        """
        Helper method to return an na_ontap_volume object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_volume object
        """
        krbrealm_obj = my_module()
        krbrealm_obj.asup_log_for_cserver = Mock(return_value=None)
        krbrealm_obj.cluster = Mock()
        krbrealm_obj.cluster.invoke_successfully = Mock()
        if kind is None:
            krbrealm_obj.server = MockONTAPConnection()
        else:
            krbrealm_obj.server = MockONTAPConnection(kind=kind)
        return krbrealm_obj

    @staticmethod
    def mock_args():
        '''Set default arguments'''
        return dict({
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!',
            'https': True,
            'validate_certs': False
        })

    @staticmethod
    def test_module_fail_when_required_args_missing():
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_module_fail_when_state_present_required_args_missing(self):
        ''' required arguments are reported as errors '''
        data = self.mock_args()
        data['state'] = 'present'
        data['vserver'] = 'vserver1'
        data['realm'] = 'NETAPP.COM'
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(data)
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_realm(self):
        ''' Test if get_krbrealm returns None for non-existent kerberos realm '''
        data = self.mock_args()
        data['vserver'] = 'none'
        data['realm'] = 'none'
        data['state'] = 'present'
        data['kdc_ip'] = 'none'
        data['kdc_vendor'] = 'Other'
        set_module_args(data)
        result = self.get_kerberos_realm_mock_object().get_krbrealm()
        assert result is None

    def test_get_existing_realm(self):
        ''' Test if get_krbrealm returns details for existing kerberos realm '''
        data = self.mock_args()
        data['vserver'] = 'vserver0'
        data['realm'] = 'EXAMPLE.COM'
        data['state'] = 'present'
        data['kdc_ip'] = '10.0.0.1'
        data['kdc_vendor'] = 'Other'
        set_module_args(data)
        result = self.get_kerberos_realm_mock_object('present_realm').get_krbrealm()
        assert result['realm']

    def test_successfully_modify_realm(self):
        ''' Test modify realm successful for modifying kdc_ip. '''
        data = self.mock_args()
        data['vserver'] = 'vserver0'
        data['realm'] = 'EXAMPLE.COM'
        data['kdc_ip'] = '192.168.10.10'
        data['state'] = 'present'
        data['kdc_ip'] = '10.0.0.1'
        data['kdc_vendor'] = 'Other'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_kerberos_realm_mock_object('present_realm').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_kerberos_realm.NetAppOntapKerberosRealm.delete_krbrealm')
    def test_successfully_delete_realm(self, delete_krbrealm):
        ''' Test successfully delete realm '''
        data = self.mock_args()
        data['state'] = 'absent'
        data['vserver'] = 'vserver0'
        data['realm'] = 'EXAMPLE.COM'
        set_module_args(data)
        obj = self.get_kerberos_realm_mock_object('present_realm')
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']
        delete_krbrealm.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_kerberos_realm.NetAppOntapKerberosRealm.create_krbrealm')
    def test_successfully_create_realm(self, create_krbrealm):
        ''' Test successfully create realm '''
        data = self.mock_args()
        data['state'] = 'present'
        data['vserver'] = 'vserver1'
        data['realm'] = 'NETAPP.COM'
        data['kdc_ip'] = '10.0.0.1'
        data['kdc_vendor'] = 'Other'
        set_module_args(data)
        obj = self.get_kerberos_realm_mock_object()
        with pytest.raises(AnsibleExitJson) as exc:
            obj.apply()
        assert exc.value.args[0]['changed']
        create_krbrealm.assert_called_with()
