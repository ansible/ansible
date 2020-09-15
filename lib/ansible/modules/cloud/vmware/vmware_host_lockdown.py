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
module: vmware_host_lockdown
short_description: Manage administrator permission for the local administrative account for the ESXi host
description:
- This module can be used to manage administrator permission for the local administrative account for the host when ESXi hostname is given.
- All parameters and VMware objects values are case sensitive.
- This module is destructive as administrator permission are managed using APIs used, please read options carefully and proceed.
- Please specify C(hostname) as vCenter IP or hostname only, as lockdown operations are not possible from standalone ESXi server.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of cluster.
    - All host systems from given cluster used to manage lockdown.
    - Required parameter, if C(esxi_hostname) is not set.
    type: str
  esxi_hostname:
    description:
    - List of ESXi hostname to manage lockdown.
    - Required parameter, if C(cluster_name) is not set.
    - See examples for specifications.
    type: list
  state:
    description:
    - State of hosts system
    - If set to C(present), all host systems will be set in lockdown mode.
    - If host system is already in lockdown mode and set to C(present), no action will be taken.
    - If set to C(absent), all host systems will be removed from lockdown mode.
    - If host system is already out of lockdown mode and set to C(absent), no action will be taken.
    default: present
    choices: [ present, absent ]
    version_added: 2.5
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Enter host system into lockdown mode
  vmware_host_lockdown:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: present
  delegate_to: localhost

- name: Exit host systems from lockdown mode
  vmware_host_lockdown:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: absent
  delegate_to: localhost

- name: Enter host systems into lockdown mode
  vmware_host_lockdown:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname:
        - '{{ esxi_hostname_1 }}'
        - '{{ esxi_hostname_2 }}'
    state: present
  delegate_to: localhost

- name: Exit host systems from lockdown mode
  vmware_host_lockdown:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname:
        - '{{ esxi_hostname_1 }}'
        - '{{ esxi_hostname_2 }}'
    state: absent
  delegate_to: localhost

- name: Enter all host system from cluster into lockdown mode
  vmware_host_lockdown:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
    state: present
  delegate_to: localhost
'''

RETURN = r'''
results:
    description: metadata about state of Host system lock down
    returned: always
    type: dict
    sample: {
                "host_lockdown_state": {
                    "DC0_C0": {
                        "current_state": "present",
                        "previous_state": "absent",
                        "desired_state": "present",
                    },
                }
            }
'''

try:
    from pyvmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


class VmwareLockdownManager(PyVmomi):
    def __init__(self, module):
        super(VmwareLockdownManager, self).__init__(module)
        if not self.is_vcenter():
            self.module.fail_json(msg="Lockdown operations are performed from vCenter only. "
                                      "hostname %s is an ESXi server. Please specify hostname "
                                      "as vCenter server." % self.module.params['hostname'])
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    def ensure(self):
        """
        Function to manage internal state management
        """
        results = dict(changed=False, host_lockdown_state=dict())
        change_list = []
        desired_state = self.params.get('state')
        for host in self.hosts:
            results['host_lockdown_state'][host.name] = dict(current_state='',
                                                             desired_state=desired_state,
                                                             previous_state=''
                                                             )
            changed = False
            try:
                if host.config.adminDisabled:
                    results['host_lockdown_state'][host.name]['previous_state'] = 'present'
                    if desired_state == 'absent':
                        host.ExitLockdownMode()
                        results['host_lockdown_state'][host.name]['current_state'] = 'absent'
                        changed = True
                    else:
                        results['host_lockdown_state'][host.name]['current_state'] = 'present'
                elif not host.config.adminDisabled:
                    results['host_lockdown_state'][host.name]['previous_state'] = 'absent'
                    if desired_state == 'present':
                        host.EnterLockdownMode()
                        results['host_lockdown_state'][host.name]['current_state'] = 'present'
                        changed = True
                    else:
                        results['host_lockdown_state'][host.name]['current_state'] = 'absent'
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(msg="Failed to manage lockdown mode for esxi"
                                          " hostname %s : %s" % (host.name, to_native(host_config_fault.msg)))
            except vim.fault.AdminDisabled as admin_disabled:
                self.module.fail_json(msg="Failed to manage lockdown mode as administrator "
                                          "permission has been disabled for "
                                          "esxi hostname %s : %s" % (host.name, to_native(admin_disabled.msg)))
            except Exception as generic_exception:
                self.module.fail_json(msg="Failed to manage lockdown mode due to generic exception for esxi "
                                          "hostname %s : %s" % (host.name, to_native(generic_exception)))
            change_list.append(changed)

        if any(change_list):
            results['changed'] = True

        self.module.exit_json(**results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='list', required=False),
        state=dict(str='str', default='present', choices=['present', 'absent'], required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ]
    )

    vmware_lockdown_mgr = VmwareLockdownManager(module)
    vmware_lockdown_mgr.ensure()


if __name__ == "__main__":
    main()
