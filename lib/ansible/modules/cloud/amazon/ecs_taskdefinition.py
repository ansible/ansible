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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ecs_taskdefinition
short_description: register a task definition in ecs
description:
    - Registers or deregisters task definitions in the Amazon Web Services (AWS) EC2 Container Service (ECS)
version_added: "2.0"
author: Mark Chance (@Java1Guy)
requirements: [ json, botocore, boto3 ]
options:
    state:
        description:
            - State whether the task definition should exist or be deleted
        required: true
        choices: ['present', 'absent']
    arn:
        description:
            - The arn of the task description to delete
        required: false
    family:
        description:
            - A Name that would be given to the task definition
        required: false
    revision:
        description:
            - A revision number for the task definition
        required: False
    force_create:
        description:
            - Always create new task definition
        required: False
        version_added: 2.5
        type: bool
    containers:
        description:
            - A list of containers definitions
        required: False
    network_mode:
        description:
            - The Docker networking mode to use for the containers in the task.
            - C(awsvpc) mode was added in Ansible 2.5
        required: false
        default: bridge
        choices: [ 'bridge', 'host', 'none', 'awsvpc' ]
        version_added: 2.3
    task_role_arn:
        description:
            - The Amazon Resource Name (ARN) of the IAM role that containers in this task can assume. All containers in this task are granted
              the permissions that are specified in this role.
        required: false
        version_added: 2.3
    execution_role_arn:
        description:
            - The Amazon Resource Name (ARN) of the task execution role that the Amazon ECS container agent and the Docker daemon can assume.
        required: false
        version_added: 2.7
    volumes:
        description:
            - A list of names of volumes to be attached
        required: False
    launch_type:
        description:
            - The launch type on which to run your task
        required: false
        version_added: 2.7
        choices: ["EC2", "FARGATE"]
    cpu:
        description:
            - The number of cpu units used by the task. If using the EC2 launch type, this field is optional and any value can be used.
              If using the Fargate launch type, this field is required and you must use one of [256, 512, 1024, 2048, 4096]
        required: false
        version_added: 2.7
    memory:
        description:
            - The amount (in MiB) of memory used by the task. If using the EC2 launch type, this field is optional and any value can be used.
              If using the Fargate launch type, this field is required and is limited by the cpu
        required: false
        version_added: 2.7
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: Create task definition
  ecs_taskdefinition:
    containers:
    - name: simple-app
      cpu: 10
      essential: true
      image: "httpd:2.4"
      memory: 300
      mountPoints:
      - containerPath: /usr/local/apache2/htdocs
        sourceVolume: my-vol
      portMappings:
      - containerPort: 80
        hostPort: 80
      logConfiguration:
        logDriver: awslogs
        options:
          awslogs-group: /ecs/test-cluster-taskdef
          awslogs-region: us-west-2
          awslogs-stream-prefix: ecs
    - name: busybox
      command:
        - >
          /bin/sh -c "while true; do echo '<html><head><title>Amazon ECS Sample App</title></head><body><div><h1>Amazon ECS Sample App</h1><h2>Congratulations!
          </h2><p>Your application is now running on a container in Amazon ECS.</p>' > top; /bin/date > date ; echo '</div></body></html>' > bottom;
          cat top date bottom > /usr/local/apache2/htdocs/index.html ; sleep 1; done"
      cpu: 10
      entryPoint:
      - sh
      - "-c"
      essential: false
      image: busybox
      memory: 200
      volumesFrom:
      - sourceContainer: simple-app
    volumes:
    - name: my-vol
    family: test-cluster-taskdef
    state: present
  register: task_output

- name: Create task definition
  ecs_taskdefinition:
    family: nginx
    containers:
    - name: nginx
      essential: true
      image: "nginx"
      portMappings:
      - containerPort: 8080
        hostPort:      8080
      cpu: 512
      memory: 1024
    state: present

- name: Create task definition
  ecs_taskdefinition:
    family: nginx
    containers:
    - name: nginx
      essential: true
      image: "nginx"
      portMappings:
      - containerPort: 8080
        hostPort:      8080
    launch_type: FARGATE
    cpu: 512
    memory: 1024
    state: present
    network_mode: awsvpc
'''
RETURN = '''
taskdefinition:
    description: a reflection of the input parameters
    type: dict
    returned: always
