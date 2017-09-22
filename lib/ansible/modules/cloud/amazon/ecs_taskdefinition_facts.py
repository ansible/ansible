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
module: ecs_taskdefinition_facts
short_description: describe a task definition in ecs
notes:
    - for details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.describe_task_definition)
description:
    - Describes a task definition in ecs.
version_added: "2.5"
author:
    - Gustavo Maia(@gurumaia)
    - Mark Chance(@Java1Guy)
    - Darek Kaczynski (@kaczynskid)
requirements: [ json, boto, botocore, boto3 ]
options:
    task_definition:
        description:
            - The name of the task definition to get details for
        required: true
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- ecs_taskdefinition_facts:
    task_definition: test-td
'''

RETURN = '''
containerDefinitions:
    description: Returns a list of complex objects representing the containers
    returned: success
    type: complex
family:
    description: The family of your task definition, used as the definition name
    returned: always
    type: string
taskDefinitionArn:
    description: ARN of the task definition
    returned: always
    type: string
taskRoleArn:
    description: The ARN of the IAM role that containers in this task can assume
    returned: when role is set
    type: string
networkMode:
    description: Network mode for the containers
    returned: always
    type: string
revision:
    description: Revision number that was queried
    returned: always
    type: int
volumes:
    description: The list of volumes in a task
    returned: always
    type: complex
status:
    description: The status of the task definition
    returned: always
    type: string
requiresAttributes:
    description: The container instance attributes required by your task
    returned: when present
    type: complex
placementConstraints:
    description: A list of placement constraint objects to use for tasks
    returned: always
    type: complex
'''  # NOQA

try:
    import boto
    import botocore
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info


class EcsTaskManager:
    """Handles ECS Tasks"""

    def __init__(self, module):
        self.module = module

        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            if not region:
                module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
            self.ecs = boto3_conn(module, conn_type='client', resource='ecs', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound as e:
            self.module.fail_json(msg="Can't authorize connection - %s" % str(e))

    def describe_task_definitions(self, family):
        # Return the full descriptions of the task definition
        return self.ecs.describe_task_definition(taskDefinition=family)['taskDefinition']
def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        task_definition=dict(required=True, type='str' )
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    task_mgr = EcsTaskManager(module)
    ecs_td_facts = task_mgr.describe_task_definitions(module.params['task_definition'])

    ecs_td_facts_result = dict(changed=False, ansible_facts=ecs_td_facts)
    module.exit_json(**ecs_td_facts_result)


if __name__ == '__main__':
    main()
