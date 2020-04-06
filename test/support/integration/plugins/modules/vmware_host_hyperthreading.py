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
module: vmware_host_hyperthreading
short_description: Enables/Disables Hyperthreading optimization for an ESXi host system
description:
- This module can be used to enable or disable Hyperthreading optimization for ESXi host systems in given vCenter infrastructure.
- It also checks if Hyperthreading is activated/deactivated and if the host needs to be restarted.
- The module informs the user if Hyperthreading is enabled but inactive because the processor is vulnerable to L1 Terminal Fault (L1TF).
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  state:
     description:
        - Enable or disable Hyperthreading.
        - You need to reboot the ESXi host if you change the configuration.
        - Make sure that Hyperthreading is enabled in the BIOS. Otherwise, it will be enabled, but never activated.
     type: str
     choices: [ enabled, disabled ]
     default: 'enabled'
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - This parameter is required if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - This parameter is required if C(esxi_hostname) is not specified.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Enable Hyperthreading for an host system
  vmware_host_hyperthreading:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: enabled
    validate_certs: no
  delegate_to: localhost

- name: Disable Hyperthreading for an host system
  vmware_host_hyperthreading:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: disabled
    validate_certs: no
  delegate_to: localhost

- name: Disable Hyperthreading for all host systems from cluster
  vmware_host_hyperthreading:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
    state: disabled
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
results:
    description: metadata about host system's Hyperthreading configuration
    returned: always
    type: dict
    sample: {
        "esxi01": {
            "msg": "Hyperthreading is already enabled and active for host 'esxi01'",
            "state_current": "active",
            "state": "enabled",
        },
    }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VmwareHostHyperthreading(PyVmomi):
    """Manage Hyperthreading for an ESXi host system"""
    def __init__(self, module):
        super(VmwareHostHyperthreading, self).__init__(module)
        cluster_name = self.params.get('cluster_name')
        esxi_host_name = self.params.get('esxi_hostname')
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system.")

    def ensure(self):
        """Manage Hyperthreading for an ESXi host system"""
        results = dict(changed=False, result=dict())
        desired_state = self.params.get('state')
        host_change_list = []
        for host in self.hosts:
            changed = False
            results['result'][host.name] = dict(msg='')

            hyperthreading_info = host.config.hyperThread

            results['result'][host.name]['state'] = desired_state
            if desired_state == 'enabled':
                # Don't do anything if Hyperthreading is already enabled
                if hyperthreading_info.config:
                    if hyperthreading_info.active:
                        results['result'][host.name]['changed'] = False
                        results['result'][host.name]['state_current'] = "active"
                        results['result'][host.name]['msg'] = "Hyperthreading is enabled and active"
                    if not hyperthreading_info.active:
                        # L1 Terminal Fault (L1TF)/Foreshadow mitigation workaround (https://kb.vmware.com/s/article/55806)
                        option_manager = host.configManager.advancedOption
                        try:
                            mitigation = option_manager.QueryOptions('VMkernel.Boot.hyperthreadingMitigation')
                        except vim.fault.InvalidName:
                            mitigation = None
                        if mitigation and mitigation[0].value:
                            results['result'][host.name]['changed'] = False
                            results['result'][host.name]['state_current'] = "enabled"
                            results['result'][host.name]['msg'] = ("Hyperthreading is enabled, but not active because the"
                                                                   " processor is vulnerable to L1 Terminal Fault (L1TF).")
                        else:
                            changed = results['result'][host.name]['changed'] = True
                            results['result'][host.name]['state_current'] = "enabled"
                            results['result'][host.name]['msg'] = ("Hyperthreading is enabled, but not active."
                                                                   " A reboot is required!")
                # Enable Hyperthreading
                else:
                    # Check if Hyperthreading is available
                    if hyperthreading_info.available:
                        if not self.module.check_mode:
                            try:
                                host.configManager.cpuScheduler.EnableHyperThreading()
                                changed = results['result'][host.name]['changed'] = True
                                results['result'][host.name]['state_previous'] = "disabled"
                                results['result'][host.name]['state_current'] = "enabled"
                                results['result'][host.name]['msg'] = (
                                    "Hyperthreading enabled for host. Reboot the host to activate it."
                                )
                            except vmodl.fault.NotSupported as not_supported:
                                # This should never happen since Hyperthreading is available
                                self.module.fail_json(
                                    msg="Failed to enable Hyperthreading for host '%s' : %s" %
                                    (host.name, to_native(not_supported.msg))
                                )
                            except (vmodl.RuntimeFault, vmodl.MethodFault) as runtime_fault:
                                self.module.fail_json(
                                    msg="Failed to enable Hyperthreading for host '%s' due to : %s" %
                                    (host.name, to_native(runtime_fault.msg))
                                )
                        else:
                            changed = results['result'][host.name]['changed'] = True
                            results['result'][host.name]['state_previous'] = "disabled"
                            results['result'][host.name]['state_current'] = "enabled"
                            results['result'][host.name]['msg'] = "Hyperthreading will be enabled"
                    else:
                        self.module.fail_json(msg="Hyperthreading optimization is not available for host '%s'" % host.name)
            elif desired_state == 'disabled':
                # Don't do anything if Hyperthreading is already disabled
                if not hyperthreading_info.config:
                    if not hyperthreading_info.active:
                        results['result'][host.name]['changed'] = False
                        results['result'][host.name]['state_current'] = "inactive"
                        results['result'][host.name]['msg'] = "Hyperthreading is disabled and inactive"
                    if hyperthreading_info.active:
                        changed = results['result'][host.name]['changed'] = True
                        results['result'][host.name]['state_current'] = "disabled"
                        results['result'][host.name]['msg'] = ("Hyperthreading is already disabled"
                                                               " but still active. A reboot is required!")
                # Disable Hyperthreading
                else:
                    # Check if Hyperthreading is available
                    if hyperthreading_info.available:
                        if not self.module.check_mode:
                            try:
                                host.configManager.cpuScheduler.DisableHyperThreading()
                                changed = results['result'][host.name]['changed'] = True
                                results['result'][host.name]['state_previous'] = "enabled"
                                results['result'][host.name]['state_current'] = "disabled"
                                results['result'][host.name]['msg'] = (
                                    "Hyperthreading disabled. Reboot the host to deactivate it."
                                )
                            except vmodl.fault.NotSupported as not_supported:
                                # This should never happen since Hyperthreading is available
                                self.module.fail_json(
                                    msg="Failed to disable Hyperthreading for host '%s' : %s" %
                                    (host.name, to_native(not_supported.msg))
                                )
                            except (vmodl.RuntimeFault, vmodl.MethodFault) as runtime_fault:
                                self.module.fail_json(
                                    msg="Failed to disable Hyperthreading for host '%s' due to : %s" %
                                    (host.name, to_native(runtime_fault.msg))
                                )
                        else:
                            changed = results['result'][host.name]['changed'] = True
                            results['result'][host.name]['state_previous'] = "enabled"
                            results['result'][host.name]['state_current'] = "disabled"
                            results['result'][host.name]['msg'] = "Hyperthreading will be disabled"
                    else:
                        self.module.fail_json(msg="Hyperthreading optimization is not available for host '%s'" % host.name)

            host_change_list.append(changed)

        if any(host_change_list):
            results['changed'] = True
        self.module.exit_json(**results)


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(default='enabled', choices=['enabled', 'disabled']),
        esxi_hostname=dict(type='str', required=False),
        cluster_name=dict(type='str', required=False),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[
                               ['cluster_name', 'esxi_hostname'],
                           ],
                           supports_check_mode=True
                           )

    hyperthreading = VmwareHostHyperthreading(module)
    hyperthreading.ensure()


if __name__ == '__main__':
    main()
