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
module: ecs_task
short_description: run, start or stop a task in ecs
description:
    - Creates or deletes instances of task definitions.
version_added: "2.0"
author: Mark Chance (@Java1Guy)
requirements: [ json, botocore, boto3 ]
options:
    operation:
        description:
            - Which task operation to execute
        required: True
        choices: ['run', 'start', 'stop']
    cluster:
        description:
            - The name of the cluster to run the task on
        required: False
    task_definition:
        description:
            - The task definition to start or run
        required: False
    overrides:
        description:
            - A dictionary of values to pass to the new instances
        required: False
    count:
        description:
            - How many new instances to start
        required: False
    task:
        description:
            - The task to stop
        required: False
    container_instances:
        description:
            - The list of container instances on which to deploy the task
        required: False
    started_by:
        description:
            - A value showing who or what started the task (for informational purposes)
        required: False
    network_configuration:
        description:
          - network configuration of the service. Only applicable for task definitions created with C(awsvpc) I(network_mode).
          - I(network_configuration) has two keys, I(subnets), a list of subnet IDs to which the task is attached and I(security_groups),
            a list of group names or group IDs for the task
        version_added: 2.6
    launch_type:
        description:
          - The launch type on which to run your service
        required: false
        version_added: 2.8
        choices: ["EC2", "FARGATE"]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Simple example of run task
- name: Run task
  ecs_task:
    operation: run
    cluster: console-sample-app-static-cluster
    task_definition: console-sample-app-static-taskdef
    count: 1
    started_by: ansible_user
  register: task_output

# Simple example of start task

- name: Start a task
  ecs_task:
      operation: start
      cluster: console-sample-app-static-cluster
      task_definition: console-sample-app-static-taskdef
      task: "arn:aws:ecs:us-west-2:172139249013:task/3f8353d1-29a8-4689-bbf6-ad79937ffe8a"
      container_instances:
      - arn:aws:ecs:us-west-2:172139249013:container-instance/79c23f22-876c-438a-bddf-55c98a3538a8
      started_by: ansible_user
      network_configuration:
        subnets:
        - subnet-abcd1234
        security_groups:
        - sg-aaaa1111
        - my_security_group
  register: task_output

- name: RUN a task on Fargate
  ecs_task:
      operation: run
      cluster: console-sample-app-static-cluster
      task_definition: console-sample-app-static-taskdef
      task: "arn:aws:ecs:us-west-2:172139249013:task/3f8353d1-29a8-4689-bbf6-ad79937ffe8a"
      started_by: ansible_user
      launch_type: FARGATE
      network_configuration:
        subnets:
        - subnet-abcd1234
        security_groups:
        - sg-aaaa1111
        - my_security_group
  register: task_output

- name: Stop a task
  ecs_task:
      operation: stop
      cluster: console-sample-app-static-cluster
      task_definition: console-sample-app-static-taskdef
      task: "arn:aws:ecs:us-west-2:172139249013:task/3f8353d1-29a8-4689-bbf6-ad79937ffe8a"
'''
RETURN = '''
task:
    description: details about the task that was started
    returned: success
    type: complex
    contains:
        taskArn:
            description: The Amazon Resource Name (ARN) that identifies the task.
            returned: always
            type: str
        clusterArn:
            description: The Amazon Resource Name (ARN) of the of the cluster that hosts the task.
            returned: only when details is true
            type: str
        taskDefinitionArn:
            description: The Amazon Resource Name (ARN) of the task definition.
            returned: only when details is true
            type: str
        containerInstanceArn:
            description: The Amazon Resource Name (ARN) of the container running the task.
            returned: only when details is true
            type: str
        overrides:
            description: The container overrides set for this task.
            returned: only when details is true
            type: list of complex
        lastStatus:
            description: The last recorded status of the task.
            returned: only when details is true
            type: str
        desiredStatus:
            description: The desired status of the task.
            returned: only when details is true
            type: str
        containers:
            description: The container details.
            returned: only when details is true
            type: list of complex
        startedBy:
            description: The used who started the task.
            returned: only when details is true
            type: str
        stoppedReason:
            description: The reason why the task was stopped.
            returned: only when details is true
            type: str
        createdAt:
            description: The timestamp of when the task was created.
            returned: only when details is true
            type: str
        startedAt:
            description: The timestamp of when the task was started.
            returned: only when details is true
            type: str
        stoppedAt:
            description: The timestamp of when the task was stopped.
            returned: only when details is true
            type: str
        launchType:
            description: The launch type on which to run your task.
            returned: always
            type: str
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_ec2_security_group_ids_from_names

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule


