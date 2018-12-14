#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: elb_target
short_description: Manage a target in a target group
description:
    - Used to register or deregister a target in a target group
version_added: "2.5"
author: "Rob White (@wimnat)"
options:
  deregister_unused:
    description:
      - The default behaviour for targets that are unused is to leave them registered. If instead you would like to remove them
        set I(deregister_unused) to yes.
    type: bool
  target_az:
    description:
      - An Availability Zone or all. This determines whether the target receives traffic from the load balancer nodes in the specified
        Availability Zone or from all enabled Availability Zones for the load balancer. This parameter is not supported if the target
        type of the target group is instance.
  target_group_arn:
    description:
      - The Amazon Resource Name (ARN) of the target group. Mutually exclusive of I(target_group_name).
  target_group_name:
    description:
      - The name of the target group. Mutually exclusive of I(target_group_arn).
  target_id:
    description:
      - The ID of the target.
    required: true
  target_port:
    description:
      - The port on which the target is listening. You can specify a port override. If a target is already registered,
        you can register it again using a different port.
    required: false
    default: The default port for a target is the port for the target group.
  target_status:
    description:
      - Blocks and waits for the target status to equal given value. For more detail on target status see
        U(https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html#target-health-states)
    required: false
    choices: [ 'initial', 'healthy', 'unhealthy', 'unused', 'draining', 'unavailable' ]
  target_status_timeout:
    description:
      - Maximum time in seconds to wait for target_status change
    required: false
    default: 60
  state:
    description:
      - Register or deregister the target.
    required: true
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
notes:
  - If you specified a port override when you registered a target, you must specify both the target ID and the port when you deregister it.
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Register an IP address target to a target group
- elb_target:
    target_group_name: myiptargetgroup
    target_id: i-1234567
    state: present

# Register an instance target to a target group
- elb_target:
    target_group_name: mytargetgroup
    target_id: i-1234567
    state: present

# Deregister a target from a target group
- elb_target:
    target_group_name: mytargetgroup
    target_id: i-1234567
    state: absent

# Modify a target to use a different port
# Register a target to a target group
- elb_target:
    target_group_name: mytargetgroup
    target_id: i-1234567
    target_port: 8080
    state: present

'''

RETURN = '''

'''

import traceback
from time import time, sleep
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (boto3_conn, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info)

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def convert_tg_name_to_arn(connection, module, tg_name):

    try:
        response = connection.describe_target_groups(Names=[tg_name])
    except ClientError as e:
        module.fail_json(msg="Unable to describe target group {0}: {1}".format(tg_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except BotoCoreError as e:
        module.fail_json(msg="Unable to describe target group {0}: {1}".format(tg_name, to_native(e)),
                         exception=traceback.format_exc())

    tg_arn = response['TargetGroups'][0]['TargetGroupArn']

    return tg_arn


def describe_targets(connection, module, tg_arn, target):

    """
    Describe targets in a target group

    :param module: ansible module object
    :param connection: boto3 connection
    :param tg_arn: target group arn
    :param target: dictionary containing target id and port
    :return:
    """

    try:
        targets = connection.describe_target_health(TargetGroupArn=tg_arn, Targets=target)['TargetHealthDescriptions']
        if not targets:
            return {}
        return targets[0]
    except ClientError as e:
        module.fail_json(msg="Unable to describe target health for target {0}: {1}".format(target, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except BotoCoreError as e:
        module.fail_json(msg="Unable to describe target health for target {0}: {1}".format(target, to_native(e)),
                         exception=traceback.format_exc())


def register_target(connection, module):

    """
    Registers a target to a target group

    :param module: ansible module object
    :param connection: boto3 connection
    :return:
    """

    target_az = module.params.get("target_az")
    target_group_arn = module.params.get("target_group_arn")
    target_id = module.params.get("target_id")
    target_port = module.params.get("target_port")
    target_status = module.params.get("target_status")
    target_status_timeout = module.params.get("target_status_timeout")
    changed = False

    if not target_group_arn:
        target_group_arn = convert_tg_name_to_arn(connection, module, module.params.get("target_group_name"))

    target = dict(Id=target_id)
    if target_az:
        target['AvailabilityZone'] = target_az
    if target_port:
        target['Port'] = target_port

    target_description = describe_targets(connection, module, target_group_arn, [target])

    if 'Reason' in target_description['TargetHealth']:
        if target_description['TargetHealth']['Reason'] == "Target.NotRegistered":
            try:
                connection.register_targets(TargetGroupArn=target_group_arn, Targets=[target])
                changed = True
                if target_status:
                    target_status_check(connection, module, target_group_arn, target, target_status, target_status_timeout)
            except ClientError as e:
                module.fail_json(msg="Unable to deregister target {0}: {1}".format(target, to_native(e)),
                                 exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            except BotoCoreError as e:
                module.fail_json(msg="Unable to deregister target {0}: {1}".format(target, to_native(e)),
                                 exception=traceback.format_exc())

    # Get all targets for the target group
    target_descriptions = describe_targets(connection, module, target_group_arn, [])

    module.exit_json(changed=changed, target_health_descriptions=camel_dict_to_snake_dict(target_descriptions), target_group_arn=target_group_arn)


def deregister_target(connection, module):

    """
    Deregisters a target to a target group

    :param module: ansible module object
    :param connection: boto3 connection
    :return:
    """

    deregister_unused = module.params.get("deregister_unused")
    target_group_arn = module.params.get("target_group_arn")
    target_id = module.params.get("target_id")
    target_port = module.params.get("target_port")
    target_status = module.params.get("target_status")
    target_status_timeout = module.params.get("target_status_timeout")
    changed = False

    if not target_group_arn:
        target_group_arn = convert_tg_name_to_arn(connection, module, module.params.get("target_group_name"))

    target = dict(Id=target_id)
    if target_port:
        target['Port'] = target_port

    target_description = describe_targets(connection, module, target_group_arn, [target])
    current_target_state = target_description['TargetHealth']['State']
    current_target_reason = target_description['TargetHealth'].get('Reason')

    needs_deregister = False

    if deregister_unused and current_target_state == 'unused':
        if current_target_reason != 'Target.NotRegistered':
            needs_deregister = True
    elif current_target_state not in ['unused', 'draining']:
        needs_deregister = True

    if needs_deregister:
        try:
            connection.deregister_targets(TargetGroupArn=target_group_arn, Targets=[target])
            changed = True
        except ClientError as e:
            module.fail_json(msg="Unable to deregister target {0}: {1}".format(target, to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except BotoCoreError as e:
            module.fail_json(msg="Unable to deregister target {0}: {1}".format(target, to_native(e)),
                             exception=traceback.format_exc())
    else:
        if current_target_reason != 'Target.NotRegistered' and current_target_state != 'draining':
            module.warn(warning="Your specified target has an 'unused' state but is still registered to the target group. " +
                                "To force deregistration use the 'deregister_unused' option.")

    if target_status:
        target_status_check(connection, module, target_group_arn, target, target_status, target_status_timeout)

    # Get all targets for the target group
    target_descriptions = describe_targets(connection, module, target_group_arn, [])

    module.exit_json(changed=changed, target_health_descriptions=camel_dict_to_snake_dict(target_descriptions), target_group_arn=target_group_arn)


def target_status_check(connection, module, target_group_arn, target, target_status, target_status_timeout):
    reached_state = False
    timeout = target_status_timeout + time()
    while time() < timeout:
        health_state = describe_targets(connection, module, target_group_arn, [target])['TargetHealth']['State']
        if health_state == target_status:
            reached_state = True
            break
        sleep(1)
    if not reached_state:
        module.fail_json(msg='Status check timeout of {0} exceeded, last status was {1}: '.format(target_status_timeout, health_state))


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            deregister_unused=dict(type='bool', default=False),
            target_az=dict(type='str'),
            target_group_arn=dict(type='str'),
            target_group_name=dict(type='str'),
            target_id=dict(type='str', required=True),
            target_port=dict(type='int'),
            target_status=dict(choices=['initial', 'healthy', 'unhealthy', 'unused', 'draining', 'unavailable'], type='str'),
            target_status_timeout=dict(type='int', default=60),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['target_group_arn', 'target_group_name']]
                           )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='elbv2', region=region, endpoint=ec2_url, **aws_connect_params)

    state = module.params.get("state")

    if state == 'present':
        register_target(connection, module)
    else:
        deregister_target(connection, module)


if __name__ == '__main__':
    main()
