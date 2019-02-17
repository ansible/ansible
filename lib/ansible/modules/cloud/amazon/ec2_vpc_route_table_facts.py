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
module: ec2_vpc_route_table_facts
short_description: Gather facts about ec2 VPC route tables in AWS
description:
    - Gather facts about ec2 VPC route tables in AWS
version_added: "2.0"
author: "Rob White (@wimnat)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html) for possible filters.
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all VPC route tables
- ec2_vpc_route_table_facts:

# Gather facts about a particular VPC route table using route table ID
- ec2_vpc_route_table_facts:
    filters:
      route-table-id: rtb-00112233

# Gather facts about any VPC route table with a tag key Name and value Example
- ec2_vpc_route_table_facts:
    filters:
      "tag:Name": Example

# Gather facts about any VPC route table within VPC with ID vpc-abcdef00
- ec2_vpc_route_table_facts:
    filters:
      vpc-id: vpc-abcdef00

'''

try:
    import boto.vpc
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import AnsibleAWSError, connect_to_aws, ec2_argument_spec, get_aws_connection_info


def get_route_table_info(route_table):

    # Add any routes to array
    routes = []
    associations = []
    for route in route_table.routes:
        routes.append(route.__dict__)
    for association in route_table.associations:
        associations.append(association.__dict__)

    route_table_info = {'id': route_table.id,
                        'routes': routes,
                        'associations': associations,
                        'tags': route_table.tags,
                        'vpc_id': route_table.vpc_id
                        }

    return route_table_info


def list_ec2_vpc_route_tables(connection, module):

    filters = module.params.get("filters")
    route_table_dict_array = []

    try:
        all_route_tables = connection.get_all_route_tables(filters=filters)
    except BotoServerError as e:
        module.fail_json(msg=e.message)

    for route_table in all_route_tables:
        route_table_dict_array.append(get_route_table_info(route_table))

    module.exit_json(route_tables=route_table_dict_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(default=None, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_vpc_route_tables(connection, module)


if __name__ == '__main__':
    main()
