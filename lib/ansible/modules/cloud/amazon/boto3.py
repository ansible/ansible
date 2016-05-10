#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: boto3
short_description: Make AWS API calls using boto3 client.
description:
    - This is a generic module to make AWS API calls using boto3 client instead of using the CLI.
    - This module is not idempontent! The idempotency needs to be implemented in the playbook
    - by making additional API calls or reading the return value. This module will always yield a changed state.
version_added: 2.3
requirements:
    - boto3
options:
  service:
    description:
      - The name of the service (ie. 's3', 'ec2', 'rds', 'emr', etc.)
    required: true
    default: null
    aliases: ['name']
  operation:
    description:
      - Service operation to call. Maps to client methods of the same name. See boto3 documentation.
    required: true
    default: null
    aliases: []
  parameters:
    description:
      - A hash/dictionary representing operations parameters. See boto3 documentation.
    required: false
    default: null
    aliases: []
author: "Eric Citaire"
extends_documentation_fragment: aws
'''

EXAMPLES = '''
- name: Describe running EMR Clusters
  boto3:
    name: emr
    region: us-east-1
    operation: list_clusters
    parameters:
      ClusterStates:
        - STARTING
        - BOOTSTRAPPING
        - RUNNING
        - WAITING
  changed_when: False
  register: emr

- set_fact:
    emr_cluster_exists: "{{ emr.response.Clusters | selectattr('Name', 'equalto', 'my-jobflow') | list | length > 0 }}"

- set_fact:
    emr_cluster_id: "{{ emr.response.Clusters | selectattr('Name', 'equalto', 'my-jobflow') | map(attribute='Id') | first }}"
  when: emr_cluster_exists

# if 'my-jobflow' cluster does not exist, create it.
- name: Create EMR Cluster
  boto3:
    name: emr
    region: us-east-1
    operation: run_job_flow
    parameters:
      Name: my-jobflow
      Applications:
        - Name: Hive
      Instances:
        KeepJobFlowAliveWhenNoSteps: True
        Ec2KeyName: my-key
        Ec2SubnetId: subnet-xxxxxxx
        EmrManagedSlaveSecurityGroup: sg-xxxxxxx
        EmrManagedMasterSecurityGroup: sg-xxxxxxx
        InstanceGroups:
          - InstanceCount: 1
            InstanceRole: MASTER
            InstanceType: m1.medium
            Market: ON_DEMAND
          - InstanceCount: 1
            InstanceRole: CORE
            InstanceType: m1.medium
            Name: Core Instance Group
            Market: ON_DEMAND
      JobFlowRole: EMR_EC2_DefaultRole
      ServiceRole: EMR_DefaultRole
      ReleaseLabel: emr-4.6.0
      VisibleToAllUsers: True
  when: not emr_cluster_exists
  register: emr_create

- set_fact:
    emr_cluster_id: "{{ emr_create.response.JobFlowId }}"
    emr_cluster_exists: True
  when: not emr_cluster_exists
'''

RETURN = '''
response:
    description: boto3 response, depending on the operation called. See boto3 documentation.
    returned: success
    type: dict
    sample: { "Clusters": [ ], "ResponseMetadata": { "HTTPStatusCode": 200, "RequestId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" } }
'''

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, get_aws_connection_info

try:
    import boto3
    from botocore.exceptions import *
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_operation_method(client, operation_name):
    valid = True
    # private method
    if operation_name[0] == '_':
        valid = False
    # client utility methods
    utility_methods = [
        'can_paginate',
        'generate_presigned_url',
        'get_paginator',
        'get_waiter',
        'meta',
        'waiter_names'
        ]
    if operation_name in utility_methods:
        valid = False
    # not an attribute
    if operation_name not in dir(client):
        valid = False
    # not callable
    operation_method = getattr(client, operation_name, None) if valid else None
    if not callable(operation_method):
        valid = False
    if valid:
        return operation_method
    else:
        return None


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        service=dict(required=True, type='str', aliases=['name']),
        operation=dict(required=True, type='str'),
        parameters=dict(default={}, type='dict')
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module')

    service = module.params.get('service')
    operation = module.params.get('operation')
    parameters = module.params.get('parameters')
    aws_access_key = module.params.get('aws_access_key')
    aws_secret_key = module.params.get('aws_secret_key')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource=service, region=region, endpoint=ec2_url, **aws_connect_kwargs)
        operation_method = get_operation_method(client, operation)
        if not operation_method:
            module.fail_json(msg='"{}" is not a valid operation for service "{}".'.format(operation, service))
        response = operation_method(**parameters)
    except Exception as e:
        module.fail_json(msg=e.message)

    module.exit_json(changed=True, response=response)


if __name__ == '__main__':
    main()
