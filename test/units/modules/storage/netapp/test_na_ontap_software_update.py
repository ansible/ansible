# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: na_ontap_software_update '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

from ansible.modules.storage.netapp.na_ontap_software_update \
    import NetAppONTAPSoftwareUpdate as my_module  # module under test

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
        if self.type == 'software_update':
            xml = self.build_software_update_info(self.parm1, self.parm2)
        self.xml_out = xml
        return xml

    def autosupport_log(self):
        ''' mock autosupport log'''
        return None

    @staticmethod
    def build_software_update_info(status, node):
        ''' build xml data for software-update-info '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {
            'num-records': 1,
            'attributes-list': {'cluster-image-info': {'node-id': node}},
            'progress-status': status,
            'attributes': {'ndu-progress-info': {'overall-status': 'completed',
                                                 'completed-node-count': '0'}},
        }
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
            hostname = '10.10.10.10'
            username = 'admin'
            password = 'admin'
            node = 'vsim1'
            package_version = 'Fattire__9.3.0'
            package_url = 'abc.com'
        else:
            hostname = 'hostname'
            username = 'username'
            password = 'password'
            node = 'abc'
            package_version = 'test'
            package_url = 'abc.com'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'nodes': node,
            'package_version': package_version,
            'package_url': package_url,
            'https': 'true'
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_image_get_called(self):
        ''' a more interesting test '''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        cluster_image_get = my_obj.cluster_image_get()
        print('Info: test_software_update_get: %s' % repr(cluster_image_get))
        assert cluster_image_get is None

    def test_ensure_apply_for_update_called(self):
        ''' updating software and checking idempotency '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'package_url': 'abc.com'})
        set_module_args(module_args)
        my_obj = my_module()
        my_obj.autosupport_log = Mock(return_value=None)
        if not self.use_vsim:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_software_update_apply: %s' % repr(exc.value))
        assert not exc.value.args[0]['changed']
        if not self.use_vsim:
            my_obj.server = MockONTAPConnection('software_update', 'async_pkg_get_phase_complete', 'abc')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_software_update_apply: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
