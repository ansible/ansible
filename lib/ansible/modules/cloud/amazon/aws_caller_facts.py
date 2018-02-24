#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aws_caller_facts
short_description: Get facts about the user and account being used to make AWS calls.
description:
    - This module returns information about the accont and user / role that the AWS access tokens are from.
    - The primary use of this is to get the account id for templating into ARNs or similar to avoid needing to specify this information in inventory.
version_added: "2.6"

author: Ed Costello    (@orthanc)

requirements: [ 'botocore', 'boto3' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Get the current caller identity facts
  aws_caller_facts:
  register: caller_facts
'''

RETURN = '''
account:
    description: The account id the access credentials are associated with.
    returned: success
    type: string
    sample: "123456789012"
arn:
    description: The arn identifying the user the credentials are associated with.
    returned: success
    type: string
    sample: arn:aws:sts::123456789012:federated-user/my-federated-user-name
user_id:
    description: |
        The user id the access credentials are associated with. Note that this may not correspond to
        anything you can look up in the case of roles or federated identities.
    returned: success
    type: string
    sample: 123456789012:my-federated-user-name
error:
    description: The details of the error response from AWS.
    returned: on client error from AWS
    type: complex
    sample: {
        "code": "InvalidParameterValue",
        "message": "Feedback notification topic is not set.",
        "type": "Sender"
    }
    contains:
        code:
            description: The AWS error code.
            type: string
        message:
            description: The AWS error message.
            type: string
        type:
            description: The AWS error type.
            type: string
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, ec2_argument_spec, get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import HAS_BOTO3

import traceback

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def main():
    argument_spec = ec2_argument_spec()
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    client = boto3_conn(module, conn_type='client', resource='sts', region=region, endpoint=ec2_url, **aws_connect_params)

    try:
        caller_identity = client.get_caller_identity()
        module.exit_json(
            changed=False,
            **camel_dict_to_snake_dict(caller_identity)
        )
    except ClientError as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except BotoCoreError as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
