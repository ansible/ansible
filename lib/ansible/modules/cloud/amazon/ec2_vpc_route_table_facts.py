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
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html) for possible filters.
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
RETURN = '''
route_tables:
    description: Information about one or more route tables.
    returned: always
    type: complex
    contains:
      associations:
        description: The associations between the route table and one or more subnets.
        returned: always
        type: complex
        contains:
            main:
              description: TIndicates whether this is the main route table.
              returned: always
              type: boolean
              sample: True
            route_table_association_id:
              description: The ID of the association between a route table and a subnet.
              returned: always
              type: string
              sample: rtbassoc-4c3f71123
            route_table_id:
              description: The ID of the route table.
              returned: always
              type: string
              sample: rtb-05641160
            subnet_id:
              description: The ID of the subnet. A subnet ID is not returned for an implicit association.
              returned: when route table has subnet associated
              type: string
              sample: subnet-db73c0ac
      propagating_vgws:
        description: Any virtual private gateway (VGW) propagating routes.
        returned: always
        type: complex
        contains:
          gateway_id:
            description: The ID of the virtual private gateway.
            returned: when gateway_id aviable
            sample: local
      route_table_id:
          description: The ID of the route table.
          returned: always
          type: string
          sample: rtb-05641160
      routes:
        description: The routes in the route table.
        returned: always
        type: complex
        contains:
            destination_cidr_block:
              description: The IPv4 CIDR block used for the destination match.
              returned: always
              type: string
              sample: 172.31.0.0/16
            destination_ipv6_cidr_block:
              description: The IPv6 CIDR block used for the destination match.
              returned: when ipv6 cidr block available
              type: string
              sample: 2001:db8:1234:1a00::/56
            destination_prefix_list_id:
              description: The prefix of the AWS service.
              returned: always
              type: string
            egress_only_internet_gateway_id :
              description: The ID of the egress-only internet gateway.
              returned: when egress_only_internet_gateway available
              type: string
            gateway_id:
              description: The ID of a gateway attached to your VPC.
              returned: when gateway available
              type: string
            instance_id:
              description: The ID of a NAT instance in your VPC.
              returned: when NAT instance is available
              type: string
            instance_owner_id:
              description: The ID of a NAT instance in your VPC.
              returned: when NAT instance is available
              type: string
            nat_gateway_id:
              description: The ID of a NAT gateway.
              returned: when NAT gateway is available
              type: string
            network_interface_id:
              description: The ID of the network interface.
              returned: when network interface is available
              type: string
            origin:
              description: Describes how the route was created.
              returned: always
              type: string    
              sample: CreateRoute
            state:       
              description: The state of the route.
              returned: always
              type: string    
              sample: active
            vpc_peering_connection_id:
              description: The ID of the VPC peering connection.
              returned: when vpc peering available
              type: string
        tags:
          description: Any tags assigned to the VPN connection.
          returned: always
          type: dict
          sample: {
                      "Name": "test-conn"
                  }
        vpc_id:
          description: The ID of the VPC peering connection.
          returned: when vpc peering available
          type: string
          sample: vpc-a01106c2

'''
import json

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by imported HAS_BOTO3

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (ec2_argument_spec, boto3_conn, ansible_dict_to_boto3_filter_list, HAS_BOTO3,
                                      camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict)


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def list_route_tables(route_table, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    params['RouteTableIds'] = module.params.get('route_table_ids')

    try:
        result = json.loads(json.dumps(route_table.describe_route_tables(**params), default=date_handler))
    except ValueError as e:
        module.fail_json_aws(e, msg="Cannot validate JSON data")
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Could not describe route tables")
    snaked_route_tables = [camel_dict_to_snake_dict(route_table) for route_table in result['RouteTables']]
    if snaked_route_tables:
        for route_table in snaked_route_tables:
            route_table['tags'] = boto3_tag_list_to_ansible_dict(route_table.get('tags', []))
    module.exit_json(changed=False, route_tables=snaked_route_tables)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            route_table_ids=dict(default=[], type='list'),
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[['vpn_connection_ids', 'filters']],
                              supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    connection = module.client('ec2')
    list_route_tables(connection, module)


if __name__ == '__main__':
    main()
