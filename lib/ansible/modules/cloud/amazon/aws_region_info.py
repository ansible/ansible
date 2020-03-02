#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
module: aws_region_info
short_description: Gather information about AWS regions.
description:
    - Gather information about AWS regions.
    - This module was called C(aws_region_facts) before Ansible 2.9. The usage did not change.
version_added: '2.5'
author: 'Henrique Rodrigues (@Sodki)'
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRegions.html) for
        possible filters. Filter names and values are case sensitive. You can also use underscores
        instead of dashes (-) in the filter keys, which will take precedence in case of conflict.
    default: {}
    type: dict
extends_documentation_fragment:
    - aws
    - ec2
requirements: [botocore, boto3]
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all regions
- aws_region_info:

# Gather information about a single region
- aws_region_info:
    filters:
      region-name: eu-west-1
'''

RETURN = '''
regions:
    returned: on success
    description: >
        Regions that match the provided filters. Each element consists of a dict with all the information related
        to that region.
    type: list
    sample: "[{
        'endpoint': 'ec2.us-west-1.amazonaws.com',
        'region_name': 'us-west-1'
    }]"
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry, ansible_dict_to_boto3_filter_list, camel_dict_to_snake_dict

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule


def main():
    argument_spec = dict(
        filters=dict(default={}, type='dict')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)
    if module._name == 'aws_region_facts':
        module.deprecate("The 'aws_region_facts' module has been renamed to 'aws_region_info'", version='2.13')

    connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    # Replace filter key underscores with dashes, for compatibility
    sanitized_filters = dict((k.replace('_', '-'), v) for k, v in module.params.get('filters').items())

    try:
        regions = connection.describe_regions(
            Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe regions.")

    module.exit_json(regions=[camel_dict_to_snake_dict(r) for r in regions['Regions']])


if __name__ == '__main__':
    main()
