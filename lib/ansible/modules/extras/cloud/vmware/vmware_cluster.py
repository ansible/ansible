#!/bin/python
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
    hostname:
        description:
            - The hostname or IP address of the vSphere vCenter
        required: True
    username:
        description:
            - The username of the vSphere vCenter
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of the vSphere vCenter
        required: True
        aliases: ['pass', 'pwd']
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


def configure_ha(enable_ha):
    das_config = vim.cluster.DasConfigInfo()
    das_config.enabled = enable_ha
    das_config.admissionControlPolicy = vim.cluster.FailoverLevelAdmissionControlPolicy()
    das_config.admissionControlPolicy.failoverLevel = 2
    return das_config


def configure_drs(enable_drs):
    drs_config = vim.cluster.DrsConfigInfo()
    drs_config.enabled = enable_drs
    # Set to partially automated
    drs_config.vmotionRate = 3
    return drs_config


def configure_vsan(enable_vsan):
    vsan_config = vim.vsan.cluster.ConfigInfo()
    vsan_config.enabled = enable_vsan
    vsan_config.defaultConfig = vim.vsan.cluster.ConfigInfo.HostDefaultInfo()
    vsan_config.defaultConfig.autoClaimStorage = False
    return vsan_config


def state_create_cluster(module):

    enable_ha = module.params['enable_ha']
    enable_drs = module.params['enable_drs']
    enable_vsan = module.params['enable_vsan']
    cluster_name = module.params['cluster_name']
    datacenter = module.params['datacenter']

    try:
        cluster_config_spec = vim.cluster.ConfigSpecEx()
        cluster_config_spec.dasConfig = configure_ha(enable_ha)
        cluster_config_spec.drsConfig = configure_drs(enable_drs)
        if enable_vsan:
            cluster_config_spec.vsanConfig = configure_vsan(enable_vsan)
        if not module.check_mode:
            datacenter.hostFolder.CreateClusterEx(cluster_name, cluster_config_spec)
        module.exit_json(changed=True)
    except vim.fault.DuplicateName:
        module.fail_json(msg="A cluster with the name %s already exists" % cluster_name)
    except vmodl.fault.InvalidArgument:
        module.fail_json(msg="Cluster configuration specification parameter is invalid")
    except vim.fault.InvalidName:
        module.fail_json(msg="%s is an invalid name for a cluster" % cluster_name)
    except vmodl.fault.NotSupported:
        # This should never happen
        module.fail_json(msg="Trying to create a cluster on an incorrect folder object")
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        # This should never happen either
        module.fail_json(msg=method_fault.msg)


def state_destroy_cluster(module):
    cluster = module.params['cluster']
    changed = True
    result = None

    try:
        if not module.check_mode:
            task = cluster.Destroy_Task()
            changed, result = wait_for_task(task)
        module.exit_json(changed=changed, result=result)
    except vim.fault.VimFault as vim_fault:
        module.fail_json(msg=vim_fault.msg)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)


def state_exit_unchanged(module):
    module.exit_json(changed=False)


def state_update_cluster(module):

    cluster_config_spec = vim.cluster.ConfigSpecEx()
    cluster = module.params['cluster']
    enable_ha = module.params['enable_ha']
    enable_drs = module.params['enable_drs']
    enable_vsan = module.params['enable_vsan']
    changed = True
    result = None

    if cluster.configurationEx.dasConfig.enabled != enable_ha:
        cluster_config_spec.dasConfig = configure_ha(enable_ha)
    if cluster.configurationEx.drsConfig.enabled != enable_drs:
        cluster_config_spec.drsConfig = configure_drs(enable_drs)
    if cluster.configurationEx.vsanConfigInfo.enabled != enable_vsan:
        cluster_config_spec.vsanConfig = configure_vsan(enable_vsan)

    try:
        if not module.check_mode:
            task = cluster.ReconfigureComputeResource_Task(cluster_config_spec, True)
            changed, result = wait_for_task(task)
        module.exit_json(changed=changed, result=result)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except TaskError as task_e:
        module.fail_json(msg=str(task_e))


def check_cluster_configuration(module):
    datacenter_name = module.params['datacenter_name']
    cluster_name = module.params['cluster_name']

    try:
        content = connect_to_api(module)
        datacenter = find_datacenter_by_name(content, datacenter_name)
        if datacenter is None:
            module.fail_json(msg="Datacenter %s does not exist, "
                                 "please create first with Ansible Module vmware_datacenter or manually."
                                 % datacenter_name)
        cluster = find_cluster_by_name_datacenter(datacenter, cluster_name)

        module.params['content'] = content
        module.params['datacenter'] = datacenter

        if cluster is None:
            return 'absent'
        else:
            module.params['cluster'] = cluster

            desired_state = (module.params['enable_ha'],
                             module.params['enable_drs'],
                             module.params['enable_vsan'])

            current_state = (cluster.configurationEx.dasConfig.enabled,
                             cluster.configurationEx.drsConfig.enabled,
                             cluster.configurationEx.vsanConfigInfo.enabled)

            if cmp(desired_state, current_state) != 0:
                return 'update'
            else:
                return 'present'
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)


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

    cluster_states = {
        'absent': {
            'present': state_destroy_cluster,
            'absent': state_exit_unchanged,
        },
        'present': {
            'update': state_update_cluster,
            'present': state_exit_unchanged,
            'absent': state_create_cluster,
        }
    }
    desired_state = module.params['state']
    current_state = check_cluster_configuration(module)

    # Based on the desired_state and the current_state call
    # the appropriate method from the dictionary
    cluster_states[desired_state][current_state](module)

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
