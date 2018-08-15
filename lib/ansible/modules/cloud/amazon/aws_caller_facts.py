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
    - This module returns information about the account and user / role from which the AWS access tokens originate.
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
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def main():
    module = AnsibleAWSModule(
        argument_spec={},
        supports_check_mode=True,
    )

    client = module.client('sts')

    try:
        caller_identity = client.get_caller_identity()
        caller_identity.pop('ResponseMetadata', None)
        module.exit_json(
            changed=False,
            **camel_dict_to_snake_dict(caller_identity)
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to retrieve caller identity')


if __name__ == '__main__':
    main()
