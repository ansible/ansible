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

from ansible.modules.storage.netapp.na_ontap_igroup \
    import NetAppOntapIgroup as igroup  # module under test

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
        if self.kind == 'igroup':
            xml = self.build_igroup()
        if self.kind == 'igroup_no_initiators':
            xml = self.build_igroup_no_initiators()
        self.xml_out = xml
        return xml

    @staticmethod
    def build_igroup():
        ''' build xml data for initiator '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'initiator-group-info': {
                    'initiators': [
                        {
                            'initiator-info': {
                                'initiator-name': 'init1'
                            }},
                        {
                            'initiator-info': {
                                'initiator-name': 'init2'
                            }}
                    ]
                }
            }
        }
        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_igroup_no_initiators():
        ''' build xml data for igroup with no initiators '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'initiator-group-info': {
                    'vserver': 'test'
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
            'name': 'test',
            'initiators': 'init1',
            'ostype': 'linux',
            'initiator_group_type': 'fcp',
            'bind_portset': 'true',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password'
        }

    def get_igroup_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_igroup object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_igroup object
        """
        obj = igroup()
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
            igroup()

    def test_get_nonexistent_igroup(self):
        ''' Test if get_igroup returns None for non-existent igroup '''
        data = self.mock_args()
        set_module_args(data)
        result = self.get_igroup_mock_object().get_igroup('dummy')
        assert result is None

    def test_get_existing_igroup_with_initiators(self):
        ''' Test if get_igroup returns list of existing initiators '''
        data = self.mock_args()
        set_module_args(data)
        result = self.get_igroup_mock_object('igroup').get_igroup(data['name'])
        assert data['initiators'] in result['initiators']
        assert result['initiators'] == ['init1', 'init2']

    def test_get_existing_igroup_without_initiators(self):
        ''' Test if get_igroup returns empty list() '''
        data = self.mock_args()
        set_module_args(data)
        result = self.get_igroup_mock_object('igroup_no_initiators').get_igroup(data['name'])
        assert result['initiators'] == []

    @patch('ansible.modules.storage.netapp.na_ontap_igroup.NetAppOntapIgroup.add_initiators')
    @patch('ansible.modules.storage.netapp.na_ontap_igroup.NetAppOntapIgroup.remove_initiators')
    def test_modify_initiator_calls_add_and_remove(self, remove, add):
        '''Test remove_initiator() is called followed by add_initiator() on modify operation'''
        data = self.mock_args()
        data['initiators'] = 'replacewithme'
        set_module_args(data)
        obj = self.get_igroup_mock_object('igroup')
        with pytest.raises(AnsibleExitJson) as exc:
            current = obj.get_igroup(data['name'])
            obj.apply()
        remove.assert_called_with(current['initiators'])
        add.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_igroup.NetAppOntapIgroup.modify_initiator')
    def test_modify_called_from_add(self, modify):
        '''Test remove_initiator() and add_initiator() calls modify'''
        data = self.mock_args()
        data['initiators'] = 'replacewithme'
        add, remove = 'igroup-add', 'igroup-remove'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_igroup_mock_object('igroup_no_initiators').apply()
        modify.assert_called_with('replacewithme', add)
        assert modify.call_count == 1      # remove nothing, add 1 new

    @patch('ansible.modules.storage.netapp.na_ontap_igroup.NetAppOntapIgroup.modify_initiator')
    def test_modify_called_from_remove(self, modify):
        '''Test remove_initiator() and add_initiator() calls modify'''
        data = self.mock_args()
        data['initiators'] = ''
        remove = 'igroup-remove'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_igroup_mock_object('igroup').apply()
        modify.assert_called_with('init2', remove)
        assert modify.call_count == 2  # remove existing 2, add nothing

    @patch('ansible.modules.storage.netapp.na_ontap_igroup.NetAppOntapIgroup.add_initiators')
    def test_successful_create(self, add):
        ''' Test successful create '''
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_igroup_mock_object().apply()
        assert exc.value.args[0]['changed']
        add.assert_called_with()

    def test_successful_delete(self):
        ''' Test successful delete '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_igroup_mock_object('igroup').apply()
        assert exc.value.args[0]['changed']

    def test_successful_modify(self):
        ''' Test successful modify '''
        data = self.mock_args()
        data['initiators'] = 'new'
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_igroup_mock_object('igroup').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_igroup.NetAppOntapIgroup.get_igroup')
    def test_successful_rename(self, get_vserver):
        '''Test successful rename'''
        data = self.mock_args()
        data['from_name'] = 'test'
        data['name'] = 'test_new'
        set_module_args(data)
        current = {
            'initiators': ['init1', 'init2']
        }
        get_vserver.side_effect = [
            None,
            current
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_igroup_mock_object().apply()
        assert exc.value.args[0]['changed']
