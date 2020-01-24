# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: aws_netapp_cvs_snapshots'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest


from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from requests import Response
from ansible.modules.cloud.amazon.aws_netapp_cvs_snapshots \
    import AwsCvsNetappSnapshot as snapshot_module


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
            'name': 'TestFilesystem',
            'fileSystemId': 'standard',
            'from_name': 'from_TestFilesystem',
            'region': 'us-east-1',
            'api_url': 'hostname.com',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def set_default_args_pass_check(self):
        return dict({
            'state': 'present',
            'name': 'testSnapshot',
            'fileSystemId': 'standard',
            'from_name': 'from_TestFilesystem',
            'region': 'us-east-1',
            'api_url': 'hostname.com',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def set_args_create_aws_netapp_cvs_snapshots(self):
        return dict({
            'state': 'present',
            'name': 'testSnapshot',
            'fileSystemId': '123-4213-432-432',
            'region': 'us-east-1',
            'api_url': 'hostname.com',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def set_args_delete_aws_netapp_cvs_snapshots(self):
        return dict({
            'state': 'absent',
            'name': 'testSnapshot',
            'region': 'us-east-1',
            'api_url': 'hostname.com',
            'api_key': 'myapikey',
            'secret_key': 'mysecretkey'
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            snapshot_module()
        print('Info: test_module_fail_when_required_args_missing: %s' % exc.value.args[0]['msg'])

    def test_module_fail_when_required_args_present(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            snapshot_module()
            exit_json(changed=True, msg="Induced arguments check")
        print('Info: test_module_fail_when_required_args_present: %s' % exc.value.args[0]['msg'])
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_snapshots.AwsCvsNetappSnapshot.getSnapshotId')
    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_snapshots.AwsCvsNetappSnapshot.getfilesystemId')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.post')
    def test_create_aws_netapp_cvs_snapshots_pass(self, get_post_api, getfilesystemId, getSnapshotId):
        set_module_args(self.set_args_create_aws_netapp_cvs_snapshots())
        my_obj = snapshot_module()
        getfilesystemId.return_value = 'fiesystemName'
        getSnapshotId.return_value = None
        get_post_api.return_value = None, None
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_aws_netapp_cvs_snapshots_pass: %s' % repr(exc.value.args[0]))
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_snapshots.AwsCvsNetappSnapshot.getSnapshotId')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.delete')
    def test_delete_aws_netapp_cvs_snapshots_pass(self, get_post_api, getSnapshotId):
        set_module_args(self.set_args_delete_aws_netapp_cvs_snapshots())
        my_obj = snapshot_module()
        getSnapshotId.return_value = "1f63b3d0-4fd4-b4fe-1ed6-c62f5f20d975"
        get_post_api.return_value = None, None
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_aws_netapp_cvs_snapshots_pass: %s' % repr(exc.value.args[0]))
        assert exc.value.args[0]['changed']
