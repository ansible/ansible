#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: vmware_cluster
short_description: Create VMware vSphere Cluster
description:
    - Create VMware vSphere Cluster
version_added: 2.0
author: Joseph Callen (@jcpowermac)
notes:
requirements:
    - Tested on ESXi 5.5
    - PyVmomi installed
options:
    datacenter_name:
        description:
            - The name of the datacenter the cluster will be created in.
        required: True
    cluster_name:
        description:
            - The name of the cluster that will be created
        required: True
    enable_ha:
        description:
            - If set to True will enable HA when the cluster is created.
        required: False
        default: False
    enable_drs:
        description:
            - If set to True will enable DRS when the cluster is created.
        required: False
        default: False
    enable_vsan:
        description:
            - If set to True will enable vSAN when the cluster is created.
        required: False
        default: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Example vmware_cluster command from Ansible Playbooks
- name: Create Cluster
      local_action: >
        vmware_cluster
        hostname="{{ ansible_ssh_host }}" username=root password=vmware
        datacenter_name="datacenter"
        cluster_name="cluster"
        enable_ha=True
        enable_drs=True
        enable_vsan=True
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


class VMwareCluster(object):
    def __init__(self, module):
        self.module = module
        self.enable_ha = module.params['enable_ha']
        self.enable_drs = module.params['enable_drs']
        self.enable_vsan = module.params['enable_vsan']
        self.cluster_name = module.params['cluster_name']
        self.desired_state = module.params['state']
        self.datacenter = None
        self.cluster = None
        self.content = connect_to_api(module)
        self.datacenter_name = module.params['datacenter_name']

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

                if cmp(desired_state, current_state) != 0:
                    return 'update'
                else:
                    return 'present'
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(datacenter_name=dict(required=True, type='str'),
                         cluster_name=dict(required=True, type='str'),
                         enable_ha=dict(default=False, required=False, type='bool'),
                         enable_drs=dict(default=False, required=False, type='bool'),
                         enable_vsan=dict(default=False, required=False, type='bool'),
                         state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_cluster = VMwareCluster(module)
    vmware_cluster.process_state()

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
