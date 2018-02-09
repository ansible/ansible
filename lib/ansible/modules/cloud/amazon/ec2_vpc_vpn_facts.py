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
author: Madhura Naniwadekar(@Madhura-CSI)
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpnConnections.html) for possible filters.
    required: false
    default: None
  vpn_connection_ids:
    description:
      - Get details of a specific VPN connections using vpn connection ID/IDs. This value should be provided as a list.
    required: false
    default: None
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
    description: List of one or VPN Connections.
    returned: always
    type: list
    sample: [
            {
                "category": "VPN",
                "customer_gateway_configuration": "<customer_gateway_configuration-xml>",
                "customer_gateway_id": "cgw-17a53c37",
                "options": {
                    "static_routes_only": false
                },
                "routes": [],
                "state": "available",
                "tags": {
                    "Name": "test-conn"
                },
                "type": "ipsec.1",
                "vgw_telemetry": [
                    {
                        "accepted_route_count": 0,
                        "last_status_change": "2018-02-09T14:35:27+00:00",
                        "outside_ip_address": "13.127.79.191",
                        "status": "DOWN",
                        "status_message": "IPSEC IS DOWN"
                    },
                    {
                        "accepted_route_count": 0,
                        "last_status_change": "2018-02-09T14:35:43+00:00",
                        "outside_ip_address": "35.154.107.155",
                        "status": "DOWN",
                        "status_message": "IPSEC IS DOWN"
                    }
                ],
                "vpn_connection_id": "vpn-f700d5c0",
                "vpn_gateway_id": "vgw-cbe56bfb"
            }
        ]
'''

import json
try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (ansible_dict_to_boto3_filter_list,
                                      boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info)


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def list_vpn_connections(connection, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    params['VpnConnectionIds'] = module.params.get('vpn_connection_ids')

    try:
        result = json.loads(json.dumps(connection.describe_vpn_connections(**params), default=date_handler))
    except Exception as e:
        module.fail_json(msg=str(e.message))
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

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)

    list_vpn_connections(connection, module)


if __name__ == '__main__':
    main()
