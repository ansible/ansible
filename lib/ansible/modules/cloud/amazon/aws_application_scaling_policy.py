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
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create scaling policy for ECS Service
- name: scaling_policy
  aws_application_scaling_policy:
  state: present
  policy_name: test_policy
  service_namespace: ecs
  resource_id: service/poc-pricing/test-as
  scalable_dimension: ecs:service:DesiredCount
  policy_type: StepScaling
  step_scaling_policy_configuration:
    AdjustmentType: ChangeInCapacity
    StepAdjustments:
      - MetricIntervalUpperBound: 123
        ScalingAdjustment: 2
      - MetricIntervalLowerBound: 123
        ScalingAdjustment: -2
    Cooldown: 123
    MetricAggregationType: Average

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
creation_time:
    description: The Unix timestamp for when the scalable target was created.
    returned: when state present
    type: string
    sample: '2017-09-28T08:22:51.881000-03:00'
'''  # NOQA

import traceback

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import _camel_to_snake, camel_dict_to_snake_dict, boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def delete_scaling_policy(connection, module):
    changed = False
    scaling_policy = connection.describe_scaling_policies(
        ServiceNamespace=module.params.get('service_namespace'),
        ResourceId=module.params.get('resource_id'),
        ScalableDimension=module.params.get('scalable_dimension'),
        PolicyNames=[module.params.get('policy_name')],
        MaxResults=1
    )

    if scaling_policy['ScalingPolicies']:
        try:
            connection.delete_scaling_policy(
                ServiceNamespace=module.params.get('service_namespace'),
                ResourceId=module.params.get('resource_id'),
                ScalableDimension=module.params.get('scalable_dimension'),
                PolicyName=module.params.get('policy_name'),
            )
            changed = True
        except Exception as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc())

    module.exit_json(changed=changed)


def create_scaling_policy(connection, module):
    scaling_policy = connection.describe_scaling_policies(
        ServiceNamespace=module.params.get('service_namespace'),
        ResourceId=module.params.get('resource_id'),
        ScalableDimension=module.params.get('scalable_dimension'),
        PolicyNames=[module.params.get('policy_name')],
        MaxResults=1
    )

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
        except Exception as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc())

    try:
        response = connection.describe_scaling_policies(
            ServiceNamespace=module.params.get('service_namespace'),
            ResourceId=module.params.get('resource_id'),
            ScalableDimension=module.params.get('scalable_dimension'),
            PolicyNames=[module.params.get('policy_name')],
            MaxResults=1
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

    if (response['ScalingPolicies']):
        snaked_response = camel_dict_to_snake_dict(response['ScalingPolicies'][0])
    else:
        snaked_response = {}
    module.exit_json(changed=changed, response=snaked_response)


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
        target_tracking_scaling_policy_configuration=dict(required=False, type='dict')
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        if not region:
            module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
        connection = boto3_conn(module, conn_type='client', resource='application-autoscaling', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.ProfileNotFound as e:
        module.fail_json(msg=str(e))

    if module.params.get("state") == 'present':
        create_scaling_policy(connection, module)
    else:
        delete_scaling_policy(connection, module)


if __name__ == '__main__':
    main()
