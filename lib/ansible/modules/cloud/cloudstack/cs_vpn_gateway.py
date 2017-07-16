#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_vpn_gateway
short_description: Manages site-to-site VPN gateways on Apache CloudStack based clouds.
description:
    - Creates and removes VPN site-to-site gateways.
version_added: "2.4"
author: "René Moser (@resmo)"
options:
  vpc:
    description:
      - Name of the VPC.
    required: true
  state:
    description:
      - State of the VPN gateway.
    required: false
    default: "present"
    choices: [ 'present', 'absent' ]
  domain:
    description:
      - Domain the VPN gateway is related to.
    required: false
    default: null
  account:
    description:
      - Account the VPN gateway is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the VPN gateway is related to.
    required: false
    default: null
  zone:
    description:
      - Name of the zone the VPC is related to.
      - If not set, default zone is used.
    required: false
    default: null
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a vpn gateway is present
- local_action:
    module: cs_vpn_gateway
    vpc: my VPC

# Ensure a vpn gateway is absent
- local_action:
    module: cs_vpn_gateway
    vpc: my VPC
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the VPN site-to-site gateway.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
public_ip:
  description: IP address of the VPN site-to-site gateway.
  returned: success
  type: string
  sample: 10.100.212.10
vpc:
  description: Name of the VPC.
  returned: success
  type: string
  sample: My VPC
domain:
  description: Domain the VPN site-to-site gateway is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the VPN site-to-site gateway is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Name of project the VPN site-to-site gateway is related to.
  returned: success
  type: string
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
