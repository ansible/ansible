#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: ec2_vpc_vpn_facts
short_description: Gather facts about VPN Connections in AWS.
description:
    - Gather facts about VPN Connections in AWS.
version_added: "2.6"
requirements: [ boto3 ]
author: Madhura Naniwadekar (@Madhura-CSI)
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpnConnections.html) for possible filters.
    required: false
  vpn_connection_ids:
    description:
      - Get details of a specific VPN connections using vpn connection ID/IDs. This value should be provided as a list.
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# # Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Gather facts about all vpn connections
  ec2_vpc_vpn_facts:

- name: Gather facts about a filtered list of vpn connections, based on tags
  ec2_vpc_vpn_facts:
    filters:
      "tag:Name": test-connection
  register: vpn_conn_facts

- name: Gather facts about vpn connections by specifying connection IDs.
  ec2_vpc_vpn_facts:
    filters:
      vpn-gateway-id: vgw-cbe66beb
  register: vpn_conn_facts
'''

RETURN = '''
vpn_connections:
    description: List of one or more VPN Connections.
    returned: always
    type: complex
    contains:
      category:
        description: The category of the VPN connection.
        returned: always
        type: str
        sample: VPN
      customer_gatway_configuration:
        description: The configuration information for the VPN connection's customer gateway (in the native XML format).
        returned: always
        type: str
      customer_gateway_id:
        description: The ID of the customer gateway at your end of the VPN connection.
        returned: always
        type: str
        sample: cgw-17a53c37
      options:
        description: The VPN connection options.
        returned: always
        type: dict
        sample: {
                    "static_routes_only": false
                }
      routes:
        description: List of static routes associated with the VPN connection.
        returned: always
        type: complex
        contains:
          destination_cidr_block:
            description: The CIDR block associated with the local subnet of the customer data center.
            returned: always
            type: str
            sample: 10.0.0.0/16
          state:
            description: The current state of the static route.
            returned: always
            type: str
            sample: available
      state:
        description: The current state of the VPN connection.
        returned: always
        type: str
        sample: available
      tags:
        description: Any tags assigned to the VPN connection.
        returned: always
        type: dict
        sample: {
                    "Name": "test-conn"
                }
      type:
        description: The type of VPN connection.
        returned: always
        type: str
        sample: ipsec.1
      vgw_telemetry:
         description: Information about the VPN tunnel.
         returned: always
         type: complex
         contains:
           accepted_route_count:
             description: The number of accepted routes.
             returned: always
             type: int
             sample: 0
         last_status_change:
             description: The date and time of the last change in status.
             returned: always
             type: datetime
             sample: 2018-02-09T14:35:27+00:00
         outside_ip_address:
             description: The Internet-routable IP address of the virtual private gateway's outside interface.
             returned: always
             type: str
             sample: 13.127.79.191
         status:
             description: The status of the VPN tunnel.
             returned: always
             type: str
             sample: DOWN
         status_message:
             description: If an error occurs, a description of the error.
             returned: always
             type: str
             sample: IPSEC IS DOWN
      vpn_connection_id:
        description: The ID of the VPN connection.
        returned: always
        type: str
        sample: vpn-f700d5c0
      vpn_gateway_id:
        description: The ID of the virtual private gateway at the AWS side of the VPN connection.
        returned: always
        type: str
        sample: vgw-cbe56bfb
'''

import json
try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (ansible_dict_to_boto3_filter_list, ec2_argument_spec,
                                      boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict)


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def list_vpn_connections(connection, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    params['VpnConnectionIds'] = module.params.get('vpn_connection_ids')

    try:
        result = json.loads(json.dumps(connection.describe_vpn_connections(**params), default=date_handler))
    except ValueError as e:
        module.fail_json_aws(e, msg="Cannot validate JSON data")
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Could not describe customer gateways")
    snaked_vpn_connections = [camel_dict_to_snake_dict(vpn_connection) for vpn_connection in result['VpnConnections']]
    if snaked_vpn_connections:
        for vpn_connection in snaked_vpn_connections:
            vpn_connection['tags'] = boto3_tag_list_to_ansible_dict(vpn_connection.get('tags', []))
    module.exit_json(changed=False, vpn_connections=snaked_vpn_connections)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            vpn_connection_ids=dict(default=[], type='list'),
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[['vpn_connection_ids', 'filters']],
                              supports_check_mode=True)

    connection = module.client('ec2')

    list_vpn_connections(connection, module)


if __name__ == '__main__':
    main()
