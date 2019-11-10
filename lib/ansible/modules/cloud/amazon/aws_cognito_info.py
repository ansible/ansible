#!/usr/bin/python
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_cognito_info
short_description: Lists cognito user pools in AWS
requirements:
  - boto3 >= 1.4.4
  - python >= 3.0
description:
    - Lists cognito pools
version_added: "2.10"
author: "Anton Tokarev (@t1bur1an)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Note: Only list of AWS Cognito pools is currently supported and maximum 60 results.

# Lists all congito user pools
- aws_cognito_info:
  register: result

- name: List user pools
  debug:
    msg: "{{ result['userpools'] }}"
'''

RETURN = '''
userpools:
  description: "List of user pools"
  returned: always
  sample:
    - creation_date: "2019-09-30T10:23:46.365000+03:00"
      id: "us-east-1_123456"
      lambda_config: {
        post_authentication: "arn",
        post_confirmation: "arn",
        pre_authentication: "arn",
        pre_sign_up: "arn",
        pre_token_generation: "arn"
        }
      last_modified_date: "2019-09-30T10:23:46.365000+03:00"
      name: myPool
  type: list
'''

import traceback

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.ec2 import (boto3_conn, ec2_argument_spec, HAS_BOTO3, camel_dict_to_snake_dict,
                                      get_aws_connection_info)


def get_userpools_list(module, connection):
    """
    Return result of userpools json encoded
    :param module:
    :param connection:
    :return:
    """
    try:
        userpools = camel_dict_to_snake_dict(connection.list_user_pools(MaxResults=60))['user_pools']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    return userpools


def main():
    """
    Get list of User Pools
    :return:
    """

    # Ensure we have an empty dict
    result = {}

    # Including ec2 argument spec
    module = AnsibleModule(argument_spec=ec2_argument_spec(), supports_check_mode=True)

    # Verify Boto3 is used
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    # Set up connection
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=HAS_BOTO3)
    connection = boto3_conn(module, conn_type='client', resource='cognito-idp', region=region, endpoint=ec2_url,
                            **aws_connect_params)

    # Gather results
    result['userpools'] = get_userpools_list(module, connection)

    # Send exit
    module.exit_json(msg="Retrieved cognito info.", **result)


if __name__ == '__main__':
    main()
