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
module: scalable_target
short_description: Manage Application Auto Scaling Scalable Targets
notes:
    - for details of the parameters and returns see
      U(http://boto3.readthedocs.io/en/latest/reference/services/application-autoscaling.html#ApplicationAutoScaling.Client.register_scalable_target)
description:
    - Creates, updates or removes a Scalable Target
version_added: "2.5"
author:
    - Gustavo Maia(@gurumaia)
requirements: [ json, botocore, boto3 ]
options:
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
    min_capacity:
        description: The minimum value to scale to in response to a scale in event. Required if I(state) is C(present).
        required: no
    max_capacity:
        description: The maximum value to scale to in response to a scale out event. Required if I(state) is C(present).
        required: no
    role_arn:
        description: The ARN of an IAM role that allows Application Auto Scaling to modify the scalable target on your behalf.
            Required if I(state) is C(present).
        required: no
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create scalable target for ECS Service
- name: scalable target
  scalable_target:
    state: present
    service_namespace: ecs
    resource_id: service/cluster-name/service-name
    scalable_dimension: ecs:service:DesiredCount
    min_capacity: 1
    max_capacity: 2
    role_arn: arn:aws:iam::123456789123:role/roleName

# Remove scalable target for ECS Service
- name: scalable target
  scalable_target:
    state: absent
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


def delete_scalable_target(connection, module):
    changed = False
    scalable_target = connection.describe_scalable_targets(
        ServiceNamespace=module.params.get('service_namespace'),
        ResourceIds=[module.params.get('resource_id')],
        ScalableDimension=module.params.get('scalable_dimension'),
        MaxResults=1
    )

    if scalable_target['ScalableTargets']:
        try:
            connection.deregister_scalable_target(
                ServiceNamespace=module.params.get('service_namespace'),
                ResourceId=module.params.get('resource_id'),
                ScalableDimension=module.params.get('scalable_dimension')
            )
            changed = True
        except Exception as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    module.exit_json(changed=changed)


def create_scalable_target(connection, module):
    scalable_target = connection.describe_scalable_targets(
        ServiceNamespace=module.params.get('service_namespace'),
        ResourceIds=[module.params.get('resource_id')],
        ScalableDimension=module.params.get('scalable_dimension'),
        MaxResults=1
    )

    changed = False

    if scalable_target['ScalableTargets']:
        scalable_target = scalable_target['ScalableTargets'][0]
        # check if the input parameters are equal to what's already configured
        for attr in ('ServiceNamespace', 'ResourceId', 'ScalableDimension', 'MinCapacity', 'MaxCapacity', 'RoleARN'):
            if scalable_target[attr] != module.params.get(_camel_to_snake(attr)):
                changed = True
                scalable_target[attr] = module.params.get(_camel_to_snake(attr))
    else:
        changed = True
        scalable_target = {
            'ServiceNamespace': module.params.get('service_namespace'),
            'ResourceId': module.params.get('resource_id'),
            'ScalableDimension': module.params.get('scalable_dimension'),
            'MinCapacity': module.params.get('min_capacity'),
            'MaxCapacity': module.params.get('max_capacity'),
            'RoleARN': module.params.get('role_arn')
        }

    if changed:
        try:
            connection.register_scalable_target(
                ServiceNamespace=scalable_target['ServiceNamespace'],
                ResourceId=scalable_target['ResourceId'],
                ScalableDimension=scalable_target['ScalableDimension'],
                MinCapacity=scalable_target['MinCapacity'],
                MaxCapacity=scalable_target['MaxCapacity'],
                RoleARN=scalable_target['RoleARN']
            )
        except Exception as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    try:
        response = connection.describe_scalable_targets(
            ServiceNamespace=scalable_target['ServiceNamespace'],
            ResourceIds=[scalable_target['ResourceId']],
            ScalableDimension=scalable_target['ScalableDimension'],
            MaxResults=1
        )
        snaked_response = camel_dict_to_snake_dict(response['ScalableTargets'][0])
    except Exception as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    module.exit_json(changed=changed, response=snaked_response)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent'], type='str'),
        service_namespace=dict(required=True, choices=['ecs', 'elasticmapreduce', 'ec2', 'appstream', 'dynamodb'], type='str'),
        resource_id=dict(required=True, type='str'),
        scalable_dimension=dict(required=True, choices=['ecs:service:DesiredCount',
                                                        'ec2:spot-fleet-request:TargetCapacity',
                                                        'elasticmapreduce:instancegroup:InstanceCount',
                                                        'appstream:fleet:DesiredCapacity',
                                                        'dynamodb:table:ReadCapacityUnits',
                                                        'dynamodb:table:WriteCapacityUnits',
                                                        'dynamodb:index:ReadCapacityUnits',
                                                        'dynamodb:index:WriteCapacityUnits'], type='str'),
        min_capacity=dict(required=False, type='int'),
        max_capacity=dict(required=False, type='int'),
        role_arn=dict(required=False, type='str')
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
        create_scalable_target(connection, module)
    else:
        delete_scalable_target(connection, module)


if __name__ == '__main__':
    main()
