#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['experimental'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: sts_caller_identity
short_description: Obtain the account id from the AWS Security Token Service
description:
    - Obtain the AWS account id from the AWS Security Token Service
version_added: "2.9"
author: Jeremy Christian (@jchristi)
options:
requirements:
    - boto3
    - botocore
    - python >= 2.6
'''

RETURN = """
sts_caller_identity:
    description: The Identity object returned by the AWS Security Token Service
    returned: always
    type: dict
    sample:
        UserId: string
        Account: string
        Arn: string
changed:
    description: False
    type: bool
    returned: always
"""


EXAMPLES = '''
'''

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (boto3_conn,
                                      ec2_argument_spec,
                                      get_aws_connection_info,
                                      AWSRetry)


@AWSRetry.jittered_backoff(retries=5, delay=2, max_delay=20)
def get_caller_identity(conn):
    return conn.get_caller_identity()

def main():
    argument_spec = ec2_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required.')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if region:
        connection = boto3_conn(module, conn_type='client', resource='sts', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    else:
        module.fail_json(msg="region must be specified")

    try:
        response = get_caller_identity(connection)
    except ClientError as e:
        module.fail_json(msg=e)

    sts_caller_id = {
        'Account': response.get('Account'),
        'Arn': response.get('Arn'),
        'UserId': response.get('UserId')
    }

    module.exit_json(changed=False, sts_caller_id=sts_caller_id)


if __name__ == '__main__':
    main()
