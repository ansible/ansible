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

from ansible.modules.storage.netapp.na_ontap_net_ifgrp \
    import NetAppOntapIfGrp as ifgrp_module  # module under test

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
        if self.kind == 'ifgrp':
            xml = self.build_ifgrp_info(self.params)
        elif self.kind == 'ifgrp-ports':
            xml = self.build_ifgrp_ports_info(self.params)
        elif self.kind == 'ifgrp-fail':
            raise netapp_utils.zapi.NaApiError(code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_ifgrp_info(ifgrp_details):
        ''' build xml data for ifgrp-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'num-records': 1,
            'attributes-list': {
                'net-port-info': {
                    'port': ifgrp_details['name'],
                    'ifgrp-distribution-function': 'mac',
                    'ifgrp-mode': ifgrp_details['mode'],
                    'node': ifgrp_details['node']
                }
            }
        }
        xml.translate_struct(attributes)
        return xml

    @staticmethod
    def build_ifgrp_ports_info(data):
        ''' build xml data for ifgrp-ports '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = {
            'attributes': {
                'net-ifgrp-info': {
                    'ports': [
                        {'lif-bindable': data['ports'][0]},
                        {'lif-bindable': data['ports'][1]},
                        {'lif-bindable': data['ports'][2]}
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
        self.mock_ifgrp = {
            'name': 'test',
            'port': 'a1',
            'node': 'test_vserver',
            'mode': 'something'
        }

    def mock_args(self):
        return {
            'name': self.mock_ifgrp['name'],
            'distribution_function': 'mac',
            'ports': [self.mock_ifgrp['port']],
            'node': self.mock_ifgrp['node'],
            'mode': self.mock_ifgrp['mode'],
            'hostname': 'test',
            'username': 'test_user',
            'password': 'test_pass!'
        }

    def get_ifgrp_mock_object(self, kind=None, data=None):
        """
        Helper method to return an na_ontap_net_ifgrp object
        :param kind: passes this param to MockONTAPConnection()
        :return: na_ontap_net_ifgrp object
        """
        obj = ifgrp_module()
        obj.autosupport_log = Mock(return_value=None)
        if data is None:
            data = self.mock_ifgrp
        obj.server = MockONTAPConnection(kind=kind, data=data)
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            ifgrp_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_nonexistent_ifgrp(self):
        ''' Test if get_ifgrp returns None for non-existent ifgrp '''
        set_module_args(self.mock_args())
        result = self.get_ifgrp_mock_object().get_if_grp()
        assert result is None

    def test_get_existing_ifgrp(self):
        ''' Test if get_ifgrp returns details for existing ifgrp '''
        set_module_args(self.mock_args())
        result = self.get_ifgrp_mock_object('ifgrp').get_if_grp()
        assert result['name'] == self.mock_ifgrp['name']

    def test_successful_create(self):
        ''' Test successful create '''
        data = self.mock_args()
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_ifgrp_mock_object().apply()
        assert exc.value.args[0]['changed']

    def test_successful_delete(self):
        ''' Test delete existing volume '''
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_ifgrp_mock_object('ifgrp').apply()
        assert exc.value.args[0]['changed']

    def test_successful_modify(self):
        ''' Test delete existing volume '''
        data = self.mock_args()
        data['ports'] = ['1', '2', '3']
        set_module_args(data)
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_ifgrp_mock_object('ifgrp').apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.get_if_grp')
    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.create_if_grp')
    def test_create_called(self, create_ifgrp, get_ifgrp):
        data = self.mock_args()
        set_module_args(data)
        get_ifgrp.return_value = None
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_ifgrp_mock_object().apply()
        get_ifgrp.assert_called_with()
        create_ifgrp.assert_called_with()

    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.add_port_to_if_grp')
    def test_if_ports_are_added_after_create(self, add_ports):
        ''' Test successful create '''
        data = self.mock_args()
        set_module_args(data)
        self.get_ifgrp_mock_object().create_if_grp()
        add_ports.assert_called_with('a1')

    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.get_if_grp')
    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.delete_if_grp')
    def test_delete_called(self, delete_ifgrp, get_ifgrp):
        data = self.mock_args()
        data['state'] = 'absent'
        set_module_args(data)
        get_ifgrp.return_value = Mock()
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_ifgrp_mock_object().apply()
        get_ifgrp.assert_called_with()
        delete_ifgrp.assert_called_with()

    def test_get_return_value(self):
        data = self.mock_args()
        set_module_args(data)
        result = self.get_ifgrp_mock_object('ifgrp').get_if_grp()
        assert result['name'] == data['name']
        assert result['mode'] == data['mode']
        assert result['node'] == data['node']

    def test_get_ports_list(self):
        data = self.mock_args()
        data['ports'] = ['e0a', 'e0b', 'e0c']
        set_module_args(data)
        result = self.get_ifgrp_mock_object('ifgrp-ports', data).get_if_grp_ports()
        assert result['ports'] == data['ports']

    def test_add_port_packet(self):
        data = self.mock_args()
        set_module_args(data)
        obj = self.get_ifgrp_mock_object('ifgrp')
        obj.add_port_to_if_grp('addme')
        assert obj.server.xml_in['port'] == 'addme'

    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.remove_port_to_if_grp')
    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.add_port_to_if_grp')
    def test_modify_ports_calls_remove_existing_ports(self, add_port, remove_port):
        ''' Test if already existing ports are not being added again '''
        data = self.mock_args()
        data['ports'] = ['1', '2']
        set_module_args(data)
        self.get_ifgrp_mock_object('ifgrp').modify_ports(current_ports=['1', '2', '3'])
        assert remove_port.call_count == 1
        assert add_port.call_count == 0

    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.remove_port_to_if_grp')
    @patch('ansible.modules.storage.netapp.na_ontap_net_ifgrp.NetAppOntapIfGrp.add_port_to_if_grp')
    def test_modify_ports_calls_add_new_ports(self, add_port, remove_port):
        ''' Test new ports are added '''
        data = self.mock_args()
        data['ports'] = ['1', '2', '3', '4']
        set_module_args(data)
        self.get_ifgrp_mock_object('ifgrp').modify_ports(current_ports=['1', '2'])
        assert remove_port.call_count == 0
        assert add_port.call_count == 2

    def test_get_ports_returns_none(self):
        set_module_args(self.mock_args())
        result = self.get_ifgrp_mock_object().get_if_grp_ports()
        assert result['ports'] == []
        result = self.get_ifgrp_mock_object().get_if_grp()
        assert result is None

    def test_if_all_methods_catch_exception(self):
        set_module_args(self.mock_args())
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_ifgrp_mock_object('ifgrp-fail').get_if_grp()
        assert 'Error getting if_group test' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_ifgrp_mock_object('ifgrp-fail').create_if_grp()
        assert 'Error creating if_group test' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_ifgrp_mock_object('ifgrp-fail').get_if_grp_ports()
        assert 'Error getting if_group ports test' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_ifgrp_mock_object('ifgrp-fail').add_port_to_if_grp('test-port')
        assert 'Error adding port test-port to if_group test' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_ifgrp_mock_object('ifgrp-fail').remove_port_to_if_grp('test-port')
        assert 'Error removing port test-port to if_group test' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            self.get_ifgrp_mock_object('ifgrp-fail').delete_if_grp()
        assert 'Error deleting if_group test' in exc.value.args[0]['msg']
