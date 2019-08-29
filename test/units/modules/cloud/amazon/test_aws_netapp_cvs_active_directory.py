# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests ONTAP Ansible module: '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from units.compat import unittest
from units.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from requests import Response


from ansible.module_utils.netapp import AwsCvsRestAPI
from ansible.modules.cloud.amazon.aws_netapp_cvs_active_directory \
    import AwsCvsNetappActiveDir as ad_module


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
            'state': 'present',
            'DNS': '101.102.103.123',
            'domain': 'mydomain.com',
            'password': 'netapp1!',
            'username': 'myuser',
            'api_url': 'myapiurl.com',
            'secret_key': 'mysecretkey',
            'api_key': 'myapikey'
        })

    def set_default_args_pass_check(self):
        return dict({
            'state': 'present',
            'DNS': '101.102.103.123',
            'domain': 'mydomain.com',
            'password': 'netapp1!',
            'region': 'us-east-1',
            'netBIOS': 'testing',
            'username': 'myuser',
            'api_url': 'myapiurl.com',
            'secret_key': 'mysecretkey',
            'api_key': 'myapikey'
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args(self.set_default_args_fail_check())
            ad_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_module_fail_when_required_args_present(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            ad_module()
            exit_json(changed=True, msg="TestCase Fail when required ars are present")
        assert exc.value.args[0]['changed']

    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_active_directory.AwsCvsNetappActiveDir.get_activedirectoryId')
    @patch('ansible.modules.cloud.amazon.aws_netapp_cvs_active_directory.AwsCvsNetappActiveDir.get_activedirectory')
    @patch('ansible.module_utils.netapp.AwsCvsRestAPI.post')
    def test_create_aws_netapp_cvs_activedir(self, get_post_api, get_aws_api, get_ad_id):
        set_module_args(self.set_default_args_pass_check())
        my_obj = ad_module()
        my_ad = {
            'region': 'us-east-1',
            'DNS': '101.102.103.123',
            'domain': 'mydomain.com',
            'password': 'netapp1!',
            'netBIOS': 'testing',
            'username': 'myuser'
        }

        get_aws_api.return_value = None
        get_post_api.return_value = None, None
        get_ad_id.return_value = "123"
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_aws_netapp_cvs_active_directory: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
