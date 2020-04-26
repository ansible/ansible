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
module: elb_classic_lb_info
short_description: Gather information about EC2 Elastic Load Balancers in AWS
description:
    - Gather information about EC2 Elastic Load Balancers in AWS
    - This module was called C(elb_classic_lb_facts) before Ansible 2.9. The usage did not change.
version_added: "2.0"
author:
  - "Michael Schultz (@mjschultz)"
  - "Fernando Jose Pando (@nand0p)"
options:
  names:
    description:
      - List of ELB names to gather information about. Pass this option to gather information about a set of ELBs, otherwise, all ELBs are returned.
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

# Gather information about all ELBs
- elb_classic_lb_info:
  register: elb_info

- debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"

# Gather information about a particular ELB
- elb_classic_lb_info:
    names: frontend-prod-elb
  register: elb_info

- debug:
    msg: "{{ elb_info.elbs.0.dns_name }}"

# Gather information about a set of ELBs
- elb_classic_lb_info:
    names:
    - frontend-prod-elb
    - backend-prod-elb
  register: elb_info

- debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"

'''

RETURN = '''
elbs:
  description: a list of load balancers
  returned: always
  type: list
  sample:
    elbs:
      - attributes:
          access_log:
            enabled: false
          connection_draining:
            enabled: true
            timeout: 300
          connection_settings:
            idle_timeout: 60
          cross_zone_load_balancing:
            enabled: true
        availability_zones:
          - "us-east-1a"
          - "us-east-1b"
          - "us-east-1c"
          - "us-east-1d"
          - "us-east-1e"
        backend_server_description: []
        canonical_hosted_zone_name: test-lb-XXXXXXXXXXXX.us-east-1.elb.amazonaws.com
        canonical_hosted_zone_name_id: XXXXXXXXXXXXXX
        created_time: '2017-08-23T18:25:03.280000+00:00'
        dns_name: test-lb-XXXXXXXXXXXX.us-east-1.elb.amazonaws.com
        health_check:
          healthy_threshold: 10
          interval: 30
          target: HTTP:80/index.html
          timeout: 5
          unhealthy_threshold: 2
        instances: []
        instances_inservice: []
        instances_inservice_count: 0
        instances_outofservice: []
        instances_outofservice_count: 0
        instances_unknownservice: []
        instances_unknownservice_count: 0
        listener_descriptions:
          - listener:
              instance_port: 80
              instance_protocol: HTTP
              load_balancer_port: 80
              protocol: HTTP
            policy_names: []
        load_balancer_name: test-lb
        policies:
          app_cookie_stickiness_policies: []
          lb_cookie_stickiness_policies: []
          other_policies: []
        scheme: internet-facing
        security_groups:
          - sg-29d13055
        source_security_group:
          group_name: default
          owner_alias: XXXXXXXXXXXX
        subnets:
          - subnet-XXXXXXXX
          - subnet-XXXXXXXX
        tags: {}
        vpc_id: vpc-c248fda4
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
    if module._name == 'elb_classic_lb_facts':
        module.deprecate("The 'elb_classic_lb_facts' module has been renamed to 'elb_classic_lb_info'", version='2.13')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='elb', region=region, endpoint=ec2_url, **aws_connect_params)

    try:
        elbs = list_elbs(connection, module.params.get('names'))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get load balancer information.")

    module.exit_json(elbs=elbs)


if __name__ == '__main__':
    main()
