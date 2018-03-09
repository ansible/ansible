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

import pytest
from copy import copy

from ansible.errors import AnsibleError

import ansible.plugins.lookup.aws_ssm as aws_ssm

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    pytestmark = pytest.mark.skip("This test requires the boto3 and botocore Python libraries")

simple_variable_success_response = {
    'Parameters': [
        {
            'Name': 'simple_variable',
            'Type': 'String',
            'Value': 'simplevalue',
            'Version': 1
        }
    ],
    'InvalidParameters': [],
    'ResponseMetadata': {
        'RequestId': '12121212-3434-5656-7878-9a9a9a9a9a9a',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-requestid': '12121212-3434-5656-7878-9a9a9a9a9a9a',
            'content-type': 'application/x-amz-json-1.1',
            'content-length': '116',
            'date': 'Tue, 23 Jan 2018 11:04:27 GMT'
        },
        'RetryAttempts': 0
    }
}

path_success_response = copy(simple_variable_success_response)
path_success_response['Parameters'] = [
    {'Name': '/testpath/too', 'Type': 'String', 'Value': 'simple_value_too', 'Version': 1},
    {'Name': '/testpath/won', 'Type': 'String', 'Value': 'simple_value_won', 'Version': 1}
]

missing_variable_response = copy(simple_variable_success_response)
missing_variable_response['Parameters'] = []
missing_variable_response['InvalidParameters'] = ['missing_variable']

some_missing_variable_response = copy(simple_variable_success_response)
some_missing_variable_response['Parameters'] = [
    {'Name': 'simple', 'Type': 'String', 'Value': 'simple_value', 'Version': 1},
    {'Name': '/testpath/won', 'Type': 'String', 'Value': 'simple_value_won', 'Version': 1}
]
some_missing_variable_response['InvalidParameters'] = ['missing_variable']


dummy_credentials = {}
dummy_credentials['boto_profile'] = None
dummy_credentials['aws_secret_key'] = "notasecret"
dummy_credentials['aws_access_key'] = "notakey"
dummy_credentials['aws_security_token'] = None
dummy_credentials['region'] = 'eu-west-1'


def test_lookup_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameters.return_value = simple_variable_success_response
    boto3_client_double = boto3_double.Session.return_value.client

    with mocker.patch.object(boto3, 'session', boto3_double):
        retval = lookup.run(["simple_variable"], {}, **dummy_credentials)
    assert(retval[0] == "simplevalue")
    boto3_client_double.assert_called_with('ssm', 'eu-west-1', aws_access_key_id='notakey',
                                           aws_secret_access_key="notasecret", aws_session_token=None)


def test_path_lookup_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    get_path_fn = boto3_double.Session.return_value.client.return_value.get_parameters_by_path
    get_path_fn.return_value = path_success_response
    boto3_client_double = boto3_double.Session.return_value.client

    with mocker.patch.object(boto3, 'session', boto3_double):
        args = copy(dummy_credentials)
        args["bypath"] = 'true'
        retval = lookup.run(["/testpath"], {}, **args)
    assert(retval[0]["/testpath/won"] == "simple_value_won")
    assert(retval[0]["/testpath/too"] == "simple_value_too")
    boto3_client_double.assert_called_with('ssm', 'eu-west-1', aws_access_key_id='notakey',
                                           aws_secret_access_key="notasecret", aws_session_token=None)
    get_path_fn.assert_called_with(Path="/testpath", Recursive=False, WithDecryption=True)


def test_return_none_for_missing_variable(mocker):
    """
    during jinja2 templates, we can't shouldn't normally raise exceptions since this blocks the ability to use defaults.

    for this reason we return ```None``` for missing variables
    """
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameters.return_value = missing_variable_response

    with mocker.patch.object(boto3, 'session', boto3_double):
        retval = lookup.run(["missing_variable"], {}, **dummy_credentials)
    assert(retval[0] is None)


def test_match_retvals_to_call_params_even_with_some_missing_variables(mocker):
    """
    If we get a complex list of variables with some missing and some not, we still have to return a
    list which matches with the original variable list.
    """
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameters.return_value = some_missing_variable_response

    with mocker.patch.object(boto3, 'session', boto3_double):
        retval = lookup.run(["simple", "missing_variable", "/testpath/won", "simple"], {}, **dummy_credentials)
    assert(retval == ["simple_value", None, "simple_value_won", "simple_value"])


error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Fake Testing Error'}}
operation_name = 'FakeOperation'


def test_warn_denied_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameters.side_effect = ClientError(error_response, operation_name)

    with pytest.raises(AnsibleError):
        with mocker.patch.object(boto3, 'session', boto3_double):
            lookup.run(["denied_variable"], {}, **dummy_credentials)
