#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cs_service_offering
description:
  - Create and delete service offerings for guest and system VMs.
  - Update display_text of existing service offering.
short_description: Manages service offerings on Apache CloudStack based clouds.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  bytes_read_rate:
    description:
      - Bytes read rate of the disk offering.
  bytes_write_rate:
    description:
      - Bytes write rate of the disk offering.
  cpu_number:
    description:
      - The number of CPUs of the service offering.
  cpu_speed:
    description:
      - The CPU speed of the service offering in MHz.
  limit_cpu_usage:
    description:
      - Restrict the CPU usage to committed service offering.
    type: bool
  deployment_planner:
    description:
      - The deployment planner heuristics used to deploy a VM of this offering.
      - If not set, the value of global config C(vm.deployment.planner) is used.
  display_text:
    description:
      - Display text of the service offering.
      - If not set, C(name) will be used as C(display_text) while creating.
  domain:
    description:
      - Domain the service offering is related to.
      - Public for all domains and subdomains if not set.
  host_tags:
    description:
      - The host tagsfor this service offering.
    aliases:
      - host_tag
  hypervisor_snapshot_reserve:
    description:
      - Hypervisor snapshot reserve space as a percent of a volume.
      - Only for managed storage using Xen or VMware.
  disk_iops_customized:
    description:
      - Whether compute offering iops is custom or not.
    default: false
  disk_iops_read_rate:
    description:
      - IO requests read rate of the disk offering.
  disk_iops_write_rate:
    description:
      - IO requests write rate of the disk offering.
  disk_iops_max:
    description:
      - Max. iops of the compute offering.
  disk_iops_min:
    description:
      - Min. iops of the compute offering.
  is_system:
    description:
      - Whether it is a system VM offering or not.
    type: bool
    default: no
  is_volatile:
    description:
      - Whether the virtual machine needs to be volatile or not.
      - Every reboot of VM the root disk is detached then destroyed and a fresh root disk is created and attached to VM.
    type: bool
    default: no
  memory:
    description:
      - The total memory of the service offering in MB.
  name:
    description:
      - Name of the service offering.
    required: true
  network_rate:
    description:
      - Data transfer rate in Mb/s allowed.
      - Supported only for non-system offering and system offerings having C(system_vm_type=domainrouter).
  offer_ha:
    description:
      - Whether HA is set for the service offering.
    type: bool
    default: no
  provisioning_type:
    description:
      - Provisioning type used to create volumes.
    choices:
      - thin
      - sparse
      - fat
  service_offering_details:
    description:
      - Details for planner, used to store specific parameters.
  state:
    description:
      - State of the service offering.
    choices:
      - present
      - absent
    default: present
  storage_type:
    description:
      - The storage type of the service offering.
    choices:
      - local
      - shared
  system_vm_type:
    description:
      - The system VM type.
      - Required if C(is_system=true).
    choices:
      - domainrouter
      - consoleproxy
      - secondarystoragevm
  storage_tags:
    description:
      - The storage tags for this service offering.
    aliases:
      - storage_tag
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a non-volatile compute service offering with local storage
  local_action:
    module: cs_service_offering
    name: Micro
    display_text: Micro 512mb 1cpu
    cpu_number: 1
    cpu_speed: 2198
    memory: 512
    host_tags: eco
    storage_type: local

- name: Create a volatile compute service offering with shared storage
  local_action:
    module: cs_service_offering
    name: Tiny
    display_text: Tiny 1gb 1cpu
    cpu_number: 1
    cpu_speed: 2198
    memory: 1024
    storage_type: shared
    is_volatile: true
    host_tags: eco
    storage_tags: eco

- name: Create or update a volatile compute service offering with shared storage
  local_action:
    module: cs_service_offering
    name: Tiny
    display_text: Tiny 1gb 1cpu
    cpu_number: 1
    cpu_speed: 2198
    memory: 1024
    storage_type: shared
    is_volatile: yes
    host_tags: eco
    storage_tags: eco

- name: Remove a compute service offering
  local_action:
    module: cs_service_offering
    name: Tiny
    state: absent

- name: Create or update a system offering for the console proxy
  local_action:
    module: cs_service_offering
    name: System Offering for Console Proxy 2GB
    display_text: System Offering for Console Proxy 2GB RAM
    is_system: yes
    system_vm_type: consoleproxy
    cpu_number: 1
    cpu_speed: 2198
    memory: 2048
    storage_type: shared
    storage_tags: perf

- name: Remove a system offering
  local_action:
    module: cs_service_offering
    name: System Offering for Console Proxy 2GB
    is_system: yes
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the service offering
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
cpu_number:
  description: Number of CPUs in the service offering
  returned: success
  type: int
  sample: 4