class EcsExecManager:
    """Handles ECS Tasks"""

    def __init__(self, module):
        self.module = module
        self.ecs = module.client('ecs')
        self.ec2 = module.client('ec2')

    def format_network_configuration(self, network_config):
        result = dict()
        if 'subnets' in network_config:
            result['subnets'] = network_config['subnets']
        else:
            self.module.fail_json(msg="Network configuration must include subnets")
        if 'security_groups' in network_config:
            groups = network_config['security_groups']
            if any(not sg.startswith('sg-') for sg in groups):
                try:
                    vpc_id = self.ec2.describe_subnets(SubnetIds=[result['subnets'][0]])['Subnets'][0]['VpcId']
                    groups = get_ec2_security_group_ids_from_names(groups, self.ec2, vpc_id)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Couldn't look up security groups")
            result['securityGroups'] = groups
        return dict(awsvpcConfiguration=result)

    def list_tasks(self, cluster_name, service_name, status):
        response = self.ecs.list_tasks(
            cluster=cluster_name,
            family=service_name,
            desiredStatus=status
        )
        if len(response['taskArns']) > 0:
            for c in response['taskArns']:
                if c.endswith(service_name):
                    return c
        return None

    def run_task(self, cluster, task_definition, overrides, count, startedBy, launch_type):
        if overrides is None:
            overrides = dict()
        params = dict(cluster=cluster, taskDefinition=task_definition,
                      overrides=overrides, count=count, startedBy=startedBy)
        if self.module.params['network_configuration']:
            params['networkConfiguration'] = self.format_network_configuration(self.module.params['network_configuration'])
        if launch_type:
            params['launchType'] = launch_type
        try:
            response = self.ecs.run_task(**params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't run task")
        # include tasks and failures
        return response['tasks']

    def start_task(self, cluster, task_definition, overrides, container_instances, startedBy):
        args = dict()
        if cluster:
            args['cluster'] = cluster
        if task_definition:
            args['taskDefinition'] = task_definition
        if overrides:
            args['overrides'] = overrides
        if container_instances:
            args['containerInstances'] = container_instances
        if startedBy:
            args['startedBy'] = startedBy
        if self.module.params['network_configuration']:
            args['networkConfiguration'] = self.format_network_configuration(self.module.params['network_configuration'])
        try:
            response = self.ecs.start_task(**args)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't start task")
        # include tasks and failures
        return response['tasks']

    def stop_task(self, cluster, task):
        response = self.ecs.stop_task(cluster=cluster, task=task)
        return response['task']

    def ecs_api_handles_launch_type(self):
        from distutils.version import LooseVersion
        # There doesn't seem to be a nice way to inspect botocore to look
        # for attributes (and networkConfiguration is not an explicit argument
        # to e.g. ecs.run_task, it's just passed as a keyword argument)
        return LooseVersion(botocore.__version__) >= LooseVersion('1.8.4')

    def ecs_api_handles_network_configuration(self):
        from distutils.version import LooseVersion
        # There doesn't seem to be a nice way to inspect botocore to look
        # for attributes (and networkConfiguration is not an explicit argument
        # to e.g. ecs.run_task, it's just passed as a keyword argument)
        return LooseVersion(botocore.__version__) >= LooseVersion('1.7.44')


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        operation=dict(required=True, choices=['run', 'start', 'stop']),
        cluster=dict(required=False, type='str'),  # R S P
        task_definition=dict(required=False, type='str'),  # R* S*
        overrides=dict(required=False, type='dict'),  # R S
        count=dict(required=False, type='int'),  # R
        task=dict(required=False, type='str'),  # P*
        container_instances=dict(required=False, type='list'),  # S*
        started_by=dict(required=False, type='str'),  # R S
        network_configuration=dict(required=False, type='dict'),
        launch_type=dict(required=False, choices=['EC2', 'FARGATE'])
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True,
                              required_if=[('launch_type', 'FARGATE', ['network_configuration'])])

    # Validate Inputs
    if module.params['operation'] == 'run':
        if 'task_definition' not in module.params and module.params['task_definition'] is None:
            module.fail_json(msg="To run a task, a task_definition must be specified")
        task_to_list = module.params['task_definition']
        status_type = "RUNNING"

    if module.params['operation'] == 'start':
        if 'task_definition' not in module.params and module.params['task_definition'] is None:
            module.fail_json(msg="To start a task, a task_definition must be specified")
        if 'container_instances' not in module.params and module.params['container_instances'] is None:
            module.fail_json(msg="To start a task, container instances must be specified")
        task_to_list = module.params['task']
        status_type = "RUNNING"

    if module.params['operation'] == 'stop':
        if 'task' not in module.params and module.params['task'] is None:
            module.fail_json(msg="To stop a task, a task must be specified")
        if 'task_definition' not in module.params and module.params['task_definition'] is None:
            module.fail_json(msg="To stop a task, a task definition must be specified")
        task_to_list = module.params['task_definition']
        status_type = "STOPPED"

    service_mgr = EcsExecManager(module)

    if module.params['network_configuration'] and not service_mgr.ecs_api_handles_network_configuration():
        module.fail_json(msg='botocore needs to be version 1.7.44 or higher to use network configuration')

    if module.params['launch_type'] and not service_mgr.ecs_api_handles_launch_type():
        module.fail_json(msg='botocore needs to be version 1.8.4 or higher to use launch type')

    existing = service_mgr.list_tasks(module.params['cluster'], task_to_list, status_type)

    results = dict(changed=False)
    if module.params['operation'] == 'run':
        if existing:
            # TBD - validate the rest of the details
            results['task'] = existing
        else:
            if not module.check_mode:
                results['task'] = service_mgr.run_task(
                    module.params['cluster'],
                    module.params['task_definition'],
                    module.params['overrides'],
                    module.params['count'],
                    module.params['started_by'],
                    module.params['launch_type'])
            results['changed'] = True

    elif module.params['operation'] == 'start':
        if existing:
            # TBD - validate the rest of the details
            results['task'] = existing
        else:
            if not module.check_mode:
                results['task'] = service_mgr.start_task(
                    module.params['cluster'],
                    module.params['task_definition'],
                    module.params['overrides'],
                    module.params['container_instances'],
                    module.params['started_by']
                )
            results['changed'] = True

    elif module.params['operation'] == 'stop':
        if existing:
            results['task'] = existing
        else:
            if not module.check_mode:
                # it exists, so we should delete it and mark changed.
                # return info about the cluster deleted
                results['task'] = service_mgr.stop_task(
                    module.params['cluster'],
                    module.params['task']
                )
            results['changed'] = True

    module.exit_json(**results)


if __name__ == '__main__':
    main()
