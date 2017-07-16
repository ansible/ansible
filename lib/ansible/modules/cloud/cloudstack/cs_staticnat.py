#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
module: cs_staticnat
short_description: Manages static NATs on Apache CloudStack based clouds.
description:
    - Create, update and remove static NATs.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  ip_address:
    description:
      - Public IP address the static NAT is assigned to.
    required: true
  vm:
    description:
      - Name of virtual machine which we make the static NAT for.
      - Required if C(state=present).
    required: false
    default: null
  vm_guest_ip:
    description:
      - VM guest NIC secondary IP address for the static NAT.
    required: false
    default: false
  network:
    description:
      - Network the IP address is related to.
    required: false
    default: null
    version_added: "2.2"
  vpc:
    description:
      - VPC the network related to.
    required: false
    default: null
    version_added: "2.3"
  state:
    description:
      - State of the static NAT.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  domain:
    description:
      - Domain the static NAT is related to.
    required: false
    default: null
  account:
    description:
      - Account the static NAT is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the static NAT is related to.
    required: false
    default: null
  zone:
    description:
      - Name of the zone in which the virtual machine is in.
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
# create a static NAT: 1.2.3.4 -> web01
- local_action:
    module: cs_staticnat
    ip_address: 1.2.3.4
    vm: web01

# remove a static NAT
- local_action:
    module: cs_staticnat
    ip_address: 1.2.3.4
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the ip_address.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
ip_address:
  description: Public IP address.
  returned: success
  type: string
  sample: 1.2.3.4
vm_name:
  description: Name of the virtual machine.
  returned: success
  type: string
  sample: web-01
vm_display_name:
  description: Display name of the virtual machine.
  returned: success
  type: string
  sample: web-01
vm_guest_ip:
  description: IP of the virtual machine.
  returned: success
  type: string
  sample: 10.101.65.152
zone:
  description: Name of zone the static NAT is related to.
  returned: success
  type: string
  sample: ch-gva-2
project:
  description: Name of project the static NAT is related to.
  returned: success
  type: string
  sample: Production
account:
  description: Account the static NAT is related to.
  returned: success
  type: string
  sample: example account
domain:
  description: Domain the static NAT is related to.
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


class AnsibleCloudStackStaticNat(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackStaticNat, self).__init__(module)
        self.returns = {
            'virtualmachinedisplayname': 'vm_display_name',
            'virtualmachinename': 'vm_name',
            'ipaddress': 'ip_address',
            'vmipaddress': 'vm_guest_ip',
        }

    def create_static_nat(self, ip_address):
        self.result['changed'] = True
        args = {
            'virtualmachineid': self.get_vm(key='id'),
            'ipaddressid': ip_address['id'],
            'vmguestip': self.get_vm_guest_ip(),
            'networkid': self.get_network(key='id')
        }
        if not self.module.check_mode:
            self.query_api('enableStaticNat', **args)

            # reset ip address and query new values
            self.ip_address = None
            ip_address = self.get_ip_address()
        return ip_address

    def update_static_nat(self, ip_address):
        args = {
            'virtualmachineid': self.get_vm(key='id'),
            'ipaddressid': ip_address['id'],
            'vmguestip': self.get_vm_guest_ip(),
            'networkid': self.get_network(key='id')
        }
        # make an alias, so we can use has_changed()
        ip_address['vmguestip'] = ip_address['vmipaddress']
        if self.has_changed(args, ip_address, ['vmguestip', 'virtualmachineid']):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('disableStaticNat', ipaddressid=ip_address['id'])
                self.poll_job(res, 'staticnat')

                self.query_api('enableStaticNat', **args)

                # reset ip address and query new values
                self.ip_address = None
                ip_address = self.get_ip_address()
        return ip_address

    def present_static_nat(self):
        ip_address = self.get_ip_address()
        if not ip_address['isstaticnat']:
            ip_address = self.create_static_nat(ip_address)
        else:
            ip_address = self.update_static_nat(ip_address)
        return ip_address

    def absent_static_nat(self):
        ip_address = self.get_ip_address()
        if ip_address['isstaticnat']:
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('disableStaticNat', ipaddressid=ip_address['id'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'staticnat')
        return ip_address


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        ip_address=dict(required=True),
        vm=dict(),
        vm_guest_ip=dict(),
        network=dict(),
        vpc=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        zone=dict(),
        domain=dict(),
        account=dict(),
        project=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_static_nat = AnsibleCloudStackStaticNat(module)

    state = module.params.get('state')
    if state in ['absent']:
        ip_address = acs_static_nat.absent_static_nat()
    else:
        ip_address = acs_static_nat.present_static_nat()

    result = acs_static_nat.get_result(ip_address)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
