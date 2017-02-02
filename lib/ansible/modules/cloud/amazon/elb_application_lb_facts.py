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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: elb_application_lb_facts
short_description: Gather facts about application ELBs in AWS
description:
    - Gather facts about application ELBs in AWS
version_added: "2.4"
author: Rob White (@wimnat)
options:
  load_balancer_arns:
    description:
      - The Amazon Resource Names (ARN) of the load balancers. You can specify up to 20 load balancers in a single call.
    required: false
  names:
    description:
      - The names of the load balancers.
    required: false

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all target groups
- elb_application_lb_facts:

# Gather facts about the target group attached to a particular ELB
- elb_application_lb_facts:
    load_balancer_arns:
      - "arn:aws:elasticloadbalancing:ap-southeast-2:001122334455:loadbalancer/app/my-elb/aabbccddeeff"

# Gather facts about a target groups named 'tg1' and 'tg2'
- elb_application_lb_facts:
    names:
      - elb1
      - elb2
'''

RETURN = '''
load_balancers:
    description: a list of load balancers
    returned: always
    type: complex
    contains:
        access_logs_s3_bucket:
            description: The name of the S3 bucket for the access logs.
            returned: when status is present
            type: string
            sample: mys3bucket
        access_logs_s3_enabled:
            description: Indicates whether access logs stored in Amazon S3 are enabled.
            returned: when status is present
            type: string
            sample: true
        access_logs_s3_prefix:
            description: The prefix for the location in the S3 bucket.
            returned: when status is present
            type: string
            sample: /my/logs
        availability_zones:
            description: The Availability Zones for the load balancer.
            returned: when status is present
            type: list
            sample: "[{'subnet_id': 'subnet-aabbccddff', 'zone_name': 'ap-southeast-2a'}]"
        canonical_hosted_zone_id:
            description: The ID of the Amazon Route 53 hosted zone associated with the load balancer.
            returned: when status is present
            type: string
            sample: ABCDEF12345678
        created_time:
            description: The date and time the load balancer was created.
            returned: when status is present
            type: string
            sample: "2015-02-12T02:14:02+00:00"
        deletion_protection_enabled:
            description: Indicates whether deletion protection is enabled.
            returned: when status is present
            type: string
            sample: true
        dns_name:
            description: The public DNS name of the load balancer.
            returned: when status is present
            type: string
            sample: internal-my-elb-123456789.ap-southeast-2.elb.amazonaws.com
        idle_timeout_timeout_seconds:
            description: The idle timeout value, in seconds.
            returned: when status is present
            type: string
            sample: 60
        ip_address_type:
            description:  The type of IP addresses used by the subnets for the load balancer.
            returned: when status is present
            type: string
            sample: ipv4
        load_balancer_arn:
            description: The Amazon Resource Name (ARN) of the load balancer.
            returned: when status is present
            type: string
            sample: arn:aws:elasticloadbalancing:ap-southeast-2:0123456789:loadbalancer/app/my-elb/001122334455
        load_balancer_name:
            description: The name of the load balancer.
            returned: when status is present
            type: string
            sample: my-elb
        scheme:
            description: Internet-facing or internal load balancer.
            returned: when status is present
            type: string
            sample: internal
        security_groups:
            description: The IDs of the security groups for the load balancer.
            returned: when status is present
            type: list
            sample: ['sg-0011223344']
        state:
            description: The state of the load balancer.
            returned: when status is present
            type: dict
            sample: "{'code': 'active'}"
        tags:
            description: The tags attached to the load balancer.
            returned: when status is present
            type: dict
            sample: "{
                'Tag': 'Example'
            }"
        type:
            description: The type of load balancer.
            returned: when status is present
            type: string
            sample: application
        vpc_id:
            description: The ID of the VPC for the load balancer.
            returned: when status is present
            type: string
            sample: vpc-0011223344
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info)

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_elb_listeners(connection, module, elb_arn):

    try:
        return connection.describe_listeners(LoadBalancerArn=elb_arn)['Listeners']
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def get_listener_rules(connection, module, listener_arn):

    try:
        return connection.describe_rules(ListenerArn=listener_arn)['Rules']
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def get_load_balancer_attributes(connection, module, load_balancer_arn):

    try:
        load_balancer_attributes = boto3_tag_list_to_ansible_dict(connection.describe_load_balancer_attributes(LoadBalancerArn=load_balancer_arn)['Attributes'])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Replace '.' with '_' in attribute key names to make it more Ansibley
    for k, v in list(load_balancer_attributes.items()):
        load_balancer_attributes[k.replace('.', '_')] = v
        del load_balancer_attributes[k]

    return load_balancer_attributes


def get_load_balancer_tags(connection, module, load_balancer_arn):

    try:
        return boto3_tag_list_to_ansible_dict(connection.describe_tags(ResourceArns=[load_balancer_arn])['TagDescriptions'][0]['Tags'])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def list_load_balancers(connection, module):

    load_balancer_arns = module.params.get("load_balancer_arns")
    names = module.params.get("names")

    try:
        load_balancer_paginator = connection.get_paginator('describe_load_balancers')
        if not load_balancer_arns and not names:
            load_balancers = load_balancer_paginator.paginate().build_full_result()
        if load_balancer_arns:
            load_balancers = load_balancer_paginator.paginate(LoadBalancerArns=load_balancer_arns).build_full_result()
        if names:
            load_balancers = load_balancer_paginator.paginate(Names=names).build_full_result()
    except ClientError as e:
        if e.response['Error']['Code'] == 'LoadBalancerNotFound':
            module.exit_json(load_balancers=[])
        else:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except NoCredentialsError as e:
        module.fail_json(msg="AWS authentication problem. " + e.message, exception=traceback.format_exc())

    for load_balancer in load_balancers['LoadBalancers']:
        # Get the attributes for each elb
        load_balancer.update(get_load_balancer_attributes(connection, module, load_balancer['LoadBalancerArn']))

        # Get the listeners for each elb
        load_balancer['listeners'] = get_elb_listeners(connection, module, load_balancer['LoadBalancerArn'])

        # For each listener, get listener rules
        for listener in load_balancer['listeners']:
            listener['rules'] = get_listener_rules(connection, module, listener['ListenerArn'])

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_load_balancers = [camel_dict_to_snake_dict(load_balancer) for load_balancer in load_balancers['LoadBalancers']]

    # Get tags for each load balancer
    for snaked_load_balancer in snaked_load_balancers:
        snaked_load_balancer['tags'] = get_load_balancer_tags(connection, module, snaked_load_balancer['load_balancer_arn'])

    module.exit_json(load_balancers=snaked_load_balancers)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            load_balancer_arns=dict(type='list'),
            names=dict(type='list')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=['load_balancer_arns', 'names'],
                           supports_check_mode=True
                           )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='elbv2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    list_load_balancers(connection, module)


if __name__ == '__main__':
    main()
