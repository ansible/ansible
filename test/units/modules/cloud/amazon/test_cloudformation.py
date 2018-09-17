# (c) 2017 Red Hat Inc.
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

import pytest
from mock import patch

from units.utils.amazon_placebo_fixtures import placeboify, maybe_sleep
from ansible.modules.cloud.amazon import cloudformation as cfn_module

basic_yaml_tpl = """
---
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Basic template that creates an S3 bucket'
Resources:
  MyBucket:
    Type: "AWS::S3::Bucket"
Outputs:
  TheName:
    Value:
      !Ref MyBucket
"""

bad_json_tpl = """{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Description": "Broken template, no comma here ->"
  "Resources": {
    "MyBucket": {
      "Type": "AWS::S3::Bucket"
    }
  }
}"""


class FakeModule(object):
    def __init__(self, **kwargs):
        self.params = kwargs

    def fail_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception('FAIL')

    def exit_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception('EXIT')


def test_invalid_template_json(placeboify):
    connection = placeboify.client('cloudformation')
    params = {
        'StackName': 'ansible-test-wrong-json',
        'TemplateBody': bad_json_tpl,
    }
    m = FakeModule(disable_rollback=False)
    with pytest.raises(Exception, message='Malformed JSON should cause the test to fail') as exc_info:
        cfn_module.create_stack(m, params, connection)
    assert exc_info.match('FAIL')
    assert "ValidationError" in m.exit_kwargs['msg']


def test_client_request_token_s3_stack(maybe_sleep, placeboify):
    connection = placeboify.client('cloudformation')
    params = {
        'StackName': 'ansible-test-client-request-token-yaml',
        'TemplateBody': basic_yaml_tpl,
        'ClientRequestToken': '3faf3fb5-b289-41fc-b940-44151828f6cf',
    }
    m = FakeModule(disable_rollback=False)
    result = cfn_module.create_stack(m, params, connection)
    assert result['changed']
    assert len(result['events']) > 1
    # require that the final recorded stack state was CREATE_COMPLETE
    # events are retrieved newest-first, so 0 is the latest
    assert 'CREATE_COMPLETE' in result['events'][0]
    connection.delete_stack(StackName='ansible-test-client-request-token-yaml')


def test_basic_s3_stack(maybe_sleep, placeboify):
    connection = placeboify.client('cloudformation')
    params = {
        'StackName': 'ansible-test-basic-yaml',
        'TemplateBody': basic_yaml_tpl
    }
    m = FakeModule(disable_rollback=False)
    result = cfn_module.create_stack(m, params, connection)
    assert result['changed']
    assert len(result['events']) > 1
    # require that the final recorded stack state was CREATE_COMPLETE
    # events are retrieved newest-first, so 0 is the latest
    assert 'CREATE_COMPLETE' in result['events'][0]
    connection.delete_stack(StackName='ansible-test-basic-yaml')


def test_delete_nonexistent_stack(maybe_sleep, placeboify):
    connection = placeboify.client('cloudformation')
    result = cfn_module.stack_operation(connection, 'ansible-test-nonexist', 'DELETE')
    assert result['changed']
    assert 'Stack does not exist.' in result['log']


def test_get_nonexistent_stack(placeboify):
    connection = placeboify.client('cloudformation')
    assert cfn_module.get_stack_facts(connection, 'ansible-test-nonexist') is None


def test_missing_template_body():
    m = FakeModule()
    with pytest.raises(Exception, message='Expected module to fail with no template') as exc_info:
        cfn_module.create_stack(
            module=m,
            stack_params={},
            cfn=None
        )
    assert exc_info.match('FAIL')
    assert not m.exit_args
    assert "Either 'template', 'template_body' or 'template_url' is required when the stack does not exist." == m.exit_kwargs['msg']
