#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_s3_bucket_facts
short_description: Lists S3 buckets in AWS
requirements:
  - boto3 >= 1.4.4
  - python >= 2.6
description:
    - Lists S3 buckets in AWS
version_added: "2.4"
author: "Gerben Geijteman (@hyperized)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Note: Only AWS S3 is currently supported

# Lists all s3 buckets
- aws_s3_bucket_facts:
'''

RETURN = '''
buckets:
  description: "List of buckets"
  returned: always
  sample:
    - creation_date: 2017-07-06 15:05:12 +00:00
      name: my_bucket
  type: list
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, HAS_BOTO3, camel_dict_to_snake_dict, \
    get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def get_bucket_list(module, connection):
    """
    Return result of list_buckets json encoded
    :param module:
    :param connection:
    :return:
    """
    try:
        buckets = camel_dict_to_snake_dict(connection.list_buckets())['buckets']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    return buckets


def main():
    """
    Get list of S3 buckets
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

    # Set up connection
    if region:
        try:
            connection = boto3_conn(module, conn_type='client', resource='s3', region=region, endpoint=ec2_url,
                                    **aws_connect_params)
        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ProfileNotFound) as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    else:
        module.fail_json(msg="AWS region must be specified (like: us-east-1)")

    # Gather results
    result['buckets'] = get_bucket_list(module, connection)

    # Send exit
    module.exit_json(msg="Retrieved s3 facts.", ansible_facts=result)


if __name__ == '__main__':
    main()
