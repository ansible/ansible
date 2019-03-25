#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: s3_logging
short_description: Manage logging facility of an s3 bucket in AWS
description:
    - Manage logging facility of an s3 bucket in AWS
version_added: "2.0"
author: Rob White (@wimnat)
options:
  name:
    description:
      - "Name of the s3 bucket."
    required: true
  state:
    description:
      - "Enable or disable logging."
    default: present
    choices: [ 'present', 'absent' ]
  target_bucket:
    description:
      - "The bucket to log to. Required when state=present."
  target_prefix:
    description:
      - "The prefix that should be prepended to the generated log files written to the target_bucket."
    default: ""
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Enable logging of s3 bucket mywebsite.com to s3 bucket mylogs
  s3_logging:
    name: mywebsite.com
    target_bucket: mylogs
    target_prefix: logs/mywebsite.com
    state: present

- name: Remove logging on an s3 bucket
  s3_logging:
    name: mywebsite.com
    state: absent

'''

try:
    import boto.ec2
    from boto.s3.connection import OrdinaryCallingFormat, Location
    from boto.exception import S3ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import AnsibleAWSError, ec2_argument_spec, get_aws_connection_info


def compare_bucket_logging(bucket, target_bucket, target_prefix):

    bucket_log_obj = bucket.get_logging_status()
    if bucket_log_obj.target != target_bucket or bucket_log_obj.prefix != target_prefix:
        return False
    else:
        return True


def enable_bucket_logging(connection, module):

    bucket_name = module.params.get("name")
    target_bucket = module.params.get("target_bucket")
    target_prefix = module.params.get("target_prefix")
    changed = False

    try:
        bucket = connection.get_bucket(bucket_name)
    except S3ResponseError as e:
        module.fail_json(msg=e.message)

    try:
        if not compare_bucket_logging(bucket, target_bucket, target_prefix):
            # Before we can enable logging we must give the log-delivery group WRITE and READ_ACP permissions to the target bucket
            try:
                target_bucket_obj = connection.get_bucket(target_bucket)
            except S3ResponseError as e:
                if e.status == 301:
                    module.fail_json(msg="the logging target bucket must be in the same region as the bucket being logged")
                else:
                    module.fail_json(msg=e.message)
            target_bucket_obj.set_as_logging_target()

            bucket.enable_logging(target_bucket, target_prefix)
            changed = True

    except S3ResponseError as e:
        module.fail_json(msg=e.message)

    module.exit_json(changed=changed)


def disable_bucket_logging(connection, module):

    bucket_name = module.params.get("name")
    changed = False

    try:
        bucket = connection.get_bucket(bucket_name)
        if not compare_bucket_logging(bucket, None, None):
            bucket.disable_logging()
            changed = True
    except S3ResponseError as e:
        module.fail_json(msg=e.message)

    module.exit_json(changed=changed)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            target_bucket=dict(required=False, default=None),
            target_prefix=dict(required=False, default=""),
            state=dict(required=False, default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region in ('us-east-1', '', None):
        # S3ism for the US Standard region
        location = Location.DEFAULT
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region
    try:
        connection = boto.s3.connect_to_region(location, is_secure=True, calling_format=OrdinaryCallingFormat(), **aws_connect_params)
        # use this as fallback because connect_to_region seems to fail in boto + non 'classic' aws accounts in some cases
        if connection is None:
            connection = boto.connect_s3(**aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
        module.fail_json(msg=str(e))

    state = module.params.get("state")

    if state == 'present':
        enable_bucket_logging(connection, module)
    elif state == 'absent':
        disable_bucket_logging(connection, module)


if __name__ == '__main__':
    main()
