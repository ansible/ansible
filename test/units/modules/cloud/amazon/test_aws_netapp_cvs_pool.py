# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Unit tests for AWS Cloud Volumes Services - Manage Pools '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from requests import Response
from ansible.modules.cloud.amazon.aws_netapp_cvs_pool \
    import NetAppAWSCVS as pool_module


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

    def set_default_args_fail_check(self):
        return dict({
            'from_name': 'TestPoolAA',
            'name': 'TestPoolAA_new',
            'serviceLevel': 'standard',
            'sizeInBytes': 4000000000000,
            'vendorID': 'ansiblePoolTestVendorA',
            'region': 'us-east-1',
            'api_url': 'hostname.invalid',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def set_default_args_pass_check(self):
        return dict({
            'state': 'present',
            'from_name': 'TestPoolAA',
            'name': 'TestPoolAA_new',
            'serviceLevel': 'standard',
            'sizeInBytes': 4000000000000,
            'vendorID': 'ansiblePoolTestVendorA',
            'region': 'us-east-1',
            'api_url': 'hostname.invalid',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def set_args_create_aws_netapp_cvs_pool(self):
        return dict({
            'state': 'present',
            'name': 'TestPoolAA',
            'serviceLevel': 'standard',
            'sizeInBytes': 4000000000000,
            'vendorID': 'ansiblePoolTestVendorA',
            'region': 'us-east-1',
            'api_url': 'hostname.invalid',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def set_args_update_aws_netapp_cvs_pool(self):
        return dict({
            'state': 'present',
            'from_name': 'TestPoolAA',
            'name': 'TestPoolAA_new',
            'serviceLevel': 'standard',
            'sizeInBytes': 4000000000000,
            'vendorID': 'ansiblePoolTestVendorA',
            'region': 'us-east-1',
            'api_url': 'hostname.invalid',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def set_args_delete_aws_netapp_cvs_pool(self):
        return dict({
            'state': 'absent',
            'name': 'TestPoolAA',
            'region': 'us-east-1',
            'api_url': 'hostname.invalid',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            pool_module()
        print('Info: test_module_fail_when_required_args_missing: %s' % exc.value.args[0]['msg'])

    def test_module_pass_when_required_args_present(self):
        ''' required arguments are present '''
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            pool_module()
            exit_json(changed=True, msg="Induced arguments check")
        print('Info: test_module_pass_when_required_args_present: %s' % exc.value.args[0]['msg'])
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_pool.NetAppAWSCVS.get_aws_netapp_cvs_pool')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.put')
    def test_update_aws_netapp_cvs_pool_pass(self, get_put_api, get_aws_api):
        set_module_args(self.set_args_update_aws_netapp_cvs_pool())
        my_obj = pool_module()
        my_pool = {
            "name": "Dummyname",
            "poolId": "1f63b3d0-4fd4-b4fe-1ed6-c62f5f20d975",
            "region": "us-east-1",
            "serviceLevel": "extreme",
            "sizeInBytes": 40000000000000000,
            "state": "available",
            "vendorID": "Dummy"
        }
        get_aws_api.return_value = my_pool
        get_put_api.return_value = my_pool, None
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_update_aws_netapp_cvs_pool_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_pool.NetAppAWSCVS.get_aws_netapp_cvs_pool')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.put')
    def test_update_aws_netapp_cvs_pool_fail(self, get_put_api, get_aws_api):
        set_module_args(self.set_args_update_aws_netapp_cvs_pool())
        my_obj = pool_module()
        my_pool = {
            "name": "Dummyname",
            "poolId": "1f63b3d0-4fd4-b4fe-1ed6-c62f5f20d975",
            "region": "us-east-1",
            "serviceLevel": "extreme",
            "sizeInBytes": 40000000000000000,
            "state": "available",
            "vendorID": "Dummy"
        }
        get_put_api.return_value = my_pool, "Error"
        get_aws_api.return_value = my_pool
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print('Info: test_update_aws_netapp_cvs_pool_fail: %s' % repr(exc.value))
        assert exc.value.args[0]['msg'] is not None

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_pool.NetAppAWSCVS.get_aws_netapp_cvs_pool')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.post')
    def test_create_aws_netapp_cvs_pool_pass(self, get_post_api, get_aws_api):
        set_module_args(self.set_args_create_aws_netapp_cvs_pool())
        my_obj = pool_module()
        my_pool = {
            "name": "Dummyname",
            "poolId": "1f63b3d0-4fd4-b4fe-1ed6-c62f5f20d975",
            "region": "us-east-1",
            "serviceLevel": "extreme",
            "sizeInBytes": 40000000000000000,
            "state": "available",
            "vendorID": "Dummy"
        }
        get_aws_api.return_value = None
        get_post_api.return_value = None, None
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_aws_netapp_cvs_pool_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_pool.NetAppAWSCVS.get_aws_netapp_cvs_pool')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.post')
    def test_create_aws_netapp_cvs_pool_fail(self, get_post_api, get_aws_api):
        set_module_args(self.set_args_create_aws_netapp_cvs_pool())
        my_obj = pool_module()
        my_pool = {
            "name": "Dummyname",
            "poolId": "1f63b3d0-4fd4-b4fe-1ed6-c62f5f20d975",
            "region": "us-east-1",
            "serviceLevel": "extreme",
            "sizeInBytes": 40000000000000000,
            "state": "available",
            "vendorID": "Dummy"
        }
        get_post_api.return_value = my_pool, "Error"
        get_aws_api.return_value = None
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print('Info: test_create_aws_netapp_cvs_pool_fail: %s' % repr(exc.value))
        assert exc.value.args[0]['msg'] is not None

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_pool.NetAppAWSCVS.get_aws_netapp_cvs_pool')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.delete')
    def test_delete_aws_netapp_cvs_pool_pass(self, get_delete_api, get_aws_api):
        set_module_args(self.set_args_delete_aws_netapp_cvs_pool())
        my_obj = pool_module()
        my_pool = {
            "name": "Dummyname",
            "poolId": "1f63b3d0-4fd4-b4fe-1ed6-c62f5f20d975",
            "region": "us-east-1",
            "serviceLevel": "extreme",
            "sizeInBytes": 40000000000000000,
            "state": "available",
            "vendorID": "Dummy"
        }
        get_aws_api.return_value = my_pool
        get_delete_api.return_value = None, None
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_delete_aws_netapp_cvs_pool_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_pool.NetAppAWSCVS.get_aws_netapp_cvs_pool')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.delete')
    def test_delete_aws_netapp_cvs_pool_fail(self, get_delete_api, get_aws_api):
        set_module_args(self.set_args_delete_aws_netapp_cvs_pool())
        my_obj = pool_module()
        my_pool = {
            "name": "Dummyname",
            "poolId": "1f63b3d0-4fd4-b4fe-1ed6-c62f5f20d975",
            "region": "us-east-1",
            "serviceLevel": "extreme",
            "sizeInBytes": 40000000000000000,
            "state": "available",
            "vendorID": "Dummy"
        }
        get_delete_api.return_value = my_pool, "Error"
        get_aws_api.return_value = my_pool
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print('Info: test_delete_aws_netapp_cvs_pool_fail: %s' % repr(exc.value))
        assert exc.value.args[0]['msg'] is not None
