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

DOCUMENTATION = '''
---
module: vmware_vm_host_drs_rule
short_description: Configure VMware DRS rule for virtual machine/s and host system/s in the given cluster
description:
- This module can be used to configure VMware DRS rule for virtual machine/s and host system/s in the given cluster.
version_added: 2.5
author:
- "Abhijeet Kasurde (@akasurde)"
notes:
- Tested on vSphere 6.5
requirements:
- "python >= 2.6"
- PyVmomi
options:
  cluster_name:
    description:
    - Desired cluster name where virtual machines and host systems are present for the DRS rule.
    required: True
  vms:
    description:
    - List of virtual machines name for which DRS rule needs to be applied.
    - Required if C(state) is set to C(present).
    - These VMs will be added to given VM group name.
  esxi_hostnames:
    description:
    - List of host system names for which DRS rule needs to applied.
    - Required if C(state) is set ot C(present).
    - These Host Systems will be added to given host group name.
  drs_rule_name:
    description:
    - The name of the DRS rule to manage.
    required: True
  enabled:
    description:
    - If set to C(True), the DRS rule will be enabled.
    - Effective only if C(state) is set to C(present).
    default: False
  mandatory:
    description:
    - If set to C(True), the DRS rule will be mandatory.
    - Effective only if C(state) is set to C(present).
    default: False
  affinity_rule:
    description:
    - If set to C(True), the DRS rule will be an Affinity rule.
    - If set to C(False), the DRS rule will be an Anti-Affinity rule.
    - Effective only if C(state) is set to C(present).
    default: False
  state:
    description:
    - If set to C(present), then the DRS rule is created if not present.
    - If set to C(present), then the DRS rule is deleted and created if present already.
    - If set to C(absent), then the DRS rule is deleted if present.
    required: False
    default: present
  vm_group_name:
    description:
    - Name of VM group which will be added to DRS rule.
    - Required if state is set to C(present).
    required: False
  host_group_name:
    description:
    - Name of Host group which will be added to DRS rule.
    - Required if state is set to C(present).
    required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Create DRS Affinity Rule for VM-Host
  vmware_vm_host_drs_rule:
    hostname: "{{ esxi }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
    cluster_name: "{{ cluster_name }}"
    validate_certs: no
    vms:
        - vm1
        - vm2
    esxi_hostnames:
        - DC0_H0
    drs_rule_name: vm1-vm2-host1-affinity-rule-001
    enabled: True
    mandatory: True
    affinity_rule: True

- name: Create DRS Anti-Affinity Rule for VM-Host
  vmware_vm_host_drs_rule:
    hostname: "{{ esxi }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
    cluster_name: "{{ cluster_name }}"
    validate_certs: no
    vms:
        - vm1
        - vm2
    esxi_hostnames:
        - DC0_H0
    drs_rule_name: vm1-vm2-host1-anti-affinity-rule-002
    enabled: True
    mandatory: True
    affinity_rule: False

- name: Delete DRS Affinity Rule for VM-VM
  vmware_vm_host_drs_rule:
    hostname: "{{ esxi }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
    cluster_name: "{{ cluster_name }}"
    validate_certs: no
    drs_rule_name: vm1-vm2-host1-affinity-rule-001
    state: absent
'''

