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
module: ecs_service_facts
short_description: list or describe services in ecs
description:
    - Lists or describes services in ecs.
version_added: "0.9"
options:
    details:
        description:
            - Set this to true if you want detailed information about the services.
        required: false
        default: 'false'
        choices: ['true', 'false']
        version_added: 1.9
    cluster:
        description:
            - The cluster ARNS in which to list the services.
        required: false
        default: 'default'
        version_added: 1.9
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic listing example
- ecs_task:
    cluster=test-cluster
    task_list=123456789012345678901234567890123456

# Basic example of deregistering task
- ecs_task:
    state: absent
    family: console-test-tdn
    revision: 1
'''
RETURN = '''
cache_updated:
    description: if the cache was updated or not
    returned: success, in some cases
    type: boolean
    sample: True
cache_update_time:
    description: time of the last cache update (0 if unknown)
    returned: success, in some cases
    type: datetime
    sample: 1425828348000
stdout:
    description: output from apt
    returned: success, when needed
    type: string
    sample: "Reading package lists...\nBuilding dependency tree...\nReading state information...\nThe following extra packages will be installed:\n  apache2-bin ..."
stderr:
    description: error output from apt
    returned: success, when needed
    type: string
    sample: "AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to ..."
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

class EcsServiceManager:
    """Handles ECS Clusters"""

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

    # def list_clusters(self):
    #   return self.client.list_clusters()
    # {'failures': [],
    # 'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'ce7b5880-1c41-11e5-8a31-47a93a8a98eb'},
    # 'clusters': [{'activeServicesCount': 0, 'clusterArn': 'arn:aws:ecs:us-west-2:777110527155:cluster/default', 'status': 'ACTIVE', 'pendingTasksCount': 0, 'runningTasksCount': 0, 'registeredContainerInstancesCount': 0, 'clusterName': 'default'}]}
    # {'failures': [{'arn': 'arn:aws:ecs:us-west-2:777110527155:cluster/bogus', 'reason': 'MISSING'}],
    # 'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': '0f66c219-1c42-11e5-8a31-47a93a8a98eb'},
    # 'clusters': []}

    def list_services(self, cluster):
        fn_args = dict()
        if cluster and cluster is not None:
            fn_args['cluster'] = cluster
        response = self.ecs.list_services(**fn_args)
        relevant_response = dict(services = response['serviceArns'])
        return relevant_response

    def describe_services(self, cluster, services):
        fn_args = dict()
        if cluster and cluster is not None:
            fn_args['cluster'] = cluster
        fn_args['services']=services.split(",")
        response = self.ecs.describe_services(**fn_args)
        relevant_response = dict(services = response['services'])
        if 'failures' in response and len(response['failures'])>0:
            relevant_response['services_not_running'] = response['failures']
        return relevant_response

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        details=dict(required=False, choices=['true', 'false'] ),
        cluster=dict(required=False, type='str' ),
        service=dict(required=False, type='str' )
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    show_details = False
    if 'details' in module.params and module.params['details'] == 'true':
        show_details = True

    task_mgr = EcsServiceManager(module)
    if show_details:
        if 'service' not in module.params or not module.params['service']:
            module.fail_json(msg="service must be specified for ecs_service_facts")
        ecs_facts = task_mgr.describe_services(module.params['cluster'], module.params['service'])
        # the bad news is the result has datetime fields that aren't JSON serializable
        # nuk'em!
        for service in ecs_facts['services']:
            del service['deployments']
            del service['events']
    else:
        ecs_facts = task_mgr.list_services(module.params['cluster'])
    ecs_facts_result = dict(changed=False, ansible_facts=ecs_facts)
    module.exit_json(**ecs_facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
