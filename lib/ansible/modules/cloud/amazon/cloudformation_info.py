#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudformation_info
short_description: Obtain information about an AWS CloudFormation stack
description:
  - Gets information about an AWS CloudFormation stack
  - This module was called C(cloudformation_facts) before Ansible 2.9, returning C(ansible_facts).
    Note that the M(cloudformation_info) module no longer returns C(ansible_facts)!
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
version_added: "2.2"
author: Justin Menga (@jmenga)
options:
    stack_name:
        description:
          - The name or id of the CloudFormation stack. Gathers information on all stacks by default.
    all_facts:
        description:
            - Get all stack information for the stack
        type: bool
        default: 'no'
    stack_events:
        description:
            - Get stack events for the stack
        type: bool
        default: 'no'
    stack_template:
        description:
            - Get stack template body for the stack
        type: bool
        default: 'no'
    stack_resources:
        description:
            - Get stack resources for the stack
        type: bool
        default: 'no'
    stack_policy:
        description:
            - Get stack policy for the stack
        type: bool
        default: 'no'
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Get summary information about a stack
- cloudformation_info:
    stack_name: my-cloudformation-stack
  register: output

- debug:
    msg: "{{ output['cloudformation']['my-cloudformation-stack'] }}"

# When the module is called as cloudformation_facts, return values are published
# in ansible_facts['cloudformation'][<stack_name>] and can be used as follows.
# Note that this is deprecated and will stop working in Ansible 2.13.

- cloudformation_facts:
    stack_name: my-cloudformation-stack

- debug:
    msg: "{{ ansible_facts['cloudformation']['my-cloudformation-stack'] }}"

# Get stack outputs, when you have the stack name available as a fact
- set_fact:
    stack_name: my-awesome-stack

- cloudformation_info:
    stack_name: "{{ stack_name }}"
  register: my_stack

- debug:
    msg: "{{ my_stack.cloudformation[stack_name].stack_outputs }}"

# Get all stack information about a stack
- cloudformation_info:
    stack_name: my-cloudformation-stack
    all_facts: true

# Get stack resource and stack policy information about a stack
- cloudformation_info:
    stack_name: my-cloudformation-stack
    stack_resources: true
    stack_policy: true

# Fail if the stack doesn't exist
- name: try to get facts about a stack but fail if it doesn't exist
  cloudformation_info:
    stack_name: nonexistent-stack
    all_facts: yes
  failed_when: cloudformation['nonexistent-stack'] is undefined

# Example dictionary outputs for stack_outputs, stack_parameters and stack_resources:
# "stack_outputs": {
#     "ApplicationDatabaseName": "dazvlpr01xj55a.ap-southeast-2.rds.amazonaws.com",
#     ...
# },
# "stack_parameters": {
#     "DatabaseEngine": "mysql",
#     "DatabasePassword": "****",
#     ...
# },
# "stack_resources": {
#     "AutoscalingGroup": "dev-someapp-AutoscalingGroup-1SKEXXBCAN0S7",
#     "AutoscalingSecurityGroup": "sg-abcd1234",
#     "ApplicationDatabase": "dazvlpr01xj55a",
#     "EcsTaskDefinition": "arn:aws:ecs:ap-southeast-2:123456789:task-definition/dev-someapp-EcsTaskDefinition-1F2VM9QB0I7K9:1"
#     ...
# }
'''

RETURN = '''
stack_description:
    description: Summary facts about the stack
    returned: if the stack exists
    type: dict
stack_outputs:
    description: Dictionary of stack outputs keyed by the value of each output 'OutputKey' parameter and corresponding value of each
                 output 'OutputValue' parameter
    returned: if the stack exists
    type: dict
stack_parameters:
    description: Dictionary of stack parameters keyed by the value of each parameter 'ParameterKey' parameter and corresponding value of
                 each parameter 'ParameterValue' parameter
    returned: if the stack exists
    type: dict
stack_events:
    description: All stack events for the stack
    returned: only if all_facts or stack_events is true and the stack exists
    type: list
stack_policy:
    description: Describes the stack policy for the stack
    returned: only if all_facts or stack_policy is true and the stack exists
    type: dict
stack_template:
    description: Describes the stack template for the stack
    returned: only if all_facts or stack_template is true and the stack exists
    type: dict
stack_resource_list:
    description: Describes stack resources for the stack
    returned: only if all_facts or stack_resourses is true and the stack exists
    type: list
stack_resources:
    description: Dictionary of stack resources keyed by the value of each resource 'LogicalResourceId' parameter and corresponding value of each
                 resource 'PhysicalResourceId' parameter
    returned: only if all_facts or stack_resourses is true and the stack exists
    type: dict
