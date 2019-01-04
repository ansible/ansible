#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Karsten Kaj Jakobsen <kj@patientsky.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = ''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec, wait_for_task, find_cluster_by_name)

class VmwareVmHostRuleDrs(PyVmomi):

    def __init__(self, module):

        super(VmwareVmHostRuleDrs, self).__init__(module)

        self.vm_group_name = module.params['vm_group_name']
        self.host_group_name = module.params['host_group_name']
        self.cluster_name = module.params['cluster_name']
        self.rule_name = module.params['drs_rule_name']
        self.enabled = module.params['enabled']
        self.mandatory = module.params['mandatory']
        self.affinity_rule = module.params['affinity_rule']
        self.state = module.params['state']

        # Sanity check for cluster
        self.cluster_obj = find_cluster_by_name(content=self.content,
                                                cluster_name=self.cluster_name)

        # Sanity check for cluster
        if self.cluster_obj is None:
            self.module.fail_json(msg="Failed to find the cluster %s" % self.cluster_name)

        # Sanity check for groups
        if self.state == 'present':
            # Get list of vm groups only if state is present
            self.vm_group_obj = self.get_group_by_name(group_name=self.vm_group_name)
            self.host_group_obj = self.get_group_by_name(group_name=self.host_group_name, host_group=True)


    def get_group_by_name(self, group_name, cluster_obj=None, host_group=False):
        """
        Return group
        Args:
            group_name: Group name
            cluster_obj: Cluster managed object

        Returns: cluster_obj.configurationEx.group

        """
        if cluster_obj is None:
            cluster_obj = self.cluster_obj

        for group in cluster_obj.configurationEx.group:

            if not host_group and isinstance(group, vim.cluster.VmGroup):
                if group.name == group_name:
                    return group
            elif host_group and isinstance(group, vim.cluster.HostGroup):
                if group.name == group_name:
                    return group

        self.module.fail_json(msg="Failed to find the group %s "
                              "in given cluster %s" % (group_name, cluster_obj.name))



    def get_rule_key_by_name(self, cluster_obj=None, rule_name=None):
        """
        Function to get a specific VM-Host DRS rule key by name
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

    def normalize_vm_host_rule_spec(self, rule_obj=None, cluster_obj=None):
        """
        Return human readable rule spec
        Args:
            rule_obj: Rule managed object
            cluster_obj: Cluster managed object

        Returns: Dictionary with VM-Host DRS Rule info

        """
        if not all([rule_obj, cluster_obj]):
            return {}

        return dict(rule_key=rule_obj.key,
                    rule_enabled=rule_obj.enabled,
                    rule_name=rule_obj.name,
                    rule_mandatory=rule_obj.mandatory,
                    rule_uuid=rule_obj.ruleUuid,
                    rule_vm_group_name=rule_obj.vmGroupName,
                    rule_affine_host_group_name=rule_obj.affineHostGroupName,
                    rule_anti_affine_host_group_name=rule_obj.antiAffineHostGroupName,
                    rule_vms=self.get_all_from_group(group_name=rule_obj.vmGroupName,
                                                     cluster_obj=cluster_obj),
                    rule_affine_hosts=self.get_all_from_group(group_name=rule_obj.affineHostGroupName,
                                                              cluster_obj=cluster_obj,
                                                              hostgroup=True),
                    rule_anti_affine_hosts=self.get_all_from_group(group_name=rule_obj.antiAffineHostGroupName,
                                                                   cluster_obj=cluster_obj,
                                                                   hostgroup=True),
                    rule_type="vm_host_rule",
                    )

    def get_all_from_group(self, group_name=None, cluster_obj=None, hostgroup=False):
        """
        Return all VM / Host names using given group name
        Args:
            group_name: Rule name
            cluster_obj: Cluster managed object
            hostgroup: True if we want only host name from group

        Returns: List of VM-Host names belonging to given group object

        """
        obj_name_list = []

        if not all([group_name, cluster_obj]):
            return obj_name_list

        for group in cluster_obj.configurationEx.group:
            if group.name == group_name:
                if not hostgroup and isinstance(group, vim.cluster.VmGroup):
                    obj_name_list = [vm.name for vm in group.vm]
                    break
                elif hostgroup and isinstance(group, vim.cluster.HostGroup):
                    obj_name_list = [host.name for host in group.host]
                    break

        return obj_name_list

    # Create
    def create(self):
        """
        Function to create a host VM-Host DRS rule if rule does not exist
        """
        rule_obj = self.get_rule_key_by_name(rule_name=self.rule_name)

        if rule_obj is not None:

            # Rule already exists, remove and create again
            # Cluster does not allow editing existing rule
            existing_rule = self.normalize_vm_host_rule_spec(rule_obj=rule_obj, cluster_obj=self.cluster_obj)

            if ((existing_rule['rule_enabled'] == self.enabled) and
                (existing_rule['rule_mandatory'] == self.mandatory) and
                (existing_rule['rule_vm_group_name'] == self.vm_group_name) and
                (existing_rule['rule_affine_host_group_name'] == self.host_group_name or existing_rule['rule_anti_affine_host_group_name'] == self.host_group_name)):

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
        Function to create VM-Host DRS rule
        """
        changed = False

        rule = vim.cluster.VmHostRuleInfo()

        rule.enabled = self.enabled
        rule.mandatory = self.mandatory
        rule.name = self.rule_name

        if self.affinity_rule:
            rule.affineHostGroupName = self.host_group_name
        else:
            rule.antiAffineHostGroupName = self.host_group_name

        rule.vmGroupName = self.vm_group_name

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
            result = self.normalize_vm_host_rule_spec(rule_obj)

        return changed, result

    # Delete
    def delete(self, rule_name=None):
        """
        Function to delete VM-Host DRS rule using name
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
        vm_group_name=dict(type='str', required=True),
        host_group_name=dict(type='str', required=True),
        cluster_name=dict(type='str', required=True),
        drs_rule_name=dict(type='str', required=True),
        enabled=dict(type='bool', default=False),
        mandatory=dict(type='bool', default=True),
        affinity_rule=dict(type='bool', default=True)
    )
    )

    required_if = [
        ['state', 'present', ['vm_group_name'], ['host_group_name']],
    ]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    results = dict(failed=False, changed=False)
    state = module.params['state']
    vm_host_drs = VmwareVmHostRuleDrs(module)

    if state == 'present':

        # Add Rule
        if module.check_mode:
            results['changed'] = True
            module.exit_json(**results)

        changed, result = vm_host_drs.create()

        if changed:
            results['changed'] = changed
        else:
            results['failed'] = True
            results['msg'] = "Failed to create VM-Host DRS rule %s" % vm_host_drs.rule_name

        results['result'] = result

    elif state == 'absent':

        # Delete Rule
        if module.check_mode:
            results['changed'] = True
            module.exit_json(**results)

        changed, result = vm_host_drs.delete()

        if changed:
            results['changed'] = changed
            results['msg'] = "VM-Host DRS rule %s deleted successfully." % vm_host_drs.rule_name
        else:
            if "No rule named" in result:
                results['msg'] = result
                module.exit_json(**results)

            results['failed'] = True
            results['msg'] = "Failed to delete VM-Host DRS rule %s" % vm_host_drs.rule_name

        results['result'] = result

    if results['changed']:
        module.exit_json(**results)
    if results['failed']:
        module.fail_json(**results)


if __name__ == '__main__':
    main()