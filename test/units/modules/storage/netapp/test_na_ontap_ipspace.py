# (c) 2018, NTT Europe Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

""" unit test for Ansible module: na_ontap_ipspace """

from __future__ import print_function
import json
import pytest

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils
from ansible.modules.storage.netapp.na_ontap_ipspace \
    import NetAppOntapIpspace as my_module
from units.compat import unittest
from units.compat.mock import patch

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
        if self.type == 'ipspace':
            xml = self.build_ipspace_info(self.parm1)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_ipspace_info(ipspace):
        '''  build xml data for ipspace '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {'net-ipspaces-info': {'ipspace': ipspace}}}
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

    def set_default_args(self):
        return dict({
            'name': 'test_ipspace',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password'
        })

    def test_fail_requiredargs_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_get_ipspace_iscalled(self):
        ''' test if get_ipspace() is called '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        ipspace = my_obj.get_ipspace()
        print('Info: test_get_ipspace: %s' % repr(ipspace))
        assert ipspace is None

    def test_ipspace_apply_iscalled(self):
        ''' test if apply() is called '''
        module_args = {'name': 'test_apply_ips'}
        module_args.update(self.set_default_args())
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.server = self.server
        ipspace = my_obj.get_ipspace()
        print('Info: test_get_ipspace: %s' % repr(ipspace))
        assert ipspace is None
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ipspace_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
        my_obj.server = MockONTAPConnection('ipspace', 'test_apply_ips')
        ipspace = my_obj.get_ipspace()
        print('Info: test_get_ipspace: %s' % repr(ipspace))
        assert ipspace is not None
        assert ipspace['name'] == 'test_apply_ips'
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ipspace_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
        ipspace = my_obj.get_ipspace()
        assert ipspace['name'] == 'test_apply_ips'
