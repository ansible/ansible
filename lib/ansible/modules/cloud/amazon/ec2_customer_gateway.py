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
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_customer_gateway
short_description: Manage an AWS customer gateway
description:
    - Manage an AWS customer gateway
version_added: "2.2"
author: Michael Baydoun (@MichaelBaydoun)
requirements: [ botocore, boto3 ]
notes:
    - You cannot create more than one customer gateway with the same IP address. If you run an identical request more than one time, the
      first request creates the customer gateway, and subsequent requests return information about the existing customer gateway. The subsequent
      requests do not create new customer gateway resources.
    - Return values contain customer_gateway and customer_gateways keys which are identical dicts. You should use
      customer_gateway. See U(https://github.com/ansible/ansible-modules-extras/issues/2773) for details.
options:
  bgp_asn:
    description:
      - Border Gateway Protocol (BGP) Autonomous System Number (ASN), required when state=present.
    required: false
    default: null
  ip_address:
    description:
      - Internet-routable IP address for customers gateway, must be a static address.
    required: true
  name:
    description:
      - Name of the customer gateway.
    required: true
  routing:
    description:
      - The type of routing.
    choices: ['static', 'dynamic']
    default: dynamic
    version_added: '2.4'
  state:
    description:
      - Create or terminate the Customer Gateway.
    required: false
    default: present
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''

# Create Customer Gateway
- ec2_customer_gateway:
    bgp_asn: 12345
    ip_address: 1.2.3.4
    name: IndianapolisOffice
    region: us-east-1
  register: cgw

# Delete Customer Gateway
- ec2_customer_gateway:
    ip_address: 1.2.3.4
    name: IndianapolisOffice
    state: absent
    region: us-east-1
  register: cgw
'''

RETURN = '''
gateway.customer_gateways:
    description: details about the gateway that was created.
    returned: success
    type: complex
    contains:
        bgp_asn:
            description: The Border Gateway Autonomous System Number.
            returned: when exists and gateway is available.
            sample: 65123
            type: string
        customer_gateway_id:
            description: gateway id assigned by amazon.
            returned: when exists and gateway is available.
            sample: cgw-cb6386a2
            type: string
        ip_address:
            description: ip address of your gateway device.
            returned: when exists and gateway is available.
            sample: 1.2.3.4
            type: string
        state:
            description: state of gateway.
            returned: when gateway exists and is available.
            state: available
            type: string
        tags:
            description: any tags on the gateway.
            returned: when gateway exists and is available, and when tags exist.
            state: available
            type: string
        type:
            description: encryption type.
            returned: when gateway exists and is available.
            sample: ipsec.1
            type: string
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


class Ec2CustomerGatewayManager:

    def __init__(self, module):
        self.module = module

        try:
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            if not region:
                module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
            self.ec2 = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except ClientError as e:
            module.fail_json(msg=e.message)

    def ensure_cgw_absent(self, gw_id):
        response = self.ec2.delete_customer_gateway(
            DryRun=False,
            CustomerGatewayId=gw_id
        )
        return response

    def ensure_cgw_present(self, bgp_asn, ip_address):
        if not bgp_asn:
            bgp_asn = 65000
        response = self.ec2.create_customer_gateway(
            DryRun=False,
            Type='ipsec.1',
            PublicIp=ip_address,
            BgpAsn=bgp_asn,
        )
        return response

    def tag_cgw_name(self, gw_id, name):
        response = self.ec2.create_tags(
            DryRun=False,
            Resources=[
                gw_id,
            ],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': name
                },
            ]
        )
        return response

    def describe_gateways(self, ip_address):
        response = self.ec2.describe_customer_gateways(
            DryRun=False,
            Filters=[
                {
                    'Name': 'state',
                    'Values': [
                        'available',
                    ]
                },
                {
                    'Name': 'ip-address',
                    'Values': [
                        ip_address,
                    ]
                }
            ]
        )
        return response


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            bgp_asn=dict(required=False, type='int'),
            ip_address=dict(required=True),
            name=dict(required=True),
            routing=dict(default='dynamic', choices=['dynamic', 'static']),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_if=[
                               ('routing', 'dynamic', ['bgp_asn'])
                           ]
                           )

    if not HAS_BOTOCORE:
        module.fail_json(msg='botocore is required.')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    gw_mgr = Ec2CustomerGatewayManager(module)

    name = module.params.get('name')

    existing = gw_mgr.describe_gateways(module.params['ip_address'])

    results = dict(changed=False)
    if module.params['state'] == 'present':
        if existing['CustomerGateways']:
            existing['CustomerGateway'] = existing['CustomerGateways'][0]
            results['gateway'] = existing
            if existing['CustomerGateway']['Tags']:
                tag_array = existing['CustomerGateway']['Tags']
                for key, value in enumerate(tag_array):
                    if value['Key'] == 'Name':
                        current_name = value['Value']
                        if current_name != name:
                            results['name'] = gw_mgr.tag_cgw_name(
                                results['gateway']['CustomerGateway']['CustomerGatewayId'],
                                module.params['name'],
                            )
                            results['changed'] = True
        else:
            if not module.check_mode:
                results['gateway'] = gw_mgr.ensure_cgw_present(
                    module.params['bgp_asn'],
                    module.params['ip_address'],
                )
                results['name'] = gw_mgr.tag_cgw_name(
                    results['gateway']['CustomerGateway']['CustomerGatewayId'],
                    module.params['name'],
                )
            results['changed'] = True

    elif module.params['state'] == 'absent':
        if existing['CustomerGateways']:
            existing['CustomerGateway'] = existing['CustomerGateways'][0]
            results['gateway'] = existing
            if not module.check_mode:
                results['gateway'] = gw_mgr.ensure_cgw_absent(
                    existing['CustomerGateway']['CustomerGatewayId']
                )
            results['changed'] = True

    pretty_results = camel_dict_to_snake_dict(results)
    module.exit_json(**pretty_results)


if __name__ == '__main__':
    main()
