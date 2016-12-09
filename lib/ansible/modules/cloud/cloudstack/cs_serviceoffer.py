#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it an/or modify
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
# along with Ansible. If not, see <http//www.gnu.or/license/>.

DOCUMENTATION = '''
---
module: cs_serviceoffer
description:
  - "Create, update, delete service offerings."
short_description: "Manages service offerings on Apache CloudStack based clouds."
version_added: "2.3"
author: "René Moser (@resmo)"
options:
  bytes_read_rate:
    default: null
    description:
      - "Bytes read rate of the disk offering."
    required: false
  bytes_write_rate:
    default: null
    description:
      - "Bytes write rate of the disk offering."
    required: false
  cpu_number:
    default: null
    description:
      - "The number of CPUs of the service offering."
    required: false
  cpu_speed:
    default: null
    description:
      - "The CPU speed of the service offering in MHz."
    required: false
  customized_iops:
    default: false
    description:
      - "Whether compute offering iops is custom or not."
    required: false
  deployment_planner:
    default: null
    description:
      - "The deployment planner heuristics used to deploy a VM of this offering."
      - "If C(null), the value of global config C(vm.deployment.planner) is used."
    required: false
  display_text:
    default: null
    description:
      - "Display text of the service offering."
      - "If not set, C(name) will be used as C(display_text) while creating."
    required: false
  domain:
    default: null
    description:
      - "Domain the service offering is related to."
    required: false
  host_tags:
    default: null
    description:
      - "The host tagsfor this service offering."
    required: false
  hypervisor_snapshot_reserve:
    default: null
    description:
      - "Hypervisor snapshot reserve space as a percent of a volume."
      - "Only for managed storage using Xen or VMware."
    required: false
  iops_read_rate:
    default: null
    description:
      - "IO requests read rate of the disk offering."
    required: false
  iops_write_rate:
    default: null
    description:
      - "IO requests write rate of the disk offering."
    required: false
  is_system:
    default: false
    description:
      - "Whether it is a system VM offering or not."
    required: false
  is_volatile:
    default: false
    description:
      - "Whether the virtual machine needs to be volatile or not."
      - "Every reboot of VM the root disk is detached then destroyed and a fresh root disk is created and attached to VM."
    required: false
  limit_cpu_use:
    default: null
    description:
      - "Restrict the CPU usage to committed service offering."
    required: false
  max_iops:
    default: null
    description:
      - "Max. iops of the compute offering."
    required: false
  memory:
    default: null
    description:
      - "The total memory of the service offering in MB."
    required: false
  min_iops:
    default: null
    description:
      - "Min. iops of the compute offering."
    required: false
  name:
    description:
      - "Name of the service offering."
    required: true
  network_rate:
    default: null
    description:
      - "Data transfer rate in Mb/s allowed."
      - "Supported only for non-system offering and system offerings having C(system_vm_type=domainrouter)."
    required: false
  offer_ha:
    default: false
    description:
      - "Whether HA is set for the service offering."
    required: false
  provisioning_type:
    choices:
      - thin
      - sparse
      - fat
    default: null
    description:
      - "Provisioning type used to create volumes."
    required: false
  service_offering_details:
    default: null
    description:
      - "Details for planner, used to store specific parameters."
    required: false
  state:
    choices:
      - present
      - absent
    default: present
    description:
      - "State of the service offering."
    required: false
  storage_type:
    choices:
      - local
      - shared
    default: null
    description:
      - "The storage type of the service offering."
    required: false
  system_vm_type:
    choices:
      - domainrouter
      - consoleproxy
      - secondarystoragevm
    default: null
    description:
      - "The system VM type."
      - "Required if C(is_system=true)."
    required: false
  tags:
    default: null
    description:
      - "The tags for this service offering."
    required: false
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create a non-volatile compute service offering with local storage
- local_action:
    module: cs_serviceoffer
    name: Micro
    description: "Micro 512mb 1cpu"
    cpu_number: 1
    cpu_speed: 2198
    memory: 512
    host_tags: eco
    storage_type: local

# Create a volatile compute service offering with shared storage
- local_action:
    module: cs_serviceoffer
    name: Tiny
    description: "Tiny 1gb 1cpu"
    cpu_number: 1
    cpu_speed: 2198
    memory: 1024
    storage_type: shared
    is_volatile: true
    host_tags: eco
    tags: eco

# Create or update a volatile compute service offering with shared storage
- local_action:
    module: cs_serviceoffer
    name: Tiny
    description: "Tiny 1gb 1cpu"
    cpu_number: 1
    cpu_speed: 2198
    memory: 1024
    storage_type: shared
    is_volatile: true
    host_tags: eco
    tags: eco

# Remove a compute service offering
- local_action:
    module: cs_serviceoffer
    name: Tiny
    state: absent

# Create or update a system offering for the console proxy
- local_action:
    module: cs_serviceoffer
    name: "System Offering for Console Proxy 2GB"
    description: "System Offering for Console Proxy 2GB RAM"
    is_system: true
    system_vm_type: consoleproxy
    cpu_number: 1
    cpu_speed: 2198
    memory: 2048
    storage_type: shared
    tags: perf

# Remove a system offering
- local_action:
    module: cs_serviceoffer
    name: "System Offering for Console Proxy 2GB"
    is_system: true
    state: absent
'''

