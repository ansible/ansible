#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: cs_vpn_customer_gateway
short_description: Manages site-to-site VPN customer gateway configurations on Apache CloudStack based clouds.
description:
    - Create, update and remove VPN customer gateways.
version_added: '2.5'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the gateway.
    type: str
    required: true
  cidrs:
    description:
      - List of guest CIDRs behind the gateway.
      - Required if I(state=present).
    type: list
    aliases: [ cidr ]
  gateway:
    description:
      - Public IP address of the gateway.
      - Required if I(state=present).
    type: str
  esp_policy:
    description:
      - ESP policy in the format e.g. C(aes256-sha1;modp1536).
      - Required if I(state=present).
    type: str
  ike_policy:
    description:
      - IKE policy in the format e.g. C(aes256-sha1;modp1536).
      - Required if I(state=present).
    type: str
  ipsec_psk:
    description:
      - IPsec Preshared-Key.
      - Cannot contain newline or double quotes.
      - Required if I(state=present).
    type: str
  ike_lifetime:
    description:
      - Lifetime in seconds of phase 1 VPN connection.
      - Defaulted to 86400 by the API on creation if not set.
    type: int
  esp_lifetime:
    description:
      - Lifetime in seconds of phase 2 VPN connection.
      - Defaulted to 3600 by the API on creation if not set.
    type: int
  dpd:
    description:
      - Enable Dead Peer Detection.
      - Disabled per default by the API on creation if not set.
    type: bool
  force_encap:
    description:
      - Force encapsulation for NAT traversal.
      - Disabled per default by the API on creation if not set.
    type: bool
  state:
    description:
      - State of the VPN customer gateway.
    type: str
    default: present
    choices: [ present, absent ]
  domain:
    description:
      - Domain the VPN customer gateway is related to.
    type: str
  account:
    description:
      - Account the VPN customer gateway is related to.
    type: str
  project:
    description:
      - Name of the project the VPN gateway is related to.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = r'''
- name: Create a vpn customer gateway
  cs_vpn_customer_gateway:
    name: my vpn customer gateway
    cidrs:
    - 192.168.123.0/24
    - 192.168.124.0/24
    esp_policy: aes256-sha1;modp1536
    gateway: 10.10.1.1
    ike_policy: aes256-sha1;modp1536
    ipsec_psk: "S3cr3Tk3Y"
  delegate_to: localhost

- name: Remove a vpn customer gateway
  cs_vpn_customer_gateway:
    name: my vpn customer gateway
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
---
id:
  description: UUID of the VPN customer gateway.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
gateway:
  description: IP address of the VPN customer gateway.
  returned: success
  type: str
  sample: 10.100.212.10
domain:
  description: Domain the VPN customer gateway is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the VPN customer gateway is related to.
  returned: success
  type: str
  sample: example account
project:
  description: Name of project the VPN customer gateway is related to.
  returned: success
  type: str
  sample: Production
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
  description: IKE policy of the VPN customer gateway.
  returned: success
  type: str
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
  description: ESP policy of the VPN customer gateway.
  returned: success
  type: str
  sample: aes256-sha1;modp1536
name:
  description: Name of this customer gateway.
  returned: success
  type: str
  sample: my vpn customer gateway
cidrs:
  description: List of CIDRs of this customer gateway.
  returned: success
  type: list
  sample: [ 10.10.10.0/24 ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackVpnCustomerGateway(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVpnCustomerGateway, self).__init__(module)
        self.returns = {
            'dpd': 'dpd',
            'esplifetime': 'esp_lifetime',
            'esppolicy': 'esp_policy',
            'gateway': 'gateway',
            'ikepolicy': 'ike_policy',
            'ikelifetime': 'ike_lifetime',
            'ipaddress': 'ip_address',
        }

    def _common_args(self):
        return {
            'name': self.module.params.get('name'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'cidrlist': ','.join(self.module.params.get('cidrs')) if self.module.params.get('cidrs') is not None else None,
            'esppolicy': self.module.params.get('esp_policy'),
            'esplifetime': self.module.params.get('esp_lifetime'),
            'ikepolicy': self.module.params.get('ike_policy'),
            'ikelifetime': self.module.params.get('ike_lifetime'),
            'ipsecpsk': self.module.params.get('ipsec_psk'),
            'dpd': self.module.params.get('dpd'),
            'forceencap': self.module.params.get('force_encap'),
            'gateway': self.module.params.get('gateway'),
        }

    def get_vpn_customer_gateway(self):
        args = {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'fetch_list': True,
        }
        vpn_customer_gateway = self.module.params.get('name')
        vpn_customer_gateways = self.query_api('listVpnCustomerGateways', **args)
        if vpn_customer_gateways:
            for vgw in vpn_customer_gateways:
                if vpn_customer_gateway.lower() in [vgw['id'], vgw['name'].lower()]:
                    return vgw

    def present_vpn_customer_gateway(self):
        vpn_customer_gateway = self.get_vpn_customer_gateway()
        required_params = [
            'cidrs',
            'esp_policy',
            'gateway',
            'ike_policy',
            'ipsec_psk',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        if not vpn_customer_gateway:
            vpn_customer_gateway = self._create_vpn_customer_gateway(vpn_customer_gateway)
        else:
            vpn_customer_gateway = self._update_vpn_customer_gateway(vpn_customer_gateway)

        return vpn_customer_gateway

    def _create_vpn_customer_gateway(self, vpn_customer_gateway):
        self.result['changed'] = True
        args = self._common_args()
        if not self.module.check_mode:
            res = self.query_api('createVpnCustomerGateway', **args)
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                vpn_customer_gateway = self.poll_job(res, 'vpncustomergateway')
        return vpn_customer_gateway

    def _update_vpn_customer_gateway(self, vpn_customer_gateway):
        args = self._common_args()
        args.update({'id': vpn_customer_gateway['id']})
        if self.has_changed(args, vpn_customer_gateway, skip_diff_for_keys=['ipsecpsk']):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('updateVpnCustomerGateway', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    vpn_customer_gateway = self.poll_job(res, 'vpncustomergateway')
        return vpn_customer_gateway

    def absent_vpn_customer_gateway(self):
        vpn_customer_gateway = self.get_vpn_customer_gateway()
        if vpn_customer_gateway:
            self.result['changed'] = True
            args = {
                'id': vpn_customer_gateway['id']
            }
            if not self.module.check_mode:
                res = self.query_api('deleteVpnCustomerGateway', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'vpncustomergateway')

        return vpn_customer_gateway

    def get_result(self, vpn_customer_gateway):
        super(AnsibleCloudStackVpnCustomerGateway, self).get_result(vpn_customer_gateway)
        if vpn_customer_gateway:
            if 'cidrlist' in vpn_customer_gateway:
                self.result['cidrs'] = vpn_customer_gateway['cidrlist'].split(',') or [vpn_customer_gateway['cidrlist']]
            # Ensure we return a bool
            self.result['force_encap'] = True if vpn_customer_gateway.get('forceencap') else False
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        domain=dict(),
        account=dict(),
        project=dict(),
        cidrs=dict(type='list', aliases=['cidr']),
        esp_policy=dict(),
        esp_lifetime=dict(type='int'),
        gateway=dict(),
        ike_policy=dict(),
        ike_lifetime=dict(type='int'),
        ipsec_psk=dict(no_log=True),
        dpd=dict(type='bool'),
        force_encap=dict(type='bool'),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_vpn_cgw = AnsibleCloudStackVpnCustomerGateway(module)

    state = module.params.get('state')
    if state == "absent":
        vpn_customer_gateway = acs_vpn_cgw.absent_vpn_customer_gateway()
    else:
        vpn_customer_gateway = acs_vpn_cgw.present_vpn_customer_gateway()

    result = acs_vpn_cgw.get_result(vpn_customer_gateway)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
