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

DOCUMENTATION = '''
---
module: iam_mfa_device_facts
short_description: List the MFA (Multi-Factor Authentication) devices registered for a user
description:
    - List the MFA (Multi-Factor Authentication) devices registered for a user
version_added: "2.2"
author: Victor Costan (@pwnall)
options:
  user_name:
    description:
      - The name of the user whose MFA devices will be listed
    required: false
    default: null
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

# List MFA devices (more details: http://docs.aws.amazon.com/IAM/latest/APIReference/API_ListMFADevices.html)
iam_mfa_device_facts:
register: mfa_devices

# Assume an existing role (more details: http://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
sts_assume_role:
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

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if region:
        connection = boto3_conn(module, conn_type='client', resource='iam', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    else:
        module.fail_json(msg="region must be specified")

    list_mfa_devices(connection, module)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