'''

import json
import traceback
from functools import partial

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (get_aws_connection_info, ec2_argument_spec, boto3_conn,
                                      camel_dict_to_snake_dict, AWSRetry, boto3_tag_list_to_ansible_dict)


class CloudFormationServiceManager:
    """Handles CloudFormation Services"""

    def __init__(self, module):
        self.module = module

        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            self.client = boto3_conn(module, conn_type='client',
                                     resource='cloudformation', region=region,
                                     endpoint=ec2_url, **aws_connect_kwargs)
            backoff_wrapper = AWSRetry.jittered_backoff(retries=10, delay=3, max_delay=30)
            self.client.describe_stacks = backoff_wrapper(self.client.describe_stacks)
            self.client.list_stack_resources = backoff_wrapper(self.client.list_stack_resources)
            self.client.describe_stack_events = backoff_wrapper(self.client.describe_stack_events)
            self.client.get_stack_policy = backoff_wrapper(self.client.get_stack_policy)
            self.client.get_template = backoff_wrapper(self.client.get_template)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(msg="Region must be specified as a parameter, in AWS_DEFAULT_REGION environment variable or in boto configuration file")
        except Exception as e:
            self.module.fail_json(msg="Can't establish connection - " + str(e), exception=traceback.format_exc())

    def describe_stacks(self, stack_name=None):
        try:
            kwargs = {'StackName': stack_name} if stack_name else {}
            func = partial(self.client.describe_stacks, **kwargs)
            response = self.paginated_response(func, 'Stacks')
            if response is not None:
                return response
            self.module.fail_json(msg="Error describing stack(s) - an empty response was returned")
        except Exception as e:
            if 'does not exist' in e.response['Error']['Message']:
                # missing stack, don't bail.
                return {}
            self.module.fail_json(msg="Error describing stack - " + to_native(e), exception=traceback.format_exc())

    def list_stack_resources(self, stack_name):
        try:
            func = partial(self.client.list_stack_resources, StackName=stack_name)
            return self.paginated_response(func, 'StackResourceSummaries')
        except Exception as e:
            self.module.fail_json(msg="Error listing stack resources - " + str(e), exception=traceback.format_exc())

    def describe_stack_events(self, stack_name):
        try:
            func = partial(self.client.describe_stack_events, StackName=stack_name)
            return self.paginated_response(func, 'StackEvents')
        except Exception as e:
            self.module.fail_json(msg="Error describing stack events - " + str(e), exception=traceback.format_exc())

    def get_stack_policy(self, stack_name):
        try:
            response = self.client.get_stack_policy(StackName=stack_name)
            stack_policy = response.get('StackPolicyBody')
            if stack_policy:
                return json.loads(stack_policy)
            return dict()
        except Exception as e:
            self.module.fail_json(msg="Error getting stack policy - " + str(e), exception=traceback.format_exc())

    def get_template(self, stack_name):
        try:
            response = self.client.get_template(StackName=stack_name)
            return response.get('TemplateBody')
        except Exception as e:
            self.module.fail_json(msg="Error getting stack template - " + str(e), exception=traceback.format_exc())

    def paginated_response(self, func, result_key, next_token=None):
        '''
        Returns expanded response for paginated operations.
        The 'result_key' is used to define the concatenated results that are combined from each paginated response.
        '''
        args = dict()
        if next_token:
            args['NextToken'] = next_token
        response = func(**args)
        result = response.get(result_key)
        next_token = response.get('NextToken')
        if not next_token:
            return result
        return result + self.paginated_response(func, result_key, next_token)


def to_dict(items, key, value):
    ''' Transforms a list of items to a Key/Value dictionary '''
    if items:
        return dict(zip([i.get(key) for i in items], [i.get(value) for i in items]))
    else:
        return dict()


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        stack_name=dict(),
        all_facts=dict(required=False, default=False, type='bool'),
        stack_policy=dict(required=False, default=False, type='bool'),
        stack_events=dict(required=False, default=False, type='bool'),
        stack_resources=dict(required=False, default=False, type='bool'),
        stack_template=dict(required=False, default=False, type='bool'),
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    is_old_facts = module._name == 'cloudformation_facts'
    if is_old_facts:
        module.deprecate("The 'cloudformation_facts' module has been renamed to 'cloudformation_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    service_mgr = CloudFormationServiceManager(module)

    if is_old_facts:
        result = {'ansible_facts': {'cloudformation': {}}}
    else:
        result = {'cloudformation': {}}

    for stack_description in service_mgr.describe_stacks(module.params.get('stack_name')):
        facts = {'stack_description': stack_description}
        stack_name = stack_description.get('StackName')

        # Create stack output and stack parameter dictionaries
        if facts['stack_description']:
            facts['stack_outputs'] = to_dict(facts['stack_description'].get('Outputs'), 'OutputKey', 'OutputValue')
            facts['stack_parameters'] = to_dict(facts['stack_description'].get('Parameters'), 'ParameterKey', 'ParameterValue')
            facts['stack_tags'] = boto3_tag_list_to_ansible_dict(facts['stack_description'].get('Tags'))

        # normalize stack description API output
        facts['stack_description'] = camel_dict_to_snake_dict(facts['stack_description'])

        # Create optional stack outputs
        all_facts = module.params.get('all_facts')
        if all_facts or module.params.get('stack_resources'):
            facts['stack_resource_list'] = service_mgr.list_stack_resources(stack_name)
            facts['stack_resources'] = to_dict(facts.get('stack_resource_list'), 'LogicalResourceId', 'PhysicalResourceId')
        if all_facts or module.params.get('stack_template'):
            facts['stack_template'] = service_mgr.get_template(stack_name)
        if all_facts or module.params.get('stack_policy'):
            facts['stack_policy'] = service_mgr.get_stack_policy(stack_name)
        if all_facts or module.params.get('stack_events'):
            facts['stack_events'] = service_mgr.describe_stack_events(stack_name)

        if is_old_facts:
            result['ansible_facts']['cloudformation'][stack_name] = facts
        else:
            result['cloudformation'][stack_name] = facts

    result['changed'] = False
    module.exit_json(**result)


if __name__ == '__main__':
    main()
