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
module: ecs_taskdefinition_facts
short_description: return facts about task definitions in ecs
description:
    - Describes or lists task definitions.
version_added: 1.9
requirements: [ json, os, boto, botocore, boto3 ]
options:
    details:
        description:
            - Set this to true if you want detailed information about the tasks.
        required: false
        default: false
    name:
        description:
            - When details is true, the name must be provided.
        required: false
    family:
        description:
            - the name of the family of task definitions to list.
        required: false
    max_results:
        description:
            - The maximum number of results to return.
        required: false
    status:
        description:
            - Show only task descriptions of the given status. If omitted, it shows all
        required: false
        choices: ['ACTIVE', 'INACTIVE']
    sort:
        description:
            - Sort order of returned list of task definitions
        required: false
        choices: ['ASC', 'DESC']

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic listing example
- name: "Get task definitions with details"
  ecs_taskdefinition_facts:
    name: test-cluster-tasks
    details: true

- name: Get task definitions with details
  ecs_taskdefinition_facts:
    status: INACTIVE
    details: true
    family: test-cluster-rbjgjoaj-task
    name: "arn:aws:ecs:us-west-2:172139249013:task-definition/test-cluster-rbjgjoaj-task:1"
'''
RETURN = '''
task_definitions:
    description: array of ARN values for the known task definitions
    type: array of string or dict if details is true
    sample: ["arn:aws:ecs:us-west-2:172139249013:task-definition/console-sample-app-static:1"]
'''
try:
    import json, os
    import boto
    import botocore
    # import module snippets
    from ansible.module_utils.basic import *
    from ansible.module_utils.ec2 import *
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

class EcsTaskManager:
    """Handles ECS Tasks"""

    def __init__(self, module):
        self.module = module

        try:
            # self.ecs = boto3.client('ecs')
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            if not region:
                module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
            self.ecs = boto3_conn(module, conn_type='client', resource='ecs', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg=str(e))

    def transmogrify(self, params, field, dictionary, arg_name):
        if field in params and params[field] is not None:
            dictionary[arg_name] = params[field]

    def list_taskdefinitions(self, params):
        fn_args = dict()
        self.transmogrify(params, 'family', fn_args, 'familyPrefix')
        self.transmogrify(params, 'max_results', fn_args, 'maxResults')
        self.transmogrify(params, 'status', fn_args, 'status')
        self.transmogrify(params, 'sort', fn_args, 'sort')
        response = self.ecs.list_task_definitions(**fn_args)
        return dict(task_definitions=response['taskDefinitionArns'])

    def describe_taskdefinition(self, task_definition):
        try:
            response = self.ecs.describe_task_definition(taskDefinition=task_definition)
        except botocore.exceptions.ClientError:
            response = dict(taskDefinition=[ dict( name=task_definition, status="MISSING")])
        relevant_response = dict(
            task_definitions = response['taskDefinition']
        )
        return relevant_response

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        details=dict(required= False, type='bool' ),
        name=dict(required=False, type='str' ),
        family=dict(required=False, type='str' ),
        max_results=dict(required=False, type='int' ),
        status=dict(required=False, choices=['ACTIVE', 'INACTIVE']),
        sort=dict(required=False, choices=['ASC', 'DESC'])
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    show_details = False
    if 'details' in module.params and module.params['details']:
        if 'name' not in module.params or not module.params['name']:
            module.fail_json(msg="task definition name must be specified for ecs_taskdefinition_facts")
        show_details = True

    task_mgr = EcsTaskManager(module)
    if show_details:
        ecs_facts = task_mgr.describe_taskdefinition(module.params['name'])
    else:
        ecs_facts = task_mgr.list_taskdefinitions(module.params)
    ecs_facts_result = dict(changed=False, ansible_facts=ecs_facts)
    module.exit_json(**ecs_facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
