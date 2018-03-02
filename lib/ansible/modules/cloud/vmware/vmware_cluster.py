#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vmware_cluster
short_description: Manage VMware vSphere clusters
description:
    - Add or remove VMware vSphere clusters.
version_added: '2.0'
author:
- Joseph Callen (@jcpowermac)
requirements:
    - Tested on ESXi 5.5
    - PyVmomi installed
options:
    cluster_name:
        description:
            - The name of the cluster that will be created.
        required: yes
    datacenter_name:
        description:
            - The name of the datacenter the cluster will be created in.
        required: yes
    enable_drs:
        description:
            - If set to C(yes) will enable DRS when the cluster is created.
        type: bool
        default: 'no'
    enable_ha:
        description:
            - If set to C(yes) will enable HA when the cluster is created.
        type: bool
        default: 'no'
    enable_vsan:
        description:
            - If set to C(yes) will enable vSAN when the cluster is created.
        type: bool
        default: 'no'
    state:
        description:
            - Create (C(present)) or remove (C(absent)) a VMware vSphere cluster.
        choices: [absent, present]
        default: present
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Create Cluster
  local_action:
    module: vmware_cluster
    hostname: '{{ ansible_ssh_host }}'
    username: root
    password: vmware
    datacenter_name: datacenter
    cluster_name: cluster
    enable_ha: yes
    enable_drs: yes
    enable_vsan: yes
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI,
                                         TaskError,
                                         connect_to_api,
                                         find_cluster_by_name_datacenter,
                                         find_datacenter_by_name,
                                         vmware_argument_spec,
                                         wait_for_task
                                         )


class VMwareCluster(object):
    def __init__(self, module):
        self.module = module
        self.cluster_name = module.params['cluster_name']
        self.datacenter_name = module.params['datacenter_name']
        self.enable_drs = module.params['enable_drs']
        self.enable_ha = module.params['enable_ha']
        self.enable_vsan = module.params['enable_vsan']
        self.desired_state = module.params['state']
        self.datacenter = None
        self.cluster = None
        self.content = connect_to_api(module)

    def process_state(self):
        cluster_states = {
            'absent': {
                'present': self.state_destroy_cluster,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'update': self.state_update_cluster,
                'present': self.state_exit_unchanged,
                'absent': self.state_create_cluster,
            }
        }
        current_state = self.check_cluster_configuration()
        # Based on the desired_state and the current_state call
        # the appropriate method from the dictionary
        cluster_states[self.desired_state][current_state]()

    def configure_ha(self):
        das_config = vim.cluster.DasConfigInfo()
        das_config.enabled = self.enable_ha
        das_config.admissionControlPolicy = vim.cluster.FailoverLevelAdmissionControlPolicy()
        das_config.admissionControlPolicy.failoverLevel = 2
        return das_config

    def configure_drs(self):
        drs_config = vim.cluster.DrsConfigInfo()
        drs_config.enabled = self.enable_drs
        # Set to partially automated
        drs_config.vmotionRate = 3
        return drs_config

    def configure_vsan(self):
        vsan_config = vim.vsan.cluster.ConfigInfo()
        vsan_config.enabled = self.enable_vsan
        vsan_config.defaultConfig = vim.vsan.cluster.ConfigInfo.HostDefaultInfo()
        vsan_config.defaultConfig.autoClaimStorage = False
        return vsan_config

    def state_create_cluster(self):
        try:
            cluster_config_spec = vim.cluster.ConfigSpecEx()
            cluster_config_spec.dasConfig = self.configure_ha()
            cluster_config_spec.drsConfig = self.configure_drs()
            if self.enable_vsan:
                cluster_config_spec.vsanConfig = self.configure_vsan()
            if not self.module.check_mode:
                self.datacenter.hostFolder.CreateClusterEx(self.cluster_name, cluster_config_spec)
            self.module.exit_json(changed=True)
        except vim.fault.DuplicateName:
            self.module.fail_json(msg="A cluster with the name %s already exists" % self.cluster_name)
        except vmodl.fault.InvalidArgument:
            self.module.fail_json(msg="Cluster configuration specification parameter is invalid")
        except vim.fault.InvalidName:
            self.module.fail_json(msg="%s is an invalid name for a cluster" % self.cluster_name)
        except vmodl.fault.NotSupported:
            # This should never happen
            self.module.fail_json(msg="Trying to create a cluster on an incorrect folder object")
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            # This should never happen either
            self.module.fail_json(msg=method_fault.msg)

    def state_destroy_cluster(self):
        changed = True
        result = None

        try:
            if not self.module.check_mode:
                task = self.cluster.Destroy_Task()
                changed, result = wait_for_task(task)
            self.module.exit_json(changed=changed, result=result)
        except vim.fault.VimFault as vim_fault:
            self.module.fail_json(msg=vim_fault.msg)
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_update_cluster(self):
        cluster_config_spec = vim.cluster.ConfigSpecEx()
        changed = True
        result = None

        if self.cluster.configurationEx.dasConfig.enabled != self.enable_ha:
            cluster_config_spec.dasConfig = self.configure_ha()
        if self.cluster.configurationEx.drsConfig.enabled != self.enable_drs:
            cluster_config_spec.drsConfig = self.configure_drs()
        if self.cluster.configurationEx.vsanConfigInfo.enabled != self.enable_vsan:
            cluster_config_spec.vsanConfig = self.configure_vsan()

        try:
            if not self.module.check_mode:
                task = self.cluster.ReconfigureComputeResource_Task(cluster_config_spec, True)
                changed, result = wait_for_task(task)
            self.module.exit_json(changed=changed, result=result)
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except TaskError as task_e:
            self.module.fail_json(msg=str(task_e))

    def check_cluster_configuration(self):
        try:
            self.datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
            if self.datacenter is None:
                self.module.fail_json(msg="Datacenter %s does not exist, "
                                          "please create first with Ansible Module vmware_datacenter or manually."
                                          % self.datacenter_name)
            self.cluster = find_cluster_by_name_datacenter(self.datacenter, self.cluster_name)

            if self.cluster is None:
                return 'absent'
            else:
                desired_state = (self.enable_ha,
                                 self.enable_drs,
                                 self.enable_vsan)

                current_state = (self.cluster.configurationEx.dasConfig.enabled,
                                 self.cluster.configurationEx.drsConfig.enabled,
                                 self.cluster.configurationEx.vsanConfigInfo.enabled)

                if desired_state != current_state:
                    return 'update'
                else:
                    return 'present'
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        datacenter_name=dict(type='str', required=True),
        enable_drs=dict(type='bool', default=False),
        enable_ha=dict(type='bool', default=False),
        enable_vsan=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_cluster = VMwareCluster(module)
    vmware_cluster.process_state()


if __name__ == '__main__':
    main()
