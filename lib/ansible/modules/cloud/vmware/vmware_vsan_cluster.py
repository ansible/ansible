#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Russell Teague <rteague2 () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
    cluster_uuid:
        description:
            - Desired cluster UUID
        required: False
extends_documentation_fragment: vmware.documentation
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
      with_items: "{{ groups['esxi'][1:] }}"

'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI, connect_to_api, get_all_objs, vmware_argument_spec,
                                         wait_for_task)


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


if __name__ == '__main__':
    main()
