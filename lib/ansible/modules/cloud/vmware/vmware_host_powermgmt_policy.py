#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
#
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
module: vmware_host_powermgmt_policy
short_description: Manages the Power Management Policy of an ESXI host system
description:
- This module can be used to manage the Power Management Policy of ESXi host systems in given vCenter infrastructure.
version_added: 2.8
author:
- Christian Kotte (@ckotte) <christian.kotte@gmx.de>
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  policy:
    description:
    - Set the Power Management Policy of the host system.
    choices: [ 'high-performance', 'balanced', 'low-power', 'custom' ]
    default: 'balanced'
    type: str
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - This is required parameter if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - This is required parameter if C(esxi_hostname) is not specified.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Set the Power Management Policy of a host system to high-performance
  vmware_host_powermgmt_policy:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_host }}'
    policy: high-performance
    validate_certs: no
  delegate_to: localhost

- name: Set the Power Management Policy of all host systems from cluster to high-performance
  vmware_host_powermgmt_policy:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
    policy: high-performance
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
result:
    description: metadata about host system's Power Management Policy
    returned: always
    type: dict
    sample: {
        "changed": true,
        "result": {
            "esxi01": {
                "changed": true,
                "current_state": "high-performance",
                "desired_state": "high-performance",
                "msg": "Power policy changed",
                "previous_state": "balanced"
            }
        }
    }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VmwareHostPowerManagement(PyVmomi):
    """
    Class to manage power management policy of an ESXi host system
    """
    def __init__(self, module):
        super(VmwareHostPowerManagement, self).__init__(module)
        cluster_name = self.params.get('cluster_name')
        esxi_host_name = self.params.get('esxi_hostname')
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system with given configuration.")

    def ensure(self):
        """
        Manage power management policy of an ESXi host system
        """
        results = dict(changed=False, result=dict())
        policy = self.params.get('policy')
        host_change_list = []
        power_policies = {
            'high-performance': {
                'key': 1,
                'short_name': 'static'
            },
            'balanced': {
                'key': 2,
                'short_name': 'dynamic'
            },
            'low-power': {
                'key': 3,
                'short_name': 'low'
            },
            'custom': {
                'key': 4,
                'short_name': 'custom'
            }
        }

        for host in self.hosts:
            changed = False
            results['result'][host.name] = dict(msg='')

            power_system = host.configManager.powerSystem

            # get current power policy
            power_system_info = power_system.info
            current_host_power_policy = power_system_info.currentPolicy

            # the "name" and "description" parameters are pretty useless
            # they store only strings containing "PowerPolicy.<shortName>.name" and "PowerPolicy.<shortName>.description"
            if current_host_power_policy.shortName == "static":
                current_policy = 'high-performance'
            elif current_host_power_policy.shortName == "dynamic":
                current_policy = 'balanced'
            elif current_host_power_policy.shortName == "low":
                current_policy = 'low-power'
            elif current_host_power_policy.shortName == "custom":
                current_policy = 'custom'

            results['result'][host.name]['desired_state'] = policy

            # Don't do anything if the power policy is already configured
            if current_host_power_policy.key == power_policies[policy]['key']:
                results['result'][host.name]['changed'] = changed
                results['result'][host.name]['previous_state'] = current_policy
                results['result'][host.name]['current_state'] = policy
                results['result'][host.name]['msg'] = "Power policy is already configured"
            else:
                # get available power policies and check if policy is included
                supported_policy = False
                power_system_capability = power_system.capability
                available_host_power_policies = power_system_capability.availablePolicy
                for available_policy in available_host_power_policies:
                    if available_policy.shortName == power_policies[policy]['short_name']:
                        supported_policy = True
                if supported_policy:
                    if not self.module.check_mode:
                        try:
                            power_system.ConfigurePowerPolicy(key=power_policies[policy]['key'])
                            changed = True
                            results['result'][host.name]['changed'] = True
                            results['result'][host.name]['msg'] = "Power policy changed"
                        except vmodl.fault.InvalidArgument:
                            self.module.fail_json(msg="Invalid power policy key provided for host '%s'" % host.name)
                        except vim.fault.HostConfigFault as host_config_fault:
                            self.module.fail_json(msg="Failed to configure power policy for host '%s': %s" %
                                                  (host.name, to_native(host_config_fault.msg)))
                    else:
                        changed = True
                        results['result'][host.name]['changed'] = True
                        results['result'][host.name]['msg'] = "Power policy will be changed"
                    results['result'][host.name]['previous_state'] = current_policy
                    results['result'][host.name]['current_state'] = policy
                else:
                    changed = False
                    results['result'][host.name]['changed'] = changed
                    results['result'][host.name]['previous_state'] = current_policy
                    results['result'][host.name]['current_state'] = current_policy
                    self.module.fail_json(msg="Power policy '%s' isn't supported for host '%s'" %
                                          (policy, host.name))

            host_change_list.append(changed)

        if any(host_change_list):
            results['changed'] = True
        self.module.exit_json(**results)


def main():
    """
    Main
    """
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        policy=dict(type='str', default='balanced',
                    choices=['high-performance', 'balanced', 'low-power', 'custom']),
        esxi_hostname=dict(type='str', required=False),
        cluster_name=dict(type='str', required=False),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[
                               ['cluster_name', 'esxi_hostname'],
                           ],
                           supports_check_mode=True
                           )

    host_power_management = VmwareHostPowerManagement(module)
    host_power_management.ensure()


if __name__ == '__main__':
    main()
