# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.ec2 import AWSRetry

# Non-ansible imports
try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass


def get_elb(connection, module, elb_name):
    """
    Get an ELB based on name. If not found, return None.

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param elb_name: Name of load balancer to get
    :return: boto3 ELB dict or None if not found
    """
    try:
        return _get_elb(connection, module, elb_name)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


@AWSRetry.jittered_backoff()
def _get_elb(connection, module, elb_name):
    """
    Get an ELB based on name using AWSRetry. If not found, return None.

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param elb_name: Name of load balancer to get
    :return: boto3 ELB dict or None if not found
    """

    try:
        load_balancer_paginator = connection.get_paginator('describe_load_balancers')
        return (load_balancer_paginator.paginate(Names=[elb_name]).build_full_result())['LoadBalancers'][0]
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == 'LoadBalancerNotFound':
            return None
        else:
            raise e


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
        listeners = (AWSRetry.jittered_backoff()(listener_paginator.paginate)(LoadBalancerArn=elb_arn).build_full_result())['Listeners']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

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
        return AWSRetry.jittered_backoff()(connection.describe_rules)(ListenerArn=listener_arn)['Rules']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


def convert_tg_name_to_arn(connection, module, tg_name):
    """
    Get ARN of a target group using the target group's name

    :param connection: AWS boto3 elbv2 connection
    :param module: Ansible module
    :param tg_name: Name of the target group
    :return: target group ARN string
    """

    try:
        response = AWSRetry.jittered_backoff()(connection.describe_target_groups)(Names=[tg_name])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

    tg_arn = response['TargetGroups'][0]['TargetGroupArn']

    return tg_arn
