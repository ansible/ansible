#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: cs_vpn_connection
short_description: Manages site-to-site VPN connections on Apache CloudStack based clouds.
description:
    - Create and remove VPN connections.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  vpc:
    description:
      - Name of the VPC the VPN connection is related to.
    required: true
  vpn_customer_gateway:
    description:
      - Name of the VPN customer gateway.
    required: true
  passive:
    description:
      - State of the VPN connection.
      - Only considered when C(state=present).
    default: no
    type: bool
  force:
    description:
      - Activate the VPN gateway if not already activated on C(state=present).
      - Also see M(cs_vpn_gateway).
    default: no
    type: bool
  state:
    description:
      - State of the VPN connection.
    default: present
    choices: [ present, absent ]
  domain:
    description:
      - Domain the VPN connection is related to.
  account:
    description:
      - Account the VPN connection is related to.
  project:
    description:
      - Name of the project the VPN connection is related to.
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = r'''
- name: Create a VPN connection with activated VPN gateway
  local_action:
    module: cs_vpn_connection
    vpn_customer_gateway: my vpn connection
    vpc: my vpc

- name: Create a VPN connection and force VPN gateway activation
  local_action:
    module: cs_vpn_connection
    vpn_customer_gateway: my vpn connection
    vpc: my vpc
    force: yes

- name: Remove a vpn connection
  local_action:
    module: cs_vpn_connection
    vpn_customer_gateway: my vpn connection
    vpc: my vpc
    state: absent
'''

RETURN = r'''
---
id:
  description: UUID of the VPN connection.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
vpn_gateway_id:
  description: UUID of the VPN gateway.
  returned: success
  type: string
  sample: 04589590-ac63-93f5-4ffc-b698b8ac38b6
domain:
  description: Domain the VPN connection is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the VPN connection is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Name of project the VPN connection is related to.
  returned: success
  type: string
  sample: Production
created:
  description: Date the connection was created.
  returned: success
  type: string
  sample: 2014-12-01T14:57:57+0100
dpd:
  description: Whether dead pear detection is enabled or not.
  returned: success
  type: bool
  sample: true
esp_lifetime:
  description: Lifetime in seconds of phase 2 VPN connection.
  returned: success
  type: int
  sample: 86400
esp_policy:
  description: IKE policy of the VPN connection.
  returned: success
  type: string
  sample: aes256-sha1;modp1536
force_encap:
  description: Whether encapsulation for NAT traversal is enforced or not.
  returned: success
  type: bool
  sample: true
ike_lifetime:
  description: Lifetime in seconds of phase 1 VPN connection.
  returned: success
  type: int
  sample: 86400
ike_policy:
  description: ESP policy of the VPN connection.
  returned: success
  type: string
  sample: aes256-sha1;modp1536
cidrs:
  description: List of CIDRs of the customer gateway.
  returned: success
  type: list
  sample: [ 10.10.10.0/24 ]
passive:
  description: Whether the connection is passive or not.
  returned: success
  type: bool
  sample: false
public_ip:
  description: IP address of the VPN gateway.
  returned: success
  type: string
  sample: 10.100.212.10
gateway:
  description: IP address of the VPN customer gateway.
  returned: success
  type: string
  sample: 10.101.214.10
state:
  description: State of the VPN connection.
  returned: success
  type: string
  sample: Connected
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackVpnConnection(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVpnConnection, self).__init__(module)
        self.returns = {
            'dpd': 'dpd',
            'esplifetime': 'esp_lifetime',
            'esppolicy': 'esp_policy',
            'gateway': 'gateway',
            'ikepolicy': 'ike_policy',
            'ikelifetime': 'ike_lifetime',
            'publicip': 'public_ip',
            'passive': 'passive',
            's2svpngatewayid': 'vpn_gateway_id',
        }
        self.vpn_customer_gateway = None

    def get_vpn_customer_gateway(self, key=None, identifier=None, refresh=False):
        if not refresh and self.vpn_customer_gateway:
            return self._get_by_key(key, self.vpn_customer_gateway)

        args = {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'fetch_list': True,
        }

        vpn_customer_gateway = identifier or self.module.params.get('vpn_customer_gateway')
        vcgws = self.query_api('listVpnCustomerGateways', **args)
        if vcgws:
            for vcgw in vcgws:
                if vpn_customer_gateway.lower() in [vcgw['id'], vcgw['name'].lower()]:
                    self.vpn_customer_gateway = vcgw
                    return self._get_by_key(key, self.vpn_customer_gateway)
        self.fail_json(msg="VPN customer gateway not found: %s" % vpn_customer_gateway)

    def get_vpn_gateway(self, key=None):
        args = {
            'vpcid': self.get_vpc(key='id'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
        }
        vpn_gateways = self.query_api('listVpnGateways', **args)
        if vpn_gateways:
            return self._get_by_key(key, vpn_gateways['vpngateway'][0])

        elif self.module.params.get('force'):
            if self.module.check_mode:
                return {}
            res = self.query_api('createVpnGateway', **args)
            vpn_gateway = self.poll_job(res, 'vpngateway')
            return self._get_by_key(key, vpn_gateway)

        self.fail_json(msg="VPN gateway not found and not forced to create one")

    def get_vpn_connection(self):
        args = {
            'vpcid': self.get_vpc(key='id'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
        }

        vpn_conns = self.query_api('listVpnConnections', **args)
        if vpn_conns:
            for vpn_conn in vpn_conns['vpnconnection']:
                if self.get_vpn_customer_gateway(key='id') == vpn_conn['s2scustomergatewayid']:
                    return vpn_conn

    def present_vpn_connection(self):
        vpn_conn = self.get_vpn_connection()

        args = {
            's2scustomergatewayid': self.get_vpn_customer_gateway(key='id'),
            's2svpngatewayid': self.get_vpn_gateway(key='id'),
            'passive': self.module.params.get('passive'),
        }

        if not vpn_conn:
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('createVpnConnection', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    vpn_conn = self.poll_job(res, 'vpnconnection')

        return vpn_conn

    def absent_vpn_connection(self):
        vpn_conn = self.get_vpn_connection()

        if vpn_conn:
            self.result['changed'] = True

            args = {
                'id': vpn_conn['id']
            }

            if not self.module.check_mode:
                res = self.query_api('deleteVpnConnection', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'vpnconnection')

        return vpn_conn

    def get_result(self, vpn_conn):
        super(AnsibleCloudStackVpnConnection, self).get_result(vpn_conn)
        if vpn_conn:
            if 'cidrlist' in vpn_conn:
                self.result['cidrs'] = vpn_conn['cidrlist'].split(',') or [vpn_conn['cidrlist']]
            # Ensure we return a bool
            self.result['force_encap'] = True if vpn_conn['forceencap'] else False
            args = {
                'key': 'name',
                'identifier': vpn_conn['s2scustomergatewayid'],
                'refresh': True,
            }
            self.result['vpn_customer_gateway'] = self.get_vpn_customer_gateway(**args)
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        vpn_customer_gateway=dict(required=True),
        vpc=dict(required=True),
        domain=dict(),
        account=dict(),
        project=dict(),
        zone=dict(),
        passive=dict(type='bool', default=False),
        force=dict(type='bool', default=False),
        state=dict(choices=['present', 'absent'], default='present'),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_vpn_conn = AnsibleCloudStackVpnConnection(module)

    state = module.params.get('state')
    if state == "absent":
        vpn_conn = acs_vpn_conn.absent_vpn_connection()
    else:
        vpn_conn = acs_vpn_conn.present_vpn_connection()

    result = acs_vpn_conn.get_result(vpn_conn)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