cpu_speed:
  description: Speed of CPUs in MHz in the service offering
  returned: success
  type: int
  sample: 2198
disk_iops_max:
  description: Max iops of the disk offering
  returned: success
  type: int
  sample: 1000
disk_iops_min:
  description: Min iops of the disk offering
  returned: success
  type: int
  sample: 500
disk_bytes_read_rate:
  description: Bytes read rate of the service offering
  returned: success
  type: int
  sample: 1000
disk_bytes_write_rate:
  description: Bytes write rate of the service offering
  returned: success
  type: int
  sample: 1000
disk_iops_read_rate:
  description: IO requests per second read rate of the service offering
  returned: success
  type: int
  sample: 1000
disk_iops_write_rate:
  description: IO requests per second write rate of the service offering
  returned: success
  type: int
  sample: 1000
created:
  description: Date the offering was created
  returned: success
  type: string
  sample: 2017-11-19T10:48:59+0000
display_text:
  description: Display text of the offering
  returned: success
  type: string
  sample: Micro 512mb 1cpu
domain:
  description: Domain the offering is into
  returned: success
  type: string
  sample: ROOT
host_tags:
  description: List of host tags
  returned: success
  type: list
  sample: [ 'eco' ]
storage_tags:
  description: List of storage tags
  returned: success
  type: list
  sample: [ 'eco' ]
is_system:
  description: Whether the offering is for system VMs or not
  returned: success
  type: bool
  sample: false
is_iops_customized:
  description: Whether the offering uses custom IOPS or not
  returned: success
  type: bool
  sample: false
is_volatile:
  description: Whether the offering is volatile or not
  returned: success
  type: bool
  sample: false
limit_cpu_usage:
  description: Whether the CPU usage is restricted to committed service offering
  returned: success
  type: bool
  sample: false
memory:
  description: Memory of the system offering
  returned: success
  type: int
  sample: 512
name:
  description: Name of the system offering
  returned: success
  type: string
  sample: Micro
offer_ha:
  description: Whether HA support is enabled in the offering or not
  returned: success
  type: bool
  sample: false
provisioning_type:
  description: Provisioning type used to create volumes
  returned: success
  type: string
  sample: thin
storage_type:
  description: Storage type used to create volumes
  returned: success
  type: string
  sample: shared
system_vm_type:
  description: System VM type of this offering
  returned: success
  type: string
  sample: consoleproxy
service_offering_details:
  description: Additioanl service offering details
  returned: success
  type: dict
  sample: "{'vgpuType': 'GRID K180Q','pciDevice':'Group of NVIDIA Corporation GK107GL [GRID K1] GPUs'}"
