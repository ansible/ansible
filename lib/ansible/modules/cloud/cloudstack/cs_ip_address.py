#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Darren Worrall <darren@iweb.co.uk>
# (c) 2015, René Moser <mail@renemoser.net>
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
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_ip_address
short_description: Manages public IP address associations on Apache CloudStack based clouds.
description:
    - Acquires and associates a public IP to an account or project. Due to API
      limitations this is not an idempotent call, so be sure to only
      conditionally call this when C(state=present)
version_added: '2.0'
author:
    - "Darren Worrall (@dazworrall)"
    - "René Moser (@resmo)"
options:
  ip_address:
    description:
      - Public IP address.
      - Required if C(state=absent)
    required: false
    default: null
  domain:
    description:
      - Domain the IP address is related to.
    required: false
    default: null
  network:
    description:
      - Network the IP address is related to.
    required: false
    default: null
  vpc:
    description:
      - VPC the IP address is related to.
    required: false
    default: null
    version_added: "2.2"
  account:
    description:
      - Account the IP address is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the IP address is related to.
    required: false
    default: null
  zone:
    description:
      - Name of the zone in which the IP address is in.
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
# Associate an IP address conditonally
- local_action:
    module: cs_ip_address
    network: My Network
  register: ip_address
  when: instance.public_ip is undefined

# Disassociate an IP address
- local_action:
    module: cs_ip_address
    ip_address: 1.2.3.4
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the Public IP address.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
ip_address:
  description: Public IP address.
  returned: success
  type: string
  sample: 1.2.3.4
zone:
  description: Name of zone the IP address is related to.
  returned: success
  type: string
  sample: ch-gva-2
project:
  description: Name of project the IP address is related to.
  returned: success
  type: string
  sample: Production
account:
  description: Account the IP address is related to.
  returned: success
  type: string
  sample: example account
domain:
  description: Domain the IP address is related to.
  returned: success
  type: string
  sample: example domain
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackIPAddress(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackIPAddress, self).__init__(module)
        self.returns = {
            'ipaddress': 'ip_address',
        }

    def get_ip_address(self, key=None):
        if self.ip_address:
            return self._get_by_key(key, self.ip_address)
        args = {
            'ipaddress': self.module.params.get('ip_address'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'vpcid': self.get_vpc(key='id'),
        }
        ip_addresses = self.cs.listPublicIpAddresses(**args)

        if ip_addresses:
            self.ip_address = ip_addresses['publicipaddress'][0]
        return self._get_by_key(key, self.ip_address)

    def associate_ip_address(self):
        self.result['changed'] = True
        args = {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'networkid': self.get_network(key='id'),
            'zoneid': self.get_zone(key='id'),
            'vpcid': self.get_vpc(key='id'),
        }
        ip_address = None
        if not self.module.check_mode:
            res = self.cs.associateIpAddress(**args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                ip_address = self.poll_job(res, 'ipaddress')
        return ip_address

    def disassociate_ip_address(self):
        ip_address = self.get_ip_address()
        if not ip_address:
            return None
        if ip_address['isstaticnat']:
            self.module.fail_json(msg="IP address is allocated via static nat")

        self.result['changed'] = True
        if not self.module.check_mode:
            res = self.cs.disassociateIpAddress(id=ip_address['id'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                self.poll_job(res, 'ipaddress')
        return ip_address


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        ip_address=dict(required=False),
        state=dict(choices=['present', 'absent'], default='present'),
        vpc=dict(),
        network=dict(),
        zone=dict(),
        domain=dict(),
        account=dict(),
        project=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_if=[
            ('state', 'absent', ['ip_address']),
        ],
        supports_check_mode=True
    )

    acs_ip_address = AnsibleCloudStackIPAddress(module)

    state = module.params.get('state')
    if state in ['absent']:
        ip_address = acs_ip_address.disassociate_ip_address()
    else:
        ip_address = acs_ip_address.associate_ip_address()

    result = acs_ip_address.get_result(ip_address)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
