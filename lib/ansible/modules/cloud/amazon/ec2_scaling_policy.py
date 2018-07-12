#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = """
module: ec2_scaling_policy
short_description: Create or delete AWS scaling policies for Autoscaling groups
description:
  - Can create or delete scaling policies for autoscaling groups
  - Referenced autoscaling groups must already exist
version_added: "1.6"
author:
  - Zacharie Eakin (@zeekin)
  - Will Thames (@willthames)
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
      - Name of the associated autoscaling group. Required if I(state) is C(present).
  adjustment_type:
    description:
      - The type of change in capacity of the autoscaling group. Required if I(state) is C(present).
    choices:
      - ChangeInCapacity
      - ExactCapacity
      - PercentChangeInCapacity
  scaling_adjustment:
    description:
      - The amount by which the autoscaling group is adjusted by the policy.
        A negative number scales the autoscaling group in. Units are numbers
        of instances for C(ExactCapacity) or C(ChangeInCapacity) or percent
        of existing instances for C(PercentChangeInCapacity).
        Required when I(policy_type) is C(SimpleScaling).
  min_adjustment_step:
    description:
      - Minimum amount of adjustment when policy is triggered. Used
        only when I(adjustment_type) is C(PercentChangeInCapacity)
  cooldown:
    description:
      - The minimum period of time between which autoscaling actions can take place.
        Used only when I(policy_type) is C(SimpleScaling).
  policy_type:
    description:
      - Auto scaling adjustment policy
    choices:
      - StepScaling
      - SimpleScaling
    version_added: "2.7"
    default: SimpleScaling
  metric_aggregation:
    description:
      - The aggregation type for the CloudWatch metrics.
      - For use when I(policy_type) is not C(SimpleScaling)
    default: Average
    choices:
      - Minimum
      - Maximum
      - Average
    version_added: "2.7"
  step_adjustments:
    description:
      - list of dicts containing I(lower_bound), I(upper_bound) and I(scaling_adjustment)
      - One item can not have a lower bound, and one item can not have an upper bound.
      - Intervals must not overlap
      - The bounds are the amount over the alarm threshold at which the adjustment will trigger.
        This means that for an alarm threshold of 50, triggering at 75 requires a lower bound of 25.
        See U(http://docs.aws.amazon.com/AutoScaling/latest/APIReference/API_StepAdjustment.html).
    version_added: "2.7"
  estimated_instance_warmup:
    description:
      - The estimated time, in seconds, until a newly launched instance can contribute to the CloudWatch metrics.
    version_added: "2.7"
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = '''
- name: Simple Scale Down policy
  ec2_scaling_policy:
    state: present
    region: US-XXX
    name: "scaledown-policy"
    adjustment_type: "ChangeInCapacity"
    asg_name: "application-asg"
    scaling_adjustment: -1
    min_adjustment_step: 1
    cooldown: 300

# For an alarm with a breach threshold of 20, the
# following creates a stepped policy:
# From 20-40 (0-20 above threshold), increase by 50% of existing capacity
# From 41-infinity, increase by 100% of existing capacity
- ec2_scaling_policy:
    state: present
    region: US-XXX
    name: "step-scale-up-policy"
    policy_type: StepScaling
    metric_aggregation: Maximum
    step_adjustments:
      - upper_bound: 20
        scaling_adjustment: 50
      - lower_bound: 20
        scaling_adjustment: 100
    adjustment_type: "PercentChangeInCapacity"
    asg_name: "application-asg"
'''

RETURN = '''
adjustment_type:
  description: Scaling policy adjustment type
  returned: always
  type: string
  sample: PercentChangeInCapacity
alarms:
  description: Cloudwatch alarms related to the policy
  returned: always
  type: complex
  contains:
    alarm_name:
      description: name of the Cloudwatch alarm
      returned: always
      type: string
      sample: cpu-very-high
    alarm_arn:
      description: ARN of the Cloudwatch alarm
      returned: always
      type: string
      sample: arn:aws:cloudwatch:us-east-2:1234567890:alarm:cpu-very-high
arn:
  description: ARN of the scaling policy. Provided for backward compatibility, value is the same as I(policy_arn)
  returned: always
  type: string
  sample: arn:aws:autoscaling:us-east-2:123456789012:scalingPolicy:59e37526-bd27-42cf-adca-5cd3d90bc3b9:autoScalingGroupName/app-asg:policyName/app-policy
as_name:
  description: Auto Scaling Group name. Provided for backward compatibility, value is the same as I(auto_scaling_group_name)
  returned: always
  type: string
  sample: app-asg
auto_scaling_group_name:
  description: Name of Auto Scaling Group
  returned: always
  type: string
  sample: app-asg
metric_aggregation_type:
  description: Method used to aggregate metrics
  returned: when I(policy_type) is C(StepScaling)
  type: string
  sample: Maximum
name:
  description: Name of the scaling policy. Provided for backward compatibility, value is the same as I(policy_name)
  returned: always
  type: string
  sample: app-policy
policy_arn:
  description: ARN of scaling policy.
  returned: always
  type: string
  sample: arn:aws:autoscaling:us-east-2:123456789012:scalingPolicy:59e37526-bd27-42cf-adca-5cd3d90bc3b9:autoScalingGroupName/app-asg:policyName/app-policy
policy_name:
  description: Name of scaling policy
  returned: always
  type: string
  sample: app-policy
policy_type:
  description: Type of auto scaling policy
  returned: always
  type: string
  sample: StepScaling
scaling_adjustment:
  description: Adjustment to make when alarm is triggered
  returned: When I(policy_type) is C(SimpleScaling)
  type: int
  sample: 1
step_adjustments:
  description: List of step adjustments
  returned: always
  type: complex
  contains:
    metric_interval_lower_bound:
      description: Lower bound for metric interval
      returned: if step has a lower bound
      type: float
      sample: 20.0
    metric_interval_upper_bound:
      description: Upper bound for metric interval
      returned: if step has an upper bound
      type: float
      sample: 40.0
    scaling_adjustment:
      description: Adjustment to make if this step is reached
      returned: always
      type: int
      sample: 50
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    import botocore
except ImportError:
    pass  # caught by imported AnsibleAWSModule


def create_scaling_policy(connection, module):
    changed = False
    asg_name = module.params['asg_name']
    policy_type = module.params['policy_type']
    policy_name = module.params['name']

    params = dict(PolicyName=policy_name,
                  PolicyType=policy_type,
                  AutoScalingGroupName=asg_name,
                  AdjustmentType=module.params['adjustment_type'])

    # min_adjustment_step attribute is only relevant if the adjustment_type
    # is set to percentage change in capacity, so it is a special case
    if module.params['adjustment_type'] == 'PercentChangeInCapacity':
        if module.params['min_adjustment_step']:
            params['MinAdjustmentMagnitude'] = module.params['min_adjustment_step']

    if policy_type == 'SimpleScaling':
        # can't use required_if because it doesn't allow multiple criteria -
        # it's only required if policy is SimpleScaling and state is present
        if not module.params['scaling_adjustment']:
            module.fail_json(msg='scaling_adjustment is required when policy_type is SimpleScaling '
                             'and state is present')
        params['ScalingAdjustment'] = module.params['scaling_adjustment']
        if module.params['cooldown']:
            params['Cooldown'] = module.params['cooldown']

    if policy_type == 'StepScaling':
        if not module.params['step_adjustments']:
            module.fail_json(msg='step_adjustments is required when policy_type is StepScaling '
                             'and state is present')
        params['StepAdjustments'] = []
        for step_adjustment in module.params['step_adjustments']:
            step_adjust_params = dict(ScalingAdjustment=step_adjustment['scaling_adjustment'])
            # Although empty bounds are allowed, not setting the 0 end of the bound seems
            # to cause problems in the UI. We'll leave the +/- infinity end unset if not set
            if not step_adjustment.get('lower_bound') and step_adjustment.get('upper_bound') > 0:
                step_adjustment['lower_bound'] = 0
            if step_adjustment.get('lower_bound'):
                step_adjust_params['MetricIntervalLowerBound'] = step_adjustment['lower_bound']
            if not step_adjustment.get('upper_bound') and step_adjustment.get('lower_bound') < 0:
                step_adjustment['upper_bound'] = 0
            if step_adjustment.get('upper_bound'):
                step_adjust_params['MetricIntervalUpperBound'] = step_adjustment['upper_bound']
            params['StepAdjustments'].append(step_adjust_params)
        if module.params['metric_aggregation']:
            params['MetricAggregationType'] = module.params['metric_aggregation']
        if module.params['estimated_instance_warmup']:
            params['EstimatedInstanceWarmup'] = module.params['estimated_instance_warmup']

    try:
        policies = connection.describe_policies(AutoScalingGroupName=asg_name,
                                                PolicyNames=[policy_name])['ScalingPolicies']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain autoscaling policy %s" % policy_name)

    before = after = {}
    if not policies:
        changed = True
    else:
        policy = policies[0]
        for key in params:
            if params[key] != policy.get(key):
                changed = True
                before[key] = params[key]
                after[key] = policy.get(key)

    if changed:
        try:
            connection.put_scaling_policy(**params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to create autoscaling policy")
        try:
            policies = connection.describe_policies(AutoScalingGroupName=asg_name,
                                                    PolicyNames=[policy_name])['ScalingPolicies']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(msg="Failed to obtain autoscaling policy %s" % policy_name)

    policy = camel_dict_to_snake_dict(policies[0])
    # Backward compatible return values
    policy['arn'] = policy['policy_arn']
    policy['as_name'] = policy['auto_scaling_group_name']
    policy['name'] = policy['policy_name']

    if before and after:
        module.exit_json(changed=changed, diff=dict(before=before, after=after), **policy)
    else:
        module.exit_json(changed=changed, **policy)


def delete_scaling_policy(connection, module):
    policy_name = module.params.get('name')

    try:
        policy = connection.describe_policies(PolicyNames=[policy_name])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to obtain autoscaling policy %s" % policy_name)

    if policy['ScalingPolicies']:
        try:
            connection.delete_policy(AutoScalingGroupName=policy['ScalingPolicies'][0]['AutoScalingGroupName'],
                                     PolicyName=policy_name)
            module.exit_json(changed=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to delete autoscaling policy")
        module.exit_json(changed=False)


def main():
    step_adjustment_spec = dict(
        lower_bound=dict(type='int'),
        upper_bound=dict(type='int'),
        scaling_adjustment=dict(type='int', required=True))

    argument_spec = dict(
        name=dict(required=True),
        adjustment_type=dict(choices=['ChangeInCapacity', 'ExactCapacity', 'PercentChangeInCapacity']),
        asg_name=dict(),
        scaling_adjustment=dict(type='int'),
        min_adjustment_step=dict(type='int'),
        cooldown=dict(type='int'),
        state=dict(default='present', choices=['present', 'absent']),
        metric_aggregation=dict(default='Average', choices=['Minimum', 'Maximum', 'Average']),
        policy_type=dict(default='SimpleScaling', choices=['SimpleScaling', 'StepScaling']),
        step_adjustments=dict(type='list', options=step_adjustment_spec),
        estimated_instance_warmup=dict(type='int')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[['state', 'present', ['asg_name', 'adjustment_type']]])

    connection = module.client('autoscaling')

    state = module.params.get('state')
    if state == 'present':
        create_scaling_policy(connection, module)
    elif state == 'absent':
        delete_scaling_policy(connection, module)


if __name__ == '__main__':
    main()
