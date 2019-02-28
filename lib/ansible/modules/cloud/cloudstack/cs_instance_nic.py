#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Marc-Aurèle Brothier @marcaurele
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_instance_nic
short_description: Manages NICs of an instance on Apache CloudStack based clouds.
description:
    - Add and remove nic to and from network
version_added: '2.4'
author:
  - Marc-Aurèle Brothier (@marcaurele)
  - René Moser (@resmo)
options:
  vm:
    description:
      - Name of instance.
    required: true
    type: str
    aliases: [ name ]
  network:
    description:
      - Name of the network.
    type: str
    required: true
  ip_address:
    description:
      - IP address to be used for the nic.
    type: str
  vpc:
    description:
      - Name of the VPC the I(vm) is related to.
    type: str
  domain:
    description:
      - Domain the instance is related to.
    type: str
  account:
    description:
      - Account the instance is related to.
    type: str
  project:
    description:
      - Name of the project the instance is deployed in.
    type: str
  zone:
    description:
      - Name of the zone in which the instance is deployed in.
      - If not set, default zone is used.
    type: str
  state:
    description:
      - State of the nic.
    type: str
    default: present
    choices: [ present, absent ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Add a nic on another network
  cs_instance_nic:
    vm: privnet
    network: privNetForBasicZone
  delegate_to: localhost

- name: Ensure IP address on a nic
  cs_instance_nic:
    vm: privnet
    ip_address: 10.10.11.32
    network: privNetForBasicZone
  delegate_to: localhost

- name: Remove a secondary nic
  cs_instance_nic:
    vm: privnet
    state: absent
    network: privNetForBasicZone
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the nic.
  returned: success
  type: str
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
vm:
  description: Name of the VM.
  returned: success
  type: str
  sample: web-01
ip_address:
  description: Primary IP of the NIC.
  returned: success
  type: str
  sample: 10.10.10.10
netmask:
  description: Netmask of the NIC.
  returned: success
  type: str
  sample: 255.255.255.0
mac_address:
  description: MAC address of the NIC.
  returned: success
  type: str
  sample: 02:00:33:31:00:e4
network:
  description: Name of the network if not default.
  returned: success
  type: str
  sample: sync network
domain:
  description: Domain the VM is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the VM is related to.
  returned: success
  type: str
  sample: example account
project:
  description: Name of project the VM is related to.
  returned: success
  type: str
  sample: Production
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (AnsibleCloudStack,
                                             cs_argument_spec,
                                             cs_required_together)


class AnsibleCloudStackInstanceNic(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackInstanceNic, self).__init__(module)
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
        nics = self.query_api('listNics', **args)
        if nics:
            self.nic = nics['nic'][0]
            return self.nic
        return None

    def get_nic_from_result(self, result):
        for nic in result.get('nic') or []:
            if nic['networkid'] == self.get_network(key='id'):
                return nic

    def add_nic(self):
        self.result['changed'] = True
        args = {
            'virtualmachineid': self.get_vm(key='id'),
            'networkid': self.get_network(key='id'),
            'ipaddress': self.module.params.get('ip_address'),
        }
        if not self.module.check_mode:
            res = self.query_api('addNicToVirtualMachine', **args)

            if self.module.params.get('poll_async'):
                vm = self.poll_job(res, 'virtualmachine')
                self.nic = self.get_nic_from_result(result=vm)
        return self.nic

    def update_nic(self, nic):
        # Do not try to update if no IP address is given
        ip_address = self.module.params.get('ip_address')
        if not ip_address:
            return nic

        args = {
            'nicid': nic['id'],
            'ipaddress': ip_address,
        }
        if self.has_changed(args, nic, ['ipaddress']):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('updateVmNicIp', **args)

                if self.module.params.get('poll_async'):
                    vm = self.poll_job(res, 'virtualmachine')
                    self.nic = self.get_nic_from_result(result=vm)
        return self.nic

    def remove_nic(self, nic):
        self.result['changed'] = True
        args = {
            'virtualmachineid': self.get_vm(key='id'),
            'nicid': nic['id'],
        }
        if not self.module.check_mode:
            res = self.query_api('removeNicFromVirtualMachine', **args)

            if self.module.params.get('poll_async'):
                self.poll_job(res, 'virtualmachine')
        return nic

    def present_nic(self):
        nic = self.get_nic()
        if not nic:
            nic = self.add_nic()
        else:
            nic = self.update_nic(nic)
        return nic

    def absent_nic(self):
        nic = self.get_nic()
        if nic:
            return self.remove_nic(nic)
        return nic

    def get_result(self, nic):
        super(AnsibleCloudStackInstanceNic, self).get_result(nic)
        if nic and not self.module.params.get('network'):
            self.module.params['network'] = nic.get('networkid')
        self.result['network'] = self.get_network(key='name')
        self.result['vm'] = self.get_vm(key='name')
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        vm=dict(required=True, aliases=['name']),
        network=dict(required=True),
        vpc=dict(),
        ip_address=dict(),
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
    )

    acs_nic = AnsibleCloudStackInstanceNic(module)

    state = module.params.get('state')
    if state == 'absent':
        nic = acs_nic.absent_nic()
    else:
        nic = acs_nic.present_nic()

    result = acs_nic.get_result(nic)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