network_rate:
  description: Data transfer rate in megabits per second allowed
  returned: success
  type: int
  sample: 1000
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackServiceOffering(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackServiceOffering, self).__init__(module)
        self.returns = {
            'cpunumber': 'cpu_number',
            'cpuspeed': 'cpu_speed',
            'deploymentplanner': 'deployment_planner',
            'diskBytesReadRate': 'disk_bytes_read_rate',
            'diskBytesWriteRate': 'disk_bytes_write_rate',
            'diskIopsReadRate': 'disk_iops_read_rate',
            'diskIopsWriteRate': 'disk_iops_write_rate',
            'maxiops': 'disk_iops_max',
            'miniops': 'disk_iops_min',
            'hypervisorsnapshotreserve': 'hypervisor_snapshot_reserve',
            'iscustomized': 'is_customized',
            'iscustomizediops': 'is_iops_customized',
            'issystem': 'is_system',
            'isvolatile': 'is_volatile',
            'limitcpuuse': 'limit_cpu_usage',
            'memory': 'memory',
            'networkrate': 'network_rate',
            'offerha': 'offer_ha',
            'provisioningtype': 'provisioning_type',
            'serviceofferingdetails': 'service_offering_details',
            'storagetype': 'storage_type',
            'systemvmtype': 'system_vm_type',
            'tags': 'storage_tags',
        }

    def get_service_offering(self):
        args = {
            'name': self.module.params.get('name'),
            'domainid': self.get_domain(key='id'),
            'issystem': self.module.params.get('is_system'),
            'systemvmtype': self.module.params.get('system_vm_type'),
        }
        service_offerings = self.query_api('listServiceOfferings', **args)
        if service_offerings:
            return service_offerings['serviceoffering'][0]

    def present_service_offering(self):
        service_offering = self.get_service_offering()
        if not service_offering:
            service_offering = self._create_offering(service_offering)
        else:
            service_offering = self._update_offering(service_offering)

        return service_offering

    def absent_service_offering(self):
        service_offering = self.get_service_offering()
        if service_offering:
            self.result['changed'] = True
            if not self.module.check_mode:
                args = {
                    'id': service_offering['id'],
                }
                self.query_api('deleteServiceOffering', **args)
        return service_offering

    def _create_offering(self, service_offering):
        self.result['changed'] = True

        system_vm_type = self.module.params.get('system_vm_type')
        is_system = self.module.params.get('is_system')

        required_params = []
        if is_system and not system_vm_type:
            required_params.append('system_vm_type')
        self.module.fail_on_missing_params(required_params=required_params)

        args = {
            'name': self.module.params.get('name'),
            'displaytext': self.get_or_fallback('display_text', 'name'),
            'bytesreadrate': self.module.params.get('disk_bytes_read_rate'),
            'byteswriterate': self.module.params.get('disk_bytes_write_rate'),
            'cpunumber': self.module.params.get('cpu_number'),
            'cpuspeed': self.module.params.get('cpu_speed'),
            'customizediops': self.module.params.get('is_iops_customized'),
            'deploymentplanner': self.module.params.get('deployment_planner'),
            'domainid': self.get_domain(key='id'),
            'hosttags': self.module.params.get('host_tags'),
            'hypervisorsnapshotreserve': self.module.params.get('hypervisor_snapshot_reserve'),
            'iopsreadrate': self.module.params.get('disk_iops_read_rate'),
            'iopswriterate': self.module.params.get('disk_iops_write_rate'),
            'maxiops': self.module.params.get('disk_iops_max'),
            'miniops': self.module.params.get('disk_iops_min'),
            'issystem': is_system,
            'isvolatile': self.module.params.get('is_volatile'),
            'memory': self.module.params.get('memory'),
            'networkrate': self.module.params.get('network_rate'),
            'offerha': self.module.params.get('offer_ha'),
            'provisioningtype': self.module.params.get('provisioning_type'),
            'serviceofferingdetails': self.module.params.get('service_offering_details'),
            'storagetype': self.module.params.get('storage_type'),
            'systemvmtype': system_vm_type,
            'tags': self.module.params.get('storage_tags'),
            'limitcpuuse': self.module.params.get('limit_cpu_usage')
        }
        if not self.module.check_mode:
            res = self.query_api('createServiceOffering', **args)
            service_offering = res['serviceoffering']
        return service_offering

    def _update_offering(self, service_offering):
        args = {
            'id': service_offering['id'],
            'name': self.module.params.get('name'),
            'displaytext': self.get_or_fallback('display_text', 'name'),
        }
        if self.has_changed(args, service_offering):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('updateServiceOffering', **args)
                service_offering = res['serviceoffering']
        return service_offering

    def get_result(self, service_offering):
        super(AnsibleCloudStackServiceOffering, self).get_result(service_offering)
        if service_offering:
            if 'hosttags' in service_offering:
                self.result['host_tags'] = service_offering['hosttags'].split(',') or [service_offering['hosttags']]

            # Prevent confusion, the api returns a tags key for storage tags.
            if 'tags' in service_offering:
                self.result['storage_tags'] = service_offering['tags'].split(',') or [service_offering['tags']]
            if 'tags' in self.result:
                del self.result['tags']

        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        display_text=dict(),
        cpu_number=dict(type='int'),
        cpu_speed=dict(type='int'),
        limit_cpu_usage=dict(type='bool'),
        deployment_planner=dict(),
        domain=dict(),
        host_tags=dict(type='list', aliases=['host_tag']),
        hypervisor_snapshot_reserve=dict(type='int'),
        disk_bytes_read_rate=dict(type='int'),
        disk_bytes_write_rate=dict(type='int'),
        disk_iops_customized=dict(type='bool'),
        disk_iops_read_rate=dict(type='int'),
        disk_iops_write_rate=dict(type='int'),
        disk_iops_max=dict(type='int'),
        disk_iops_min=dict(type='int'),
        is_system=dict(type='bool', default=False),
        is_volatile=dict(type='bool'),
        is_iops_customized=dict(type='bool'),
        memory=dict(type='int'),
        network_rate=dict(type='int'),
        offer_ha=dict(type='bool'),
        provisioning_type=dict(choices=['thin', 'sparse', 'fat']),
        service_offering_details=dict(type='bool'),
        storage_type=dict(choice=['local', 'shared']),
        system_vm_type=dict(choice=['domainrouter', 'consoleproxy', 'secondarystoragevm']),
        storage_tags=dict(type='list', aliases=['storage_tag']),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_so = AnsibleCloudStackServiceOffering(module)

    state = module.params.get('state')
    if state == "absent":
        service_offering = acs_so.absent_service_offering()
    else:
        service_offering = acs_so.present_service_offering()

    result = acs_so.get_result(service_offering)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
