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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: elb_target
short_description: Manage a target in a target group
description:
    - Used to register or deregister a target in a target group
version_added: "2.4"
author: "Rob White (@wimnat)"
options:
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

# Register a target to a target group
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
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info)

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def convert_tg_name_to_arn(connection, module, tg_name):

    try:
        response = connection.describe_target_groups(Names=[tg_name])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

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
        return connection.describe_target_health(TargetGroupArn=tg_arn, Targets=target)['TargetHealthDescriptions'][0]
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def register_target(connection, module):

    """
    Registers a target to a target group

    :param module: ansible module object
    :param connection: boto3 connection
    :return:
    """

    target_group_arn = module.params.get("target_group_arn")
    target_id = module.params.get("target_id")
    target_port = module.params.get("target_port")
    changed = False

    if not target_group_arn:
        target_group_arn = convert_tg_name_to_arn(connection, module, module.params.get("target_group_name"))

    target = dict(Id=target_id)
    if target_port:
        target['Port'] = target_port

    try:
        target_description = describe_targets(connection, module, target_group_arn, [target])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if target_description['TargetHealth']['Reason'] == "Target.NotRegistered":
        try:
            connection.register_targets(TargetGroupArn=target_group_arn, Targets=[target])
            changed = True
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

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

    target_group_arn = module.params.get("target_group_arn")
    target_id = module.params.get("target_id")
    target_port = module.params.get("target_port")
    changed = False

    if not target_group_arn:
        target_group_arn = convert_tg_name_to_arn(connection, module, module.params.get("target_group_name"))

    target = dict(Id=target_id)
    if target_port:
        target['Port'] = target_port

    try:
        target_description = describe_targets(connection, module, target_group_arn, [target])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if target_description['TargetHealth']['Reason'] != "Target.NotRegistered":
        try:
            connection.deregister_targets(TargetGroupArn=target_group_arn, Targets=[target])
            changed = True
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Get all targets for the target group
    target_descriptions = describe_targets(connection, module, target_group_arn, [])

    module.exit_json(changed=changed, target_health_descriptions=camel_dict_to_snake_dict(target_descriptions), target_group_arn=target_group_arn)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            target_group_arn=dict(type='str'),
            target_group_name=dict(type='str'),
            target_id=dict(type='str', required=True),
            target_port=dict(type='int'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=['target_group_arn', 'target_group_name']
                           )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='elbv2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    state = module.params.get("state")

    if state == 'present':
        register_target(connection, module)
    else:
        deregister_target(connection, module)

if __name__ == '__main__':
    main()
