# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests for ONTAP Ansible module: na_ontap_portset'''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_portset \
    import NetAppONTAPPortset as my_module  # module under test

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

    def __init__(self, kind=None, parm1=None, parm2=None, parm3=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.parm2 = parm2
        self.parm3 = parm3
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'portset':
            xml = self.build_portset_info(self.parm1, self.parm2, self.parm3)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_portset_info(portset, vserver, type):
        ''' build xml data for vserser-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {'portset-info': {'portset-name': portset,
                                                     'vserver': vserver, 'portset-type': type,
                                                     'portset-port-total': '0'}}}
        xml.translate_struct(data)
        print(xml.to_string())
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
        self.use_vsim = False

    def set_default_args(self):
        if self.use_vsim:
            hostname = '10.193.77.154'
            username = 'admin'
            password = 'netapp1!'
            name = 'test'
            type = 'mixed'
            vserver = 'ansible_test'
            ports = ['a1', 'a2']
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            name = 'name'
            type = 'mixed'
            vserver = 'vserver'
            ports = ['a1', 'a2']
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'name': name,
            'type': type,
            'vserver': vserver,
            'ports': ports
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_portset_get_called(self):
        ''' a more interesting test '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        portset = my_obj.portset_get()
        print('Info: test_portset_get: %s' % repr(portset))
        assert portset is None

    def test_ensure_portset_apply_called(self):
        ''' Test successful create '''
        module_args = {'name': 'create'}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = self.server
        portset = my_obj.portset_get()
        print('Info: test_portset_get: %s' % repr(portset))
        assert portset is None
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_portset_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('portset', 'create', 'vserver', 'mixed')
        portset = my_obj.portset_get()
        print('Info: test_portset_get: %s' % repr(portset))
        assert portset is not None
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_portset_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    def test_modify_ports(self):
        ''' Test modify_portset method '''
        module_args = {'ports': ['l1', 'l2']}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('portset')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_portset_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    def test_delete_portset(self):
        ''' Test successful delete '''
        module_args = {'state': 'absent'}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('portset')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_portset_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
