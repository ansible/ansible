#!/usr/bin/python

# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ecs_instance
short_description: Manage the state of an ECS instance.
description:
    - Manage the state of an ECS instance. Valid states are either ACTIVE or DRAINING. See
      U(https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_UpdateContainerInstancesState.html) for details.
version_added: "2.7"
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  cluster:
    description:
      - The short name or full Amazon Resource Name (ARN) of the cluster that hosts the container instance to update. If you do
        not specify a cluster, the default cluster is assumed.
    required: false
  container_instances:
    description:
      - A list of container instance IDs or full ARN entries.
    required: true
  status:
    description:
      - The container instance state with which to update the container instance.
    required: true
    choices: ['ACTIVE', 'DRAINING']
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Set an ECS instance state to ACTIVE in the xyz cluster
- ecs_instance:
    cluster: xyz
    container_instances:
      - i-1234567890
    state: ACTIVE

# Set two instances in the default cluster to DRAINING
- ecs_instance:
    container_instances:
      - i-1234567890
      - i-1234567891
    state: DRAINING

'''

RETURN = '''
container_instances:
  description: The list of container instances.
  returned: always
  type: list
  sample: []
failures:
  description: Any failures associated with the call.
  returned: always
  type: list
  sample: []
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

# Non-ansible imports
try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass


def _get_container_id_from_arn(container_arn_or_id):
    """
    Get the ECS container instance ID from its arn

    :param container_arn_or_id: either an ARN or ID of an ECS instance
    :return: the instance ID portion only as a string
    """

    if container_arn_or_id.startswith("arn:aws:ecs"):
        return container_arn_or_id.split("/")[-1]
    else:
        return container_arn_or_id


def _list_ecs_cluster_instances(connection, module, cluster_name):
    """
    Get a list of container instances of a particular ECS cluster

    :param connection: AWS boto3 ecs connection
    :param module: Ansible module
    :param cluster_name: name of ECS cluster to lookup instances for
    :return: full list of instance ARNs attached to the cluster
    """

    try:
        ecs_cluster_instances_paginator = connection.get_paginator('list_container_instances')
        if cluster_name is None:
            return ecs_cluster_instances_paginator.paginate().build_full_result()['containerInstanceArns']
        else:
            return ecs_cluster_instances_paginator.paginate(cluster=cluster_name).build_full_result()['containerInstanceArns']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


def _describe_ecs_cluster_instance(connection, module, cluster_name, instance_arn):
    """
    Describe an ECS cluster instance by ARN. This will only ever return one instance result.

    :param connection: AWS boto3 ecs connection
    :param module: Ansible module
    :param cluster_name: ECS cluster name
    :param instance_arn: ECS instance ARN
    :return: the first (and should be only) result - a dict containing ECS cluster instance detail
    """

    try:
        return connection.describe_container_instances(cluster=cluster_name, containerInstances=[instance_arn])['containerInstances'][0]
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


def _check_instance_status(connection, module, cluster, container_instance, current_instances, status):
    """
    For each existing instance check to see if it matches the container_instance arn/id. If it does, check the state.
    :param connection: AWS boto3 ecs connection
    :param module: Ansible module
    :param cluster: ECS cluster name
    :param container_instance: ARN or ID of ECS container instance
    :param current_instances: list of dicts containing current ECS container instances in the cluster
    :param status: the instance status that the user has passed
    :return: True if instance is found in existing instances and state is same as user has passed, else False
    """

    instance_status_correct = False

    for current_instance in current_instances:
        current_instance_detail = _describe_ecs_cluster_instance(connection, module, cluster, current_instance)
        if container_instance.startswith("arn:aws:ecs"):
            if current_instance_detail['containerInstanceArn'] == container_instance and current_instance_detail['status'] == status.upper():
                instance_status_correct = True
                break
        elif _get_container_id_from_arn(current_instance_detail['containerInstanceArn']) == container_instance \
                and current_instance_detail['status'] == status.upper():
            instance_status_correct = True
            break

    return instance_status_correct


def main():

    argument_spec = (
        dict(
            cluster=dict(type='str'),
            container_instances=dict(type='list', required=True),
            status=dict(type='str', required=True, choices=['ACTIVE', 'DRAINING'])
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    connection = module.client('ecs')

    cluster = module.params.get('cluster')
    container_instances = module.params.get('container_instances')
    status = module.params.get('status')
    update_status = False
    changed = False

    # Get current instances of cluster
    current_instances = _list_ecs_cluster_instances(connection, module, cluster)

    # For each instance check if its status needs updating. As soon as we find one that does then break and complete action
    for container_instance in container_instances:
        if not _check_instance_status(connection, module, cluster, container_instance, current_instances, status):
            update_status = True
            break

    if update_status:
        if cluster is None:
            try:
                result = connection.update_container_instances_state(containerInstances=container_instances, status=status)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e)
            changed = True
        else:
            try:
                result = connection.update_container_instances_state(cluster=cluster, containerInstances=container_instances, status=status)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e)
            changed = True

    if changed:
        module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))
    else:
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