RETURN = r'''
result:
    description: metadata about the VM and HOST DRS Rule
    returned: when state is present
    type: dict
    sample: {
            "rule_affine_host_group_name": "host_grp_0002",
            "rule_anti_affine_host_group_name": null,
            "rule_enabled": true,
            "rule_key": 23,
            "rule_mandatory": true,
            "rule_name": "vm_host_drs_rule_0001",
            "rule_uuid": "52146b5c-a206-2f3a-f63f-d739756140c5",
            "rule_vm_group_name": "vm_grp_0002"
        }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec, wait_for_task,
                                         find_vm_by_id, find_cluster_by_name)


class VmwareHostDrs(PyVmomi):
    def __init__(self, module):
        super(VmwareHostDrs, self).__init__(module)
        self.vm_list = module.params['vms']
        self.hosts_list = module.params['esxi_hostnames']
        self.cluster_name = module.params['cluster_name']
        self.rule_name = module.params['drs_rule_name']
        self.enabled = module.params['enabled']
        self.mandatory = module.params['mandatory']
        self.affinity_rule = module.params['affinity_rule']
        self.state = module.params['state']

        # Sanity check for cluster
        self.cluster_obj = find_cluster_by_name(content=self.content,
                                                cluster_name=self.cluster_name)
        if self.cluster_obj is None:
            self.module.fail_json(msg="Failed to find the cluster %s" % self.cluster_name)
        # Sanity check for virtual machines
        self.vm_obj_list = []
        self.hosts_obj_list = []
        if self.state == 'present':
            # Get list of VMs only if state is present
            # Create VM Group
            self.vm_obj_list = self.get_all_vms_info()
            self.vm_group_name = self.params.get('vm_group_name')
            changed, result = self.create_vm_group(vms_obj_list=self.vm_obj_list, vm_group_name=self.vm_group_name)
            if not changed:
                self.module.fail_json(msg="Failed to create VM group due to %s" % result)
            # Create Host Group
            self.hosts_obj_list = self.get_all_hosts_info()
            self.host_group_name = self.params.get('host_group_name')
            changed, result = self.create_host_group(hosts_obj_list=self.hosts_obj_list, host_group_name=self.host_group_name)
            if not changed:
                self.module.fail_json(msg="Failed to create Host group due to %s" % result)

    # Getter
    def get_all_hosts_info(self, hosts_list=None):
        """
        Function to get all Host System objects using name from given cluster
        Args:
            hosts_list: Name of host systems

        Returns: List of Host system managed objects

        """
        hosts_obj_list = []
        if hosts_list is None:
            hosts_list = self.hosts_list

        for host_system in hosts_list:
            host_obj = self.find_hostsystem_by_name(host_name=host_system)
            if host_obj is None:
                self.module.fail_json(msg="Failed to find the host system %s "
                                          "in the given cluster %s" % (host_system,
                                                                       self.cluster_name))
            hosts_obj_list.append(host_obj)
        return hosts_obj_list

    def get_all_vms_info(self, vms_list=None):
        """
        Function to get all VM objects using name from given cluster
        Args:
            vms_list: List of VM names

        Returns: List of VM managed objects

        """
        vm_obj_list = []
        if vms_list is None:
            vms_list = self.vm_list

        for vm_name in vms_list:
            vm_obj = find_vm_by_id(content=self.content, vm_id=vm_name,
                                   vm_id_type='vm_name', cluster=self.cluster_obj)
            if vm_obj is None:
                self.module.fail_json(msg="Failed to find the virtual machine %s "
                                          "in the given cluster %s" % (vm_name,
                                                                       self.cluster_name))
            vm_obj_list.append(vm_obj)
        return vm_obj_list

    def create_host_group(self, cluster_obj=None, hosts_obj_list=None, host_group_name=None):
        """
        Function to create host system group which is required to create DRS rule
        Args:
            cluster_obj: Cluster managed object
            hosts_obj_list: List of host managed objects
            host_group_name: Name of host group

        Returns: True if host group is created, False if not

        """
        host_group_created = False
        if cluster_obj is None:
            cluster_obj = self.cluster_obj

        host_group_spec = vim.cluster.HostGroup()
        host_group_spec.name = host_group_name
        host_group_spec.host = hosts_obj_list

        cluster_group_spec = vim.cluster.GroupSpec()
        cluster_group_spec.operation = 'add'
        config_spec = vim.cluster.ConfigSpecEx()
        config_spec.groupSpec.append(cluster_group_spec)

        try:
            host_group_task = cluster_obj.ReconfigureEx(spec=config_spec, modify=True)
            host_group_created, result = wait_for_task(host_group_task)
        except vmodl.fault.InvalidRequest as e:
            result = to_native(e.msg)
        except Exception as e:
            result = to_native(e)

        return host_group_created, result

    def create_vm_group(self, cluster_obj=None, vms_obj_list=None, vm_group_name=None):
        """
        Function to create group of virtual machine for DRS rule
        Args:
            cluster_obj: Cluster managed object
            vms_obj_list: List of Virtual machine managed objects
            vm_group_name: Name of virtual machine group

        Returns: True if Group is created, False if not.

        """
        vm_group_created = False
        if cluster_obj is None:
            cluster_obj = self.cluster_obj

        vm_group_spec = vim.cluster.VmGroup()
        vm_group_spec.name = vm_group_name
        vm_group_spec.vm = vms_obj_list

        cluster_group_spec = vim.cluster.GroupSpec()
        cluster_group_spec.operation = 'add'
        config_spec = vim.cluster.ConfigSpecEx()
        config_spec.groupSpec.append(cluster_group_spec)

        try:
            vm_group_task = cluster_obj.ReconfigureEx(spec=config_spec, modify=True)
            vm_group_created, result = wait_for_task(vm_group_task)
        except vmodl.fault.InvalidRequest as e:
            result = to_native(e.msg)
        except Exception as e:
            result = to_native(e)

        return vm_group_created, result

    def get_rule_key_by_name(self, cluster_obj=None, rule_name=None):
        """
        Function to get a specific DRS rule key by name
        Args:
            rule_name: Name of rule
            cluster_obj: Cluster managed object

        Returns: Rule Object if found or None

        """
        if cluster_obj is None:
            cluster_obj = self.cluster_obj

        if rule_name:
            rules_list = [rule for rule in cluster_obj.configuration.rule if rule.name == rule_name and isinstance(rule, vim.cluster.VmHostRuleInfo)]
            if rules_list:
                return rules_list[0]
        # No rule found
        return None

    @staticmethod
    def normalize_rule_spec(rule_obj=None):
        """
        Function to return human readable rule spec
        Args:
            rule_obj: Rule managed object

        Returns: Dictionary with Rule info

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
                    )

    # Create
    def create(self):
        """
        Function to create a DRS rule if rule does not exists
        """
        rule_obj = self.get_rule_key_by_name(rule_name=self.rule_name)
        if rule_obj is not None:
            # Rule already exists, remove and create again
            # Cluster does not allow editing existing rule
            existing_rule = self.normalize_rule_spec(rule_obj=rule_obj)
            if ((existing_rule['rule_vm_group_name'] == self.vm_group_name) or
                    (existing_rule['rule_anti_affine_host_group_name'] == self.host_group_name) or
                    (existing_rule['rule_affine_host_group_name'] == self.host_group_name) or
                    (existing_rule['rule_enabled'] != self.enabled) or
                    (existing_rule['rule_mandatory'] != self.mandatory)):
                # Delete existing rule as we cannot edit it
                changed, result = self.delete(rule_name=self.rule_name)
                if not changed:
                    self.module.fail_json(msg="Failed to delete while updating rule %s due to %s" % (self.rule_name, result))
        changed, result = self.create_rule_spec()
        return changed, result

    def create_rule_spec(self):
        """
        Function to create DRS rule
        """
        host_group_created = False
        host_host_rule_info = vim.cluster.VmHostRuleInfo()

        host_host_rule_info.name = self.rule_name
        host_host_rule_info.enabled = self.enabled
        host_host_rule_info.mandatory = self.mandatory
        host_host_rule_info.vmGroupName = self.vm_group_name
        if self.affinity_rule:
            host_host_rule_info.affineHostGroupName = self.host_group_name
        else:
            host_host_rule_info.antiAffineHostGroupName = self.host_group_name

        rule_spec = vim.cluster.RuleSpec()
        rule_spec.operation = 'add'
        rule_spec.info = host_host_rule_info

        config_spec = vim.cluster.ConfigSpecEx()
        config_spec.rulesSpec.append(rule_spec)
        try:
            host_group_task = self.cluster_obj.ReconfigureEx(spec=config_spec, modify=True)
            host_group_created, result = wait_for_task(host_group_task)
        except vmodl.fault.InvalidRequest as e:
            result = to_native(e.msg)
        except Exception as e:
            result = to_native(e)

        if host_group_created:
            rule_obj = self.get_rule_key_by_name(rule_name=self.rule_name)
            result = self.normalize_rule_spec(rule_obj)

        return host_group_created, result

    # Delete
    def delete(self, rule_name=None):
        """
        Function to delete DRS rule using name
        """
        changed = False
        if rule_name is None:
            rule_name = self.rule_name

        rule = self.get_rule_key_by_name(rule_name=rule_name)
        if rule is not None:
            rule_key = int(rule.key)
            rule_spec = vim.cluster.RuleSpec(removeKey=rule_key, operation='remove')
            config_spec = vim.cluster.ConfigSpecEx(rulesSpec=[rule_spec])
            try:
                task = self.cluster_obj.ReconfigureEx(config_spec, modify=True)
                changed, result = wait_for_task(task)
            except vmodl.fault.InvalidRequest as e:
                result = to_native(e.msg)
            except Exception as e:
                result = to_native(e)
        else:
            result = 'No rule named %s exists' % self.rule_name
        return changed, result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        vms=dict(type='list'),
        esxi_hostnames=dict(type='list'),
        host_group_name=dict(type='str'),
        vm_group_name=dict(type='str'),
        cluster_name=dict(type='str', required=True),
        drs_rule_name=dict(type='str', required=True),
        enabled=dict(type='bool', default=False),
        mandatory=dict(type='bool', default=False),
        affinity_rule=dict(type='bool', default=True),
    )
    )

    required_if = [
        ['state', 'present', ['vms', 'esxi_hostnames', 'vm_group_name', 'host_group_name']],
    ]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    results = dict(failed=False, changed=False)
    state = module.params['state']
    vm_drs = VmwareHostDrs(module)

    if state == 'present':
        # Add Rule
        if module.check_mode:
            results['changed'] = True
            module.exit_json(**results)
        changed, result = vm_drs.create()
        if changed:
            results['changed'] = changed
        else:
            results['failed'] = True
            results['msg'] = "Failed to create DRS rule %s" % vm_drs.rule_name

        results['result'] = result
    elif state == 'absent':
        # Delete Rule
        if module.check_mode:
            results['changed'] = True
            module.exit_json(**results)
        changed, result = vm_drs.delete()
        if changed:
            results['changed'] = changed
        else:
            results['failed'] = True
            results['msg'] = "Failed to delete DRS rule %s" % vm_drs.rule_name
        results['result'] = result

    if results['changed']:
        module.exit_json(**results)
    if results['failed']:
        module.fail_json(**results)


if __name__ == '__main__':
    main()
