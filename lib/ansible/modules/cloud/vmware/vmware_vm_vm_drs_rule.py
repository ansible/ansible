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
module: vmware_vm_vm_drs_rule
short_description: Configure VMware DRS Affinity rule for virtual machine in given cluster
description:
- This module can be used to configure VMware DRS Affinity rule for virtual machine in given cluster.
version_added: 2.5
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- "python >= 2.6"
- PyVmomi
options:
  cluster_name:
    description:
    - Desired cluster name where virtual machines are present for the DRS rule.
    required: True
  vms:
    description:
    - List of virtual machines name for which DRS rule needs to be applied.
    - Required if C(state) is set to C(present).
  drs_rule_name:
    description:
    - The name of the DRS rule to manage.
    required: True
  enabled:
    description:
    - If set to C(True), the DRS rule will be enabled.
    - Effective only if C(state) is set to C(present).
    default: False
    type: bool
  mandatory:
    description:
    - If set to C(True), the DRS rule will be mandatory.
    - Effective only if C(state) is set to C(present).
    default: False
    type: bool
  affinity_rule:
    description:
    - If set to C(True), the DRS rule will be an Affinity rule.
    - If set to C(False), the DRS rule will be an Anti-Affinity rule.
    - Effective only if C(state) is set to C(present).
    default: True
    type: bool
  state:
    description:
    - If set to C(present), then the DRS rule is created if not present.
    - If set to C(present), then the DRS rule is deleted and created if present already.
    - If set to C(absent), then the DRS rule is deleted if present.
    required: False
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Create DRS Affinity Rule for VM-VM
  vmware_vm_vm_drs_rule:
    hostname: "{{ esxi }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
    cluster_name: "{{ cluster_name }}"
    validate_certs: no
    vms:
        - vm1
        - vm2
    drs_rule_name: vm1-vm2-affinity-rule-001
    enabled: True
    mandatory: True
    affinity_rule: True

- name: Create DRS Anti-Affinity Rule for VM-VM
  vmware_vm_vm_drs_rule:
    hostname: "{{ esxi }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
    cluster_name: "{{ cluster_name }}"
    validate_certs: no
    vms:
        - vm1
        - vm2
    drs_rule_name: vm1-vm2-affinity-rule-001
    enabled: True
    mandatory: True
    affinity_rule: False

- name: Delete DRS Affinity Rule for VM-VM
  vmware_vm_vm_drs_rule:
    hostname: "{{ esxi }}"
    username: "{{ esxi_username }}"
    password: "{{ esxi_password }}"
    cluster_name: "{{ cluster_name }}"
    validate_certs: no
    drs_rule_name: vm1-vm2-affinity-rule-001
    state: absent
'''

RETURN = r'''
result:
    description: metadata about DRS VM and VM rule
    returned: when state is present
    type: dict
    sample: {
            "rule_enabled": false,
            "rule_key": 20,
            "rule_mandatory": true,
            "rule_name": "drs_rule_0014",
            "rule_uuid": "525f3bc0-253f-825a-418e-2ec93bffc9ae",
            "rule_vms": [
                "VM_65",
                "VM_146"
            ]
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


class VmwareDrs(PyVmomi):
    def __init__(self, module):
        super(VmwareDrs, self).__init__(module)
        self.vm_list = module.params['vms']
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
        if self.state == 'present':
            # Get list of VMs only if state is present
            self.vm_obj_list = self.get_all_vms_info()

    # Getter
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
                                          "in given cluster %s" % (vm_name,
                                                                   self.cluster_name))
            vm_obj_list.append(vm_obj)
        return vm_obj_list

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
            rules_list = [rule for rule in cluster_obj.configuration.rule if rule.name == rule_name]
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
                    rule_vms=[vm.name for vm in rule_obj.vm],
                    rule_affinity=True if isinstance(rule_obj, vim.cluster.AffinityRuleSpec) else False,
                    )

    # Create
    def create(self):
        """
        Function to create a DRS rule if rule does not exist
        """
        rule_obj = self.get_rule_key_by_name(rule_name=self.rule_name)
        if rule_obj is not None:
            # Rule already exists, remove and create again
            # Cluster does not allow editing existing rule
            existing_rule = self.normalize_rule_spec(rule_obj=rule_obj)
            if ((sorted(existing_rule['rule_vms']) == sorted(self.vm_list)) and
                    (existing_rule['rule_enabled'] == self.enabled) and
                    (existing_rule['rule_mandatory'] == self.mandatory) and
                    (existing_rule['rule_affinity'] == self.affinity_rule)):
                # Rule is same as existing rule, evacuate
                self.module.exit_json(changed=False, result=existing_rule)
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
        changed = False
        if self.affinity_rule:
            rule = vim.cluster.AffinityRuleSpec()
        else:
            rule = vim.cluster.AntiAffinityRuleSpec()

        rule.vm = self.vm_obj_list
        rule.enabled = self.enabled
        rule.mandatory = self.mandatory
        rule.name = self.rule_name

        rule_spec = vim.cluster.RuleSpec(info=rule, operation='add')
        config_spec = vim.cluster.ConfigSpecEx(rulesSpec=[rule_spec])

        try:
            task = self.cluster_obj.ReconfigureEx(config_spec, modify=True)
            changed, result = wait_for_task(task)
        except vmodl.fault.InvalidRequest as e:
            result = to_native(e.msg)
        except Exception as e:
            result = to_native(e)

        if changed:
            rule_obj = self.get_rule_key_by_name(rule_name=self.rule_name)
            result = self.normalize_rule_spec(rule_obj)

        return changed, result

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
        cluster_name=dict(type='str', required=True),
        drs_rule_name=dict(type='str', required=True),
        enabled=dict(type='bool', default=False),
        mandatory=dict(type='bool', default=False),
        affinity_rule=dict(type='bool', default=True),
    )
    )

    required_if = [
        ['state', 'present', ['vms']],
    ]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    results = dict(failed=False, changed=False)
    state = module.params['state']
    vm_drs = VmwareDrs(module)

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
            results['msg'] = "DRS rule %s deleted successfully." % vm_drs.rule_name
        else:
            if "No rule named" in result:
                results['msg'] = result
                module.exit_json(**results)

            results['failed'] = True
            results['msg'] = "Failed to delete DRS rule %s" % vm_drs.rule_name
        results['result'] = result

    if results['changed']:
        module.exit_json(**results)
    if results['failed']:
        module.fail_json(**results)


if __name__ == '__main__':
    main()
