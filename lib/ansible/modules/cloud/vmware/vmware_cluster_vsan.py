#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
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
module: vmware_cluster_vsan
short_description: Manages virtual storage area network (vSAN) configuration on VMware vSphere clusters
description:
    - Manages vSAN on VMware vSphere clusters.
    - All values and VMware object names are case sensitive.
version_added: '2.9'
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
requirements:
    - Tested on ESXi 5.5 and 6.5.
    - PyVmomi installed.
options:
    cluster_name:
      description:
      - The name of the cluster to be managed.
      type: str
      required: yes
    datacenter:
      description:
      - The name of the datacenter.
      type: str
      required: yes
      aliases: [ datacenter_name ]
    enable_vsan:
      description:
      - Whether to enable vSAN.
      type: bool
      default: 'no'
    vsan_auto_claim_storage:
      description:
      - Whether the VSAN service is configured to automatically claim local storage
        on VSAN-enabled hosts in the cluster.
      type: bool
      default: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r"""
- name: Enable vSAN
  vmware_cluster_vsan:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
    enable_vsan: yes
  delegate_to: localhost

- name: Enable vSAN and claim storage automatically
  vmware_cluster_vsan:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter_name: DC0
    cluster_name: "{{ cluster_name }}"
    enable_vsan: True
    vsan_auto_claim_storage: True
  delegate_to: localhost
"""

RETURN = r"""#
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, TaskError, find_datacenter_by_name,
                                         vmware_argument_spec, wait_for_task)
from ansible.module_utils._text import to_native


class VMwareCluster(PyVmomi):
    def __init__(self, module):
        super(VMwareCluster, self).__init__(module)
        self.cluster_name = module.params['cluster_name']
        self.datacenter_name = module.params['datacenter']
        self.enable_vsan = module.params['enable_vsan']
        self.datacenter = None
        self.cluster = None

        self.datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
        if self.datacenter is None:
            self.module.fail_json(msg="Datacenter %s does not exist." % self.datacenter_name)

        self.cluster = self.find_cluster_by_name(cluster_name=self.cluster_name)
        if self.cluster is None:
            self.module.fail_json(msg="Cluster %s does not exist." % self.cluster_name)

    def check_vsan_config_diff(self):
        """
        Check VSAN configuration diff
        Returns: True if there is diff, else False

        """
        vsan_config = self.cluster.configurationEx.vsanConfigInfo

        if vsan_config.enabled != self.enable_vsan or \
                vsan_config.defaultConfig.autoClaimStorage != self.params.get('vsan_auto_claim_storage'):
            return True
        return False

    def configure_vsan(self):
        """
        Manage VSAN configuration

        """
        changed, result = False, None

        if self.check_vsan_config_diff():
            if not self.module.check_mode:
                cluster_config_spec = vim.cluster.ConfigSpecEx()
                cluster_config_spec.vsanConfig = vim.vsan.cluster.ConfigInfo()
                cluster_config_spec.vsanConfig.enabled = self.enable_vsan
                cluster_config_spec.vsanConfig.defaultConfig = vim.vsan.cluster.ConfigInfo.HostDefaultInfo()
                cluster_config_spec.vsanConfig.defaultConfig.autoClaimStorage = self.params.get('vsan_auto_claim_storage')
                try:
                    task = self.cluster.ReconfigureComputeResource_Task(cluster_config_spec, True)
                    changed, result = wait_for_task(task)
                except vmodl.RuntimeFault as runtime_fault:
                    self.module.fail_json(msg=to_native(runtime_fault.msg))
                except vmodl.MethodFault as method_fault:
                    self.module.fail_json(msg=to_native(method_fault.msg))
                except TaskError as task_e:
                    self.module.fail_json(msg=to_native(task_e))
                except Exception as generic_exc:
                    self.module.fail_json(msg="Failed to update cluster"
                                              " due to generic exception %s" % to_native(generic_exc))
            else:
                changed = True

        self.module.exit_json(changed=changed, result=result)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        datacenter=dict(type='str', required=True, aliases=['datacenter_name']),
        # VSAN
        enable_vsan=dict(type='bool', default=False),
        vsan_auto_claim_storage=dict(type='bool', default=False),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_cluster_vsan = VMwareCluster(module)
    vmware_cluster_vsan.configure_vsan()


if __name__ == '__main__':
    main()