RETURN = '''
---
id:
  description: "UUID of the service offering."
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackServiceOffering(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackServiceOffering, self).__init__(module)
        self.returns = {
            'cpunumber': 'cpu_number',
            'cpuspeed': 'cpu_speed',
            'isvolatile': 'is_volatile',
            'deploymentplanner': 'deployment_planner',
            'diskBytesReadRate': 'bytes_read_rate',
            'diskBytesWriteRate': 'bytes_write_rate',
            'diskIopsReadRate': 'iops_read_rate',
            'diskIopsWriteRate': 'iops_write_rate',
            'hosttags': 'host_tags',
            'hypervisorsnapshotreserve': 'hypervisor_snapshot_reserve',
            'iscustomizediops': 'customized_iops',
            'issystem': 'is_system',
            'isvolatile': 'is_volatile',
            'limitcpuuse': 'limit_cpu_use',
            'maxiops': 'max_iops',
            'miniops': 'min_iops',
            'memory': 'memory',
            'networkrate': 'network_rate',
            'offerha': 'offer_ha',
            'provisioningtype': 'provisioning_type',
            'serviceofferingdetails': 'service_offering_details',
            'storagetype': 'storage_type',
            'systemvmtype': 'system_vm_type',
        }
        self.service_offering = None

    def get_service_offering(self):
        if not self.service_offering:
            service_offering = self.module.params.get('name')
            args = {
                'domainid': self.get_domain(key='id'),
                'issystem': self.module.params.get('is_system'),
                'systemvmtype': self.module.params.get('system_vm_type'),
            }
            service_offerings = self.cs.listServiceOfferings(**args)
            if service_offerings:
                for s in service_offerings['serviceoffering']:
                    if service_offering in [s['name'], s['displaytext'], s['id']]:
                        self.service_offering = s
                        break
        return self.service_offering

    def present_service_offering(self):
        service_offering = self.get_service_offering()
        if not service_offering:
            service_offering = self._create(service_offering)
        else:
            service_offering = self._update(service_offering)

        if service_offering:
            service_offering = self.ensure_tags(resource=service_offering, resource_type='ServiceOffering')

        return service_offering

    def absent_service_offering(self):
        service_offering = self.get_service_offering()
        args = {
            'id': service_offering['id'],
        }
        if service_offering:
            if not self.module.check_mode:
                res = self.cs.deleteServiceOffering(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return service_offering

    def _create(self, service_offering):
        self.result['changed'] = True
        args = {
            'name': self.module.params.get('name'),
            'displayname': self.get_or_fallback('display_text', 'name'),
            'bytesreadrate': self.module.params.get('bytes_read_rate'),
            'byteswriterate': self.module.params.get('bytes_write_rate'),
            'cpunumber': self.module.params.get('cpu_number'),
            'cpuspeed': self.module.params.get('cpu_speed'),
            'customizediops': self.module.params.get('customized_iops'),
            'deploymentplanner': self.module.params.get('deployment_planner'),
            'domainid': self.get_domain(key='id'),
            'hosttags': ','.join(self.module.params.get('host_tags') or []),
            'hypervisorsnapshotreserve': self.module.params.get('hypervisor_snapshot_reserve'),
            'iopsreadrate': self.module.params.get('iops_read_rate'),
            'iopswriterate': self.module.params.get('iops_write_rate'),
            'issystem': self.module.params.get('is_system'),
            'isvolatile': self.module.params.get('is_volatile'),
            'maxiops': self.module.params.get('max_iops'),
            'miniops': self.module.params.get('min_iops'),
            'memory': self.module.params.get('memory'),
            'networkrate': self.module.params.get('network_rate'),
            'offerha': self.module.params.get('offer_ha'),
            'provisioningtype': self.module.params.get('provisioning_type'),
            'serviceofferingdetails': self.module.params.get('service_offering_details'),
            'storagetype': self.module.params.get('storage_type'),
            'systemvmtype': self.module.params.get('system_vm_type'),
        }
        if not self.module.check_mode:
            service_offering = self.cs.createServiceOffering(**args)
            if service_offering and 'errortext' in service_offering:
                self.module.fail_json(msg="Failed: '%s'" % service_offering['errortext'])
        return service_offering

    def _update(self, service_offering):
        args = {
            'id': service_offering['id'],
            'name': self.module.params.get('name'),
            'displayname': self.get_or_fallback('display_text', 'name'),
        }
        if self.has_changed(args, service_offering):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.cs.updateServiceOffering(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                service_offering = res['serviceoffering']
        return service_offering

def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        display_name=dict(default=None),
        bytes_read_rate=dict(default=None),
        bytes_write_rate=dict(default=None),
        cpu_number=dict(type='int', default=None),
        cpu_speed=dict(type='int', default=None),
        customized_iops=dict(type='bool', default=None),
        deployment_planner=dict(default=None),
        domain=dict(default=None),
        host_tags=dict(type='list', default=None),
        hypervisor_snapshot_reserve=dict(type='int', default=None),
        iops_read_rate=dict(type='int', default=None),
        iops_write_rate=dict(type='int', default=None),
        is_system=dict(type='bool', default=False),
        is_volatile=dict(type='bool', default=None),
        limit_cpu_use=dict(default=None),
        max_iops=dict(type='int', default=None),
        min_iops=dict(type='int', default=None),
        memory=dict(type='int', default=None),
        network_rate=dict(type='int', default=None),
        offer_ha=dict(type='bool', default=None),
        provisioning_type=dict(choices=['thin', 'sparse', 'fat'], default=None),
        service_offering_details=dict(type='bool', default=None),
        storage_type=dict(choice=['local', 'shared'], default=None),
        system_vm_type=dict(choice=['domainrouter', 'consoleproxy', 'secondarystoragevm'], default=None),
        tags=dict(type='list', aliases=['tag'], default=None),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_if=[
            ('is_system', True, ['system_vm_type']),
        ],
        supports_check_mode=True
    )

    try:
        acs_so = AnsibleCloudStackServiceOffering(module)

        state = module.params.get('state')
        if state == "absent":
            service_offering = acs_so.absent_service_offering()
        else:
            service_offering = acs_so.present_service_offering()

        result = acs_so.get_result(service_offering)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
