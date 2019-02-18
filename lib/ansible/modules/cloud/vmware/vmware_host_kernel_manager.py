#!/usr/bin/python

# Copyright: (c) 2019, Aaron Longchamps, <a.j.longchamps@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_host_kernel_manager
short_description: Manage kernel module options on ESXi hosts
description:
- This module can be used to manage kernel module options on ESXi hosts.
- All connected ESXi hosts in scope will be configured when specified.
- If a host is not connected at time of configuration, it will be marked as such in the output.
- Kernel module options may require a reboot to take effect which is not covered here.
- You can use M(reboot) or M(vmware_host_powerstate) module to reboot all ESXi host systems.
version_added: '2.8'
author:
- Aaron Longchamps (@alongchamps)
notes:
- Tested on vSphere 6.0
requirements:
- python >= 2.7
- PyVmomi
options:
  esxi_hostname:
    description:
    - Name of the ESXi host to work on.
    - This parameter is required if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the VMware cluster to work on.
    - All ESXi hosts in this cluster will be configured.
    - This parameter is required if C(esxi_hostname) is not specified.
    type: str
  kernel_module_name:
    description:
    - Name of the kernel module to be configured.
    required: true
    type: str
  kernel_module_option:
    description:
    - Specified configurations will be applied to the given module.
    - These values are specified in key=value pairs and separated by a space when there are multiple options.
    required: true
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Configure IPv6 to be off via tcpip4 kernel module
  vmware_host_kernel_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    kernel_module_name: "tcpip4"
    kernel_module_option: "ipv6=0"

- name: Using cluster_name, configure vmw_psp_rr options
  vmware_host_kernel_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ virtual_cluster_name }}'
    kernel_module_name: "vmw_psp_rr"
    kernel_module_option: "maxPathsPerDevice=2"
'''

RETURN = r'''
results:
    description:
    - dict with information on what was changed, by ESXi host in scope.
    returned: success
    type: dict
    sample: {
    "results": {
        "myhost01.example.com": {
            "changed": true,
            "configured_options": "ipv6=0",
            "msg": "Options have been changed on the kernel module",
            "original_options": "ipv6=1"
        }
    }
}
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


class VmwareKernelManager(PyVmomi):
    def __init__(self, module):
        self.module = module
        super(VmwareKernelManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        self.kernel_module_name = self.params.get('kernel_module_name')
        self.kernel_module_option = self.params.get('kernel_module_option')
        self.results = {}

        if not self.hosts:
            self.module.fail_json(msg="Failed to find a host system that matches the specified criteria")

    # find kernel module options for a given kmod_name. If the name is not right, this will throw an exception
    def get_kernel_module_option(self, host, kmod_name):
        host_kernel_manager = host.configManager.kernelModuleSystem

        try:
            return host_kernel_manager.QueryConfiguredModuleOptionString(self.kernel_module_name)
        except vim.fault.NotFound as kernel_fault:
            self.module.fail_json(msg="Failed to find kernel module on host '%s'. More information: %s" % (host.name, to_native(kernel_fault.msg)))

    # configure the provided kernel module with the specified options
    def apply_kernel_module_option(self, host, kmod_name, kmod_option):
        host_kernel_manager = host.configManager.kernelModuleSystem

        if host_kernel_manager:
            try:
                if not self.module.check_mode:
                    host_kernel_manager.UpdateModuleOptionString(kmod_name, kmod_option)
            except vim.fault.NotFound as kernel_fault:
                self.module.fail_json(msg="Failed to find kernel module on host '%s'. More information: %s" % (host.name, to_native(kernel_fault)))
            except Exception as kernel_fault:
                self.module.fail_json(msg="Failed to configure kernel module for host '%s' due to: %s" % (host.name, to_native(kernel_fault)))

    # evaluate our current configuration against desired options and save results
    def check_host_configuration_state(self):
        change_list = []

        for host in self.hosts:
            changed = False
            msg = ""
            self.results[host.name] = dict()

            if host.runtime.connectionState == "connected":
                host_kernel_manager = host.configManager.kernelModuleSystem

                if host_kernel_manager:
                    # keep track of original options on the kernel module
                    original_options = self.get_kernel_module_option(host, self.kernel_module_name)
                    desired_options = self.kernel_module_option

                    # apply as needed, also depending on check mode
                    if original_options != desired_options:
                        changed = True
                        if self.module.check_mode:
                            msg = "Options would be changed on the kernel module"
                        else:
                            self.apply_kernel_module_option(host, self.kernel_module_name, desired_options)
                            msg = "Options have been changed on the kernel module"
                            self.results[host.name]['configured_options'] = desired_options
                    else:
                        msg = "Options are already the same"

                    change_list.append(changed)
                    self.results[host.name]['changed'] = changed
                    self.results[host.name]['msg'] = msg
                    self.results[host.name]['original_options'] = original_options

                else:
                    msg = "No kernel module manager found on host %s - impossible to configure." % host.name
                    self.results[host.name]['changed'] = changed
                    self.results[host.name]['msg'] = msg
            else:
                msg = "Host %s is disconnected and cannot be changed." % host.name
                self.results[host.name]['changed'] = changed
                self.results[host.name]['msg'] = msg

        self.module.exit_json(changed=any(change_list), results=self.results)


def main():
    argument_spec = vmware_argument_spec()
    # add the arguments we're going to use for this module
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        kernel_module_name=dict(type='str', required=True),
        kernel_module_option=dict(type='str', required=True),
    )

    # make sure we have a valid target cluster_name or esxi_hostname (not both)
    # and also enable check mode
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        mutually_exclusive=[
            ['cluster_name', 'esxi_hostname'],
        ],
    )

    vmware_host_config = VmwareKernelManager(module)
    vmware_host_config.check_host_configuration_state()


if __name__ == '__main__':
    main()
