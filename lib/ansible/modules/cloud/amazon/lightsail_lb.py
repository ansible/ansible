#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: lightsail_lb
short_description: Creates or deletes load balancer and attaches running instances to the created load balancer in AWS Lightsail.
description:
     - Create or delete a load balancer in AWS Lightsail.
version_added: "2.8"
author: "Gencebay Demir (@gencebay)"
options:
  state:
    description:
      - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  name:
    description:
      - The name of the load balancer.
    required: true
  attachInstances:
    description:
      - An array of strings representing the instance name(s) you want to attach to your load balancer.
  port:
    description:
      - The instance port where you're creating your load balancer.
    default: 80
  healthCheckPath:
    description:
      - The path you provided to perform the load balancer health check.

requirements:
  - "python >= 2.6"
  - boto3

extends_documentation_fragment:
  - aws
  - ec2
'''


EXAMPLES = '''
# Create a new load balancer
- lightsail_lb:
    state: present
    name: loadbalancer1
    region: eu-central-1
    attachInstances: ["Ubuntu-512MB-1", "Ubuntu-512MB-2"]
    port: 80
    healthCheckPath: /api/health
  register: lb_result

- debug:
    msg: "DNS name is {{ lb_result.loadbalancer.dns_name }}"
  when: lb_result.loadbalancer.dns_name is defined

- debug:
    msg: "Protocol is {{ lb_result.loadbalancer.protocol }}"
  when: lb_result.loadbalancer.protocol is defined

# Delete the load balancer if present
- lightsail_lb:
    state: absent
    region: eu-central-1
    name: loadbalancer1

'''

RETURN = '''
changed:
  description: if a load balancer has been modified/created
  returned: always
  type: bool
  sample:
    changed: true
loadbalancer:
  description: load balancer info
  returned: when state is present
  type: dict
  sample:
    {
        "changed":true,
        "loadbalancer":{
            "arn":"arn:aws:lightsail:eu-central-1:731382453814:LoadBalancer/de77b828-3aa0-49b8-8cc5-fb0e69da3782",
            "configuration_options":{
                "session_stickiness_enabled":"false",
                "session_stickiness_lb__cookie_duration_seconds":"86400"
            },
            "created_at":"2018-12-18T10:12:47.878000+03:00",
            "dns_name":"1438df7092a3bd6db5f749796584d140-1104323986.eu-central-1.elb.amazonaws.com",
            "health_check_path":"/api/health",
            "instance_health_summary":[
                {
                    "instance_health":"initial",
                    "instance_health_reason":"Lb.RegistrationInProgress",
                    "instance_name":"Ubuntu-512MB-Frankfurt-1"
                },
                {
                    "instance_health":"initial",
                    "instance_health_reason":"Lb.RegistrationInProgress",
                    "instance_name":"Ubuntu-512MB-Frankfurt-2"
                }
            ],
            "instance_port":80,
            "location":{
                "availability_zone":"all",
                "region_name":"eu-central-1"
            },
            "name":"loadbalancer1",
            "protocol":"HTTP",
            "public_ports":[
                80
            ],
            "resource_type":"LoadBalancer",
            "state":"provisioning",
            "support_code":"301507506052/arn:aws:elasticloadbalancing:eu-central-1:301507506052:loadbalancer/app/1438df7092a3bd6db5f749796584d140/e469715075649370",
            "tags":[

            ],
            "tls_certificate_summaries":[

            ]
        }
    }
'''

import traceback

try:
    import botocore
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

try:
    import boto3
except ImportError:
    # will be caught by imported HAS_BOTO3
    pass

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (ec2_argument_spec, get_aws_connection_info, boto3_conn,
                                      HAS_BOTO3, camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list)


def get_load_balancer_info(client, name):
    ''' handle exceptions where this function is called '''
    loadbalancer = None
    try:
        loadbalancer = client.get_load_balancer(loadBalancerName=name)
    except botocore.exceptions.ClientError as e:
        raise
    return loadbalancer['loadBalancer']


def find_instance_info(client, instance_name):
    ''' handle exceptions where this function is called '''
    inst = None
    try:
        inst = client.get_instance(instanceName=instance_name)
    except botocore.exceptions.ClientError as e:
        raise
    return inst['instance']


def create_load_balancer(module, client, name):
    """
    Create a load balancer

    module: Ansible module object
    client: authenticated lightsail connection object
    name: name of load balancer

    Returns a dictionary of load balancer information
    """

    changed = False

    loadbalancer = None
    try:
        loadbalancer = client.get_load_balancer(loadBalancerName=name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NotFoundException':
            module.fail_json(msg='Error finding load balancer {0}, error: {1}'.format(name, e))

    loadBalancerName = module.params.get('name')
    instancePort = module.params.get('port')
    healthCheckPath = module.params.get('healthCheckPath')
    attachInstances = module.params.get('attachInstances')

    resp = None
    if loadbalancer is None:
        try:
            resp = client.create_load_balancer(
                loadBalancerName=loadBalancerName,
                instancePort=instancePort,
                healthCheckPath=healthCheckPath
            )
            resp = resp['operations'][0]
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg='Unable to create the load balancer {0}, error: {1}'.format(loadBalancerName, e))
        changed = True

        if attachInstances is not None:
            try:
                for instanceName in attachInstances:
                    find_instance_info(client, instanceName)

                attachedResp = client.attach_instances_to_load_balancer(
                    loadBalancerName=loadBalancerName,
                    instanceNames=attachInstances
                )
                attachedResp = attachedResp['operations'][0]
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg='Unable to attach {0}, error: {1}'.format(loadBalancerName, e))

    loadbalancer = get_load_balancer_info(client, loadBalancerName)
    return (changed, loadbalancer)


def delete_load_balancer(module, client, lb_name):
    """
    Terminates the load balancer

    module: Ansible module object
    client: authenticated lightsail connection object
    lb_name: name of load balancer to delete

    Returns a dictionary of the load balancer information
    """
    changed = False

    loadbalancer = None
    try:
        loadbalancer = get_load_balancer_info(client, lb_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NotFoundException':
            module.fail_json(msg='Error finding load balancer {0}, error: {1}'.format(lb_name, e))

    if loadbalancer is not None:
        try:
            client.delete_load_balancer(loadBalancerName=lb_name)
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg='Error deleting load balancer {0}, error: {1}'.format(lb_name, e))

    return (changed, loadbalancer)


def core(module):
    region = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg='region must be specified')

    client = module.client('lightsail')

    changed = False
    state = module.params['state']
    name = module.params['name']

    if state == 'absent':
        changed, lb_dict = delete_load_balancer(module, client, name)
    elif state == 'present':
        changed, lb_dict = create_load_balancer(module, client, name)

    if lb_dict is None:
        lb_dict = {}

    module.exit_json(changed=changed, loadbalancer=camel_dict_to_snake_dict(lb_dict))


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        attachInstances=dict(type='list', default=[]),
        port=dict(type='int', default=80),
        healthCheckPath=dict(type='str', default=None)
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    try:
        core(module)
    except (botocore.exceptions.ClientError, Exception) as e:
        module.fail_json_aws(e)


if __name__ == '__main__':
    main()
