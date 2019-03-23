# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: na_ontap_cifs_server '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_cifs_server \
    import NetAppOntapcifsServer as my_module  # module under test

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

    def __init__(self, kind=None, parm1=None, parm2=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.parm2 = parm2
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'cifs_server':
            xml = self.build_vserver_info(self.parm1, self.parm2)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_vserver_info(cifs_server, admin_status):
        ''' build xml data for cifs-server-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {'num-records': 1,
                'attributes-list': {'cifs-server-config': {'cifs-server': cifs_server,
                                                           'administrative-status': admin_status}}}
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
            cifs_server = 'test'
            vserver = 'ansible_test'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            cifs_server = 'name'
            vserver = 'vserver'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'cifs_server_name': cifs_server,
            'vserver': vserver
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_cifs_server_get_called(self):
        ''' a more interesting test '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        cifs_server = my_obj.get_cifs_server()
        print('Info: test_cifs_server_get: %s' % repr(cifs_server))
        assert cifs_server is None

    def test_ensure_cifs_server_apply_for_create_called(self):
        ''' creating cifs server and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'cifs_server_name': 'create'})
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_server_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cifs_server', 'create', 'up')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_server_apply_for_create: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']

    def test_ensure_cifs_server_apply_for_delete_called(self):
        ''' deleting cifs server and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'cifs_server_name': 'delete'})
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cifs_server', 'delete', 'up')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_server_apply: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']
        module_args.update({'state': 'absent'})
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cifs_server', 'delete', 'up')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_cifs_server_delete: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    def test_ensure_start_cifs_server_called(self):
        ''' starting cifs server and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'cifs_server_name': 'delete'})
        module_args.update({'service_state': 'started'})
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cifs_server', 'test', 'up')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ensure_start_cifs_server: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']
        module_args.update({'service_state': 'stopped'})
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cifs_server', 'test', 'up')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ensure_start_cifs_server: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    def test_ensure_stop_cifs_server_called(self):
        ''' stopping cifs server and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'cifs_server_name': 'delete'})
        module_args.update({'service_state': 'stopped'})
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cifs_server', 'test', 'down')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ensure_stop_cifs_server: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']
        module_args.update({'service_state': 'started'})
        set_module_args(module_args)
        my_obj = my_module()
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('cifs_server', 'test', 'down')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ensure_stop_cifs_server: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
