#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
module: aws_region_facts
short_description: Gather facts about AWS regions.
description:
    - Gather facts about AWS regions.
version_added: '2.4'
author: 'Henrique Rodrigues (github.com/Sodki)'
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See \
      U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRegions.html) for \
      possible filters. Filter names and values are case sensitive. You can also use underscores (_) \
      instead of dashes (-) in the filter keys, which will take precedence in case of conflict.
    required: false
    default: {}
extends_documentation_fragment:
    - aws
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
    description: >
        Regions that match the provided filters. Each element consists of a dict with all the information related
        to that region.
    type: list
    sample: "[{
        'endpoint': 'ec2.us-west-1.amazonaws.com',
        'region_name': 'us-west-1'
    }]"
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec, boto3_conn
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, camel_dict_to_snake_dict, HAS_BOTO3

try:
    from botocore.exceptions import ClientError
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

    if region:
        connection = boto3_conn(
            module,
            conn_type='client',
            resource='ec2',
            region=region,
            endpoint=ec2_url,
            **aws_connect_params
        )
    else:
        module.fail_json(msg='region must be specified')

    # Replace filter key underscores with dashes, for compatibility
    sanitized_filters = dict((k.replace('_', '-'), v) for k,v in module.params.get('filters').items())

    try:
        regions = connection.describe_regions(
            Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    module.exit_json(regions=[camel_dict_to_snake_dict(r) for r in regions['Regions']])


if __name__ == '__main__':
    main()
