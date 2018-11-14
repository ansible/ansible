#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, VMware, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_dvswitch_nioc_resource
short_description: Manage distributed switch Network IO Control resources.
description:
    - This module can be used to manage distributed switch Network IO Control resource
      allocations for a host infrastructure traffic classes. This module supports
      Network IO Control version2 and version3.
version_added: 2.8
author:
    - Joseph Andreatta (@vmwjoseph)
notes:
    - Tested on vSphere 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch:
        description:
        - The name of the distributed switch.
        required: True
    resources:
        description:
        - 'List of dicts containing
           { name: Resource name is one of the following: "faultTolerance", "hbr", "iSCSI", "management", "nfs", "vdp",
                   "virtualMachine", "vmotion", "vsan"
             limit: The maximum allowed usage for a traffic class belonging to this resource pool per host physical NIC.
                    reservation: (Ignored if NIOC version is set to version2) Amount of bandwidth resource that is
                    guaranteed available to the host infrastructure traffic class. If the utilization is less than the
                    reservation, the extra bandwidth is used for other host infrastructure traffic class types.
                    Reservation is not allowed to exceed the value of limit, if limit is set. Unit is Mbits/sec.
             shares_level: The allocation level ("low", "normal", "high", "custom"). The level is a simplified view
                           of shares. Levels map to a pre-determined set of numeric values for shares.
             shares: Ignored unless shares_level is "custom".  The number of shares allocated.
             reservation: Ignored unless using NIOC version3. Amount of bandwidth resource that is guaranteed
                          available to the host infrastructure traffic class.
           }'
        required: True
extends_documentation_fragment: vmware.documentation
'''

RETURN = r'''
resources_changed:
    description:
    - list of resources which were changed
    returned: success
    type: list
    sample: [ "vmotion", "vsan" ]
'''

EXAMPLES = '''
- name: Configure NIOC resources
  vmware_dvswitch_nioc_resource:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: false
    switch: dvSwitch
    resources:
        - name: vmotion
          limit: -1
          reservation: 128
          shares_level: normal
        - name: vsan
          limit: -1
          shares_level: custom
          shares: 99
          reservation: 256
  delegate_to: localhost
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (PyVmomi,
                                         HAS_PYVMOMI,
                                         connect_to_api,
                                         find_datacenter_by_name,
                                         find_dvs_by_name,
                                         vmware_argument_spec,
                                         wait_for_task
                                         )


