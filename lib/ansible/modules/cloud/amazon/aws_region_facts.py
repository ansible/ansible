#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
module: aws_region_facts
short_description: Gather facts about AWS regions.
description:
    - Gather facts about AWS regions.
version_added: '2.5'
author: 'Henrique Rodrigues (github.com/Sodki)'
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRegions.html) for
        possible filters. Filter names and values are case sensitive. You can also use underscores
        instead of dashes (-) in the filter keys, which will take precedence in case of conflict.
    default: {}
extends_documentation_fragment:
    - aws
    - ec2
requirements: [botocore, boto3]
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all regions
- aws_region_facts:

# Gather facts about a single region
- aws_region_facts:
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


import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec, boto3_conn
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, camel_dict_to_snake_dict, HAS_BOTO3

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(
        module,
        conn_type='client',
        resource='ec2',
        region=region,
        endpoint=ec2_url,
        **aws_connect_params
    )

    # Replace filter key underscores with dashes, for compatibility
    sanitized_filters = dict((k.replace('_', '-'), v) for k, v in module.params.get('filters').items())

    try:
        regions = connection.describe_regions(
            Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except ClientError as e:
        module.fail_json(msg="Unable to describe regions: {0}".format(to_native(e)),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except BotoCoreError as e:
        module.fail_json(msg="Unable to describe regions: {0}".format(to_native(e)),
                         exception=traceback.format_exc())

    module.exit_json(regions=[camel_dict_to_snake_dict(r) for r in regions['Regions']])


if __name__ == '__main__':
    main()
