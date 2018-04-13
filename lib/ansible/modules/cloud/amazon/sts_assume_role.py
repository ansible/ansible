#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: sts_assume_role
short_description: Assume a role using AWS Security Token Service and obtain temporary credentials
description:
    - Assume a role using AWS Security Token Service and obtain temporary credentials
version_added: "2.0"
author:
    - Boris Ekelchik (@bekelchik)
    - Marek Piatek (@piontas)
options:
  role_arn:
    description:
      - The Amazon Resource Name (ARN) of the role that the caller is
        assuming (http://docs.aws.amazon.com/IAM/latest/UserGuide/Using_Identifiers.html#Identifiers_ARNs)
    required: true
  role_session_name:
    description:
      - Name of the role's session - will be used by CloudTrail
    required: true
  policy:
    description:
      - Supplemental policy to use in addition to assumed role's policies.
  duration_seconds:
    description:
      - The duration, in seconds, of the role session. The value can range from 900 seconds (15 minutes) to 3600 seconds (1 hour).
        By default, the value is set to 3600 seconds.
  external_id:
    description:
      - A unique identifier that is used by third parties to assume a role in their customers' accounts.
  mfa_serial_number:
    description:
      - The identification number of the MFA device that is associated with the user who is making the AssumeRole call.
  mfa_token:
    description:
      - The value provided by the MFA device, if the trust policy of the role being assumed requires MFA.
notes:
  - In order to use the assumed role in a following playbook task you must pass the access_key, access_secret and access_token
extends_documentation_fragment:
    - aws
    - ec2
requirements:
    - boto3
    - botocore
    - python >= 2.6
'''

RETURN = '''
sts_creds:
    description: The temporary security credentials, which include an access key ID, a secret access key, and a security (or session) token
    returned: always
    type: dict
    sample:
      access_key: XXXXXXXXXXXXXXXXXXXX
      expiration: 2017-11-11T11:11:11+00:00
      secret_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      session_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
sts_user:
    description: The Amazon Resource Name (ARN) and the assumed role ID
    returned: always
    type: dict
    sample:
      assumed_role_id: arn:aws:sts::123456789012:assumed-role/demo/Bob
      arn: ARO123EXAMPLE123:Bob
changed:
    description: True if obtaining the credentials succeeds
    type: bool
    returned: always
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Assume an existing role (more details: http://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
sts_assume_role:
  role_arn: "arn:aws:iam::123456789012:role/someRole"
  role_session_name: "someRoleSession"
register: assumed_role

# Use the assumed role above to tag an instance in account 123456789012
ec2_tag:
  aws_access_key: "{{ assumed_role.sts_creds.access_key }}"
  aws_secret_key: "{{ assumed_role.sts_creds.secret_key }}"
  security_token: "{{ assumed_role.sts_creds.session_token }}"
  resource: i-xyzxyz01
  state: present
  tags:
    MyNewTag: value

'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (boto3_conn, get_aws_connection_info,
                                      ec2_argument_spec, camel_dict_to_snake_dict)

try:
    from botocore.exceptions import ClientError, ParamValidationError
except ImportError:
    pass  # caught by imported AnsibleAWSModule


def _parse_response(response):
    credentials = response.get('Credentials', {})
    user = response.get('AssumedRoleUser', {})

    sts_cred = {
        'access_key': credentials.get('AccessKeyId'),
        'secret_key': credentials.get('SecretAccessKey'),
        'session_token': credentials.get('SessionToken'),
        'expiration': credentials.get('Expiration')

    }
    sts_user = camel_dict_to_snake_dict(user)
    return sts_cred, sts_user


def assume_role_policy(connection, module):
    params = {
        'RoleArn': module.params.get('role_arn'),
        'RoleSessionName': module.params.get('role_session_name'),
        'Policy': module.params.get('policy'),
        'DurationSeconds': module.params.get('duration_seconds'),
        'ExternalId': module.params.get('external_id'),
        'SerialNumber': module.params.get('mfa_serial_number'),
        'TokenCode': module.params.get('mfa_token')
    }
    changed = False

    kwargs = dict((k, v) for k, v in params.items() if v is not None)

    try:
        response = connection.assume_role(**kwargs)
        changed = True
    except (ClientError, ParamValidationError) as e:
        module.fail_json_aws(e)

    sts_cred, sts_user = _parse_response(response)
    module.exit_json(changed=changed, sts_creds=sts_cred, sts_user=sts_user)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            role_arn=dict(required=True, default=None),
            role_session_name=dict(required=True, default=None),
            duration_seconds=dict(required=False, default=None, type='int'),
            external_id=dict(required=False, default=None),
            policy=dict(required=False, default=None),
            mfa_serial_number=dict(required=False, default=None),
            mfa_token=dict(required=False, default=None)
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='sts',
                                region=region, endpoint=ec2_url, **aws_connect_kwargs)

    else:
        module.fail_json(msg="region must be specified")

    assume_role_policy(connection, module)


if __name__ == '__main__':
    main()
