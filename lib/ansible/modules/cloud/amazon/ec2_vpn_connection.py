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
module: ec2_vpn_connection
short_description: Manage an AWS VPN Connection
description:
  - Manage an AWS VPN Connection
version_added: "2.3"
author: James Cunningham (@jamescun)
requirements: [ botocore, boto3 ]
options:
  state:
    description: Create or Delete an AWS VPN Connection.
    required: False
    default: present
    choices: [ 'present', 'absent' ]
  vpn_connection_id:
    description: VPN Connection ID (required for state=absent).
    required: False
  vpn_gateway_id:
    description: VPN Gateway ID (required for state=present).
    required: False
  customer_gateway_id:
    description: Customer Gateway ID (required for state=present).
    require: False
  static_routes_only:
    description: Whether the VPN connection uses static routes only. Static routes must be used for devices that don't support BGP.
    required: False
    default: False
'''

EXAMPLES = '''
# Create a VPN Connection
- ec2_vpn_connection:
    state: present
    vpn_gateway_id: vgw-abcdefgh
    customer_gateway_id: cgw-abcdefgh
    region: us-east-1
  register: vpn

# Delete a VPN Connection
- ec2_vpn_connection:
  state: absent
  vpn_connection_id: vpn-abcdefgh
'''

RETURN = '''
vpn.connection:
  description: Information about the VPN connection
  returned: success
  type: complex
  contains:
    state:
      description: The current state of the VPN connection.
      type: string
      sample: available
    type:
      description: The type of VPN connection.
      type: string
      sample: ipsec.1
    vpn_connection_id:
      description: The ID of the VPN connection.
      type: string
      sample: vpn-abcdefgh
    vpn_gateway_id:
      description: The ID of the virtual private gateway at the AWS side of the VPN connection.
      type: string
      sample: vgw-abcdefgh
    customer_gateway_id:
      description: The ID of the customer gateway at your end of the VPN connection.
      type: string
      sample: cgw-abcdefgh
'''

try:
    from botocore.exceptions import ClientError
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (boto3_conn, camel_dict_to_snake_dict,
    ec2_argument_spec, get_aws_connection_info)


def create_vpn_connection(module, ec2):
    filters=[
        {'Name': 'state', 'Values': ['pending', 'available']},
        {'Name': 'customer-gateway-id', 'Values': [module.params.get('customer_gateway_id')]},
        {'Name': 'vpn-gateway-id', 'Values': [module.params.get('vpn_gateway_id')]},
    ]

    if module.params.get('static_routes_only'):
        filters.append({'Name': 'option.static-routes-only', 'Values': ['true']})

    vpns = ec2.describe_vpn_connections(Filters=filters)

    if vpns['VpnConnections']:
        # only one will ever be returned for a (customer-gateway-id, vpn-gateway-id) pair
        return (camel_dict_to_snake_dict(vpns['VpnConnections'][0]), False)
    else:
        vpn = ec2.create_vpn_connection(
            DryRun=False,
            Type='ipsec.1',
            CustomerGatewayId=module.params.get('customer_gateway_id'),
            VpnGatewayId=module.params.get('vpn_gateway_id'),
            Options={
                'StaticRoutesOnly': module.params.get('static_routes_only'),
            },
        )

        return (camel_dict_to_snake_dict(vpn['VpnConnection']), True)


def delete_vpn_connection(module, ec2):
    vpns = ec2.describe_vpn_connections(
        VpnConnectionIds=[module.params.get('vpn_connection_id')],
        Filters=[
            {'Name': 'state', 'Values': ['pending','available']},
        ],
    )

    deleted_ids = []

    for vpn in vpns['VpnConnections']:
        ec2.delete_vpn_connection(VpnConnectionId=vpn['VpnConnectionId'])
        deleted_ids.append(vpn['VpnConnectionId'])

    return (deleted_ids)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            vpn_connection_id=dict(required=False),
            customer_gateway_id=dict(required=False),
            vpn_gateway_id=dict(required=False),
            static_routes_only=dict(required=False,default=False,type='bool'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['customer_gateway_id', 'vpn_gateway_id']),
            ('state', 'absent', ['vpn_connection_id']),
        ],
    )

    if not HAS_BOTOCORE:
        module.fail_json(msg='botocore is required.')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')


    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        if not region:
            module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
        ec2 = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except ClientError as e:
        module.fail_json(msg=e.message)

    state = module.params.get('state')

    if state == 'present':
        (connection, changed) = create_vpn_connection(module, ec2)
        module.exit_json(changed=changed, connection=connection)
    elif state == 'absent':
        deleted_ids = delete_vpn_connection(module, ec2)
        changed = (len(deleted_ids) > 0)
        module.exit_json(changed=changed, removed=deleted_ids)


if __name__ == '__main__':
    main()
