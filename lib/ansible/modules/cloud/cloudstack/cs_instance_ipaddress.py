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
module: cs_instance_ipaddress
short_description: Manages IPs of an instance on Apache CloudStack based clouds.
description:
    - Add and remove IPs to and from a NIC of an instance.
version_added: "2.4"
author: "René Moser (@resmo)"
options:
  vm:
    description:
      - Name of instance.
    required: true
    aliases: [ name ]
  network:
    description:
      - Name of the network.
      - Required to find the NIC if instance has multiple networks assigned.
  vm_guest_ip:
    description:
      - Secondary IP address to be added to the instance nic.
      - If not set, the API always returns a new IP address and idempotency is not given.
    aliases: [ secondary_ip ]
  vpc:
    description:
      - Name of the VPC the C(vm) is related to.
  domain:
    description:
      - Domain the instance is related to.
  account:
    description:
      - Account the instance is related to.
  project:
    description:
      - Name of the project the instance is deployed in.
  zone:
    description:
      - Name of the zone in which the instance is deployed in.
      - If not set, default zone is used.
  state:
    description:
      - State of the ipaddress.
    default: present
    choices: [ present, absent ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Assign a specific IP to the default NIC of the VM
- local_action:
    module: cs_instance_ipaddress
    vm: customer_xy
    vm_guest_ip: 10.10.10.10

# Assign an IP to the default NIC of the VM
# Note: If vm_guest_ip is not set, you will get a new IP address on every run.
- local_action:
    module: cs_instance_ipaddress
    vm: customer_xy

# Remove a specific IP from the default NIC
- local_action:
    module: cs_instance_ipaddress
    vm: customer_xy
    vm_guest_ip: 10.10.10.10
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the NIC.
  returned: success
  type: string
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
vm:
  description: Name of the VM.
  returned: success
  type: string
  sample: web-01
ip_address:
  description: Primary IP of the NIC.
  returned: success
  type: string
  sample: 10.10.10.10
netmask:
  description: Netmask of the NIC.
  returned: success
  type: string
  sample: 255.255.255.0
mac_address:
  description: MAC address of the NIC.
  returned: success
  type: string
  sample: 02:00:33:31:00:e4
vm_guest_ip:
  description: Secondary IP of the NIC.
  returned: success
  type: string
  sample: 10.10.10.10
network:
  description: Name of the network if not default.
  returned: success
  type: string
  sample: sync network
domain:
  description: Domain the VM is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the VM is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Name of project the VM is related to.
  returned: success
  type: string
  sample: Production
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    CloudStackException,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackInstanceIpaddress(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackInstanceIpaddress, self).__init__(module)
        self.vm_guest_ip = self.module.params.get('vm_guest_ip')
        self.nic = None
        self.returns = {
            'ipaddress': 'ip_address',
            'macaddress': 'mac_address',
            'netmask': 'netmask',
        }

    def get_nic(self):
        if self.nic:
            return self.nic
        args = {
            'virtualmachineid': self.get_vm(key='id'),
            'networkid': self.get_network(key='id'),
        }
        nics = self.cs.listNics(**args)
        if nics:
            self.nic = nics['nic'][0]
            return self.nic
        self.fail_json(msg="NIC for VM %s in network %s not found" % (self.get_vm(key='name'), self.get_network(key='name')))

    def get_secondary_ip(self):
        nic = self.get_nic()
        if self.vm_guest_ip:
            secondary_ips = nic.get('secondaryip') or []
            for secondary_ip in secondary_ips:
                if secondary_ip['ipaddress'] == self.vm_guest_ip:
                    return secondary_ip
        return None

    def present_nic_ip(self):
        nic = self.get_nic()
        if not self.get_secondary_ip():
            self.result['changed'] = True
            args = {
                'nicid': nic['id'],
                'ipaddress': self.vm_guest_ip,
            }

            if not self.module.check_mode:
                res = self.cs.addIpToNic(**args)

                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    nic = self.poll_job(res, 'nicsecondaryip')
                    # Save result for RETURNS
                    self.vm_guest_ip = nic['ipaddress']
        return nic

    def absent_nic_ip(self):
        nic = self.get_nic()
        secondary_ip = self.get_secondary_ip()
        if secondary_ip:
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.cs.removeIpFromNic(id=secondary_ip['id'])
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % nic['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'nicsecondaryip')
        return nic

    def get_result(self, nic):
        super(AnsibleCloudStackInstanceIpaddress, self).get_result(nic)
        if nic and not self.module.params.get('network'):
            self.module.params['network'] = nic.get('networkid')
        self.result['network'] = self.get_network(key='name')
        self.result['vm'] = self.get_vm(key='name')
        self.result['vm_guest_ip'] = self.vm_guest_ip
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        vm=dict(required=True, aliases=['name']),
        vm_guest_ip=dict(aliases=['secondary_ip']),
        network=dict(),
        vpc=dict(),
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
        supports_check_mode=True,
        required_if=([
            ('state', 'absent', ['vm_guest_ip'])
        ])
    )

    try:
        acs_instance_ipaddress = AnsibleCloudStackInstanceIpaddress(module)

        state = module.params.get('state')

        if state == 'absent':
            nic = acs_instance_ipaddress.absent_nic_ip()
        else:
            nic = acs_instance_ipaddress.present_nic_ip()

        result = acs_instance_ipaddress.get_result(nic)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
