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
module: iam_mfa_device_info
short_description: List the MFA (Multi-Factor Authentication) devices registered for a user
description:
    - List the MFA (Multi-Factor Authentication) devices registered for a user
    - This module was called C(iam_mfa_device_facts) before Ansible 2.9. The usage did not change.
version_added: "2.2"
author: Victor Costan (@pwnall)
options:
  user_name:
    description:
      - The name of the user whose MFA devices will be listed
    type: str
extends_documentation_fragment:
    - aws
    - ec2
requirements:
    - boto3
    - botocore
'''

RETURN = """
mfa_devices:
    description: The MFA devices registered for the given user
    returned: always
    type: list
    sample:
      - enable_date: "2016-03-11T23:25:36+00:00"
        serial_number: arn:aws:iam::085120003701:mfa/pwnall
        user_name: pwnall
      - enable_date: "2016-03-11T23:25:37+00:00"
        serial_number: arn:aws:iam::085120003702:mfa/pwnall
        user_name: pwnall
"""

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# List MFA devices (more details: https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListMFADevices.html)
- iam_mfa_device_info:
  register: mfa_devices

# Assume an existing role (more details: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- sts_assume_role:
    mfa_serial_number: "{{ mfa_devices.mfa_devices[0].serial_number }}"
    role_arn: "arn:aws:iam::123456789012:role/someRole"
    role_session_name: "someRoleSession"
  register: assumed_role
'''

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, camel_dict_to_snake_dict, ec2_argument_spec,
                                      get_aws_connection_info)


def list_mfa_devices(connection, module):
    user_name = module.params.get('user_name')
    changed = False

    args = {}
    if user_name is not None:
        args['UserName'] = user_name
    try:
        response = connection.list_mfa_devices(**args)
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            user_name=dict(required=False, default=None)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)
    if module._name == 'iam_mfa_device_facts':
        module.deprecate("The 'iam_mfa_device_facts' module has been renamed to 'iam_mfa_device_info'", version='2.13')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if region:
        connection = boto3_conn(module, conn_type='client', resource='iam', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    else:
        module.fail_json(msg="region must be specified")

    list_mfa_devices(connection, module)


if __name__ == '__main__':
    main()
