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

DOCUMENTATION = '''
---
module: ec2_vpc_subnet_facts
short_description: Gather facts about ec2 VPC subnets in AWS
description:
    - Gather facts about ec2 VPC subnets in AWS
version_added: "2.1"
author: "Rob White (@wimnat)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSubnets.html) for possible filters.
    required: false
    default: null
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all VPC subnets
- ec2_vpc_subnet_facts:

# Gather facts about a particular VPC subnet using ID
- ec2_vpc_subnet_facts:
    filters:
      subnet-id: subnet-00112233

# Gather facts about any VPC subnet with a tag key Name and value Example
- ec2_vpc_subnet_facts:
    filters:
      "tag:Name": Example

# Gather facts about any VPC subnet within VPC with ID vpc-abcdef00
- ec2_vpc_subnet_facts:
    filters:
      vpc-id: vpc-abcdef00

'''

try:
    import boto.vpc
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def get_subnet_info(subnet):

    subnet_info = { 'id': subnet.id,
                    'availability_zone': subnet.availability_zone,
                    'available_ip_address_count': subnet.available_ip_address_count,
                    'cidr_block': subnet.cidr_block,
                    'default_for_az': subnet.defaultForAz,
                    'map_public_ip_on_launch': subnet.mapPublicIpOnLaunch,
                    'state': subnet.state,
                    'tags': subnet.tags,
                    'vpc_id': subnet.vpc_id
                  }

    return subnet_info

def list_ec2_vpc_subnets(connection, module):

    filters = module.params.get("filters")
    subnet_dict_array = []

    try:
        all_subnets = connection.get_all_subnets(filters=filters)
    except BotoServerError as e:
        module.fail_json(msg=e.message)

    for subnet in all_subnets:
        subnet_dict_array.append(get_subnet_info(subnet))

    module.exit_json(subnets=subnet_dict_array)


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
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_vpc_subnets(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
