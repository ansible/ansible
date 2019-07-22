# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests for ONTAP Ansible module na_ontap_gather_facts '''

from __future__ import print_function
import json
import pytest
import sys

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_gather_facts import main as gather_facts_main
from ansible.modules.storage.netapp.na_ontap_gather_facts import __finditem as gather_facts_finditem
from ansible.modules.storage.netapp.na_ontap_gather_facts \
    import NetAppONTAPGatherFacts as gather_facts_module  # module under test

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

    def __init__(self, kind=None):
        ''' save arguments '''
        self.type = kind
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        print(xml.to_string())
        if self.type == 'vserver':
            xml = self.build_vserver_info()
        elif self.type == 'net_port':
            xml = self.build_net_port_info()
        elif self.type == 'zapi_error':
            error = netapp_utils.zapi.NaApiError('test', 'error')
            raise error
        self.xml_out = xml
        return xml

    @staticmethod
    def build_vserver_info():
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes = netapp_utils.zapi.NaElement('attributes-list')
        attributes.add_node_with_children('vserver-info',
                                          **{'vserver-name': 'test_vserver'})
        xml.add_child_elem(attributes)
        return xml

    @staticmethod
    def build_net_port_info():
        ''' build xml data for net-port-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        attributes_list = netapp_utils.zapi.NaElement('attributes-list')
        num_net_port_info = 2
        for i in range(num_net_port_info):
            net_port_info = netapp_utils.zapi.NaElement('net-port-info')
            net_port_info.add_new_child('node', 'node_' + str(i))
            net_port_info.add_new_child('port', 'port_' + str(i))
            net_port_info.add_new_child('broadcast_domain', 'test_domain_' + str(i))
            net_port_info.add_new_child('ipspace', 'ipspace' + str(i))
            attributes_list.add_child_elem(net_port_info)
        xml.add_child_elem(attributes_list)
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
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
        }

    def get_gather_facts_mock_object(self, kind=None):
        """
        Helper method to return an na_ontap_gather_facts object
        """
        module = basic.AnsibleModule(
            argument_spec=netapp_utils.na_ontap_host_argument_spec(),
            supports_check_mode=True
        )
        obj = gather_facts_module(module)
        obj.netapp_info = dict()
        if kind is None:
            obj.server = MockONTAPConnection()
        else:
            obj.server = MockONTAPConnection(kind)
        return obj

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            self.get_gather_facts_mock_object()
        print('Info: %s' % exc.value.args[0]['msg'])

    @patch('ansible.module_utils.netapp.ems_log_event')
    def test_ensure_command_called(self, mock_ems_log):
        ''' calling get_all will raise a KeyError exception '''
        set_module_args(self.mock_args())
        my_obj = self.get_gather_facts_mock_object('vserver')
        with pytest.raises(KeyError) as exc:
            my_obj.get_all(['net_interface_info'])
        if sys.version_info >= (2, 7):
            msg = 'net-interface-info'
            assert exc.value.args[0] == msg

    @patch('ansible.module_utils.netapp.ems_log_event')
    def test_get_generic_get_iter(self, mock_ems_log):
        '''calling get_generic_get_iter will return expected dict'''
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('net_port')
        result = obj.get_generic_get_iter(
            'net-port-get-iter',
            attribute='net-port-info',
            field=('node', 'port'),
            query={'max-records': '1024'}
        )
        assert result.get('node_0:port_0')
        assert result.get('node_1:port_1')

    @patch('ansible.modules.storage.netapp.na_ontap_gather_facts.NetAppONTAPGatherFacts.get_all')
    def test_main(self, get_all):
        '''test main method.'''
        set_module_args(self.mock_args())
        get_all.side_effect = [
            {'test_get_all':
                {'vserver_login_banner_info': 'test_vserver_login_banner_info', 'vserver_info': 'test_vserver_info'}}
        ]
        with pytest.raises(AnsibleExitJson) as exc:
            gather_facts_main()
        assert exc.value.args[0]['state'] == 'info'

    @patch('ansible.modules.storage.netapp.na_ontap_gather_facts.NetAppONTAPGatherFacts.get_generic_get_iter')
    def test_get_ifgrp_info(self, get_generic_get_iter):
        '''test get_ifgrp_info with empty ifgrp_info'''
        set_module_args(self.mock_args())
        get_generic_get_iter.side_effect = [
            {}
        ]
        obj = self.get_gather_facts_mock_object()
        obj.netapp_info['net_port_info'] = {}
        result = obj.get_ifgrp_info()
        assert result == {}

    def test_ontapi_error(self):
        '''test ontapi will raise zapi error'''
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('zapi_error')
        with pytest.raises(AnsibleFailJson) as exc:
            obj.ontapi()
        assert exc.value.args[0]['msg'] == 'Error calling API system-get-ontapi-version: NetApp API failed. Reason - test:error'

    def test_call_api_error(self):
        '''test call_api will raise zapi error'''
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('zapi_error')
        with pytest.raises(AnsibleFailJson) as exc:
            obj.call_api('nvme-get-iter')
        assert exc.value.args[0]['msg'] == 'Error calling API nvme-get-iter: NetApp API failed. Reason - test:error'

    def test_find_item(self):
        '''test __find_item return expected key value'''
        obj = {"A": 1, "B": {"C": {"D": 2}}}
        key = "D"
        result = gather_facts_finditem(obj, key)
        assert result == 2

    def test_subset_return_all_complete(self):
        ''' Check all returns all of the entries if version is high enough '''
        version = '140'         # change this if new ZAPIs are supported
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        subset = obj.get_subset(['all'], version)
        assert set(obj.fact_subsets.keys()) == subset

    def test_subset_return_all_partial(self):
        ''' Check all returns a subset of the entries if version is low enough '''
        version = '120'         # low enough so that some ZAPIs are not supported
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        subset = obj.get_subset(['all'], version)
        all_keys = obj.fact_subsets.keys()
        assert set(all_keys) > subset
        supported_keys = filter(lambda key: obj.fact_subsets[key]['min_version'] <= version, all_keys)
        assert set(supported_keys) == subset

    def test_subset_return_one(self):
        ''' Check single entry returns one '''
        version = '120'         # low enough so that some ZAPIs are not supported
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        subset = obj.get_subset(['net_interface_info'], version)
        assert len(subset) == 1

    def test_subset_return_multiple(self):
        ''' Check that more than one entry returns the same number '''
        version = '120'         # low enough so that some ZAPIs are not supported
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        subset_entries = ['net_interface_info', 'net_port_info']
        subset = obj.get_subset(subset_entries, version)
        assert len(subset) == len(subset_entries)

    def test_subset_return_bad(self):
        ''' Check that a bad subset entry will error out '''
        version = '120'         # low enough so that some ZAPIs are not supported
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        with pytest.raises(AnsibleFailJson) as exc:
            subset = obj.get_subset(['net_interface_info', 'my_invalid_subset'], version)
        print('Info: %s' % exc.value.args[0]['msg'])
        assert exc.value.args[0]['msg'] == 'Bad subset: my_invalid_subset'

    def test_subset_return_unsupported(self):
        ''' Check that a new subset entry will error out on an older system '''
        version = '120'         # low enough so that some ZAPIs are not supported
        key = 'nvme_info'       # only supported starting at 140
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        with pytest.raises(AnsibleFailJson) as exc:
            subset = obj.get_subset(['net_interface_info', key], version)
        print('Info: %s' % exc.value.args[0]['msg'])
        msg = 'Remote system at version %s does not support %s' % (version, key)
        assert exc.value.args[0]['msg'] == msg

    def test_subset_return_none(self):
        ''' Check usable subset can be empty '''
        version = '!'   # lower then 0, so that no ZAPI is supported
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        subset = obj.get_subset(['all'], version)
        assert len(subset) == 0

    def test_subset_return_all_expect_one(self):
        ''' Check !x returns all of the entries except x if version is high enough '''
        version = '140'         # change this if new ZAPIs are supported
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        subset = obj.get_subset(['!net_interface_info'], version)
        assert len(obj.fact_subsets.keys()) == len(subset) + 1
        subset.add('net_interface_info')
        assert set(obj.fact_subsets.keys()) == subset

    def test_subset_return_all_expect_three(self):
        ''' Check !x,!y,!z returns all of the entries except x, y, z if version is high enough '''
        version = '140'         # change this if new ZAPIs are supported
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        subset = obj.get_subset(['!net_interface_info', '!nvme_info', '!ontap_version'], version)
        assert len(obj.fact_subsets.keys()) == len(subset) + 3
        subset.update(['net_interface_info', 'nvme_info', 'ontap_version'])
        assert set(obj.fact_subsets.keys()) == subset

    def test_subset_return_none_with_exclusion(self):
        ''' Check usable subset can be empty with !x '''
        version = '!'   # lower then 0, so that no ZAPI is supported
        key = 'net_interface_info'
        set_module_args(self.mock_args())
        obj = self.get_gather_facts_mock_object('vserver')
        with pytest.raises(AnsibleFailJson) as exc:
            subset = obj.get_subset(['!' + key], version)
        print('Info: %s' % exc.value.args[0]['msg'])
        msg = 'Remote system at version %s does not support %s' % (version, key)
        assert exc.value.args[0]['msg'] == msg
