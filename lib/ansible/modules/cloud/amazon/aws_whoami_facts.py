#!/usr/bin/python

# Copyright: (c) 2018, Jonathan I. Davila <jonathan@davila.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: aws_whoami_facts
short_description: detemine the currently authenticated IAM user or role
description:
    - Expose the currently authenticated IAM user or role as an Ansible fact.
    - This module will always attempt to get an IAM user first.
    - If a role is detected as a result of trying to get the user then it will try to get the role.
notes:
    - The user/role must have permissions in IAM to describe users and/or roles or this module will not return anything
version_added: 2.7
requirements: [ 'botocore', 'boto3' ]
author: Jonathan I. Davila (@defionscode)
extends_documentation_fragment:
    - aws
    - ec2
'''


EXAMPLES = r'''
# Get the IAM authorized user of the Ansible control machine

- name: Get AWS Whoami facts
  aws_whoami_facts:
  delegate_to: localhost

# Get the IAM role of the EC2 instance
- name: Get AWS Whoami facts
  aws_whoami_facts:

# Show the username of the IAM user
- name: Debug IAM username
  debug:
      var: aws_iam_user['user_name']
'''


RETURN = r'''
ansible_facts:
  returned: always
  type: complex
  description: Base ansible facts dict
  contains:
    aws_iam_role:
      description: The AWS IAM role object
      returned: when running inside an ec2 instance that has an associate IAM role
      type: complex
      contains:
        arn:
          description: The ARN of the IAM role
          returned: when aws_iam_role is returned
          type: string
          sample: arn:aws:iam::1234567890:role/read-only
        assume_role_policy_document:
          description: The policy document for assume role privileges
          returned: when aws_iam_role is returned
          type: complex
          sample:
              statement:
                  - action: "sts:AssumeRole"
                    effect: Allow
                    principal:
                        service: ec2.amazonaws.com
              version: 2012-10-17
        create_date:
          description: The date the IAM role was created
          returned: when aws_iam_role is returned
          type: string
          sample: '2017-05-17T15:49:57+00:00'
        description:
          description: The role's description
          returned: when aws_iam_role is returned
          type: string
          sample: "Allows EC2 instanes to call AWS services on your behalf"
        max_sesson_duration:
          description: The length of time, in seconds, of how long an individual session can last for.
          returned: when aws_iam_role is returned
          type: integer
          sample: 3600
        path:
          description: The IAM path for the role
          returned: when aws_iam_role is returned
          type: string
          sample: /
        role_id:
          description: The identifier for the IAM role
          returned: when aws_iam_user is returned
          type: string
          sample: AXXXXZZDDDQIXXXA
        role_name:
          description: The human-friendly username of the IAM role
          returned: when aws_iam_role is returned
          type: string
          sample: s3upload

    aws_iam_user:
      description: The AWS IAM user object
      returned: When AWS IAM credentials are identified NOT ran on an ec2 instance with an associated role
      type: complex
      contains:
        arn:
          description: The ARN of the IAM user
          returned: when aws_iam_user is returned
          type: string
          sample: arn:aws:iam::1234567890:user/mr_peanut
        create_date:
          description: The date the IAM user was created
          returned: when aws_iam_user is returned
          type: string
          sample: '2017-05-17T15:49:57+00:00'
        password_last_used:
          description: The date stamp of the last successful auth via password by the IAM user
          returned: when aws_iam_user is returned
          type: string
          sample: '2018-07-03T12:50:17+00:00'
        path:
          description: The IAM path for the user
          returned: when aws_iam_user is returned
          type: string
          sample: /
        user_id:
          description: The identifier for the IAM user
          returned: when aws_iam_user is returned
          type: string
          sample: AXXXXXXXXXXXA
        user_name:
          description: The human-friendly username of the IAM user
          returned: when aws_iam_user is returned
          type: string
          sample: mr_peanut
'''


try:
    import botocore
    from botocore.exceptions import ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.urls import Request
import json


def get_role(client):
    r = Request()
    role_meta = r.open('GET', 'http://169.254.169.254/latest/meta-data/iam/info').read().decode('utf-8')
    role_meta_json = json.loads(role_meta)
    try:
        role_arn = role_meta_json['InstanceProfileArn']
        role_data = client.get_role(RoleName=role_arn.split('/')[-1])
        return camel_dict_to_snake_dict(role_data['Role'])
    except KeyError:
        # No instance profile so no role to report in results
        return None
    except ClientError as e:
        raise e


def get_user(client):
    try:
        user_data = client.get_user()
        return camel_dict_to_snake_dict(user_data.get('User'))
    except ClientError as e:
        if 'Must specify userName' in e.response['Error']['Message']:
            # Means we probably have a role
            return None
        else:
            raise e


def main():
    module = AnsibleAWSModule(argument_spec=dict())
    client = module.client('iam')

    try:
        result = get_user(client)
    except Exception as e:
        module.fail_json_aws(e, msg="Error in trying invoke the IAM API to get user information")

    if result:
        module.exit_json(ansible_facts=dict(aws_iam_user=result))
    else:
        try:
            result = get_role(client)
        except Exception as e:
            module.fail_json_aws(e, msg="Unable to get role information")

    if result:
        module.exit_json(ansible_facts=dict(aws_iam_role=result))
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
