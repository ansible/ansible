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
module: ecs_task_facts
short_description: return facts about tasks in ecs
description:
    - Describes or lists tasks.
version_added: 2.0
options:
    details:
        description:
            - Set this to true if you want detailed information about the tasks.
        required: false
        default: false
        type: bool
    cluster:
        description:
            - The cluster in which to list tasks if other than the 'default'.
        required: false
        default: 'default'
        type: str
    task_list:
        description:
            - Set this to a list of task identifiers.  If 'details' is false, this is required.
        required: false
    family:
        required: False
        type: str

    container_instance:
        required: False
        type: 'str'
    max_results:
        required: False
        type: 'int'
    started_by:
        required: False
        type: 'str'
    service_name:
        required: False
        type: 'str'
    desired_status:
        required: False
        choices=['RUNNING', 'PENDING', 'STOPPED']

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic listing example
- ecs_task_facts:
    cluster=test-cluster
    task_list=123456789012345678901234567890123456

# Listing tasks with details
- ecs_task_facts:
    details: true
    cluster=test-cluster
    task_list=123456789012345678901234567890123456

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
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            if not region:
                module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
            self.ecs = boto3_conn(module, conn_type='client', resource='ecs', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg="Can't authorize connection - "+str(e))

    def transmogrify(self, params, field, dictionary, arg_name):
        if field in params and params[field] is not None:
            dictionary[arg_name] = params[field]

    def list_tasks(self, params):
        fn_args = dict()
        self.transmogrify(params, 'cluster', fn_args, 'cluster')
        self.transmogrify(params, 'container_instance', fn_args, 'containerInstance')
        self.transmogrify(params, 'family', fn_args, 'family')
        self.transmogrify(params, 'max_results', fn_args, 'maxResults')
        self.transmogrify(params, 'started_by', fn_args, 'startedBy')
        self.transmogrify(params, 'service_name', fn_args, 'startedBy')
        self.transmogrify(params, 'desired_status', fn_args, 'desiredStatus')
        relevant_response = dict()
        try:
            response = self.ecs.list_tasks(**fn_args)
            relevant_response['tasks'] = response['taskArns']
        except botocore.exceptions.ClientError:
            relevant_response['tasks'] = []
        return relevant_response

    def describe_tasks(self, cluster_name, tasks):
        response = self.ecs.describe_tasks(
            cluster=cluster_name if cluster_name else '',
            tasks=tasks.split(",") if tasks else []
        )
        relevant_response = dict(
            tasks = response['tasks'],
            tasks_not_running = response['failures'])
        return relevant_response

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        details=dict(required=False, type='bool' ),
        cluster=dict(required=False, type='str' ),
        task_list = dict(required=False, type='str'),
        family=dict(required= False, type='str' ),
        container_instance=dict(required=False, type='str' ),
        max_results=dict(required=False, type='int' ),
        started_by=dict(required=False, type='str' ),
        service_name=dict(required=False, type='str' ),
        desired_status=dict(required=False, choices=['RUNNING', 'PENDING', 'STOPPED'])
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    task_to_describe = module.params['family']
    show_details = False
    if 'details' in module.params and module.params['details']:
        show_details = True

    task_mgr = EcsTaskManager(module)
    if show_details:
        if 'task_list' not in module.params or not module.params['task_list']:
            module.fail_json(msg="task_list must be specified for ecs_task_facts")
        ecs_facts = task_mgr.describe_tasks(module.params['cluster'], module.params['task_list'])
    else:
        ecs_facts = task_mgr.list_tasks(module.params)
    ecs_facts_result = dict(changed=False, ansible_facts=ecs_facts)
    module.exit_json(**ecs_facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
