#
# (c) 2016 Michael De La Rue
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish

from __future__ import (absolute_import, division, print_function)

from nose.plugins.skip import SkipTest
import unittest
import pytest
import json
import copy
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic
from ansible.compat.tests.mock import Mock, patch
from ansible.module_utils.ec2 import HAS_BOTO3
if not HAS_BOTO3:
    raise SkipTest("test_ec2_asg.py requires the `boto3`, and `botocore` modules")

#lambda is a keyword so we have to hack this.
_temp = __import__("ansible.modules.cloud.amazon.lambda")

lda=getattr(_temp.modules.cloud.amazon,"lambda")


exit_return_dict={}

def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

base_function_config={
    'FunctionName' : 'lambda_name',
    'Role' : 'arn:aws:iam::987654321012:role/lambda_basic_execution',
    'Handler' : 'lambda_python.my_handler',
    'Description' : 'this that the other',
    'Timeout' : 3,
    'MemorySize' : 128,
    'Runtime' : 'python2.7',
    'CodeSha256' : 'AqMZ+xptM7aC9VXu+5jyp1sqO+Nj4WFMNzQxtPMP2n8=',
}

one_change_function_config=copy.copy(base_function_config)
one_change_function_config['Timeout']=4
two_change_function_config=copy.copy(one_change_function_config)
two_change_function_config['Role']='arn:aws:iam::987654321012:role/lambda_advanced_execution'

base_module_args={
    "region": "us-west-1",
    "name": "lambda_name",
    "state": "present",
    "zip_file": "test/units/modules/cloud/amazon/fixtures/thezip.zip",
    "runtime": 'python2.7',
    "role": 'arn:aws:iam::987654321012:role/lambda_basic_execution',
    "memory_size": 128,
    "timeout" : 3,
    "handler": 'lambda_python.my_handler'
}

fake_lambda_connection = Mock()


#TODO: def test_handle_different_types_in_config_params(monkeypatch):

def test_update_lambda_if_config_changed(monkeypatch):

    fake_lambda_connection.get_function.configure_mock(
        return_value={
            'Configuration' : two_change_function_config
        }
    )
    fake_lambda_connection.update_function_configuration.configure_mock(
        return_value={
            'Version' : 1
        }
    )
    fake_boto3_conn=Mock(return_value=fake_lambda_connection)

    set_module_args(base_module_args)
    @patch("ansible.modules.cloud.amazon.lambda.boto3_conn", fake_boto3_conn)
    def call_module():
        with pytest.raises(SystemExit):
            lda.main()

    call_module()

    #guard against calling other than for a lambda connection (e.g. IAM)
    assert(len(fake_boto3_conn.mock_calls) == 1)
    assert(len(fake_lambda_connection.update_function_configuration.mock_calls) == 1)

def test_update_lambda_if_only_one_config_item_changed(monkeypatch):

    fake_lambda_connection = Mock()
    fake_lambda_connection.get_function.configure_mock(
        return_value={
            'Configuration' : one_change_function_config
        }
    )
    fake_lambda_connection.update_function_configuration.configure_mock(
        return_value={
            'Version' : 1
        }
    )
    fake_boto3_conn=Mock(return_value=fake_lambda_connection)

    @patch("ansible.modules.cloud.amazon.lambda.boto3_conn", fake_boto3_conn)
    def call_module():
        with pytest.raises(SystemExit):
            lda.main()

    call_module()

    #guard against calling other than for a lambda connection (e.g. IAM)
    assert(len(fake_boto3_conn.mock_calls) == 1)
    assert(len(fake_lambda_connection.update_function_configuration.mock_calls) == 1)

def test_dont_update_lambda_if_nothing_changed(monkeypatch):

    fake_lambda_connection = Mock()
    fake_lambda_connection.get_function.configure_mock(
        return_value={
            'Configuration' : base_function_config
        }
    )
    fake_lambda_connection.update_function_configuration.configure_mock(
        return_value={
            'Version' : 1
        }
    )
    fake_boto3_conn=Mock(return_value=fake_lambda_connection)

    @patch("ansible.modules.cloud.amazon.lambda.boto3_conn", fake_boto3_conn)
    def call_module():
        with pytest.raises(SystemExit):
            lda.main()

    call_module()

    #guard against calling other than for a lambda connection (e.g. IAM)
    assert(len(fake_boto3_conn.mock_calls) == 1)
    assert(len(fake_lambda_connection.update_function_configuration.mock_calls) == 0)

def test_warn_region_not_specified():

    set_module_args({
        "name": "lambda_name",
        "state": "present",
        # Module is called without a region causing error
        # "region": "us-east-1",
        "zip_file": "test/units/modules/cloud/amazon/fixtures/thezip.zip",
        "runtime": 'python2.7',
        "role": 'arn:aws:iam::987654321012:role/lambda_basic_execution',
        "handler": 'lambda_python.my_handler'})

    class AnsibleFailJson(Exception):
        pass

    def fail_json(*args, **kwargs):
        kwargs['failed'] = True
        raise AnsibleFailJson(kwargs)

    def call_module():
        with patch.object(basic.AnsibleModule, 'fail_json', fail_json):
            with pytest.raises(AnsibleFailJson) as e:
                lda.main()
        result=e.value
        assert("region must be specified" in result[0]['msg'])

    call_module()

