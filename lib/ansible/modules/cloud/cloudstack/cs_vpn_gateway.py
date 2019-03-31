#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_vpn_gateway
short_description: Manages site-to-site VPN gateways on Apache CloudStack based clouds.
description:
    - Creates and removes VPN site-to-site gateways.
version_added: '2.4'
author: René Moser (@resmo)
options:
  vpc:
    description:
      - Name of the VPC.
    type: str
    required: true
  state:
    description:
      - State of the VPN gateway.
    type: str
    default: present
    choices: [ present, absent ]
  domain:
    description:
      - Domain the VPN gateway is related to.
    type: str
  account:
    description:
      - Account the VPN gateway is related to.
    type: str
  project:
    description:
      - Name of the project the VPN gateway is related to.
    type: str
  zone:
    description:
      - Name of the zone the VPC is related to.
      - If not set, default zone is used.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Ensure a vpn gateway is present
  cs_vpn_gateway:
    vpc: my VPC
  delegate_to: localhost

- name: Ensure a vpn gateway is absent
  cs_vpn_gateway:
    vpc: my VPC
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the VPN site-to-site gateway.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
public_ip:
  description: IP address of the VPN site-to-site gateway.
  returned: success
  type: str
  sample: 10.100.212.10
vpc:
  description: Name of the VPC.
  returned: success
  type: str
  sample: My VPC
domain:
  description: Domain the VPN site-to-site gateway is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the VPN site-to-site gateway is related to.
  returned: success
  type: str
  sample: example account
project:
  description: Name of project the VPN site-to-site gateway is related to.
  returned: success
  type: str
  sample: Production
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackVpnGateway(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVpnGateway, self).__init__(module)
        self.returns = {
            'publicip': 'public_ip'
        }

    def get_vpn_gateway(self):
        args = {
            'vpcid': self.get_vpc(key='id'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id')
        }
        vpn_gateways = self.query_api('listVpnGateways', **args)
        if vpn_gateways:
            return vpn_gateways['vpngateway'][0]
        return None

    def present_vpn_gateway(self):
        vpn_gateway = self.get_vpn_gateway()
        if not vpn_gateway:
            self.result['changed'] = True
            args = {
                'vpcid': self.get_vpc(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'projectid': self.get_project(key='id')
            }
            if not self.module.check_mode:
                res = self.query_api('createVpnGateway', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    vpn_gateway = self.poll_job(res, 'vpngateway')

        return vpn_gateway

    def absent_vpn_gateway(self):
        vpn_gateway = self.get_vpn_gateway()
        if vpn_gateway:
            self.result['changed'] = True
            args = {
                'id': vpn_gateway['id']
            }
            if not self.module.check_mode:
                res = self.query_api('deleteVpnGateway', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'vpngateway')

        return vpn_gateway

    def get_result(self, vpn_gateway):
        super(AnsibleCloudStackVpnGateway, self).get_result(vpn_gateway)
        if vpn_gateway:
            self.result['vpc'] = self.get_vpc(key='name')
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        vpc=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        domain=dict(),
        account=dict(),
        project=dict(),
        zone=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_vpn_gw = AnsibleCloudStackVpnGateway(module)

    state = module.params.get('state')
    if state == "absent":
        vpn_gateway = acs_vpn_gw.absent_vpn_gateway()
    else:
        vpn_gateway = acs_vpn_gw.present_vpn_gateway()

    result = acs_vpn_gw.get_result(vpn_gateway)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
