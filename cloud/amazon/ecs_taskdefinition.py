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
module: ecs_taskdefinition
short_description: register a task definition in ecs
description:
    - Creates or terminates task definitions
version_added: "2.0"
requirements: [ json, boto, botocore, boto3 ]
options:
    state:
        description:
            - State whether the task definition should exist or be deleted
        required: true
        choices=['present', 'absent']

    arn:
        description:
            - The arn of the task description to delete
        required: false

    family:
        =dict(required=False, type='str' ),

    revision:
        required: False
        type: int

    containers:
        required: False
        type: list of dicts with container definitions

    volumes:
        required: False
        type: list of name
'''

EXAMPLES = '''
- name: "Create task definition"
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
    - name: busybox
      command:
        - "/bin/sh -c \"while true; do echo '<html> <head> <title>Amazon ECS Sample App</title> <style>body {margin-top: 40px; background-color: #333;} </style> </head><body> <div style=color:white;text-align:center> <h1>Amazon ECS Sample App</h1> <h2>Congratulations!</h2> <p>Your application is now running on a container in Amazon ECS.</p>' > top; /bin/date > date ; echo '</div></body></html>' > bottom; cat top date bottom > /usr/local/apache2/htdocs/index.html ; sleep 1; done\""
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
'''
RETURN = '''
taskdefinition:
    description: a reflection of the input parameters
    type: dict inputs plus revision, status, taskDefinitionArn
'''
try:
    import json
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

    def describe_task(self, task_name):
        try:
            response = self.ecs.describe_task_definition(taskDefinition=task_name)
            return response['taskDefinition']
        except botocore.exceptions.ClientError:
            return None

    def register_task(self, family, container_definitions, volumes):
        response = self.ecs.register_task_definition(family=family,
            containerDefinitions=container_definitions, volumes=volumes)
        return response['taskDefinition']

    def deregister_task(self, taskArn):
        response = self.ecs.deregister_task_definition(taskDefinition=taskArn)
        return response['taskDefinition']

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent'] ),
        arn=dict(required=False, type='str' ),
        family=dict(required=False, type='str' ),
        revision=dict(required=False, type='int' ),
        containers=dict(required=False, type='list' ),
        volumes=dict(required=False, type='list' )
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    task_to_describe = None
    # When deregistering a task, we can specify the ARN OR
    # the family and revision.
    if module.params['state'] == 'absent':
        if 'arn' in module.params and module.params['arn'] is not None:
            task_to_describe = module.params['arn']
        elif 'family' in module.params and module.params['family'] is not None and 'revision' in module.params and module.params['revision'] is not None:
            task_to_describe = module.params['family']+":"+str(module.params['revision'])
        else:
            module.fail_json(msg="To use task definitions, an arn or family and revision must be specified")
    # When registering a task, we can specify the ARN OR
    # the family and revision.
    if module.params['state'] == 'present':
        if not 'family' in module.params:
            module.fail_json(msg="To use task definitions, a family must be specified")
        if not 'containers' in module.params:
            module.fail_json(msg="To use task definitions, a list of containers must be specified")
        task_to_describe = module.params['family']

    task_mgr = EcsTaskManager(module)
    existing = task_mgr.describe_task(task_to_describe)

    results = dict(changed=False)
    if module.params['state'] == 'present':
        if existing and 'status' in existing and existing['status']=="ACTIVE":
            results['taskdefinition']=existing
        else:
            if not module.check_mode:
                # doesn't exist. create it.
                volumes = []
                if 'volumes' in module.params:
                    volumes = module.params['volumes']
                if volumes is None:
                    volumes = []
                results['taskdefinition'] = task_mgr.register_task(module.params['family'],
                    module.params['containers'], volumes)
            results['changed'] = True

    # delete the cloudtrai
    elif module.params['state'] == 'absent':
        if not existing:
            pass
        else:
            # it exists, so we should delete it and mark changed.
            # return info about the cluster deleted
            results['taskdefinition'] = existing
            if 'status' in existing and existing['status']=="INACTIVE":
                results['changed'] = False
            else:
                if not module.check_mode:
                    task_mgr.deregister_task(task_to_describe)
                results['changed'] = True

    module.exit_json(**results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
