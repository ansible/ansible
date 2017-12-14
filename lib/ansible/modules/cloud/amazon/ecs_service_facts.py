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
module: ecs_service_facts
short_description: list or describe services in ecs
notes:
    - for details of the parameters and returns see U(http://boto3.readthedocs.org/en/latest/reference/services/ecs.html)
description:
    - Lists or describes services in ecs.
version_added: "2.1"
author:
    - "Mark Chance (@java1guy)"
    - "Darek Kaczynski (@kaczynskid)"
requirements: [ json, botocore, boto3 ]
options:
    details:
        description:
            - Set this to true if you want detailed information about the services.
        required: false
        default: 'false'
        choices: ['true', 'false']
    cluster:
        description:
            - The cluster ARNS in which to list the services.
        required: false
        default: 'default'
    service:
        description:
            - The service to get details for (required if details is true)
        required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic listing example
- ecs_service_facts:
    cluster: test-cluster
    service: console-test-service
    details: true

# Basic listing example
- ecs_service_facts:
    cluster: test-cluster
'''

RETURN = '''
services:
    description: When details is false, returns an array of service ARNs, otherwise an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        clusterArn:
            description: The Amazon Resource Name (ARN) of the of the cluster that hosts the service.
            returned: always
            type: string
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
                    type: string
                containerName:
                    description: The name of the container to associate with the load balancer.
                    returned: always
                    type: string
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
            description: The Amazon Resource Name (ARN) that identifies the service. The ARN contains the arn:aws:ecs namespace, followed by the region of the service, the AWS account ID of the service owner, the service namespace, and then the service name. For example, arn:aws:ecs:region :012345678910 :service/my-service .
            returned: always
            type: string
        serviceName:
            description: A user-generated string used to identify the service
            returned: always
            type: string
        status:
            description: The valid values are ACTIVE, DRAINING, or INACTIVE.
            returned: always
            type: string
        taskDefinition:
            description: The ARN of a task definition to use for tasks in the service.
            returned: always
            type: string
        deployments:
            description: list of service deployments
            returned: always
            type: list of complex
        events:
            description: lost of service events
            returned: always
            type: list of complex
'''  # NOQA

try:
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info


class EcsServiceManager:
    """Handles ECS Services"""

    def __init__(self, module):
        self.module = module

        # self.ecs = boto3.client('ecs')
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        self.ecs = boto3_conn(module, conn_type='client', resource='ecs', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    # def list_clusters(self):
    #   return self.client.list_clusters()
    # {'failures': [],
    # 'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'ce7b5880-1c41-11e5-8a31-47a93a8a98eb'},
    # 'clusters': [{'activeServicesCount': 0, 'clusterArn': 'arn:aws:ecs:us-west-2:777110527155:cluster/default',
    #               'status': 'ACTIVE', 'pendingTasksCount': 0, 'runningTasksCount': 0, 'registeredContainerInstancesCount': 0, 'clusterName': 'default'}]}
    # {'failures': [{'arn': 'arn:aws:ecs:us-west-2:777110527155:cluster/bogus', 'reason': 'MISSING'}],
    # 'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': '0f66c219-1c42-11e5-8a31-47a93a8a98eb'},
    # 'clusters': []}

    def list_services(self, cluster):
        fn_args = dict()
        if cluster and cluster is not None:
            fn_args['cluster'] = cluster
        response = self.ecs.list_services(**fn_args)
        relevant_response = dict(services=response['serviceArns'])
        return relevant_response

    def describe_services(self, cluster, services):
        fn_args = dict()
        if cluster and cluster is not None:
            fn_args['cluster'] = cluster
        fn_args['services'] = services.split(",")
        response = self.ecs.describe_services(**fn_args)
        relevant_response = dict(services=map(self.extract_service_from, response['services']))
        if 'failures' in response and len(response['failures']) > 0:
            relevant_response['services_not_running'] = response['failures']
        return relevant_response

    def extract_service_from(self, service):
        # some fields are datetime which is not JSON serializable
        # make them strings
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


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        details=dict(required=False, type='bool', default=False),
        cluster=dict(required=False, type='str'),
        service=dict(required=False, type='str')
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    show_details = module.params.get('details', False)

    task_mgr = EcsServiceManager(module)
    if show_details:
        if 'service' not in module.params or not module.params['service']:
            module.fail_json(msg="service must be specified for ecs_service_facts")
        ecs_facts = task_mgr.describe_services(module.params['cluster'], module.params['service'])
    else:
        ecs_facts = task_mgr.list_services(module.params['cluster'])

    ecs_facts_result = dict(changed=False, ansible_facts=ecs_facts)
    module.exit_json(**ecs_facts_result)


if __name__ == '__main__':
    main()
