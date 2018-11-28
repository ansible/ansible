#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: ec2_scaling_policy
short_description: Create or delete AWS scaling policies for Autoscaling groups
description:
  - Can create or delete scaling policies for autoscaling groups
  - Referenced autoscaling groups must already exist
version_added: "1.6"
author: "Zacharie Eakin (@Zeekin)"
options:
  state:
    description:
      - register or deregister the policy
    required: true
    choices: ['present', 'absent']
  name:
    description:
      - Unique name for the scaling policy
    required: true
  asg_name:
    description:
      - Name of the associated autoscaling group
    required: true
  adjustment_type:
    description:
      - The type of change in capacity of the autoscaling group
    required: false
    choices: ['ChangeInCapacity','ExactCapacity','PercentChangeInCapacity']
  scaling_adjustment:
    description:
      - The amount by which the autoscaling group is adjusted by the policy
    required: false
  min_adjustment_step:
    description:
      - Minimum amount of adjustment when policy is triggered
    required: false
  cooldown:
    description:
      - The minimum period of time between which autoscaling actions can take place
    required: false
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = '''
- ec2_scaling_policy:
    state: present
    region: US-XXX
    name: "scaledown-policy"
    adjustment_type: "ChangeInCapacity"
    asg_name: "slave-pool"
    scaling_adjustment: -1
    min_adjustment_step: 1
    cooldown: 300
'''

import traceback

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
# from ansible.module_utils.ec2 import (AnsibleAWSError, HAS_BOTO, connect_to_aws, ec2_argument_spec, get_aws_connection_info)
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, HAS_BOTO3, camel_dict_to_snake_dict, get_aws_connection_info, AWSRetry


@AWSRetry.jittered_backoff()
def describe_policies_with_backoff(connection, asg_name, sp_name):
    return connection.describe_policies(
        AutoScalingGroupName=asg_name,
        PolicyNames=[sp_name]
    )['ScalingPolicies']


@AWSRetry.jittered_backoff()
def put_scaling_policy_with_backoff(connection, sp):
    return connection.put_scaling_policy(**sp)


@AWSRetry.jittered_backoff()
def delete_policy_with_backoff(connection, asg_name, sp_name):
    return connection.delete_policy(
        AutoScalingGroupName=asg_name,
        PolicyName=sp_name)


def create_scaling_policy(connection, module):
    sp_name = module.params.get('name')
    adjustment_type = module.params.get('adjustment_type')
    asg_name = module.params.get('asg_name')
    scaling_adjustment = module.params.get('scaling_adjustment')
    min_adjustment_step = module.params.get('min_adjustment_step')
    cooldown = module.params.get('cooldown')

    scaling_policies = describe_policies_with_backoff(connection, asg_name, sp_name)

    if not scaling_policies:
        sp = dict(
            AutoScalingGroupName=asg_name,
            PolicyName=sp_name,
            AdjustmentType=adjustment_type,
            ScalingAdjustment=scaling_adjustment,
            Cooldown=cooldown
        )
        if adjustment_type == 'PercentChangeInCapacity':
            sp['MinAdjustmentStep'] = min_adjustment_step

        try:
            put_scaling_policy_with_backoff(connection, sp)
            policy = describe_policies_with_backoff(connection, asg_name, sp_name)[0]
            module.exit_json(changed=True, **policy)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to update Scaling Policy.",
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except botocore.exceptions.BotoCoreError as e:
                module.fail_json(msg="Failed to update Scaling Policy.",
                                 exception=traceback.format_exc())
    else:
        policy = scaling_policies[0]
        changed = False
        sp = dict(
            AutoScalingGroupName=policy['AutoScalingGroupName'],
            PolicyName=policy['PolicyName'],
            AdjustmentType=policy['AdjustmentType'],
            ScalingAdjustment=policy['ScalingAdjustment'],
            Cooldown=policy['Cooldown']
        )

        # check attributes
        for attr in (
                ('AdjustmentType', 'adjustment_type'),
                ('ScalingAdjustment', 'scaling_adjustment'),
                ('Cooldown', 'cooldown')):
            if policy[attr[0]] != module.params.get(attr[1]):
                changed = True
                sp[attr[0]] = module.params.get(attr[1])

        # min_adjustment_step attribute is only relevant if the adjustment_type
        # is set to percentage change in capacity, so it is a special case
        if module.params.get('adjustment_type') == 'PercentChangeInCapacity':
            if policy.get('MinAdjustmentStep') != module.params.get('min_adjustment_step'):
                changed = True
            sp['MinAdjustmentStep'] = module.params.get('min_adjustment_step')

        try:
            if changed:
                put_scaling_policy_with_backoff(connection, sp)
                policy = describe_policies_with_backoff(connection, asg_name, sp_name)[0]
            module.exit_json(changed=changed, **policy)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to update Scaling Policy.",
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except botocore.exceptions.BotoCoreError as e:
                module.fail_json(msg="Failed to update Scaling Policy.",
                                 exception=traceback.format_exc())


def delete_scaling_policy(connection, module):
    sp_name = module.params.get('name')
    asg_name = module.params.get('asg_name')

    scaling_policies = describe_policies_with_backoff(connection, asg_name, sp_name)

    if scaling_policies:
        try:
            delete_policy_with_backoff(connection, asg_name, sp_name)
            module.exit_json(changed=True)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to delete Scaling Policy.",
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except botocore.exceptions.BotoCoreError as e:
                module.fail_json(msg="Failed to delete Scaling Policy.",
                                 exception=traceback.format_exc())
        except botocore.exceptions.BotoServerError as e:
            module.exit_json(changed=False, msg=str(e))
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            adjustment_type=dict(type='str', choices=['ChangeInCapacity', 'ExactCapacity', 'PercentChangeInCapacity']),
            asg_name=dict(required=True, type='str'),
            scaling_adjustment=dict(type='int'),
            min_adjustment_step=dict(type='int'),
            cooldown=dict(type='int'),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module,
                            conn_type='client',
                            resource='autoscaling',
                            region=region,
                            endpoint=ec2_url,
                            **aws_connect_params)

    state = module.params.get('state')

    if state == 'present':
        create_scaling_policy(connection, module)
    elif state == 'absent':
        delete_scaling_policy(connection, module)


if __name__ == '__main__':
    main()
