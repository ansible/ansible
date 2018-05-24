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
module: vmware_drs_rule_facts
short_description: Gathers facts about DRS rule on the given cluster
description:
- 'This module can be used to gather facts about DRS VM-VM and VM-HOST rules from the given cluster'
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
    - Name of the cluster.
    - DRS facts for the given cluster will be returned.
    - This is required parameter if C(datacenter) parameter is not provided.
  datacenter:
    description:
    - Name of the datacenter.
    - DRS facts for all the clusters from the given datacenter will be returned.
    - This is required parameter if C(cluster_name) parameter is not provided.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather DRS facts about given Cluster
  vmware_drs_rule_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
  register: cluster_drs_facts

- name: Gather DRS facts about all Clusters in given datacenter
  vmware_drs_rule_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
  register: datacenter_drs_facts
'''

RETURN = r'''
drs_rule_facts:
    description: metadata about DRS rule from given cluster / datacenter
    returned: always
    type: dict
    sample: {
            "DC0_C0": [
                {
                    "rule_enabled": true,
                    "rule_key": 1,
                    "rule_mandatory": true,
                    "rule_name": "drs_rule_0001",
                    "rule_type": "vm_vm_rule",
                    "rule_uuid": "52be5061-665a-68dc-3d25-85cd2d37e114",
                    "rule_vms": [
                        "VM_65",
                        "VM_146"
                    ]
                },
            ]
            }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, find_datacenter_by_name, get_all_objs


class VmwareDrsFactManager(PyVmomi):
    def __init__(self, module):
        super(VmwareDrsFactManager, self).__init__(module)

        datacenter_name = self.params.get('datacenter', None)
        if datacenter_name:
            datacenter_obj = find_datacenter_by_name(self.content, datacenter_name=datacenter_name)
            self.cluster_obj_list = []
            if datacenter_obj:
                folder = datacenter_obj.hostFolder
                self.cluster_obj_list = get_all_objs(self.content, [vim.ClusterComputeResource], folder)
            else:
                self.module.fail_json(changed=False, msg="Datacenter '%s' not found" % datacenter_name)

        cluster_name = self.params.get('cluster_name', None)
        if cluster_name:
            cluster_obj = self.find_cluster_by_name(cluster_name=cluster_name)
            if cluster_obj is None:
                self.module.fail_json(changed=False, msg="Cluster '%s' not found" % cluster_name)
            else:
                self.cluster_obj_list = [cluster_obj]

    @staticmethod
    def normalize_vm_vm_rule_spec(rule_obj=None):
        """
        Function to return human readable rule spec
        Args:
            rule_obj: Rule managed object

        Returns: Dictionary with DRS VM VM Rule info

        """
        if rule_obj is None:
            return {}
        return dict(rule_key=rule_obj.key,
                    rule_enabled=rule_obj.enabled,
                    rule_name=rule_obj.name,
                    rule_mandatory=rule_obj.mandatory,
                    rule_uuid=rule_obj.ruleUuid,
                    rule_vms=[vm.name for vm in rule_obj.vm],
                    rule_type="vm_vm_rule",
                    )

    @staticmethod
    def normalize_vm_host_rule_spec(rule_obj=None):
        """
        Function to return human readable rule spec
        Args:
            rule_obj: Rule managed object

        Returns: Dictionary with DRS VM HOST Rule info

        """
        if rule_obj is None:
            return {}
        return dict(rule_key=rule_obj.key,
                    rule_enabled=rule_obj.enabled,
                    rule_name=rule_obj.name,
                    rule_mandatory=rule_obj.mandatory,
                    rule_uuid=rule_obj.ruleUuid,
                    rule_vm_group_name=rule_obj.vmGroupName,
                    rule_affine_host_group_name=rule_obj.affineHostGroupName,
                    rule_anti_affine_host_group_name=rule_obj.antiAffineHostGroupName,
                    rule_type="vm_host_rule",
                    )

    def gather_drs_rule_facts(self):
        """
        Function to gather DRS rule facts about given cluster
        Returns: Dictinary of clusters with DRS facts

        """
        cluster_rule_facts = dict()
        for cluster_obj in self.cluster_obj_list:
            cluster_rule_facts[cluster_obj.name] = []
            for drs_rule in cluster_obj.configuration.rule:
                if isinstance(drs_rule, vim.cluster.VmHostRuleInfo):
                    cluster_rule_facts[cluster_obj.name].append(self.normalize_vm_host_rule_spec(rule_obj=drs_rule))
                else:
                    cluster_rule_facts[cluster_obj.name].append(self.normalize_vm_vm_rule_spec(rule_obj=drs_rule))

        return cluster_rule_facts


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter=dict(type='str', required=False),
        cluster_name=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'datacenter'],
        ]
    )

    vmware_drs_facts = VmwareDrsFactManager(module)
    module.exit_json(changed=False, drs_rule_facts=vmware_drs_facts.gather_drs_rule_facts())


if __name__ == "__main__":
    main()
