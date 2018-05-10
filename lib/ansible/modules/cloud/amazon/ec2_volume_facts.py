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
module: ec2_volume_facts
short_description: Gather facts about ec2 volumes in AWS
description:
  - Gather facts about ec2 volumes in AWS
version_added: '2.6'
author: Rob White (@wimnat)
requirements: [ boto3, botocore ]
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html) for possible filters.
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all volumes
- ec2_vol_facts:

# Gather facts about a particular volume using volume ID
- ec2_vol_facts:
    filters:
      volume-id: vol-00112233

# Gather facts about any volume with a tag key Name and value Example
- ec2_vol_facts:
    filters:
      "tag:Name": Example

# Gather facts about any volume that is attached
- ec2_vol_facts:
    filters:
      attachment.status: attached

'''

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''

from copy import copy

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry, ansible_dict_to_boto3_filter_list, boto3_tag_list_to_ansible_dict
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by AnsibleAWSModule


def format_volume_info(volume):
    volume_info = camel_dict_to_snake_dict(volume, ignore_list=['Tags'])
    if 'tags' in volume_info:
        volume_info['tags'] = boto3_tag_list_to_ansible_dict(volume_info['tags'])
    else:
        volume_info['tags'] = {}

    return volume_info


@AWSRetry.jittered_backoff()
def _get_volumes(ec2, filters):
    paginator = ec2.get_paginator('describe_volumes')
    return paginator.paginate(Filters=filters).search('Volumes[]')


def main():
    argument_spec = dict(
        filters=dict(default={}, type='dict')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        ec2 = module.client('ec2')
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to connect to EC2')

    volumes = _get_volumes(ec2, ansible_dict_to_boto3_filter_list(module.params['filters']))
    formatted_volumes = [format_volume_info(v) for v in volumes]

    module.exit_json(volumes=formatted_volumes)


if __name__ == '__main__':
    main()
