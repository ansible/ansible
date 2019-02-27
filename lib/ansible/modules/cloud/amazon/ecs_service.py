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
module: ecs_service
short_description: create, terminate, start or stop a service in ecs
description:
  - Creates or terminates ecs services.
notes:
  - the service role specified must be assumable (i.e. have a trust relationship for the ecs service, ecs.amazonaws.com)
  - for details of the parameters and returns see U(https://boto3.readthedocs.io/en/latest/reference/services/ecs.html)
  - An IAM role must have been previously created
version_added: "2.1"
author:
    - "Mark Chance (@Java1Guy)"
    - "Darek Kaczynski (@kaczynskid)"
    - "Stephane Maarek (@simplesteph)"
    - "Zac Blazic (@zacblazic)"

requirements: [ json, botocore, boto3 ]
options:
    state:
        description:
          - The desired state of the service
        required: true
        choices: ["present", "absent", "deleting"]
    name:
        description:
          - The name of the service
        required: true
    cluster:
        description:
          - The name of the cluster in which the service exists
        required: false
    task_definition:
        description:
          - The task definition the service will run. This parameter is required when state=present
        required: false
    load_balancers:
        description:
          - The list of ELBs defined for this service
        required: false
    desired_count:
        description:
          - The count of how many instances of the service. This parameter is required when state=present
        required: false
    client_token:
        description:
          - Unique, case-sensitive identifier you provide to ensure the idempotency of the request. Up to 32 ASCII characters are allowed.
        required: false
    role:
        description:
          - The name or full Amazon Resource Name (ARN) of the IAM role that allows your Amazon ECS container agent to make calls to your load balancer
            on your behalf. This parameter is only required if you are using a load balancer with your service, in a network mode other than `awsvpc`.
        required: false
    delay:
        description:
          - The time to wait before checking that the service is available
        required: false
        default: 10
    repeat:
        description:
          - The number of times to check that the service is available
        required: false
        default: 10
    force_new_deployment:
        description:
          - Force deployment of service even if there are no changes
        required: false
        version_added: 2.8
        type: bool
    deployment_configuration:
        description:
          - Optional parameters that control the deployment_configuration; format is '{"maximum_percent":<integer>, "minimum_healthy_percent":<integer>}
        required: false
        version_added: 2.3
    placement_constraints:
        description:
          - The placement constraints for the tasks in the service
        required: false
        version_added: 2.4
    placement_strategy:
        description:
          - The placement strategy objects to use for tasks in your service. You can specify a maximum of 5 strategy rules per service
        required: false
        version_added: 2.4
    network_configuration:
        description:
          - network configuration of the service. Only applicable for task definitions created with C(awsvpc) I(network_mode).
          - assign_public_ip requires botocore >= 1.8.4
        suboptions:
          subnets:
            description:
              - A list of subnet IDs to associate with the task
            version_added: 2.6
          security_groups:
            description:
              - A list of security group names or group IDs to associate with the task
            version_added: 2.6
          assign_public_ip:
            description:
              - Whether the task's elastic network interface receives a public IP address. This option requires botocore >= 1.8.4.
            type: bool
            version_added: 2.7
    launch_type:
        description:
          - The launch type on which to run your service
        required: false
        version_added: 2.7
        choices: ["EC2", "FARGATE"]
    health_check_grace_period_seconds:
        description:
          - Seconds to wait before health checking the freshly added/updated services. This option requires botocore >= 1.8.20.
        required: false
        version_added: 2.8
    service_registries:
        description:
          - describes service disovery registries this service will register with.
        required: false
        version_added: 2.8
        suboptions:
            container_name:
                description:
                  - container name for service disovery registration
            container_port:
                description:
                  - container port for service disovery registration
            arn:
                description:
                  - Service discovery registry ARN
    scheduling_strategy:
        description:
          - The scheduling strategy, defaults to "REPLICA" if not given to preserve previous behavior
        required: false
        version_added: 2.8
        choices: ["DAEMON", "REPLICA"]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- ecs_service:
    state: present
    name: console-test-service
    cluster: new_cluster
    task_definition: 'new_cluster-task:1'
    desired_count: 0

# Basic provisioning example
- ecs_service:
    name: default
    state: present
    cluster: new_cluster

- name: create ECS service on VPC network
  ecs_service:
    state: present
    name: console-test-service
    cluster: new_cluster
    task_definition: 'new_cluster-task:1'
    desired_count: 0
    network_configuration:
      subnets:
      - subnet-abcd1234
      security_groups:
      - sg-aaaa1111
      - my_security_group

# Simple example to delete
- ecs_service:
    name: default
    state: absent
    cluster: new_cluster

# With custom deployment configuration (added in version 2.3), placement constraints and strategy (added in version 2.4)
- ecs_service:
    state: present
    name: test-service
    cluster: test-cluster
    task_definition: test-task-definition
    desired_count: 3
    deployment_configuration:
      minimum_healthy_percent: 75
      maximum_percent: 150
    placement_constraints:
      - type: memberOf
        expression: 'attribute:flavor==test'
    placement_strategy:
      - type: binpack
        field: memory
'''

RETURN = '''
service:
    description: Details of created service.
    returned: when creating a service
    type: complex
    contains:
        clusterArn:
            description: The Amazon Resource Name (ARN) of the of the cluster that hosts the service.
            returned: always
            type: str
        desiredCount:
            description: The desired number of instantiations of the task definition to keep running on the service.
            returned: always
            type: int
        loadBalancers:
            description: A list of load balancer objects
            returned: always
            type: complex
            contains:
                loadBalancerName:
                    description: the name
                    returned: always
                    type: str
                containerName:
                    description: The name of the container to associate with the load balancer.
                    returned: always
                    type: str
                containerPort:
                    description: The port on the container to associate with the load balancer.
                    returned: always
                    type: int
        pendingCount:
            description: The number of tasks in the cluster that are in the PENDING state.
            returned: always
            type: int
        runningCount:
            description: The number of tasks in the cluster that are in the RUNNING state.
            returned: always
            type: int
        serviceArn:
            description: The Amazon Resource Name (ARN) that identifies the service. The ARN contains the arn:aws:ecs namespace, followed by the region
                         of the service, the AWS account ID of the service owner, the service namespace, and then the service name. For example,
                         arn:aws:ecs:region :012345678910 :service/my-service .
            returned: always
            type: str
        serviceName:
            description: A user-generated string used to identify the service
            returned: always
            type: str
        status:
            description: The valid values are ACTIVE, DRAINING, or INACTIVE.
            returned: always
            type: str
        taskDefinition:
            description: The ARN of a task definition to use for tasks in the service.
            returned: always
            type: str
        deployments:
            description: list of service deployments
            returned: always
            type: list of complex
        deploymentConfiguration:
            description: dictionary of deploymentConfiguration
            returned: always
            type: complex
            contains:
                maximumPercent:
                    description: maximumPercent param
                    returned: always
                    type: int
                minimumHealthyPercent:
                    description: minimumHealthyPercent param
                    returned: always
                    type: int
        events:
            description: list of service events
            returned: always
            type: list of complex
        placementConstraints:
            description: List of placement constraints objects
            returned: always
            type: list of complex
            contains:
                type:
                    description: The type of constraint. Valid values are distinctInstance and memberOf.
                    returned: always
                    type: str
                expression:
                    description: A cluster query language expression to apply to the constraint. Note you cannot specify an expression if the constraint type is
                                 distinctInstance.
                    returned: always
                    type: str
        placementStrategy:
            description: List of placement strategy objects
            returned: always
            type: list of complex
            contains:
                type:
                    description: The type of placement strategy. Valid values are random, spread and binpack.
                    returned: always
                    type: str
                field:
                    description: The field to apply the placement strategy against. For the spread placement strategy, valid values are instanceId
                                 (or host, which has the same effect), or any platform or custom attribute that is applied to a container instance,
                                 such as attribute:ecs.availability-zone. For the binpack placement strategy, valid values are CPU and MEMORY.
                    returned: always
                    type: str
ansible_facts:
    description: Facts about deleted service.
    returned: when deleting a service
    type: complex
    contains:
        service:
            description: Details of deleted service in the same structure described above for service creation.
            returned: when service existed and was deleted
            type: complex
'''
import time

DEPLOYMENT_CONFIGURATION_TYPE_MAP = {
    'maximum_percent': 'int',
    'minimum_healthy_percent': 'int'
}

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import snake_dict_to_camel_dict, map_complex_type, get_ec2_security_group_ids_from_names

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule


class EcsServiceManager:
    """Handles ECS Services"""

    def __init__(self, module):
        self.module = module
        self.ecs = module.client('ecs')
        self.ec2 = module.client('ec2')

    def format_network_configuration(self, network_config):
        result = dict()
        if network_config['subnets'] is not None:
            result['subnets'] = network_config['subnets']
        else:
            self.module.fail_json(msg="Network configuration must include subnets")
        if network_config['security_groups'] is not None:
            groups = network_config['security_groups']
            if any(not sg.startswith('sg-') for sg in groups):
                try:
                    vpc_id = self.ec2.describe_subnets(SubnetIds=[result['subnets'][0]])['Subnets'][0]['VpcId']
                    groups = get_ec2_security_group_ids_from_names(groups, self.ec2, vpc_id)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Couldn't look up security groups")
            result['securityGroups'] = groups
        if network_config['assign_public_ip'] is not None:
            if self.module.botocore_at_least('1.8.4'):
                if network_config['assign_public_ip'] is True:
                    result['assignPublicIp'] = "ENABLED"
                else:
                    result['assignPublicIp'] = "DISABLED"
            else:
                self.module.fail_json(msg='botocore needs to be version 1.8.4 or higher to use assign_public_ip in network_configuration')
        return dict(awsvpcConfiguration=result)

    def find_in_array(self, array_of_services, service_name, field_name='serviceArn'):
        for c in array_of_services:
            if c[field_name].endswith(service_name):
                return c
        return None

    def describe_service(self, cluster_name, service_name):
        response = self.ecs.describe_services(
            cluster=cluster_name,
            services=[service_name])
        msg = ''
        if len(response['failures']) > 0:
            c = self.find_in_array(response['failures'], service_name, 'arn')
            msg += ", failure reason is " + c['reason']
            if c and c['reason'] == 'MISSING':
                return None
            # fall thru and look through found ones
        if len(response['services']) > 0:
            c = self.find_in_array(response['services'], service_name)
            if c:
                return c
        raise Exception("Unknown problem describing service %s." % service_name)

    def is_matching_service(self, expected, existing):
        if expected['task_definition'] != existing['taskDefinition']:
            return False

        if (expected['load_balancers'] or []) != existing['loadBalancers']:
            return False

        # expected is params. DAEMON scheduling strategy returns desired count equal to
        # number of instances running; don't check desired count if scheduling strat is daemon
        if (expected['scheduling_strategy'] != 'DAEMON'):
            if (expected['desired_count'] or 0) != existing['desiredCount']:
                return False

        return True

    def create_service(self, service_name, cluster_name, task_definition, load_balancers,
                       desired_count, client_token, role, deployment_configuration,
                       placement_constraints, placement_strategy, health_check_grace_period_seconds,
                       network_configuration, service_registries, launch_type, scheduling_strategy):

        params = dict(
            cluster=cluster_name,
            serviceName=service_name,
            taskDefinition=task_definition,
            loadBalancers=load_balancers,
            clientToken=client_token,
            role=role,
            deploymentConfiguration=deployment_configuration,
            placementConstraints=placement_constraints,
            placementStrategy=placement_strategy
        )
        if network_configuration:
            params['networkConfiguration'] = network_configuration
        if launch_type:
            params['launchType'] = launch_type
        if self.health_check_setable(params) and health_check_grace_period_seconds is not None:
            params['healthCheckGracePeriodSeconds'] = health_check_grace_period_seconds
        if service_registries:
            params['serviceRegistries'] = service_registries
        # desired count is not required if scheduling strategy is daemon
        if desired_count is not None:
            params['desiredCount'] = desired_count

        if scheduling_strategy:
            params['schedulingStrategy'] = scheduling_strategy
        response = self.ecs.create_service(**params)
        return self.jsonize(response['service'])

    def update_service(self, service_name, cluster_name, task_definition,
                       desired_count, deployment_configuration, network_configuration,
                       health_check_grace_period_seconds, force_new_deployment):
        params = dict(
            cluster=cluster_name,
            service=service_name,
            taskDefinition=task_definition,
            deploymentConfiguration=deployment_configuration)
        if network_configuration:
            params['networkConfiguration'] = network_configuration
        if force_new_deployment:
            params['forceNewDeployment'] = force_new_deployment
        if health_check_grace_period_seconds is not None:
            params['healthCheckGracePeriodSeconds'] = health_check_grace_period_seconds
        # desired count is not required if scheduling strategy is daemon
        if desired_count is not None:
            params['desiredCount'] = desired_count

        response = self.ecs.update_service(**params)
        return self.jsonize(response['service'])

    def jsonize(self, service):
        # some fields are datetime which is not JSON serializable
        # make them strings
        if 'createdAt' in service:
            service['createdAt'] = str(service['createdAt'])
        if 'deployments' in service:
            for d in service['deployments']:
                if 'createdAt' in d:
                    d['createdAt'] = str(d['createdAt'])
                if 'updatedAt' in d:
                    d['updatedAt'] = str(d['updatedAt'])
        if 'events' in service:
            for e in service['events']:
                if 'createdAt' in e:
                    e['createdAt'] = str(e['createdAt'])
        return service

    def delete_service(self, service, cluster=None):
        return self.ecs.delete_service(cluster=cluster, service=service)

    def ecs_api_handles_network_configuration(self):
        # There doesn't seem to be a nice way to inspect botocore to look
        # for attributes (and networkConfiguration is not an explicit argument
        # to e.g. ecs.run_task, it's just passed as a keyword argument)
        return self.module.botocore_at_least('1.7.44')

    def health_check_setable(self, params):
        load_balancers = params.get('loadBalancers', [])
        # check if botocore (and thus boto3) is new enough for using the healthCheckGracePeriodSeconds parameter
        return len(load_balancers) > 0 and self.module.botocore_at_least('1.8.20')


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent', 'deleting']),
        name=dict(required=True, type='str'),
        cluster=dict(required=False, type='str'),
        task_definition=dict(required=False, type='str'),
        load_balancers=dict(required=False, default=[], type='list'),
        desired_count=dict(required=False, type='int'),
        client_token=dict(required=False, default='', type='str'),
        role=dict(required=False, default='', type='str'),
        delay=dict(required=False, type='int', default=10),
        repeat=dict(required=False, type='int', default=10),
        force_new_deployment=dict(required=False, default=False, type='bool'),
        deployment_configuration=dict(required=False, default={}, type='dict'),
        placement_constraints=dict(required=False, default=[], type='list'),
        placement_strategy=dict(required=False, default=[], type='list'),
        health_check_grace_period_seconds=dict(required=False, type='int'),
        network_configuration=dict(required=False, type='dict', options=dict(
            subnets=dict(type='list'),
            security_groups=dict(type='list'),
            assign_public_ip=dict(type='bool')
        )),
        launch_type=dict(required=False, choices=['EC2', 'FARGATE']),
        service_registries=dict(required=False, type='list', default=[]),
        scheduling_strategy=dict(required=False, choices=['DAEMON', 'REPLICA'])
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              required_if=[('state', 'present', ['task_definition']),
                                           ('launch_type', 'FARGATE', ['network_configuration'])],
                              required_together=[['load_balancers', 'role']])

    if module.params['state'] == 'present' and module.params['scheduling_strategy'] == 'REPLICA':
        if module.params['desired_count'] is None:
            module.fail_json(msg='state is present, scheduling_strategy is REPLICA; missing desired_count')

    service_mgr = EcsServiceManager(module)
    if module.params['network_configuration']:
        if not service_mgr.ecs_api_handles_network_configuration():
            module.fail_json(msg='botocore needs to be version 1.7.44 or higher to use network configuration')
        network_configuration = service_mgr.format_network_configuration(module.params['network_configuration'])
    else:
        network_configuration = None

    deployment_configuration = map_complex_type(module.params['deployment_configuration'],
                                                DEPLOYMENT_CONFIGURATION_TYPE_MAP)

    deploymentConfiguration = snake_dict_to_camel_dict(deployment_configuration)
    serviceRegistries = list(map(snake_dict_to_camel_dict, module.params['service_registries']))

    try:
        existing = service_mgr.describe_service(module.params['cluster'], module.params['name'])
    except Exception as e:
        module.fail_json(msg="Exception describing service '" + module.params['name'] + "' in cluster '" + module.params['cluster'] + "': " + str(e))

    results = dict(changed=False)

    if module.params['launch_type']:
        if not module.botocore_at_least('1.8.4'):
            module.fail_json(msg='botocore needs to be version 1.8.4 or higher to use launch_type')
    if module.params['force_new_deployment']:
        if not module.botocore_at_least('1.8.4'):
            module.fail_json(msg='botocore needs to be version 1.8.4 or higher to use force_new_deployment')
    if module.params['health_check_grace_period_seconds']:
        if not module.botocore_at_least('1.8.20'):
            module.fail_json(msg='botocore needs to be version 1.8.20 or higher to use health_check_grace_period_seconds')

    if module.params['state'] == 'present':

        matching = False
        update = False

        if existing and 'status' in existing and existing['status'] == "ACTIVE":
            if module.params['force_new_deployment']:
                update = True
            elif service_mgr.is_matching_service(module.params, existing):
                matching = True
                results['service'] = existing
            else:
                update = True

        if not matching:
            if not module.check_mode:

                role = module.params['role']
                clientToken = module.params['client_token']

                loadBalancers = []
                for loadBalancer in module.params['load_balancers']:
                    if 'containerPort' in loadBalancer:
                        loadBalancer['containerPort'] = int(loadBalancer['containerPort'])
                    loadBalancers.append(loadBalancer)

                for loadBalancer in loadBalancers:
                    if 'containerPort' in loadBalancer:
                        loadBalancer['containerPort'] = int(loadBalancer['containerPort'])

                if update:
                    # check various parameters and boto versions and give a helpful erro in boto is not new enough for feature

                    if module.params['scheduling_strategy']:
                        if not module.botocore_at_least('1.10.37'):
                            module.fail_json(msg='botocore needs to be version 1.10.37 or higher to use scheduling_strategy')
                        elif (existing['schedulingStrategy']) != module.params['scheduling_strategy']:
                            module.fail_json(msg="It is not possible to update the scheduling strategy of an existing service")

                    if module.params['service_registries']:
                        if not module.botocore_at_least('1.9.15'):
                            module.fail_json(msg='botocore needs to be version 1.9.15 or higher to use service_registries')
                        elif (existing['serviceRegistries'] or []) != serviceRegistries:
                            module.fail_json(msg="It is not possible to update the service registries of an existing service")

                    if (existing['loadBalancers'] or []) != loadBalancers:
                        module.fail_json(msg="It is not possible to update the load balancers of an existing service")

                    # update required
                    response = service_mgr.update_service(module.params['name'],
                                                          module.params['cluster'],
                                                          module.params['task_definition'],
                                                          module.params['desired_count'],
                                                          deploymentConfiguration,
                                                          network_configuration,
                                                          module.params['health_check_grace_period_seconds'],
                                                          module.params['force_new_deployment'])

                else:
                    try:
                        response = service_mgr.create_service(module.params['name'],
                                                              module.params['cluster'],
                                                              module.params['task_definition'],
                                                              loadBalancers,
                                                              module.params['desired_count'],
                                                              clientToken,
                                                              role,
                                                              deploymentConfiguration,
                                                              module.params['placement_constraints'],
                                                              module.params['placement_strategy'],
                                                              module.params['health_check_grace_period_seconds'],
                                                              network_configuration,
                                                              serviceRegistries,
                                                              module.params['launch_type'],
                                                              module.params['scheduling_strategy']
                                                              )
                    except botocore.exceptions.ClientError as e:
                        module.fail_json_aws(e, msg="Couldn't create service")

                results['service'] = response

            results['changed'] = True

    elif module.params['state'] == 'absent':
        if not existing:
            pass
        else:
            # it exists, so we should delete it and mark changed.
            # return info about the cluster deleted
            del existing['deployments']
            del existing['events']
            results['ansible_facts'] = existing
            if 'status' in existing and existing['status'] == "INACTIVE":
                results['changed'] = False
            else:
                if not module.check_mode:
                    try:
                        service_mgr.delete_service(
                            module.params['name'],
                            module.params['cluster']
                        )
                    except botocore.exceptions.ClientError as e:
                        module.fail_json_aws(e, msg="Couldn't delete service")
                results['changed'] = True

    elif module.params['state'] == 'deleting':
        if not existing:
            module.fail_json(msg="Service '" + module.params['name'] + " not found.")
            return
        # it exists, so we should delete it and mark changed.
        # return info about the cluster deleted
        delay = module.params['delay']
        repeat = module.params['repeat']
        time.sleep(delay)
        for i in range(repeat):
            existing = service_mgr.describe_service(module.params['cluster'], module.params['name'])
            status = existing['status']
            if status == "INACTIVE":
                results['changed'] = True
                break
            time.sleep(delay)
        if i is repeat - 1:
            module.fail_json(msg="Service still not deleted after " + str(repeat) + " tries of " + str(delay) + " seconds each.")
            return

    module.exit_json(**results)


if __name__ == '__main__':
    main()
