#
# (c) 2017 Michael De La Rue
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
import json
import copy
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic
from ansible.compat.tests.mock import MagicMock, Mock, patch
from ansible.module_utils.ec2 import HAS_BOTO3
if not HAS_BOTO3:
    raise SkipTest("test_ec2_asg.py requires the `boto3`, and `botocore` modules")

# lambda is a keyword so we have to hack this.
_temp = __import__("ansible.modules.cloud.amazon.lambda")
lda = getattr(_temp.modules.cloud.amazon,"lambda")

def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

base_lambda_config={
    'FunctionName' : 'lambda_name',
    'Role' : 'arn:aws:iam::987654321012:role/lambda_basic_execution',
    'Handler' : 'lambda_python.my_handler',
    'Description' : 'this that the other',
    'Timeout' : 3,
    'MemorySize' : 128,
    'Runtime' : 'python2.7',
    'CodeSha256' : 'AqMZ+xptM7aC9VXu+5jyp1sqO+Nj4WFMNzQxtPMP2n8=',
}

one_change_lambda_config=copy.copy(base_lambda_config)
one_change_lambda_config['Timeout']=4
two_change_lambda_config=copy.copy(one_change_lambda_config)
two_change_lambda_config['Role']='arn:aws:iam::987654321012:role/lambda_advanced_execution'
code_change_lambda_config=copy.copy(base_lambda_config)
code_change_lambda_config['CodeSha256']='P+Zy8U4T4RiiHWElhL10VBKj9jw4rSJ5bm/TiW+4Rts='

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


def make_mock_connection(config):
    """return a mock of ansible's boto3_conn ready to return a mock AWS API client"""
    lambda_client_double = MagicMock()
    lambda_client_double.get_function.configure_mock(
        return_value={
            'Configuration' : config
        }
    )
    lambda_client_double.update_function_configuration.configure_mock(
        return_value={
            'Version' : 1
        }
    )
    fake_boto3_conn=Mock(return_value=lambda_client_double)
    return (fake_boto3_conn, lambda_client_double)


class AnsibleFailJson(Exception):
    pass


def fail_json_double(*args, **kwargs):
    """works like fail_json but returns module results inside exception instead of stdout"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


#TODO: def test_handle_different_types_in_config_params():


def test_update_lambda_if_code_changed():

    set_module_args(base_module_args)
    (boto3_conn_double, lambda_client_double)=make_mock_connection(code_change_lambda_config)

    with patch.object(lda, 'boto3_conn', boto3_conn_double):
        try:
            lda.main()
        except SystemExit:
            pass

    # guard against calling other than for a lambda connection (e.g. IAM)
    assert(len(boto3_conn_double.mock_calls) == 1), "multiple boto connections used unexpectedly"
    assert(len(lambda_client_double.update_function_configuration.mock_calls) == 0), \
        "unexpectedly updatede lambda configuration when only code changed"
    assert(len(lambda_client_double.update_function_configuration.mock_calls) < 2), \
        "lambda function update called multiple times when only one time should be needed"
    assert(len(lambda_client_double.update_function_code.mock_calls) > 1), \
        "failed to update lambda function when code changed"
    # 3 because after uploading we call into the return from mock to try to find what function version
    # was returned so the MagicMock actually sees two calls for one update.
    assert(len(lambda_client_double.update_function_code.mock_calls) < 3), \
        "lambda function code update called multiple times when only one time should be needed"

def test_update_lambda_if_config_changed():

    set_module_args(base_module_args)
    (boto3_conn_double,lambda_client_double)=make_mock_connection(two_change_lambda_config)

    with patch.object(lda, 'boto3_conn', boto3_conn_double):
        try:
            lda.main()
        except SystemExit:
            pass

    # guard against calling other than for a lambda connection (e.g. IAM)
    assert(len(boto3_conn_double.mock_calls) == 1), "multiple boto connections used unexpectedly"
    assert(len(lambda_client_double.update_function_configuration.mock_calls) > 0), \
        "failed to update lambda function when configuration changed"
    assert(len(lambda_client_double.update_function_configuration.mock_calls) < 2), \
        "lambda function update called multiple times when only one time should be needed"
    assert(len(lambda_client_double.update_function_code.mock_calls) == 0), \
        "updated lambda code when no change should have happened"

def test_update_lambda_if_only_one_config_item_changed():

    set_module_args(base_module_args)
    (boto3_conn_double,lambda_client_double)=make_mock_connection(one_change_lambda_config)

    with patch.object(lda, 'boto3_conn', boto3_conn_double):
        try:
            lda.main()
        except SystemExit:
            pass

    # guard against calling other than for a lambda connection (e.g. IAM)
    assert(len(boto3_conn_double.mock_calls) == 1), "multiple boto connections used unexpectedly"
    assert(len(lambda_client_double.update_function_configuration.mock_calls) > 0), \
        "failed to update lambda function when configuration changed"
    assert(len(lambda_client_double.update_function_configuration.mock_calls) < 2), \
        "lambda function update called multiple times when only one time should be needed"
    assert(len(lambda_client_double.update_function_code.mock_calls) == 0), \
        "updated lambda code when no change should have happened"

def test_dont_update_lambda_if_nothing_changed():

    set_module_args(base_module_args)
    (boto3_conn_double,lambda_client_double)=make_mock_connection(base_lambda_config)

    with patch.object(lda, 'boto3_conn', boto3_conn_double):
        try:
            lda.main()
        except SystemExit:
            pass

    # guard against calling other than for a lambda connection (e.g. IAM)
    assert(len(boto3_conn_double.mock_calls) == 1), "multiple boto connections used unexpectedly"
    assert(len(lambda_client_double.update_function_configuration.mock_calls) == 0), \
        "updated lambda function when no configuration changed"
    assert(len(lambda_client_double.update_function_code.mock_calls) == 0 ), \
        "updated lambda code when no change should have happened"

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

    get_aws_connection_info_double=Mock(return_value=(None,None,None))

    with patch.object(lda, 'get_aws_connection_info', get_aws_connection_info_double):
        with patch.object(basic.AnsibleModule, 'fail_json', fail_json_double):
            try:
                lda.main()
            except AnsibleFailJson as e:
                result = e.args[0]
                assert("region must be specified" in result['msg'])
