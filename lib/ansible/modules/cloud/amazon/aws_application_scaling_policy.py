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
module: aws_application_scaling_policy
short_description: Manage Application Auto Scaling Scaling Policies
notes:
    - for details of the parameters and returns see
      U(http://boto3.readthedocs.io/en/latest/reference/services/application-autoscaling.html#ApplicationAutoScaling.Client.put_scaling_policy)
description:
    - Creates, updates or removes a Scaling Policy
version_added: "2.5"
author:
    - Gustavo Maia(@gurumaia)
    - Chen Leibovich(@chenl87)
requirements: [ json, botocore, boto3 ]
options:
    policy_name:
        description: The name of the scaling policy.
        required: yes
    service_namespace:
        description: The namespace of the AWS service.
        required: yes
        choices: ['ecs', 'elasticmapreduce', 'ec2', 'appstream', 'dynamodb']
    resource_id:
        description: The identifier of the resource associated with the scalable target.
        required: yes
    scalable_dimension:
        description: The scalable dimension associated with the scalable target.
        required: yes
        choices: [ 'ecs:service:DesiredCount',
                   'ec2:spot-fleet-request:TargetCapacity',
                   'elasticmapreduce:instancegroup:InstanceCount',
                   'appstream:fleet:DesiredCapacity',
                   'dynamodb:table:ReadCapacityUnits',
                   'dynamodb:table:WriteCapacityUnits',
                   'dynamodb:index:ReadCapacityUnits',
                   'dynamodb:index:WriteCapacityUnits']
    policy_type:
        description: The policy type.
        required: yes
        choices: ['StepScaling', 'TargetTrackingScaling']
    step_scaling_policy_configuration:
        description: A step scaling policy. This parameter is required if you are creating a policy and the policy type is StepScaling.
        required: no
    target_tracking_scaling_policy_configuration:
        description: A target tracking policy. This parameter is required if you are creating a new policy and the policy type is TargetTrackingScaling.
        required: no
    minimum_tasks:
        description: The minimum value to scale to in response to a scale in event.
            This parameter is required if you are creating a first new policy for the specified service.
        required: no
        version_added: "2.6"
    maximum_tasks:
        description: The maximum value to scale to in response to a scale out event.
            This parameter is required if you are creating a first new policy for the specified service.
        required: no
        version_added: "2.6"
    override_task_capacity:
        description: Whether or not to override values of minimum and/or maximum tasks if it's already set.
        required: no
        default: no
        type: bool
        version_added: "2.6"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create step scaling policy for ECS Service
- name: scaling_policy
  aws_application_scaling_policy:
    state: present
    policy_name: test_policy
    service_namespace: ecs
    resource_id: service/poc-pricing/test-as
    scalable_dimension: ecs:service:DesiredCount
    policy_type: StepScaling
    minimum_tasks: 1
    maximum_tasks: 6
    step_scaling_policy_configuration:
      AdjustmentType: ChangeInCapacity
      StepAdjustments:
        - MetricIntervalUpperBound: 123
          ScalingAdjustment: 2
        - MetricIntervalLowerBound: 123
          ScalingAdjustment: -2
      Cooldown: 123
      MetricAggregationType: Average

# Create target tracking scaling policy for ECS Service
- name: scaling_policy
  aws_application_scaling_policy:
    state: present
    policy_name: test_policy
    service_namespace: ecs
    resource_id: service/poc-pricing/test-as
    scalable_dimension: ecs:service:DesiredCount
    policy_type: TargetTrackingScaling
    minimum_tasks: 1
    maximum_tasks: 6
    target_tracking_scaling_policy_configuration:
      TargetValue: 60
      PredefinedMetricSpecification:
        PredefinedMetricType: ECSServiceAverageCPUUtilization
      ScaleOutCooldown: 60
      ScaleInCooldown: 60

# Remove scalable target for ECS Service
- name: scaling_policy
  aws_application_scaling_policy:
    state: absent
    policy_name: test_policy
    policy_type: StepScaling
    service_namespace: ecs
    resource_id: service/cluster-name/service-name
    scalable_dimension: ecs:service:DesiredCount
'''

RETURN = '''
alarms:
    description: List of the CloudWatch alarms associated with the scaling policy
    returned: when state present
    type: complex
    contains:
        alarm_arn:
            description: The Amazon Resource Name (ARN) of the alarm
            returned: when state present
            type: string
        alarm_name:
            description: The name of the alarm
            returned: when state present
            type: string
service_namespace:
    description: The namespace of the AWS service.
    returned: when state present
    type: string
    sample: ecs
resource_id:
    description: The identifier of the resource associated with the scalable target.
    returned: when state present
    type: string
    sample: service/cluster-name/service-name
scalable_dimension:
    description: The scalable dimension associated with the scalable target.
    returned: when state present
    type: string
    sample: ecs:service:DesiredCount
policy_arn:
    description: The Amazon Resource Name (ARN) of the scaling policy..
    returned: when state present
    type: string
policy_name:
    description: The name of the scaling policy.
    returned: when state present
    type: string
policy_type:
    description: The policy type.
    returned: when state present
    type: string    
min_capacity:
    description: The minimum value to scale to in response to a scale in event. Required if I(state) is C(present).
    returned: when state present
    type: int
    sample: 1
max_capacity:
    description: The maximum value to scale to in response to a scale out event. Required if I(state) is C(present).
    returned: when state present
    type: int
    sample: 2
role_arn:
    description: The ARN of an IAM role that allows Application Auto Scaling to modify the scalable target on your behalf. Required if I(state) is C(present).
    returned: when state present
    type: string
    sample: arn:aws:iam::123456789123:role/roleName
step_scaling_policy_configuration:
    description: The step scaling policy.
    returned: when state present and the policy type is StepScaling
    type: complex
    contains:
        adjustment_type:
            description: The adjustment type
            returned: when state present and the policy type is StepScaling
            type: string
            sample: "ChangeInCapacity, PercentChangeInCapacity, ExactCapacity"
        cooldown:
            description: The amount of time, in seconds, after a scaling activity completes 
                where previous trigger-related scaling activities can influence future scaling events
            returned: when state present and the policy type is StepScaling
            type: int
            sample: 60
        metric_aggregation_type:
            description: The aggregation type for the CloudWatch metrics
            returned: when state present and the policy type is StepScaling
            type: string
            sample: "Average, Minimum, Maximum"
        step_adjustments:
            description: A set of adjustments that enable you to scale based on the size of the alarm breach
            returned: when state present and the policy type is StepScaling
            type: list of complex
target_tracking_scaling_policy_configuration:
    description: The target tracking policy.
    returned: when state present and the policy type is TargetTrackingScaling
    type: complex
    contains:
        predefined_metric_specification:
            description: A predefined metric
            returned: when state present and the policy type is TargetTrackingScaling
            type: complex
            contains:
                predefined_metric_type:
                    description: The metric type
                    returned: when state present and the policy type is TargetTrackingScaling
                    type: string
                    sample: "ECSServiceAverageCPUUtilization, ECSServiceAverageMemoryUtilization"
                resource_label:
                    description: Identifies the resource associated with the metric type
                    returned: when metric type is ALBRequestCountPerTarget
                    type: string
        scale_in_cooldown:
            description: The amount of time, in seconds, after a scale in activity completes before another scale in activity can start
            returned: when state present and the policy type is TargetTrackingScaling
            type: int
            sample: 60
        scale_out_cooldown:
            description: The amount of time, in seconds, after a scale out activity completes before another scale out activity can start
            returned: when state present and the policy type is TargetTrackingScaling
            type: int
            sample: 60
        target_value:
            description: The target value for the metric
            returned: when state present and the policy type is TargetTrackingScaling
            type: int
            sample: 70
creation_time:
    description: The Unix timestamp for when the scalable target was created.
    returned: when state present
    type: string
    sample: '2017-09-28T08:22:51.881000-03:00'
'''  # NOQA

import traceback

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import _camel_to_snake, camel_dict_to_snake_dict, ec2_argument_spec

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule


# Merge the results of the scalable target creation and policy deletion/creation
# There's no risk in overriding values since mutual keys have the same values in our case
def merge_results(scalable_target_result, policy_result):
    if scalable_target_result['changed'] or policy_result['changed']:
        changed = True
    else:
        changed = False

    merged_response = scalable_target_result['response'].copy()
    merged_response.update(policy_result['response'])

    return {"changed": changed, "response": merged_response}


def delete_scaling_policy(connection, module):
    changed = False
    try:
        scaling_policy = connection.describe_scaling_policies(
            ServiceNamespace=module.params.get('service_namespace'),
            ResourceId=module.params.get('resource_id'),
            ScalableDimension=module.params.get('scalable_dimension'),
            PolicyNames=[module.params.get('policy_name')],
            MaxResults=1
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe scaling policies")

    if scaling_policy['ScalingPolicies']:
        try:
            connection.delete_scaling_policy(
                ServiceNamespace=module.params.get('service_namespace'),
                ResourceId=module.params.get('resource_id'),
                ScalableDimension=module.params.get('scalable_dimension'),
                PolicyName=module.params.get('policy_name'),
            )
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to delete scaling policy")

    return {"changed": changed}


def create_scalable_target(connection, module):
    changed = False

    try:
        scalable_targets = connection.describe_scalable_targets(
            ServiceNamespace=module.params.get('service_namespace'),
            ResourceIds=[
                module.params.get('resource_id'),
            ],
            ScalableDimension=module.params.get('scalable_dimension')
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to describe scalable targets")

    # Scalable target registration will occur if:
    # 1. There is no scalable target registered for this service
    # 2. A scalable target exists, different min/max values are defined and override is set to "yes"
    if (
        not scalable_targets['ScalableTargets']
        or (
            module.params.get('override_task_capacity')
            and (
                scalable_targets['ScalableTargets'][0]['MinCapacity'] != module.params.get('minimum_tasks')
                or scalable_targets['ScalableTargets'][0]['MaxCapacity'] != module.params.get('maximum_tasks')
            )
        )
    ):
        changed = True
        try:
            connection.register_scalable_target(
                ServiceNamespace=module.params.get('service_namespace'),
                ResourceId=module.params.get('resource_id'),
                ScalableDimension=module.params.get('scalable_dimension'),
                MinCapacity=module.params.get('minimum_tasks'),
                MaxCapacity=module.params.get('maximum_tasks')
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to register scalable target")

    try:
        response = connection.describe_scalable_targets(
            ServiceNamespace=module.params.get('service_namespace'),
            ResourceIds=[
                module.params.get('resource_id'),
            ],
            ScalableDimension=module.params.get('scalable_dimension')
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe scalable targets")

    if (response['ScalableTargets']):
        snaked_response = camel_dict_to_snake_dict(response['ScalableTargets'][0])
    else:
        snaked_response = {}

    return {"changed": changed, "response": snaked_response}


def create_scaling_policy(connection, module):
    try:
        scaling_policy = connection.describe_scaling_policies(
            ServiceNamespace=module.params.get('service_namespace'),
            ResourceId=module.params.get('resource_id'),
            ScalableDimension=module.params.get('scalable_dimension'),
            PolicyNames=[module.params.get('policy_name')],
            MaxResults=1
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe scaling policies")

    changed = False

    if scaling_policy['ScalingPolicies']:
        scaling_policy = scaling_policy['ScalingPolicies'][0]
        # check if the input parameters are equal to what's already configured
        for attr in ('PolicyName',
                     'ServiceNamespace',
                     'ResourceId',
                     'ScalableDimension',
                     'PolicyType',
                     'StepScalingPolicyConfiguration',
                     'TargetTrackingScalingPolicyConfiguration'):
            if attr in scaling_policy and scaling_policy[attr] != module.params.get(_camel_to_snake(attr)):
                changed = True
                scaling_policy[attr] = module.params.get(_camel_to_snake(attr))
    else:
        changed = True
        scaling_policy = {
            'PolicyName': module.params.get('policy_name'),
            'ServiceNamespace': module.params.get('service_namespace'),
            'ResourceId': module.params.get('resource_id'),
            'ScalableDimension': module.params.get('scalable_dimension'),
            'PolicyType': module.params.get('policy_type'),
            'StepScalingPolicyConfiguration': module.params.get('step_scaling_policy_configuration'),
            'TargetTrackingScalingPolicyConfiguration': module.params.get('target_tracking_scaling_policy_configuration')
        }

    if changed:
        try:
            if (module.params.get('step_scaling_policy_configuration')):
                connection.put_scaling_policy(
                    PolicyName=scaling_policy['PolicyName'],
                    ServiceNamespace=scaling_policy['ServiceNamespace'],
                    ResourceId=scaling_policy['ResourceId'],
                    ScalableDimension=scaling_policy['ScalableDimension'],
                    PolicyType=scaling_policy['PolicyType'],
                    StepScalingPolicyConfiguration=scaling_policy['StepScalingPolicyConfiguration']
                )
            elif (module.params.get('target_tracking_scaling_policy_configuration')):
                connection.put_scaling_policy(
                    PolicyName=scaling_policy['PolicyName'],
                    ServiceNamespace=scaling_policy['ServiceNamespace'],
                    ResourceId=scaling_policy['ResourceId'],
                    ScalableDimension=scaling_policy['ScalableDimension'],
                    PolicyType=scaling_policy['PolicyType'],
                    TargetTrackingScalingPolicyConfiguration=scaling_policy['TargetTrackingScalingPolicyConfiguration']
                )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to create scaling policy")

    try:
        response = connection.describe_scaling_policies(
            ServiceNamespace=module.params.get('service_namespace'),
            ResourceId=module.params.get('resource_id'),
            ScalableDimension=module.params.get('scalable_dimension'),
            PolicyNames=[module.params.get('policy_name')],
            MaxResults=1
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe scaling policies")

    if (response['ScalingPolicies']):
        snaked_response = camel_dict_to_snake_dict(response['ScalingPolicies'][0])
    else:
        snaked_response = {}

    return {"changed": changed, "response": snaked_response}


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent'], type='str'),
        policy_name=dict(required=True, type='str'),
        service_namespace=dict(required=True, choices=['ecs', 'elasticmapreduce', 'ec2', 'appstream', 'dynamodb'], type='str'),
        resource_id=dict(required=True, type='str'),
        scalable_dimension=dict(required=True, choices=['ecs:service:DesiredCount',
                                                        'ec2:spot-fleet-request:TargetCapacity',
                                                        'elasticmapreduce:instancegroup:InstanceCount',
                                                        'appstream:fleet:DesiredCapacity',
                                                        'dynamodb:table:ReadCapacityUnits',
                                                        'dynamodb:table:WriteCapacityUnits',
                                                        'dynamodb:index:ReadCapacityUnits',
                                                        'dynamodb:index:WriteCapacityUnits'
                                                        ], type='str'),
        policy_type=dict(required=True, choices=['StepScaling', 'TargetTrackingScaling'], type='str'),
        step_scaling_policy_configuration=dict(required=False, type='dict'),
        target_tracking_scaling_policy_configuration=dict(required=False, type='dict'),
        minimum_tasks=dict(required=False, type='int'),
        maximum_tasks=dict(required=False, type='int'),
        override_task_capacity=dict(required=False, type=bool)
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('application-autoscaling')

    if module.params.get("state") == 'present':
        # A scalable target must be registered prior to creating a scaling policy
        scalable_target_result = create_scalable_target(connection, module)
        policy_result = create_scaling_policy(connection, module)
        # Merge the results of the scalable target creation and policy deletion/creation
        # There's no risk in overriding values since mutual keys have the same values in our case
        merged_result = merge_results(scalable_target_result, policy_result)
        module.exit_json(**merged_result)
    else:
        policy_result = delete_scaling_policy(connection, module)
        module.exit_json(**policy_result)


if __name__ == '__main__':
    main()
