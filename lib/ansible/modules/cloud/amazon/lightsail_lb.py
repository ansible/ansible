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
  region:
    description:
      - The AWS Region name.
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

from ansible.module_utils.basic import AnsibleModule
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
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg='region must be specified')

    client = None
    try:
        client = boto3_conn(module, conn_type='client', resource='lightsail',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
        module.fail_json(msg='Failed while connecting to the lightsail service: %s' % e, exception=traceback.format_exc())

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
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        attachInstances=dict(type='list', default=[]),
        port=dict(type='int', default=80),
        healthCheckPath=dict(type='str', default=None)
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    if not HAS_BOTOCORE:
        module.fail_json(msg='Python module "botocore" is missing, please install it')

    try:
        core(module)
    except (botocore.exceptions.ClientError, Exception) as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

if __name__ == '__main__':
    main()
