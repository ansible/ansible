#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Russell Teague <rteague2 () csc.com>
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
module: vmware_vsan_cluster
short_description: Configure VSAN clustering on an ESXi host
description:
    - This module can be used to configure VSAN clustering on an ESXi host
version_added: 2.0
author: "Russell Teague (@mtnbikenc)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    hostname:
        description:
            - The hostname or IP address of the ESXi Server
        required: True
    username:
        description:
            - The username of the ESXi Server
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of ESXi Server
        required: True
        aliases: ['pass', 'pwd']
    cluster_uuid:
        description:
            - Desired cluster UUID
        required: False
'''

EXAMPLES = '''
# Example command from Ansible Playbook

- name: Configure VMware VSAN Cluster
  hosts: deploy_node
  gather_facts: False
  tags:
    - vsan
  tasks:
    - name: Configure VSAN on first host
      vmware_vsan_cluster:
         hostname: "{{ groups['esxi'][0] }}"
         username: "{{ esxi_username }}"
         password: "{{ site_password }}"
      register: vsan_cluster

    - name: Configure VSAN on remaining hosts
      vmware_vsan_cluster:
         hostname: "{{ item }}"
         username: "{{ esxi_username }}"
         password: "{{ site_password }}"
         cluster_uuid: "{{ vsan_cluster.cluster_uuid }}"
      with_items: groups['esxi'][1:]

'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def create_vsan_cluster(host_system, new_cluster_uuid):
    host_config_manager = host_system.configManager
    vsan_system = host_config_manager.vsanSystem

    vsan_config = vim.vsan.host.ConfigInfo()
    vsan_config.enabled = True

    if new_cluster_uuid is not None:
        vsan_config.clusterInfo = vim.vsan.host.ConfigInfo.ClusterInfo()
        vsan_config.clusterInfo.uuid = new_cluster_uuid

    vsan_config.storageInfo = vim.vsan.host.ConfigInfo.StorageInfo()
    vsan_config.storageInfo.autoClaimStorage = True

    task = vsan_system.UpdateVsan_Task(vsan_config)
    changed, result = wait_for_task(task)

    host_status = vsan_system.QueryHostStatus()
    cluster_uuid = host_status.uuid

    return changed, result, cluster_uuid


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(cluster_uuid=dict(required=False, type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    new_cluster_uuid = module.params['cluster_uuid']

    try:
        content = connect_to_api(module, False)
        host = get_all_objs(content, [vim.HostSystem])
        if not host:
            module.fail_json(msg="Unable to locate Physical Host.")
        host_system = host.keys()[0]
        changed, result, cluster_uuid = create_vsan_cluster(host_system, new_cluster_uuid)
        module.exit_json(changed=changed, result=result, cluster_uuid=cluster_uuid)

    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
