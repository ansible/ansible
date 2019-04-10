# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test for ONTAP Command Ansible module '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_command \
    import NetAppONTAPCommand as my_module  # module under test

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
        # print(xml.to_string())

        if self.type == 'version':
            priv = xml.get_child_content('priv')
            xml = self.build_version(priv)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_version(priv):
        ''' build xml data for version '''
        prefix = 'NetApp Release'
        if priv == 'advanced':
            prefix = '\n' + prefix
        xml = netapp_utils.zapi.NaElement('results')
        xml.add_new_child('cli-output', prefix)
        # print(xml.to_string())
        return xml


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        self.server = MockONTAPConnection(kind='version')
        # whether to use a mock or a simulator
        self.use_vsim = False

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    @staticmethod
    def set_default_args(vsim=False):
        ''' populate hostname/username/password '''
        if vsim:
            hostname = '10.193.78.219'
            username = 'admin'
            password = 'netapp1!'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'https': True,
            'validate_certs': False
        })

    def call_command(self, module_args, vsim=False):
        ''' utility function to call apply '''
        module_args.update(self.set_default_args(vsim=vsim))
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not vsim:
            # mock the connection
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        msg = exc.value.args[0]['msg']
        return msg

    def test_default_priv(self):
        ''' make sure privilege is not required '''
        module_args = {
            'command': 'version',
        }
        msg = self.call_command(module_args, vsim=self.use_vsim)
        needle = b'<cli-output>NetApp Release'
        assert needle in msg
        print('Version (raw): %s' % msg)

    def test_admin_priv(self):
        ''' make sure admin is accepted '''
        module_args = {
            'command': 'version',
            'privilege': 'admin',
        }
        msg = self.call_command(module_args, vsim=self.use_vsim)
        needle = b'<cli-output>NetApp Release'
        assert needle in msg
        print('Version (raw): %s' % msg)

    def test_advanced_priv(self):
        ''' make sure advanced is not required '''
        module_args = {
            'command': 'version',
            'privilege': 'advanced',
        }
        msg = self.call_command(module_args, vsim=self.use_vsim)
        # Interestingly, the ZAPI returns a slightly different response
        needle = b'<cli-output>\nNetApp Release'
        assert needle in msg
        print('Version (raw): %s' % msg)