'''

try:
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, camel_dict_to_snake_dict, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils._text import to_text


class EcsTaskManager:
    """Handles ECS Tasks"""

    def __init__(self, module):
        self.module = module

        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        self.ecs = boto3_conn(module, conn_type='client', resource='ecs', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    def describe_task(self, task_name):
        try:
            response = self.ecs.describe_task_definition(taskDefinition=task_name)
            return response['taskDefinition']
        except botocore.exceptions.ClientError:
            return None

    def register_task(self, family, task_role_arn, execution_role_arn, network_mode, container_definitions, volumes, launch_type, cpu, memory):
        validated_containers = []

        # Ensures the number parameters are int as required by boto
        for container in container_definitions:
            for param in ('memory', 'cpu', 'memoryReservation'):
                if param in container:
                    container[param] = int(container[param])

            if 'portMappings' in container:
                for port_mapping in container['portMappings']:
                    for port in ('hostPort', 'containerPort'):
                        if port in port_mapping:
                            port_mapping[port] = int(port_mapping[port])
                    if network_mode == 'awsvpc' and 'hostPort' in port_mapping:
                        if port_mapping['hostPort'] != port_mapping.get('containerPort'):
                            self.module.fail_json(msg="In awsvpc network mode, host port must be set to the same as "
                                                  "container port or not be set")

            validated_containers.append(container)

        params = dict(
            family=family,
            taskRoleArn=task_role_arn,
            networkMode=network_mode,
            containerDefinitions=container_definitions,
            volumes=volumes
        )
        if cpu:
            params['cpu'] = cpu
        if memory:
            params['memory'] = memory
        if launch_type:
            params['requiresCompatibilities'] = [launch_type]
        if execution_role_arn:
            params['executionRoleArn'] = execution_role_arn

        try:
            response = self.ecs.register_task_definition(**params)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

        return response['taskDefinition']

    def describe_task_definitions(self, family):
        data = {
            "taskDefinitionArns": [],
            "nextToken": None
        }

        def fetch():
            # Boto3 is weird about params passed, so only pass nextToken if we have a value
            params = {
                'familyPrefix': family
            }

            if data['nextToken']:
                params['nextToken'] = data['nextToken']

            result = self.ecs.list_task_definitions(**params)
            data['taskDefinitionArns'] += result['taskDefinitionArns']
            data['nextToken'] = result.get('nextToken', None)
            return data['nextToken'] is not None

        # Fetch all the arns, possibly across multiple pages
        while fetch():
            pass

        # Return the full descriptions of the task definitions, sorted ascending by revision
        return list(
            sorted(
                [self.ecs.describe_task_definition(taskDefinition=arn)['taskDefinition'] for arn in data['taskDefinitionArns']],
                key=lambda td: td['revision']
            )
        )

    def deregister_task(self, taskArn):
        response = self.ecs.deregister_task_definition(taskDefinition=taskArn)
        return response['taskDefinition']


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        arn=dict(required=False, type='str'),
        family=dict(required=False, type='str'),
        revision=dict(required=False, type='int'),
        force_create=dict(required=False, default=False, type='bool'),
        containers=dict(required=False, type='list'),
        network_mode=dict(required=False, default='bridge', choices=['bridge', 'host', 'none', 'awsvpc'], type='str'),
        task_role_arn=dict(required=False, default='', type='str'),
        execution_role_arn=dict(required=False, default='', type='str'),
        volumes=dict(required=False, type='list'),
        launch_type=dict(required=False, choices=['EC2', 'FARGATE']),
        cpu=dict(),
        memory=dict(required=False, type='str')
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              required_if=[('launch_type', 'FARGATE', ['cpu', 'memory'])]
                              )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    task_to_describe = None
    task_mgr = EcsTaskManager(module)
    results = dict(changed=False)

    if module.params['launch_type']:
        if not module.botocore_at_least('1.8.4'):
            module.fail_json(msg='botocore needs to be version 1.8.4 or higher to use launch_type')

    if module.params['execution_role_arn']:
        if not module.botocore_at_least('1.10.44'):
            module.fail_json(msg='botocore needs to be version 1.10.44 or higher to use execution_role_arn')

    if module.params['containers']:
        for container in module.params['containers']:
            for environment in container.get('environment', []):
                environment['value'] = to_text(environment['value'])

    if module.params['state'] == 'present':
        if 'containers' not in module.params or not module.params['containers']:
            module.fail_json(msg="To use task definitions, a list of containers must be specified")

        if 'family' not in module.params or not module.params['family']:
            module.fail_json(msg="To use task definitions, a family must be specified")

        network_mode = module.params['network_mode']
        launch_type = module.params['launch_type']
        if launch_type == 'FARGATE' and network_mode != 'awsvpc':
            module.fail_json(msg="To use FARGATE launch type, network_mode must be awsvpc")

        family = module.params['family']
        existing_definitions_in_family = task_mgr.describe_task_definitions(module.params['family'])

        if 'revision' in module.params and module.params['revision']:
            # The definition specifies revision. We must gurantee that an active revision of that number will result from this.
            revision = int(module.params['revision'])

            # A revision has been explicitly specified. Attempt to locate a matching revision
            tasks_defs_for_revision = [td for td in existing_definitions_in_family if td['revision'] == revision]
            existing = tasks_defs_for_revision[0] if len(tasks_defs_for_revision) > 0 else None

            if existing and existing['status'] != "ACTIVE":
                # We cannot reactivate an inactive revision
                module.fail_json(msg="A task in family '%s' already exists for revsion %d, but it is inactive" % (family, revision))
            elif not existing:
                if not existing_definitions_in_family and revision != 1:
                    module.fail_json(msg="You have specified a revision of %d but a created revision would be 1" % revision)
                elif existing_definitions_in_family and existing_definitions_in_family[-1]['revision'] + 1 != revision:
                    module.fail_json(msg="You have specified a revision of %d but a created revision would be %d" %
                                         (revision, existing_definitions_in_family[-1]['revision'] + 1))
        else:
            existing = None

            def _right_has_values_of_left(left, right):
                # Make sure the values are equivalent for everything left has
                for k, v in left.items():
                    if not ((not v and (k not in right or not right[k])) or (k in right and v == right[k])):
                        # We don't care about list ordering because ECS can change things
                        if isinstance(v, list) and k in right:
                            left_list = v
                            right_list = right[k] or []

                            if len(left_list) != len(right_list):
                                return False

                            for list_val in left_list:
                                if list_val not in right_list:
                                    return False
                        else:
                            return False

                # Make sure right doesn't have anything that left doesn't
                for k, v in right.items():
                    if v and k not in left:
                        return False

                return True

            def _task_definition_matches(requested_volumes, requested_containers, requested_task_role_arn, existing_task_definition):
                if td['status'] != "ACTIVE":
                    return None

                if requested_task_role_arn != td.get('taskRoleArn', ""):
                    return None

                existing_volumes = td.get('volumes', []) or []

                if len(requested_volumes) != len(existing_volumes):
                    # Nope.
                    return None

                if len(requested_volumes) > 0:
                    for requested_vol in requested_volumes:
                        found = False

                        for actual_vol in existing_volumes:
                            if _right_has_values_of_left(requested_vol, actual_vol):
                                found = True
                                break

                        if not found:
                            return None

                existing_containers = td.get('containerDefinitions', []) or []

                if len(requested_containers) != len(existing_containers):
                    # Nope.
                    return None

                for requested_container in requested_containers:
                    found = False

                    for actual_container in existing_containers:
                        if _right_has_values_of_left(requested_container, actual_container):
                            found = True
                            break

                    if not found:
                        return None

                return existing_task_definition

            # No revision explicitly specified. Attempt to find an active, matching revision that has all the properties requested
            for td in existing_definitions_in_family:
                requested_volumes = module.params['volumes'] or []
                requested_containers = module.params['containers'] or []
                requested_task_role_arn = module.params['task_role_arn']
                existing = _task_definition_matches(requested_volumes, requested_containers, requested_task_role_arn, td)

                if existing:
                    break

        if existing and not module.params.get('force_create'):
            # Awesome. Have an existing one. Nothing to do.
            results['taskdefinition'] = existing
        else:
            if not module.check_mode:
                # Doesn't exist. create it.
                volumes = module.params.get('volumes', []) or []
                results['taskdefinition'] = task_mgr.register_task(module.params['family'],
                                                                   module.params['task_role_arn'],
                                                                   module.params['execution_role_arn'],
                                                                   module.params['network_mode'],
                                                                   module.params['containers'],
                                                                   volumes,
                                                                   module.params['launch_type'],
                                                                   module.params['cpu'],
                                                                   module.params['memory'])
            results['changed'] = True

    elif module.params['state'] == 'absent':
        # When de-registering a task definition, we can specify the ARN OR the family and revision.
        if module.params['state'] == 'absent':
            if 'arn' in module.params and module.params['arn'] is not None:
                task_to_describe = module.params['arn']
            elif 'family' in module.params and module.params['family'] is not None and 'revision' in module.params and \
                    module.params['revision'] is not None:
                task_to_describe = module.params['family'] + ":" + str(module.params['revision'])
            else:
                module.fail_json(msg="To use task definitions, an arn or family and revision must be specified")

        existing = task_mgr.describe_task(task_to_describe)

        if not existing:
            pass
        else:
            # It exists, so we should delete it and mark changed. Return info about the task definition deleted
            results['taskdefinition'] = existing
            if 'status' in existing and existing['status'] == "INACTIVE":
                results['changed'] = False
            else:
                if not module.check_mode:
                    task_mgr.deregister_task(task_to_describe)
                results['changed'] = True

    module.exit_json(**results)


if __name__ == '__main__':
    main()
