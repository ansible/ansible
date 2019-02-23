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

from ansible.modules.storage.netapp.na_ontap_lun_copy \
    import NetAppOntapLUNCopy as my_module  # module under test

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

    def __init__(self, kind=None, parm1=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'destination_vserver':
            xml = self.build_lun_info(self.parm1)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_lun_info(data):
        ''' build xml data for lun-info '''
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
        self.mock_lun_copy = {
            'source_vserver': 'ansible',
            'destination_path': '/vol/test/test_copy_dest_dest_new_reviewd_new',
            'source_path': '/vol/test/test_copy_1',
            'destination_vserver': 'ansible',
            'state': 'present'
        }

    def mock_args(self):

        return {
            'source_vserver': self.mock_lun_copy['source_vserver'],
            'destination_path': self.mock_lun_copy['destination_path'],
            'source_path': self.mock_lun_copy['source_path'],
            'destination_vserver': self.mock_lun_copy['destination_vserver'],
            'state': self.mock_lun_copy['state'],
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
        }
        # self.server = MockONTAPConnection()

    def get_lun_copy_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_lun_copy object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_interface object
        """
        lun_copy_obj = my_module()
        lun_copy_obj.autosupport_log = Mock(return_value=None)
        if kind is None:
            lun_copy_obj.server = MockONTAPConnection()
        else:
            lun_copy_obj.server = MockONTAPConnection(kind=kind)
        return lun_copy_obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_create_error_missing_param(self):
        ''' Test if create throws an error if required param 'destination_vserver' is not specified'''
        data = self.mock_args()
        del data['destination_vserver']
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_lun_copy_mock_object('lun_copy').copy_lun()
        msg = 'Error: Missing one or more required parameters for copying lun: ' \
              'destination_path, source_path, destination_path'
        expected = sorted(','.split(msg))
        received = sorted(','.split(exc.value.args[0]['msg']))
        assert expected == received

    def test_successful_copy(self):
        ''' Test successful create '''
        # data = self.mock_args()
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_lun_copy_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_copy_idempotency(self):
        ''' Test create idempotency '''
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_lun_copy_mock_object('destination_vserver').apply()
        assert not exc.value.args[0]['changed']
