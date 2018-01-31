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

from ansible.compat.tests.mock import MagicMock, patch
from ansible.errors import AnsibleError

try:
    import ansible.plugins.lookup.aws_ssm as aws_ssm
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

missing_variable_fail_response = copy(simple_variable_success_response)
missing_variable_fail_response['Parameters'] = []
missing_variable_fail_response['InvalidParameters'] = ['missing_variable']


def test_lookup_variable():
    lookup = aws_ssm.LookupModule()

    boto3_client_double = MagicMock()
    boto3_client_double.return_value.get_parameters.return_value = simple_variable_success_response

    with patch.object(boto3, 'client', boto3_client_double):
        retval = lookup.run(["simple_variable"], {})
    assert(retval[0] == "simplevalue")


def test_path_lookup_variable():
    lookup = aws_ssm.LookupModule()

    boto3_client_double = MagicMock()
    boto3_client_double.return_value.get_parameters_by_path.return_value = path_success_response

    with patch.object(boto3, 'client', boto3_client_double):
        retval = lookup.run(["/testpath", "bypath"], {})
    assert(retval["/testpath/won"] == "simple_value_won")
    assert(retval["/testpath/too"] == "simple_value_too")


def test_warn_missing_variable():
    lookup = aws_ssm.LookupModule()

    boto3_client_double = MagicMock()
    # boto3_client_double.return_value.get_parameter_by_path.return_value = "simplevalue"
    boto3_client_double.return_value.get_parameters.return_value = missing_variable_fail_response

    with pytest.raises(AnsibleError):
        with patch.object(boto3, 'client', boto3_client_double):
            lookup.run(["missing_variable"], {})


error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Fake Testing Error'}}
operation_name = 'FakeOperation'


def test_warn_denied_variable():
    lookup = aws_ssm.LookupModule()

    boto3_client_double = MagicMock()
    # boto3_client_double.return_value.get_parameter_by_path.return_value = "simplevalue"
    boto3_client_double.return_value.get_parameters.side_effect = ClientError(error_response, operation_name)

    with pytest.raises(AnsibleError):
        with patch.object(boto3, 'client', boto3_client_double):
            lookup.run(["denied_variable"], {})
