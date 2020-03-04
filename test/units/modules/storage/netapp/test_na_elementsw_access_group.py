''' unit test for Ansible module: na_elementsw_account.py '''

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as netapp_utils

if not netapp_utils.has_sf_sdk():
    pytestmark = pytest.mark.skip('skipping as missing required SolidFire Python SDK')

from ansible.modules.storage.netapp.na_elementsw_access_group \
    import ElementSWAccessGroup as my_module  # module under test


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


ADD_ERROR = 'some_error_in_add_access_group'


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

    def list_volume_access_groups(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' build access_group list: access_groups.name, access_groups.account_id '''
        access_groups = list()
        access_group_list = self.Bunch(volume_access_groups=access_groups)
        return access_group_list

    def create_volume_access_group(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' We don't check the return code, but could force an exception '''
        if self.force_error and 'add' in self.where:
            # The module does not check for a specific exception :(
            raise OSError(ADD_ERROR)

    def get_account_by_name(self, *args, **kwargs):  # pylint: disable=unused-argument
        ''' returns account_id '''
        if self.force_error and 'account_id' in self.where:
            account_id = None
        else:
            account_id = 1
        print('account_id', account_id)
        account = self.Bunch(account_id=account_id)
        result = self.Bunch(account=account)
        return result


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_ensure_command_called(self, mock_create_sf_connection):
        ''' a more interesting test '''
        set_module_args({
            'state': 'present',
            'name': 'element_groupname',
            'account_id': 'element_account_id',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
        })
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection()
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            # It may not be a good idea to start with apply
            # More atomic methods can be easier to mock
            my_obj.apply()
        print(exc.value.args[0])
        assert exc.value.args[0]['changed']

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_check_error_reporting_on_add_exception(self, mock_create_sf_connection):
        ''' a more interesting test '''
        set_module_args({
            'state': 'present',
            'name': 'element_groupname',
            'account_id': 'element_account_id',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
        })
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection(force_error=True, where=['add'])
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            # It may not be a good idea to start with apply
            # More atomic methods can be easier to mock
            # apply() is calling list_accounts() and add_account()
            my_obj.apply()
        print(exc.value.args[0])
        message = 'Error creating volume access group element_groupname: %s' % ADD_ERROR
        assert exc.value.args[0]['msg'] == message

    @patch('ansible.module_utils.netapp.create_sf_connection')
    def test_check_error_reporting_on_invalid_account_id(self, mock_create_sf_connection):
        ''' a more interesting test '''
        set_module_args({
            'state': 'present',
            'name': 'element_groupname',
            'account_id': 'element_account_id',
            'volumes': ['volume1'],
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
        })
        # my_obj.sfe will be assigned a MockSFConnection object:
        mock_create_sf_connection.return_value = MockSFConnection(force_error=True, where=['account_id'])
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            # It may not be a good idea to start with apply
            # More atomic methods can be easier to mock
            # apply() is calling list_accounts() and add_account()
            my_obj.apply()
        print(exc.value.args[0])
        message = 'Error: Specified account id "%s" does not exist.' % 'element_account_id'
        assert exc.value.args[0]['msg'] == message
