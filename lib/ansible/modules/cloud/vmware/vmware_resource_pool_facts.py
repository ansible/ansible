#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_resource_pool_facts
short_description: Gathers facts about resource pool information
description:
- This module can be used to gather facts about all resource configuration information.
version_added: '2.6'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather resource pool facts about all resource pools available
  vmware_resource_pool_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
  register: rp_facts
  delegate_to: localhost
'''

RETURN = r'''
resource_pool_facts:
    description: metadata about resource pool configuration
    returned: on success
    type: list
    sample: [
        {
            "cpu_allocation_expandable_reservation": false,
            "cpu_allocation_limit": 4121,
            "cpu_allocation_overhead_limit": null,
            "cpu_allocation_reservation": 4121,
            "cpu_allocation_shares": 9000,
            "cpu_allocation_shares_level": "custom",
            "mem_allocation_expandable_reservation": false,
            "mem_allocation_limit": 961,
            "mem_allocation_overhead_limit": null,
            "mem_allocation_reservation": 961,
            "mem_allocation_shares": 9000,
            "mem_allocation_shares_level": "custom",
            "name": "Resources",
            "overall_status": "green",
            "owner": "DC0_H0",
            "runtime_cpu_max_usage": 4121,
            "runtime_cpu_overall_usage": 0,
            "runtime_cpu_reservation_used": 0,
            "runtime_cpu_reservation_used_vm": 0,
            "runtime_cpu_unreserved_for_pool": 4121,
            "runtime_cpu_unreserved_for_vm": 4121,
            "runtime_memory_max_usage": 1007681536,
            "runtime_memory_overall_usage": 0,
            "runtime_memory_reservation_used": 0,
            "runtime_memory_reservation_used_vm": 0,
            "runtime_memory_unreserved_for_pool": 1007681536,
            "runtime_memory_unreserved_for_vm": 1007681536
        },
    ]
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, get_all_objs


class ResourcePoolFactsManager(PyVmomi):
    def __init__(self, module):
        super(ResourcePoolFactsManager, self).__init__(module)

    def gather_rp_facts(self):
        resource_pool_facts = []
        rps = get_all_objs(self.content, [vim.ResourcePool])
        for rp in rps:
            tmp_facts = dict(
                name=rp.name,
                cpu_allocation_reservation=rp.config.cpuAllocation.reservation,
                cpu_allocation_expandable_reservation=rp.config.cpuAllocation.expandableReservation,
                cpu_allocation_limit=rp.config.cpuAllocation.limit,
                cpu_allocation_shares=rp.config.cpuAllocation.shares.shares,
                cpu_allocation_shares_level=rp.config.cpuAllocation.shares.level,
                cpu_allocation_overhead_limit=rp.config.cpuAllocation.overheadLimit,
                mem_allocation_reservation=rp.config.memoryAllocation.reservation,
                mem_allocation_expandable_reservation=rp.config.memoryAllocation.expandableReservation,
                mem_allocation_limit=rp.config.memoryAllocation.limit,
                mem_allocation_shares=rp.config.memoryAllocation.shares.shares,
                mem_allocation_shares_level=rp.config.memoryAllocation.shares.level,
                mem_allocation_overhead_limit=rp.config.memoryAllocation.overheadLimit,
                owner=rp.owner.name,
                overall_status=rp.summary.runtime.overallStatus,
                runtime_cpu_reservation_used=rp.summary.runtime.cpu.reservationUsed,
                runtime_cpu_reservation_used_vm=rp.summary.runtime.cpu.reservationUsedForVm,
                runtime_cpu_unreserved_for_pool=rp.summary.runtime.cpu.unreservedForPool,
                runtime_cpu_unreserved_for_vm=rp.summary.runtime.cpu.unreservedForVm,
                runtime_cpu_overall_usage=rp.summary.runtime.cpu.overallUsage,
                runtime_cpu_max_usage=rp.summary.runtime.cpu.maxUsage,
                runtime_memory_reservation_used=rp.summary.runtime.memory.reservationUsed,
                runtime_memory_reservation_used_vm=rp.summary.runtime.memory.reservationUsedForVm,
                runtime_memory_unreserved_for_pool=rp.summary.runtime.memory.unreservedForPool,
                runtime_memory_unreserved_for_vm=rp.summary.runtime.memory.unreservedForVm,
                runtime_memory_overall_usage=rp.summary.runtime.memory.overallUsage,
                runtime_memory_max_usage=rp.summary.runtime.memory.maxUsage,
            )

            resource_pool_facts.append(tmp_facts)
        return resource_pool_facts


def main():
    argument_spec = vmware_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    vmware_rp_mgr = ResourcePoolFactsManager(module)
    module.exit_json(changed=False, resource_pool_facts=vmware_rp_mgr.gather_rp_facts())


if __name__ == "__main__":
    main()
