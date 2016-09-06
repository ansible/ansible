#!/usr/bin/python
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

DOCUMENTATION = '''
---
module: cloudformation_facts
short_description: Obtain facts about an AWS CloudFormation stack
description:
  - Gets information about an AWS CloudFormation stack
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
version_added: "2.2"
author: Justin Menga (@jmenga)
options:
    stack_name:
        description:
          - The name or id of the CloudFormation stack
        required: true
    all_facts:
        description:
            - Get all stack information for the stack
        required: false
        default: false
    stack_events:
        description:
            - Get stack events for the stack
        required: false
        default: false
    stack_template:
        description:
            - Get stack template body for the stack
        required: false
        default: false
    stack_resources:
        description:
            - Get stack resources for the stack
        required: false
        default: false
    stack_policy:
        description:
            - Get stack policy for the stack
        required: false
        default: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Get summary information about a stack
- cloudformation_facts:
    stack_name: my-cloudformation-stack

# Facts are published in ansible_facts['cloudformation'][<stack_name>]
- debug: msg={{ ansible_facts['cloudformation']['my-cloudformation-stack'] }}

# Get all stack information about a stack
- cloudformation_facts:
    stack_name: my-cloudformation-stack
    all_facts: true

# Get stack resource and stack policy information about a stack
- cloudformation_facts:
    stack_name: my-cloudformation-stack
    stack_resources: true
    stack_policy: true

# Example dictionary outputs for stack_outputs, stack_parameters and stack_resources:
"stack_outputs": {
    "ApplicationDatabaseName": "dazvlpr01xj55a.ap-southeast-2.rds.amazonaws.com",
    ...
},
"stack_parameters": {
    "DatabaseEngine": "mysql",
    "DatabasePassword": "****",
    ...
},
"stack_resources": {
    "AutoscalingGroup": "dev-someapp-AutoscalingGroup-1SKEXXBCAN0S7",
    "AutoscalingSecurityGroup": "sg-abcd1234",
    "ApplicationDatabase": "dazvlpr01xj55a",
    "EcsTaskDefinition": "arn:aws:ecs:ap-southeast-2:123456789:task-definition/dev-someapp-EcsTaskDefinition-1F2VM9QB0I7K9:1"
    ...
}
'''

RETURN = '''
stack_description:
    description: Summary facts about the stack
    returned: always
    type: dict
stack_outputs:
    description: Dictionary of stack outputs keyed by the value of each output 'OutputKey' parameter and corresponding value of each output 'OutputValue' parameter
    returned: always
    type: dict
stack_parameters:
    description: Dictionary of stack parameters keyed by the value of each parameter 'ParameterKey' parameter and corresponding value of each parameter 'ParameterValue' parameter
    returned: always
    type: dict
stack_events:
    description: All stack events for the stack
    returned: only if all_facts or stack_events is true
    type: list of events
stack_policy:
    description: Describes the stack policy for the stack
    returned: only if all_facts or stack_policy is true
    type: dict
stack_template:
    description: Describes the stack template for the stack
    returned: only if all_facts or stack_template is true
    type: dict
stack_resource_list:
    description: Describes stack resources for the stack
    returned: only if all_facts or stack_resourses is true
    type: list of resources
stack_resources:
    description: Dictionary of stack resources keyed by the value of each resource 'LogicalResourceId' parameter and corresponding value of each resource 'PhysicalResourceId' parameter
    returned: only if all_facts or stack_resourses is true
    type: dict
'''

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec
from ansible.module_utils.basic import AnsibleModule
from functools import partial
import json
import traceback

class CloudFormationServiceManager:
    """Handles CloudFormation Services"""

    def __init__(self, module):
        self.module = module

        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            self.client = boto3_conn(module, conn_type='client',
                                     resource='cloudformation', region=region,
                                     endpoint=ec2_url, **aws_connect_kwargs)
        except botocore.exceptions.NoRegionError:
            self.module.fail_json(msg="Region must be specified as a parameter, in AWS_DEFAULT_REGION environment variable or in boto configuration file")
        except Exception as e:
            self.module.fail_json(msg="Can't establish connection - " + str(e), exception=traceback.format_exc(e))

    def describe_stack(self, stack_name):
        try:
            func = partial(self.client.describe_stacks,StackName=stack_name)
            response = self.paginated_response(func, 'Stacks')
            if response:
                return response[0]
            self.module.fail_json(msg="Error describing stack - an empty response was returned")
        except Exception as e:
            self.module.fail_json(msg="Error describing stack - " + str(e), exception=traceback.format_exc(e))

    def list_stack_resources(self, stack_name):
        try:
            func = partial(self.client.list_stack_resources,StackName=stack_name)
            return self.paginated_response(func, 'StackResourceSummaries')
        except Exception as e:
            self.module.fail_json(msg="Error listing stack resources - " + str(e), exception=traceback.format_exc(e))

    def describe_stack_events(self, stack_name):
        try:
            func = partial(self.client.describe_stack_events,StackName=stack_name)
            return self.paginated_response(func, 'StackEvents')
        except Exception as e:
            self.module.fail_json(msg="Error describing stack events - " + str(e), exception=traceback.format_exc(e))

    def get_stack_policy(self, stack_name):
        try:
            response = self.client.get_stack_policy(StackName=stack_name)
            stack_policy = response.get('StackPolicyBody')
            if stack_policy:
                return json.loads(stack_policy)
            return dict()
        except Exception as e:
            self.module.fail_json(msg="Error getting stack policy - " + str(e), exception=traceback.format_exc(e))

    def get_template(self, stack_name):
        try:
            response = self.client.get_template(StackName=stack_name)
            return response.get('TemplateBody')
        except Exception as e:
            self.module.fail_json(msg="Error getting stack template - " + str(e), exception=traceback.format_exc(e))

    def paginated_response(self, func, result_key, next_token=None):
        '''
        Returns expanded response for paginated operations.
        The 'result_key' is used to define the concatenated results that are combined from each paginated response.
        '''
        args=dict()
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
        return dict(zip([i[key] for i in items], [i[value] for i in items]))
    else:
        return dict()

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        stack_name=dict(required=True, type='str' ),
        all_facts=dict(required=False, default=False, type='bool'),
        stack_policy=dict(required=False, default=False, type='bool'),
        stack_events=dict(required=False, default=False, type='bool'),
        stack_resources=dict(required=False, default=False, type='bool'),
        stack_template=dict(required=False, default=False, type='bool'),
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    # Describe the stack
    service_mgr = CloudFormationServiceManager(module)
    stack_name = module.params.get('stack_name')
    result = {
        'ansible_facts': { 'cloudformation': { stack_name:{} } }
    }
    facts = result['ansible_facts']['cloudformation'][stack_name]
    facts['stack_description'] = service_mgr.describe_stack(stack_name)

    # Create stack output and stack parameter dictionaries
    if facts['stack_description']:
        facts['stack_outputs'] = to_dict(facts['stack_description'].get('Outputs'), 'OutputKey', 'OutputValue')
        facts['stack_parameters'] = to_dict(facts['stack_description'].get('Parameters'), 'ParameterKey', 'ParameterValue')

    # normalize stack description API output
    facts['stack_description'] = camel_dict_to_snake_dict(facts['stack_description'])
    # camel2snake doesn't handle NotificationARNs properly, so let's fix that
    facts['stack_description']['notification_arns'] = facts['stack_description'].pop('notification_ar_ns', [])

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

    result['changed'] = False
    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
