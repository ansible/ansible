# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: na_ontap_ucadapter '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_ucadapter \
    import NetAppOntapadapter as my_module  # module under test

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
        if self.type == 'ucadapter':
            xml = self.build_ucadapter_info(self.parm1)
        self.xml_out = xml
        return xml

    def autosupport_log(self):
        ''' mock autosupport log'''
        return None

    @staticmethod
    def build_ucadapter_info(status):
        ''' build xml data for ucadapter_info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'attributes': {'uc-adapter-info': {
            'mode': 'fc',
            'pending-mode': 'abc',
            'type': 'target',
            'pending-type': 'intitiator',
            'status': status,
        }}}
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
            hostname = '10.192.39.6'
            username = 'admin'
            password = 'netapp123'
            node_name = 'bumblebee-reloaded-01'
            adapter_name = '0f'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            node_name = 'abc'
            adapter_name = '0f'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'node_name': node_name,
            'adapter_name': adapter_name,
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_ucadapter_get_called(self):
        ''' fetching ucadapter details '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        get_adapter = my_obj.get_adapter()
        print('Info: test_ucadapter_get: %s' % repr(get_adapter))
        assert get_adapter is None

    def test_ensure_apply_for_ucadapter_called(self):
        ''' configuring ucadaptor and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'type': 'target'})
        module_args.update({'mode': 'initiator'})
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.autosupport_log = Mock(return_value=None)
        if not self.use_vsim:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ucadapter_apply: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('ucadapter', 'up')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ucadapter_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
