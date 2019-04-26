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

from ansible.modules.storage.netapp.na_ontap_igroup_initiator \
    import NetAppOntapIgroupInitiator as initiator  # module under test

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
        if self.kind == 'initiator':
            xml = self.build_igroup_initiator()
        self.xml_out = xml
        return xml

    @staticmethod
    def build_igroup_initiator():
        ''' build xml data for initiator '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'initiator-group-info': {
                    'initiators': [
                        {'initiator-info': {
                            'initiator-name': 'init1'
                        }},
                        {'initiator-info': {
                            'initiator-name': 'init2'
                        }}
                    ]
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
        self.server = MockONTAPConnection()

    def mock_args(self):
        return {
            'vserver': 'vserver',
            'name': 'init1',
            'initiator_group': 'test',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password'
        }

    def get_initiator_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_initiator object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_initiator object
        """
        obj = initiator()
        obj.autosupport_log = Mock(return_value=None)
        if kind is None:
            obj.server = MockONTAPConnection()
        else:
            obj.server = MockONTAPConnection(kind=kind)
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            initiator()

    def test_get_nonexistent_initiator(self):
        ''' Test if get_initiators returns None for non-existent initiator '''
        data = self.mock_args()
        data['name'] = 'idontexist'
        set_module_args(data)
        result = self.get_initiator_mock_object('initiator').get_initiators()
        assert data['name'] not in result

    def test_get_nonexistent_igroup(self):
        ''' Test if get_initiators returns None for non-existent igroup '''
        data = self.mock_args()
        data['name'] = 'idontexist'
        set_module_args(data)
        result = self.get_initiator_mock_object().get_initiators()
        assert result == []

    def test_get_existing_initiator(self):
        ''' Test if get_initiator returns None for existing initiator '''
        data = self.mock_args()
        set_module_args(data)
        result = self.get_initiator_mock_object(kind='initiator').get_initiators()
        assert data['name'] in result
        assert result == ['init1', 'init2']     # from build_igroup_initiators()

    def test_successful_add(self):
        ''' Test successful add'''
        data = self.mock_args()
        data['name'] = 'iamnew'
        set_module_args(data)
        obj = self.get_initiator_mock_object('initiator')
        with pytest.raises(AnsibleExitJson) as exc:
            current = obj.get_initiators()
            obj.apply()
        assert data['name'] not in current
        assert exc.value.args[0]['changed']

    def test_successful_add_idempotency(self):
        ''' Test successful add idempotency '''
        data = self.mock_args()
        set_module_args(data)
        obj = self.get_initiator_mock_object('initiator')
        with pytest.raises(AnsibleExitJson) as exc:
            current_list = obj.get_initiators()
            obj.apply()
        assert data['name'] in current_list
        assert not exc.value.args[0]['changed']

    def test_successful_remove(self):
        ''' Test successful remove '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        obj = self.get_initiator_mock_object('initiator')
        with pytest.raises(AnsibleExitJson) as exc:
            current_list = obj.get_initiators()
            obj.apply()
        assert data['name'] in current_list
        assert exc.value.args[0]['changed']

    def test_successful_remove_idempotency(self):
        ''' Test successful remove idempotency'''
        data = self.mock_args()
        data['state'] = 'absent'
        data['name'] = 'alreadyremoved'
        set_module_args(data)
        obj = self.get_initiator_mock_object('initiator')
        with pytest.raises(AnsibleExitJson) as exc:
            current_list = obj.get_initiators()
            obj.apply()
        assert data['name'] not in current_list
        assert not exc.value.args[0]['changed']