class VMwareDVSwitchNIOCResource(PyVmomi):

    def __init__(self, module):
        super(VMwareDVSwitchNIOCResource, self).__init__(module)

        self.dvs = None
        self.switch = module.params['switch']
        self.resources = module.params['resources']

    def find_netioc_by_key(self, resource_name):
        config = None
        if self.dvs.config.networkResourceControlVersion == "version3":
            config = self.dvs.config.infrastructureTrafficResourceConfig
        elif self.dvs.config.networkResourceControlVersion == "version2":
            config = self.dvs.networkResourcePool

        for obj in config:
            if obj.key == resource_name:
                return obj
        return None

    def check_resources(self):
        result = {'changed': False, 'resources_changed': list()}
        changes = list()

        self.dvs = find_dvs_by_name(self.content, self.switch)
        if self.dvs is None:
            self.module.fail_json(msg="DVS named '%s' was not found" % self.switch)

        for resource in self.resources:
            if self.check_resource_state(resource) == 'update':
                changes.append(resource)
                result['resources_changed'].append(resource['name'])

        # Apply all required changes
        if len(changes) > 0:
            result.update(
                changed=True
            )
            if not self.module.check_mode:
                self.set_nioc_resources(changes)

        self.module.exit_json(**result)

    def check_resource_state(self, resource):
        resource_cfg = self.find_netioc_by_key(resource['name'])
        if resource_cfg is None:
            self.module.fail_json(msg="NetIOC resource named '%s' was not found" % resource['name'])

        rc = {
            "limit": resource_cfg.allocationInfo.limit,
            "shares_level": resource_cfg.allocationInfo.shares.level
        }
        if resource_cfg.allocationInfo.shares.level == 'custom':
            rc["shares"] = resource_cfg.allocationInfo.shares.shares
        if self.dvs.config.networkResourceControlVersion == "version3":
            rc["reservation"] = resource_cfg.allocationInfo.reservation

        for k, v in rc.items():
            if k in resource and v != resource[k]:
                return 'update'
        return 'valid'

    def set_nioc_resources(self, resources):
        if self.dvs.config.networkResourceControlVersion == 'version3':
                self._update_version3_resources(resources)
        elif self.dvs.config.networkResourceControlVersion == 'version2':
                self._update_version2_resources(resources)

    def _update_version3_resources(self, resources):
        allocations = list()

        for resource in resources:
            allocation = vim.DistributedVirtualSwitch.HostInfrastructureTrafficResource()
            allocation.allocationInfo = vim.DistributedVirtualSwitch.HostInfrastructureTrafficResource.ResourceAllocation()
            allocation.key = resource['name']
            if 'limit' in resource:
                allocation.allocationInfo.limit = resource['limit']
            if 'reservation' in resource:
                allocation.allocationInfo.reservation = resource['reservation']
            if 'shares_level' in resource:
                allocation.allocationInfo.shares = vim.SharesInfo()
                allocation.allocationInfo.shares.level = resource['shares_level']
                if 'shares' in resource and resource['shares_level'] == 'custom':
                    allocation.allocationInfo.shares.shares = resource['shares']
                elif resource['shares_level'] == 'custom':
                    self.module.fail_json(
                        msg="Resource %s, shares_level set to custom but shares not specified" % resource['name']
                    )

            allocations.append(allocation)

        spec = vim.DistributedVirtualSwitch.ConfigSpec()
        spec.configVersion = self.dvs.config.configVersion
        spec.infrastructureTrafficResourceConfig = allocations

        task = self.dvs.ReconfigureDvs_Task(spec)
        changed, result = wait_for_task(task)
        return changed

    def _update_version2_resources(self, resources):
        allocations = list()

        for resoucre in resources:
            allocation = vim.DVSNetworkResourcePoolConfigSpec()
            allocation.allocationInfo = vim.DVSNetworkResourcePoolAllocationInfo()
            allocation.key = self.resource_name
            allocation.configVersion = self.dvs.config.configVersion
            if 'limit' in resource:
                allocation.allocationInfo.limit = self.limit
            if 'shares_level' in resource:
                allocation.allocationInfo.shares = vim.SharesInfo()
                allocation.allocationInfo.shares.level = resource['shares_level']
                if 'shares' in resource and resource['shares_level'] == 'custom':
                    allocation.allocationInfo.shares.shares = resource['shares']

            allocations.append(allocation)

        self.dvs.UpdateNetworkResourcePool(allocations)
        return True


def main():
    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            switch=dict(required=True, type='str'),
            resources=dict(
                type='list',
                elements='dict',
                options=dict(
                    name=dict(
                        type='str',
                        required=True,
                        choices=[
                            'faultTolerance',
                            'hbr',
                            'iSCSI',
                            'management',
                            'nfs',
                            'vdp',
                            'virtualMachine',
                            'vmotion',
                            'vsan'
                        ]
                    ),
                    limit=dict(type='int', default=-1),
                    shares_level=dict(
                        type='str',
                        required=False,
                        choices=[
                            'low',
                            'normal',
                            'high',
                            'custom'
                        ]
                    ),
                    shares=dict(type='int', required=False),
                    reservation=dict(type='int', default=0)
                )
            ),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        vmware_dvswitch_nioc_resource = VMwareDVSwitchNIOCResource(module)
        vmware_dvswitch_nioc_resource.check_resources()
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=to_native(runtime_fault.msg))
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=to_native(method_fault.msg))
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
