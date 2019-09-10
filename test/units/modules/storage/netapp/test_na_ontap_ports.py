# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests for ONTAP Ansible module: na_ontap_port'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_ports \
    import NetAppOntapPorts as port_module  # module under test

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


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def mock_args(self, choice):
        if choice == 'broadcast_domain':
            return {
                'names': ['test_port_1', 'test_port_2'],
                'resource_name': 'test_domain',
                'resource_type': 'broadcast_domain',
                'hostname': 'test',
                'username': 'test_user',
                'password': 'test_pass!'
            }
        elif choice == 'portset':
            return {
                'names': ['test_lif'],
                'resource_name': 'test_portset',
                'resource_type': 'portset',
                'hostname': 'test',
                'username': 'test_user',
                'password': 'test_pass!',
                'vserver': 'test_vserver'
            }

    def get_port_mock_object(self):
        """
        Helper method to return an na_ontap_port object
        """
        port_obj = port_module()
        port_obj.asup_log_for_cserver = Mock(return_value=None)
        port_obj.server = Mock()
        port_obj.server.invoke_successfully = Mock()

        return port_obj

    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.add_broadcast_domain_ports')
    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.get_broadcast_domain_ports')
    def test_successfully_add_broadcast_domain_ports(self, get_broadcast_domain_ports, add_broadcast_domain_ports):
        ''' Test successful add broadcast domain ports '''
        data = self.mock_args('broadcast_domain')
        set_module_args(data)
        get_broadcast_domain_ports.side_effect = [
            []
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object().apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.add_broadcast_domain_ports')
    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.get_broadcast_domain_ports')
    def test_add_broadcast_domain_ports_idempotency(self, get_broadcast_domain_ports, add_broadcast_domain_ports):
        ''' Test add broadcast domain ports idempotency '''
        data = self.mock_args('broadcast_domain')
        set_module_args(data)
        get_broadcast_domain_ports.side_effect = [
            ['test_port_1', 'test_port_2']
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object().apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.add_portset_ports')
    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.portset_get')
    def test_successfully_add_portset_ports(self, portset_get, add_portset_ports):
        ''' Test successful add portset ports '''
        data = self.mock_args('portset')
        set_module_args(data)
        portset_get.side_effect = [
            []
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object().apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.add_portset_ports')
    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.portset_get')
    def test_add_portset_ports_idempotency(self, portset_get, add_portset_ports):
        ''' Test add portset ports idempotency '''
        data = self.mock_args('portset')
        set_module_args(data)
        portset_get.side_effect = [
            ['test_lif']
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object().apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.add_broadcast_domain_ports')
    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.get_broadcast_domain_ports')
    def test_successfully_remove_broadcast_domain_ports(self, get_broadcast_domain_ports, add_broadcast_domain_ports):
        ''' Test successful remove broadcast domain ports '''
        data = self.mock_args('broadcast_domain')
        data['state'] = 'absent'
        set_module_args(data)
        get_broadcast_domain_ports.side_effect = [
            ['test_port_1', 'test_port_2']
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object().apply()
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.add_portset_ports')
    @patch('ansible.modules.storage.netapp.na_ontap_ports.NetAppOntapPorts.portset_get')
    def test_remove_add_portset_ports(self, portset_get, add_portset_ports):
        ''' Test successful remove portset ports '''
        data = self.mock_args('portset')
        data['state'] = 'absent'
        set_module_args(data)
        portset_get.side_effect = [
            ['test_lif']
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            self.get_port_mock_object().apply()
        assert exc.value.args[0]['changed']
