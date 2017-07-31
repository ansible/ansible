#!/usr/bin/python
#
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
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: ec2_vpc_net_facts
short_description: Gather facts about ec2 VPCs in AWS
description:
    - Gather facts about ec2 VPCs in AWS
version_added: "2.1"
author: "Rob White (@wimnat)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcs.html) for possible filters.
    required: false
    default: null

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all VPCs
- ec2_vpc_net_facts:

# Gather facts about a particular VPC using VPC ID
- ec2_vpc_net_facts:
    filters:
      vpc-id: vpc-00112233

# Gather facts about any VPC with a tag key Name and value Example
- ec2_vpc_net_facts:
    filters:
      "tag:Name": Example

'''
import traceback

try:
    import boto.vpc
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import connect_to_aws, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils._text import to_native


def get_vpc_info(vpc):

    try:
        classic_link = vpc.classic_link_enabled
    except AttributeError:
        classic_link = False

    vpc_info = { 'id': vpc.id,
                 'instance_tenancy': vpc.instance_tenancy,
                 'classic_link_enabled': classic_link,
                 'dhcp_options_id': vpc.dhcp_options_id,
                 'state': vpc.state,
                 'is_default': vpc.is_default,
                 'cidr_block': vpc.cidr_block,
                 'tags': vpc.tags
               }

    return vpc_info

def list_ec2_vpcs(connection, module):

    filters = module.params.get("filters")
    vpc_dict_array = []

    try:
        all_vpcs = connection.get_all_vpcs(filters=filters)
    except BotoServerError as e:
        module.fail_json(msg=e.message)

    for vpc in all_vpcs:
        vpc_dict_array.append(get_vpc_info(vpc))

    module.exit_json(vpcs=vpc_dict_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters = dict(default=None, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, Exception) as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_vpcs(connection, module)


if __name__ == '__main__':
    main()
