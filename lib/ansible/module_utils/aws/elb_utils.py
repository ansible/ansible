#!/usr/bin/env python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Ansible imports
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

# Non-ansible imports
try:
    from botocore.exceptions import ClientError
except ImportError:
    pass
import traceback


def get_elb(connection, module, elb_name):
    """
    Get an ELB based on name. If not found, return None.

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param elb_name: Name of load balancer to get
    :return: boto3 ELB dict or None if not found
    """

    try:
        load_balancer_paginator = connection.get_paginator('describe_load_balancers')
        return (load_balancer_paginator.paginate(Names=[elb_name]).build_full_result())['LoadBalancers'][0]
    except ClientError as e:
        if e.response['Error']['Code'] == 'LoadBalancerNotFound':
            return None
        else:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def get_elb_listener(connection, module, elb_arn, listener_port):
    """
    Get an ELB listener based on the port provided. If not found, return None.

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param elb_arn: ARN of the ELB to look at
    :param listener_port: Port of the listener to look for
    :return: boto3 ELB listener dict or None if not found
    """

    try:
        listener_paginator = connection.get_paginator('describe_listeners')
        listeners = (listener_paginator.paginate(LoadBalancerArn=elb_arn).build_full_result())['Listeners']
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    l = None

    for listener in listeners:
        if listener['Port'] == listener_port:
            l = listener
            break

    return l


def get_elb_listener_rules(connection, module, listener_arn):
    """
    Get rules for a particular ELB listener using the listener ARN.

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param listener_arn: ARN of the ELB listener
    :return: boto3 ELB rules list
    """

    try:
        return connection.describe_rules(ListenerArn=listener_arn)['Rules']
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def convert_tg_name_to_arn(connection, module, tg_name):
    """
    Get ARN of a target group using the target group's name

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param tg_name: Name of the target group
    :return: target group ARN string
    """

    try:
        response = connection.describe_target_groups(Names=[tg_name])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    tg_arn = response['TargetGroups'][0]['TargetGroupArn']

    return tg_arn
