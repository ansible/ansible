#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 VMware, Inc.
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
short_description: Manage distributed vSwitch Network IO Control resource
description:
    - Manages distributed vSwitch Network IO Control Resource
version_added: future
author:
- Joseph Andreatta (@vmwjoseph) <joseph () vmware.com>
notes:
    - Tested on vSphere 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter_name:
        description:
            - The name of the datacenter that will contain the dvSwitch
        required: True
    switch_name:
        description:
            - The name of the switch to create or remove
        required: True
    resource_name:
        description:
            - The name of the NICO resource
        required: True
    limit:
        description:
            - The maximum allowed usage for a traffic class belonging to this resource pool per host physical NIC.
        default: -1
        required: False
    reservation
        description:
            - (Ignored if NIOC version is set to version2) Amount of bandwidth resource that is guaranteed available
            to the host infrastructure traffic class. If the utilization is less than the reservation, the extra bandwidth
            is used for other host infrastructure traffic class types. Reservation is not allowed to exceed the value of limit,
            if limit is set. Unit is Mbits/sec.
        default: 0
        required: False
    shares_level:
        description:
            - The allocation level. The level is a simplified view of shares. Levels map to a pre-determined set of numeric values for shares.
        default: normal
        choices:
            - 'custom'
            - 'high'
            - 'low'
            - 'normal'
        required: False
    shares:
        description:
            - (Ignored if shares_level is not set to 'custom').  The number of shares allocated.
        default: 50
        required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Configure NIOC resource
  local_action:
    module: vmware_dvswitch_nioc_resource
    hostname: vcenter_ip_or_hostname
    username: vcenter_username
    password: vcenter_password
    switch_name: dvSwitch
    resource_name: vmotion
    limit: -1
    reservation: 1024
    shares_level: normal
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI,
                                         connect_to_api,
                                         find_datacenter_by_name,
                                         find_dvs_by_name,
                                         vmware_argument_spec,
                                         wait_for_task
                                         )


class VMwareDVSwitchNIOCResource(object):

    def __init__(self, module):
        self.module = module
        self.dvs = None
        self.switch_name = self.module.params['switch_name']
        self.resource_name = self.module.params['resource_name']
        self.limit = self.module.params['limit']
        self.reservation = self.module.params['reservation']
        self.shares_level = self.module.params['shares_level']
        self.shares = self.module.params['shares']
        self.content = connect_to_api(module)

    def find_netioc_by_key(self):
        config = None
        if self.dvs.config.networkResourceControlVersion == "version3":
            config = self.dvs.config.infrastructureTrafficResourceConfig
        elif self.dvs.config.networkResourceControlVersion == "version2":
            config = self.dvs.networkResourcePool

        for obj in config:
            if obj.key == self.resource_name:
                return obj
        return None

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def check_resource_state(self):
        changed=False
        result=None

        self.dvs = find_dvs_by_name(self.content, self.switch_name)

        if self.dvs is None:
            self.module.fail_json(msg="DVS named '%s' was not found" % self.switch_name)

        resource_cfg = self.find_netioc_by_key()
        if resource_cfg is None:
            self.module.fail_json(msg="NetIOC resource named '%s' was not found" % self.resource_name)

        rc = {
             "limit": resource_cfg.allocationInfo.limit,
             "shares_level": resource_cfg.allocationInfo.shares.level
             }
        if resource_cfg.allocationInfo.shares.level == 'custom':
            rc["shares"] = resource_cfg.allocationInfo.shares.shares
        if self.dvs.config.networkResourceControlVersion == "version3":
            rc["reservation"] = resource_cfg.allocationInfo.reservation

        for k,v in rc.items():
            if v != getattr(self,k):
                changed = True
                if not self.module.check_mode:
                    if self.dvs.config.networkResourceControlVersion == 'version3':

                        allocation = vim.DistributedVirtualSwitch.HostInfrastructureTrafficResource()
                        allocation.key = self.resource_name
                        allocation.allocationInfo = vim.DistributedVirtualSwitch.HostInfrastructureTrafficResource.ResourceAllocation()
                        allocation.allocationInfo.limit = self.limit
                        allocation.allocationInfo.reservation = self.reservation
                        allocation.allocationInfo.shares = vim.SharesInfo()
                        allocation.allocationInfo.shares.shares = self.shares
                        allocation.allocationInfo.shares.level = self.shares_level

                        spec = vim.DistributedVirtualSwitch.ConfigSpec()
                        spec.configVersion = self.dvs.config.configVersion
                        spec.infrastructureTrafficResourceConfig = [allocation]

                        task = self.dvs.ReconfigureDvs_Task(spec)
                        changed, result = wait_for_task(task)

                    elif self.dvs.config.networkResourceControlVersion == 'version2':
                        spec = vim.DVSNetworkResourcePoolConfigSpec()
                        spec.key = self.resource_name
                        spec.configVersion = resource_cfg.configVersion

                        spec.allocationInfo = vim.DVSNetworkResourcePoolAllocationInfo()
                        spec.allocationInfo.limit = self.limit
                        spec.allocationInfo.shares = vim.SharesInfo()
                        spec.allocationInfo.shares.shares = self.shares
                        spec.allocationInfo.shares.level = self.shares_level
                        attempts = 0
                        while attempts < 3:
                            try:
                                self.dvs.UpdateNetworkResourcePool([spec])
                                break
                            except vim.fault.ConcurrentAccess as e:
                                attempts += 1
                                sleep(5)
                                continue
                        if attempts > 3:
                          self.module.fail_json(msg="vim.fault.ConcurrentAccess failure - out of retries")
                        result = 'Updated %s' % self.resource_name

        self.module.exit_json(changed=changed, result=str(result))


def main():
    argument_spec = vmware_argument_spec()

    argument_spec.update(dict(switch_name=dict(required=True, type='str'),
                              resource_name=dict(required=True, type='str'),
                              limit=dict(default=-1, type='int'),
                              reservation=dict(default=0, type='int'),
                              shares_level=dict(default='normal', choices=['normal', 'custom', 'low', 'high'], type='str'),
                              shares=dict(default=50, type='int')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    try:
        vmware_dvswitch_nioc_resource = VMwareDVSwitchNIOCResource(module)
        vmware_dvswitch_nioc_resource.check_resource_state()
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
