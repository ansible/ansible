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
module: elb_target_group_facts
short_description: Gather facts about ELB target groups in AWS
description:
    - Gather facts about ELB target groups in AWS
version_added: "2.4"
requirements: [ boto3 ]
author: Rob White (@wimnat)
options:
  load_balancer_arn:
    description:
      - The Amazon Resource Name (ARN) of the load balancer.
    required: false
  target_group_arns:
    description:
      - The Amazon Resource Names (ARN) of the target groups.
    required: false
  names:
    description:
      - The names of the target groups.
    required: false
  collect_targets_health:
    description:
      - When set to "yes", output contains targets health description
    required: false
    default: no
    type: bool
    version_added: 2.8

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all target groups
- elb_target_group_facts:

# Gather facts about the target group attached to a particular ELB
- elb_target_group_facts:
    load_balancer_arn: "arn:aws:elasticloadbalancing:ap-southeast-2:001122334455:loadbalancer/app/my-elb/aabbccddeeff"

# Gather facts about a target groups named 'tg1' and 'tg2'
- elb_target_group_facts:
    names:
      - tg1
      - tg2

'''

RETURN = '''
target_groups:
    description: a list of target groups
    returned: always
    type: complex
    contains:
        deregistration_delay_timeout_seconds:
            description: The amount time for Elastic Load Balancing to wait before changing the state of a deregistering target from draining to unused.
            returned: always
            type: int
            sample: 300
        health_check_interval_seconds:
            description: The approximate amount of time, in seconds, between health checks of an individual target.
            returned: always
            type: int
            sample: 30
        health_check_path:
            description: The destination for the health check request.
            returned: always
            type: str
            sample: /index.html
        health_check_port:
            description: The port to use to connect with the target.
            returned: always
            type: str
            sample: traffic-port
        health_check_protocol:
            description: The protocol to use to connect with the target.
            returned: always
            type: str
            sample: HTTP
        health_check_timeout_seconds:
            description: The amount of time, in seconds, during which no response means a failed health check.
            returned: always
            type: int
            sample: 5
        healthy_threshold_count:
            description: The number of consecutive health checks successes required before considering an unhealthy target healthy.
            returned: always
            type: int
            sample: 5
        load_balancer_arns:
            description: The Amazon Resource Names (ARN) of the load balancers that route traffic to this target group.
            returned: always
            type: list
            sample: []
        matcher:
            description: The HTTP codes to use when checking for a successful response from a target.
            returned: always
            type: dict
            sample: {
                "http_code": "200"
            }
        port:
            description: The port on which the targets are listening.
            returned: always
            type: int
            sample: 80
        protocol:
            description: The protocol to use for routing traffic to the targets.
            returned: always
            type: str
            sample: HTTP
        stickiness_enabled:
            description: Indicates whether sticky sessions are enabled.
            returned: always
            type: bool
            sample: true
        stickiness_lb_cookie_duration_seconds:
            description: Indicates whether sticky sessions are enabled.
            returned: always
            type: int
            sample: 86400
        stickiness_type:
            description: The type of sticky sessions.
            returned: always
            type: str
            sample: lb_cookie
        tags:
            description: The tags attached to the target group.
            returned: always
            type: dict
            sample: "{
                'Tag': 'Example'
            }"
        target_group_arn:
            description: The Amazon Resource Name (ARN) of the target group.
            returned: always
            type: str
            sample: "arn:aws:elasticloadbalancing:ap-southeast-2:01234567890:targetgroup/mytargetgroup/aabbccddee0044332211"
        targets_health_description:
            description: Targets health description.
            returned: when collect_targets_health is enabled
            type: complex
            contains:
                health_check_port:
                    description: The port to check target health.
                    returned: always
                    type: str
                    sample: '80'
                target:
                    description: The target metadata.
                    returned: always
                    type: complex
                    contains:
                        id:
                            description: The ID of the target.
                            returned: always
                            type: str
                            sample: i-0123456789
                        port:
                            description: The port to use to connect with the target.
                            returned: always
                            type: int
                            sample: 80
                target_health:
                    description: The target health status.
                    returned: always
                    type: complex
                    contains:
                        state:
                            description: The state of the target health.
                            returned: always
                            type: str
                            sample: healthy
        target_group_name:
            description: The name of the target group.
            returned: always
            type: str
            sample: mytargetgroup
        unhealthy_threshold_count:
            description: The number of consecutive health check failures required before considering the target unhealthy.
            returned: always
            type: int
            sample: 2
        vpc_id:
            description: The ID of the VPC for the targets.
            returned: always
            type: str
            sample: vpc-0123456
'''

import traceback

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info)


def get_target_group_attributes(connection, module, target_group_arn):

    try:
        target_group_attributes = boto3_tag_list_to_ansible_dict(connection.describe_target_group_attributes(TargetGroupArn=target_group_arn)['Attributes'])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Replace '.' with '_' in attribute key names to make it more Ansibley
    return dict((k.replace('.', '_'), v)
                for (k, v) in target_group_attributes.items())


def get_target_group_tags(connection, module, target_group_arn):

    try:
        return boto3_tag_list_to_ansible_dict(connection.describe_tags(ResourceArns=[target_group_arn])['TagDescriptions'][0]['Tags'])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def get_target_group_targets_health(connection, module, target_group_arn):

    try:
        return connection.describe_target_health(TargetGroupArn=target_group_arn)['TargetHealthDescriptions']
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def list_target_groups(connection, module):

    load_balancer_arn = module.params.get("load_balancer_arn")
    target_group_arns = module.params.get("target_group_arns")
    names = module.params.get("names")
    collect_targets_health = module.params.get("collect_targets_health")

    try:
        target_group_paginator = connection.get_paginator('describe_target_groups')
        if not load_balancer_arn and not target_group_arns and not names:
            target_groups = target_group_paginator.paginate().build_full_result()
        if load_balancer_arn:
            target_groups = target_group_paginator.paginate(LoadBalancerArn=load_balancer_arn).build_full_result()
        if target_group_arns:
            target_groups = target_group_paginator.paginate(TargetGroupArns=target_group_arns).build_full_result()
        if names:
            target_groups = target_group_paginator.paginate(Names=names).build_full_result()
    except ClientError as e:
        if e.response['Error']['Code'] == 'TargetGroupNotFound':
            module.exit_json(target_groups=[])
        else:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except NoCredentialsError as e:
        module.fail_json(msg="AWS authentication problem. " + e.message, exception=traceback.format_exc())

    # Get the attributes and tags for each target group
    for target_group in target_groups['TargetGroups']:
        target_group.update(get_target_group_attributes(connection, module, target_group['TargetGroupArn']))

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_target_groups = [camel_dict_to_snake_dict(target_group) for target_group in target_groups['TargetGroups']]

    # Get tags for each target group
    for snaked_target_group in snaked_target_groups:
        snaked_target_group['tags'] = get_target_group_tags(connection, module, snaked_target_group['target_group_arn'])
        if collect_targets_health:
            snaked_target_group['targets_health_description'] = [camel_dict_to_snake_dict(
                target) for target in get_target_group_targets_health(connection, module, snaked_target_group['target_group_arn'])]

    module.exit_json(target_groups=snaked_target_groups)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            load_balancer_arn=dict(type='str'),
            target_group_arns=dict(type='list'),
            names=dict(type='list'),
            collect_targets_health=dict(default=False, type='bool', required=False)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['load_balancer_arn', 'target_group_arns', 'names']],
                           supports_check_mode=True
                           )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='elbv2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    list_target_groups(connection, module)


if __name__ == '__main__':
    main()
