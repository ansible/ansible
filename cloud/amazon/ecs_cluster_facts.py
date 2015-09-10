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
module: ecs_cluster_facts
short_description: list or describe clusters or their instances in ecs
description:
    - Lists or describes clusters or cluster instances in ecs.
version_added: "2.0"
options:
    details:
        description:
            - Set this to true if you want detailed information.
        required: false
        default: false
    cluster:
        description:
            - The cluster ARNS to list.
        required: false
        default: 'default'
    instances:
        description:
            - The instance ARNS to list.
        required: false
        default: None (returns all)
    option:
        description:
            - Whether to return information about clusters or their instances
        required: false
        choices: ['clusters', 'instances']
        default: 'clusters'
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
clusters:
    description: 
        - array of cluster ARNs when details is false
        - array of dicts when details is true
    sample: [ "arn:aws:ecs:us-west-2:172139249013:cluster/test-cluster" ]
'''
try:
    import json, os
    import boto
    import botocore
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    # import module snippets
    from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

class EcsClusterManager:
    """Handles ECS Clusters"""

    def __init__(self, module):
        self.module = module

        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            if not region:
                module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
            self.ecs = boto3_conn(module, conn_type='client', resource='ecs', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg="Can't authorize connection - "+str(e))

    def list_container_instances(self, cluster):
        response = self.ecs.list_container_instances(cluster=cluster)
        relevant_response = dict(instances = response['containerInstanceArns'])
        return relevant_response

    def describe_container_instances(self, cluster, instances):
        response = self.ecs.describe_container_instances(
            clusters=cluster,
            containerInstances=instances.split(",") if instances else []
        )
        relevant_response = dict()
        if 'containerInstances' in response and len(response['containerInstances'])>0:
            relevant_response['instances'] = response['containerInstances']
        if 'failures' in response and len(response['failures'])>0:
            relevant_response['instances_not_running'] = response['failures']
        return relevant_response

    def list_clusters(self):
        response = self.ecs.list_clusters()
        relevant_response = dict(clusters = response['clusterArns'])
        return relevant_response

    def describe_clusters(self, cluster):
        response = self.ecs.describe_clusters(
            clusters=cluster.split(",") if cluster else []
        )
        relevant_response = dict()
        if 'clusters' in response and len(response['clusters'])>0:
            relevant_response['clusters'] = response['clusters']
        if 'failures' in response and len(response['failures'])>0:
            relevant_response['clusters_not_running'] = response['failures']
        return relevant_response

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        details=dict(required=False, type='bool' ),
        cluster=dict(required=False, type='str' ),
        instances=dict(required=False, type='str' ),
        option=dict(required=False, choices=['clusters', 'instances'], default='clusters')
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    show_details = False
    if 'details' in module.params and module.params['details']:
        show_details = True

    task_mgr = EcsClusterManager(module)
    if module.params['option']=='clusters':
        if show_details:
            ecs_facts = task_mgr.describe_clusters(module.params['cluster'])
        else:
            ecs_facts = task_mgr.list_clusters()
    if module.params['option']=='instances':
        if show_details:
            ecs_facts = task_mgr.describe_container_instances(module.params['cluster'], module.params['instances'])
        else:
            ecs_facts = task_mgr.list_container_instances(module.params['cluster'])
    ecs_facts_result = dict(changed=False, ansible_facts=ecs_facts)
    module.exit_json(**ecs_facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
