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
module: ecs_taskdefinition_info
short_description: describe a task definition in ecs
notes:
    - for details of the parameters and returns see
      U(http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.Client.describe_task_definition)
    - This module was called C(ecs_taskdefinition_facts) before Ansible 2.9. The usage did not change.
description:
    - Describes a task definition in ecs.
version_added: "2.5"
author:
    - Gustavo Maia (@gurumaia)
    - Mark Chance (@Java1Guy)
    - Darek Kaczynski (@kaczynskid)
requirements: [ json, botocore, boto3 ]
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

- ecs_taskdefinition_info:
    task_definition: test-td
'''

RETURN = '''
container_definitions:
    description: Returns a list of complex objects representing the containers
    returned: success
    type: complex
    contains:
        name:
            description: The name of a container.
            returned: always
            type: str
        image:
            description: The image used to start a container.
            returned: always
            type: str
        cpu:
            description: The number of cpu units reserved for the container.
            returned: always
            type: int
        memoryReservation:
            description: The soft limit (in MiB) of memory to reserve for the container.
            returned: when present
            type: int
        links:
            description: Links to other containers.
            returned: when present
            type: str
        portMappings:
            description: The list of port mappings for the container.
            returned: always
            type: complex
            contains:
                containerPort:
                    description: The port number on the container.
                    returned: when present
                    type: int
                hostPort:
                    description: The port number on the container instance to reserve for your container.
                    returned: when present
                    type: int
                protocol:
                    description: The protocol used for the port mapping.
                    returned: when present
                    type: str
        essential:
            description: Whether this is an essential container or not.
            returned: always
            type: bool
        entryPoint:
            description: The entry point that is passed to the container.
            returned: when present
            type: str
        command:
            description: The command that is passed to the container.
            returned: when present
            type: str
        environment:
            description: The environment variables to pass to a container.
            returned: always
            type: complex
            contains:
                name:
                    description: The name of the environment variable.
                    returned: when present
                    type: str
                value:
                    description: The value of the environment variable.
                    returned: when present
                    type: str
        mountPoints:
            description: The mount points for data volumes in your container.
            returned: always
            type: complex
            contains:
                sourceVolume:
                    description: The name of the volume to mount.
                    returned: when present
                    type: str
                containerPath:
                    description: The path on the container to mount the host volume at.
                    returned: when present
                    type: str
                readOnly:
                    description: If this value is true , the container has read-only access to the volume.
                      If this value is false , then the container can write to the volume.
                    returned: when present
                    type: bool
        volumesFrom:
            description: Data volumes to mount from another container.
            returned: always
            type: complex
            contains:
                sourceContainer:
                    description: The name of another container within the same task definition to mount volumes from.
                    returned: when present
                    type: str
                readOnly:
                    description: If this value is true , the container has read-only access to the volume.
                      If this value is false , then the container can write to the volume.
                    returned: when present
                    type: bool
        hostname:
            description: The hostname to use for your container.
            returned: when present
            type: str
        user:
            description: The user name to use inside the container.
            returned: when present
            type: str
        workingDirectory:
            description: The working directory in which to run commands inside the container.
            returned: when present
            type: str
        disableNetworking:
            description: When this parameter is true, networking is disabled within the container.
            returned: when present
            type: bool
        privileged:
            description: When this parameter is true, the container is given elevated
              privileges on the host container instance (similar to the root user).
            returned: when present
            type: bool
        readonlyRootFilesystem:
            description: When this parameter is true, the container is given read-only access to its root file system.
            returned: when present
            type: bool
        dnsServers:
            description: A list of DNS servers that are presented to the container.
            returned: when present
            type: str
        dnsSearchDomains:
            description: A list of DNS search domains that are presented to the container.
            returned: when present
            type: str
        extraHosts:
            description: A list of hostnames and IP address mappings to append to the /etc/hosts file on the container.
            returned: when present
            type: complex
            contains:
                hostname:
                    description: The hostname to use in the /etc/hosts entry.
                    returned: when present
                    type: str
                ipAddress:
                    description: The IP address to use in the /etc/hosts entry.
                    returned: when present
                    type: str
        dockerSecurityOptions:
            description: A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems.
            returned: when present
            type: str
        dockerLabels:
            description: A key/value map of labels to add to the container.
            returned: when present
            type: str
        ulimits:
            description: A list of ulimits to set in the container.
            returned: when present
            type: complex
            contains:
                name:
                    description: The type of the ulimit .
                    returned: when present
                    type: str
                softLimit:
                    description: The soft limit for the ulimit type.
                    returned: when present
                    type: int
                hardLimit:
                    description: The hard limit for the ulimit type.
                    returned: when present
                    type: int
        logConfiguration:
            description: The log configuration specification for the container.
            returned: when present
            type: str
        options:
            description: The configuration options to send to the log driver.
            returned: when present
            type: str

family:
    description: The family of your task definition, used as the definition name
    returned: always
    type: str
task_definition_arn:
    description: ARN of the task definition
    returned: always
    type: str
task_role_arn:
    description: The ARN of the IAM role that containers in this task can assume
    returned: when role is set
    type: str
network_mode:
    description: Network mode for the containers
    returned: always
    type: str
revision:
    description: Revision number that was queried
    returned: always
    type: int
volumes:
    description: The list of volumes in a task
    returned: always
    type: complex
    contains:
        name:
            description: The name of the volume.
            returned: when present
            type: str
        host:
            description: The contents of the host parameter determine whether your data volume
              persists on the host container instance and where it is stored.
            returned: when present
            type: bool
        source_path:
            description: The path on the host container instance that is presented to the container.
            returned: when present
            type: str
status:
    description: The status of the task definition
    returned: always
    type: str
requires_attributes:
    description: The container instance attributes required by your task
    returned: when present
    type: complex
    contains:
        name:
            description: The name of the attribute.
            returned: when present
            type: str
        value:
            description: The value of the attribute.
            returned: when present
            type: str
        targetType:
            description: The type of the target with which to attach the attribute.
            returned: when present
            type: str
        targetId:
            description: The ID of the target.
            returned: when present
            type: str
placement_constraints:
    description: A list of placement constraint objects to use for tasks
    returned: always
    type: complex
    contains:
        type:
            description: The type of constraint.
            returned: when present
            type: str
        expression:
            description: A cluster query language expression to apply to the constraint.
            returned: when present
            type: str
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported AnsibleAWSModule


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        task_definition=dict(required=True, type='str')
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'ecs_taskdefinition_facts':
        module.deprecate("The 'ecs_taskdefinition_facts' module has been renamed to 'ecs_taskdefinition_info'", version='2.13')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    ecs = boto3_conn(module, conn_type='client', resource='ecs',
                     region=region, endpoint=ec2_url, **aws_connect_kwargs)

    try:
        ecs_td = ecs.describe_task_definition(taskDefinition=module.params['task_definition'])['taskDefinition']
    except botocore.exceptions.ClientError:
        ecs_td = {}

    module.exit_json(changed=False, **camel_dict_to_snake_dict(ecs_td))


if __name__ == '__main__':
    main()
