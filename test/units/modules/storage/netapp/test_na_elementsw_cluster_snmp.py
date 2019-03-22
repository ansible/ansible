# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit test for Ansible module: na_elementsw_cluster_snmp.py '''

from __future__ import print_function
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

if not netapp_utils.has_sf_sdk():
    pytestmark = pytest.mark.skip('skipping as missing required SolidFire Python SDK')

from ansible.modules.storage.netapp.na_elementsw_cluster_snmp \
    import ElementSWClusterSnmp as my_module  # module under test


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


GET_ERROR = 'some_error_in_get_snmp_info'


class MockSFConnection(object):
    ''' mock connection to ElementSW host '''

    class Bunch(object):  # pylint: disable=too-few-public-methods
        ''' create object with arbitrary attributes '''
        def __init__(self, **kw):
            ''' called with (k1=v1, k2=v2), creates obj.k1, obj.k2 with values v1, v2 '''
            setattr(self, '__dict__', kw)

    def __init__(self, force_error=False, where=None):
        ''' save arguments '''
        self.force_error = force_error
        self.where = where


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args(self):
        return dict({
            'hostname': '10.117.78.131',
            'username': 'admin',
            'password': 'netapp1!',
        })

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_module_fail_when_required_args_missing(self, mock_create_sf_connection):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value)

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_enable_snmp_called(self, mock_create_sf_connection):
        ''' test if enable_snmp is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'snmp_v3_enabled': True,
                            'state': 'present'})
        module_args.update({'usm_users': {'access': 'rouser',
                                          'name': 'TestUser',
                                          'password': 'ChangeMe@123',
                                          'passphrase': 'ChangeMe@123',
                                          'secLevel': 'auth', }})

        module_args.update({'networks': {'access': 'ro',
                                         'cidr': 24,
                                         'community': 'TestNetwork',
                                         'network': '192.168.0.1', }})
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_if_enable_snmp_called: %s' % repr(exc.value))
        assert exc.value

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_configure_snmp_from_version_3_TO_version_2_called(self, mock_create_sf_connection):
        ''' test if configure snmp from version_3 to version_2'''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'snmp_v3_enabled': False,
                            'state': 'present'})
        module_args.update({'usm_users': {'access': 'rouser',
                                          'name': 'TestUser',
                                          'password': 'ChangeMe@123',
                                          'passphrase': 'ChangeMe@123',
                                          'secLevel': 'auth', }})

        module_args.update({'networks': {'access': 'ro',
                                         'cidr': 24,
                                         'community': 'TestNetwork',
                                         'network': '192.168.0.1', }})
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ensure_configure_snmp_from_version_3_TO_version_2_called: %s' % repr(exc.value))
        assert exc.value

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_configure_snmp_from_version_2_TO_version_3_called(self, mock_create_sf_connection):
        ''' test if configure snmp from version_2 to version_3'''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'snmp_v3_enabled': True,
                            'state': 'present'})
        module_args.update({'usm_users': {'access': 'rouser',
                                          'name': 'TestUser_sample',
                                          'password': 'ChangeMe@123',
                                          'passphrase': 'ChangeMe@123',
                                          'secLevel': 'auth', }})

        module_args.update({'networks': {'access': 'ro',
                                         'cidr': 24,
                                         'community': 'TestNetwork',
                                         'network': '192.168.0.1', }})
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_ensure_configure_snmp_from_version_2_TO_version_3_called: %s' % repr(exc.value))
        assert exc.value

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_disable_snmp_called(self, mock_create_sf_connection):
        ''' test if disable_snmp is called '''
        module_args = {}
        module_args.update(self.set_default_args())
        module_args.update({'state': 'absent'})
        set_module_args(module_args)
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_if_disable_snmp_called: %s' % repr(exc.value))
        assert exc.value
