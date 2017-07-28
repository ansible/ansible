#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: elb_classic_lb_facts
short_description: Gather facts about EC2 Elastic Load Balancers in AWS
description:
    - Gather facts about EC2 Elastic Load Balancers in AWS
version_added: "2.0"
author:
  - "Michael Schultz (github.com/mjschultz)"
  - "Fernando Jose Pando (@nand0p)"
options:
  names:
    description:
      - List of ELB names to gather facts about. Pass this option to gather facts about a set of ELBs, otherwise, all ELBs are returned.
    required: false
    default: null
    aliases: ['elb_ids', 'ec2_elbs']
extends_documentation_fragment:
    - aws
    - ec2
requirements:
  - botocore
  - boto3
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Output format tries to match ec2_elb_lb module input parameters

# Gather facts about all ELBs
- elb_classic_lb_facts:
  register: elb_facts

- debug:
    msg: "{{ item.dns_name }}"
  with_items: "{{ elb_facts.elbs }}"

# Gather facts about a particular ELB
- elb_classic_lb_facts:
    names: frontend-prod-elb
  register: elb_facts

- debug:
    msg: "{{ elb_facts.elbs.0.dns_name }}"

# Gather facts about a set of ELBs
- elb_classic_lb_facts:
    names:
    - frontend-prod-elb
    - backend-prod-elb
  register: elb_facts

- debug:
    msg: "{{ item.dns_name }}"
  with_items: "{{ elb_facts.elbs }}"

'''

import traceback

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    AWSRetry,
    boto3_conn,
    ec2_argument_spec,
    get_aws_connection_info,
    camel_dict_to_snake_dict,
    boto3_tag_list_to_ansible_dict
)

try:
    import botocore
except ImportError:
    pass


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_elbs(connection, names):
    paginator = connection.get_paginator('describe_load_balancers')
    load_balancers = paginator.paginate(LoadBalancerNames=names).build_full_result().get('LoadBalancerDescriptions', [])
    results = []

    for lb in load_balancers:
        description = camel_dict_to_snake_dict(lb)
        name = lb['LoadBalancerName']
        instances = lb.get('Instances', [])
        description['tags'] = get_tags(connection, name)
        description['instances_inservice'], description['instances_inservice_count'] = lb_instance_health(connection, name, instances, 'InService')
        description['instances_outofservice'], description['instances_outofservice_count'] = lb_instance_health(connection, name, instances, 'OutOfService')
        description['instances_unknownservice'], description['instances_unknownservice_count'] = lb_instance_health(connection, name, instances, 'Unknown')
        description['attributes'] = get_lb_attributes(connection, name)
        results.append(description)
    return results


def get_lb_attributes(connection, name):
    attributes = connection.describe_load_balancer_attributes(LoadBalancerName=name).get('LoadBalancerAttributes', {})
    return camel_dict_to_snake_dict(attributes)


def get_tags(connection, load_balancer_name):
    tags = connection.describe_tags(LoadBalancerNames=[load_balancer_name])['TagDescriptions']
    if not tags:
        return {}
    return boto3_tag_list_to_ansible_dict(tags[0]['Tags'])


def lb_instance_health(connection, load_balancer_name, instances, state):
    instance_states = connection.describe_instance_health(LoadBalancerName=load_balancer_name, Instances=instances).get('InstanceStates', [])
    instate = [instance['InstanceId'] for instance in instance_states if instance['State'] == state]
    return instate, len(instate)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        names={'default': [], 'type': 'list'}
    )
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="region must be specified")

    try:
        connection = boto3_conn(module,
                                conn_type='client',
                                resource='elb',
                                region=region,
                                endpoint=ec2_url,
                                **aws_connect_params)
    except (botocore.exceptions.PartialCredentialsError, botocore.exceptions.ProfileNotFound) as e:
        module.fail_json_aws(e, msg="Can't authorize connection. Check your credentials and profile.")

    try:
        elbs = list_elbs(connection, module.params.get('names'))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get load balancer facts.")

    module.exit_json(elb_classic_facts=elbs)


if __name__ == '__main__':
    main()
