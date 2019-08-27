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

DOCUMENTATION = r'''
---
author:
  - "Karsten Kaj Jakobsen (@karstenjakobsen)"
description:
  - "This module can be used to create VM-Host rules in a given cluster."
extends_documentation_fragment: vmware.documentation
module: vmware_vm_host_drs_rule
notes:
  - "Tested on vSphere 6.5 and 6.7"
options:
  affinity_rule:
    default: true
    description:
      - "If set to C(True), the DRS rule will be an Affinity rule."
      - "If set to C(False), the DRS rule will be an Anti-Affinity rule."
      - "Effective only if C(state) is set to C(present)."
    type: bool
  datacenter:
    aliases:
      - datacenter_name
    description:
      - "Datacenter to search for given cluster. If not set, we use first cluster we encounter with C(cluster_name)."
    required: false
    type: str
  cluster_name:
    description:
      - "Cluster to create VM-Host rule."
    required: true
    type: str
  drs_rule_name:
    description:
      - "Name of rule to create or remove."
    required: true
    type: str
  enabled:
    default: false
    description:
      - "If set to C(True), the DRS rule will be enabled."
      - "Effective only if C(state) is set to C(present)."
    type: bool
  host_group_name:
    description:
      - "Name of Host group to use with rule."
      - "Effective only if C(state) is set to C(present)."
    required: true
    type: str
  mandatory:
    default: false
    description:
      - "If set to C(True), the DRS rule will be mandatory."
      - "Effective only if C(state) is set to C(present)."
    type: bool
  state:
    choices:
      - present
      - absent
    default: present
    description:
      - "If set to C(present) and the rule doesn't exists then the rule will be created."
      - "If set to C(absent) and the rule exists then the rule will be deleted."
    required: true
    type: str
  vm_group_name:
    description:
      - "Name of VM group to use with rule."
      - "Effective only if C(state) is set to C(present)."
    required: true
    type: str
requirements:
  - "python >= 2.6"
  - PyVmomi
short_description: "Creates vm/host group in a given cluster"
version_added: "2.8"

'''

EXAMPLES = r'''
---
- name: "Create mandatory DRS Affinity rule for VM/Host"
  vmware_vm_host_drs_rule:
    hostname: "{{ vcenter_hostname }}"
    password: "{{ vcenter_password }}"
    username: "{{ vcenter_username }}"
    validate_certs: False
    cluster_name: DC0_C0
    drs_rule_name: drs_rule_host_aff_0001
    host_group_name: DC0_C0_HOST_GR1
    vm_group_name: DC0_C0_VM_GR1
    mandatory: True
    enabled: True
    affinity_rule: True
'''

RETURN = r'''

'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec, wait_for_task, find_cluster_by_name,
                                         find_datacenter_by_name)


class VmwareVmHostRuleDrs(PyVmomi):
    """
    Class to manage VM HOST DRS Rules
    """

    def __init__(self, module):
        """
        Doctring: Init
        """

        super(VmwareVmHostRuleDrs, self).__init__(module)

        self.__datacenter_name = module.params.get('datacenter', None)
        self.__datacenter_obj = None
        self.__cluster_name = module.params['cluster_name']
        self.__cluster_obj = None
        self.__vm_group_name = module.params.get('vm_group_name', None)
        self.__host_group_name = module.params.get('host_group_name', None)
        self.__rule_name = module.params['drs_rule_name']
        self.__enabled = module.params['enabled']
        self.__mandatory = module.params['mandatory']
        self.__affinity_rule = module.params['affinity_rule']
        self.__state = module.params['state']
        self.__msg = 'Nothing to see here...'
        self.__result = dict()
        self.__changed = False

        if self.__datacenter_name is not None:

            self.__datacenter_obj = find_datacenter_by_name(self.content, self.__datacenter_name)

            if self.__datacenter_obj is None and module.check_mode is False:
                raise Exception("Datacenter '%s' not found" % self.__datacenter_name)

        self.__cluster_obj = find_cluster_by_name(content=self.content,
                                                  cluster_name=self.__cluster_name,
                                                  datacenter=self.__datacenter_obj)

        # Throw error if cluster does not exist
        if self.__cluster_obj is None and module.check_mode is False:
            raise Exception("Cluster '%s' not found" % self.__cluster_name)

        # Dont populate lists if we are deleting group
        if self.__state == 'present':
            # Get list of vm groups only if state is present
            self.__vm_group_obj = self.__get_group_by_name(group_name=self.__vm_group_name)
            self.__host_group_obj = self.__get_group_by_name(group_name=self.__host_group_name, host_group=True)

    def get_msg(self):
        """
        Returns message for Ansible result
        Args: none

        Returns: string
        """
        return self.__msg

    def get_result(self):
        """
        Returns result for Ansible
        Args: none

        Returns: dict
        """
        return self.__result

    def get_changed(self):
        """
        Returns if anything changed
        Args: none

        Returns: boolean
        """
        return self.__changed

    def __get_group_by_name(self, group_name, cluster_obj=None, host_group=False):
        """
        Return group
        Args:
            group_name: Group name
            cluster_obj: Cluster managed object

        Returns: cluster_obj.configurationEx.group

        """
        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        for group in cluster_obj.configurationEx.group:

            if not host_group and isinstance(group, vim.cluster.VmGroup):
                if group.name == group_name:
                    return group
            elif host_group and isinstance(group, vim.cluster.HostGroup):
                if group.name == group_name:
                    return group

        raise Exception("Failed to find the group %s in given cluster %s" % (group_name, cluster_obj.name))

    def __get_rule_key_by_name(self, cluster_obj=None, rule_name=None):
        """
        Function to get a specific VM-Host DRS rule key by name
        Args:
            rule_name: Name of rule
            cluster_obj: Cluster managed object

        Returns: Rule Object if found or None

        """

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        if rule_name is None:
            rule_name = self.__rule_name

        if rule_name:
            rules_list = [rule for rule in cluster_obj.configuration.rule if rule.name == rule_name]
            if rules_list:
                return rules_list[0]

        # No rule found
        return None

    def __normalize_vm_host_rule_spec(self, rule_obj, cluster_obj=None):
        """
        Return human readable rule spec
        Args:
            rule_obj: Rule managed object
            cluster_obj: Cluster managed object

        Returns: Dictionary with VM-Host DRS Rule info

        """
        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

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
                    rule_vms=self.__get_all_from_group(group_name=rule_obj.vmGroupName,
                                                       cluster_obj=cluster_obj),
                    rule_affine_hosts=self.__get_all_from_group(group_name=rule_obj.affineHostGroupName,
                                                                cluster_obj=cluster_obj,
                                                                host_group=True),
                    rule_anti_affine_hosts=self.__get_all_from_group(group_name=rule_obj.antiAffineHostGroupName,
                                                                     cluster_obj=cluster_obj,
                                                                     host_group=True),
                    rule_type="vm_host_rule"
                    )

    def __get_all_from_group(self, group_name=None, cluster_obj=None, host_group=False):
        """
        Return all VM / Host names using given group name
        Args:
            group_name: Rule name
            cluster_obj: Cluster managed object
            host_group: True if we want only host name from group

        Returns: List of VM-Host names belonging to given group object

        """
        obj_name_list = []

        if not all([group_name, cluster_obj]):
            return obj_name_list

        for group in cluster_obj.configurationEx.group:
            if group.name == group_name:
                if not host_group and isinstance(group, vim.cluster.VmGroup):
                    obj_name_list = [vm.name for vm in group.vm]
                    break
                elif host_group and isinstance(group, vim.cluster.HostGroup):
                    obj_name_list = [host.name for host in group.host]
                    break

        return obj_name_list

    def __check_rule_has_changed(self, rule_obj, cluster_obj=None):
        """
        Function to check if the rule being edited has changed
        """

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        existing_rule = self.__normalize_vm_host_rule_spec(rule_obj=rule_obj, cluster_obj=cluster_obj)

        # Check if anything has changed
        if ((existing_rule['rule_enabled'] == self.__enabled) and
            (existing_rule['rule_mandatory'] == self.__mandatory) and
            (existing_rule['rule_vm_group_name'] == self.__vm_group_name) and
            (existing_rule['rule_affine_host_group_name'] == self.__host_group_name or
             existing_rule['rule_anti_affine_host_group_name'] == self.__host_group_name)):

            return False
        else:
            return True

    def create(self):
        """
        Function to create a host VM-Host DRS rule if rule does not exist
        """
        rule_obj = self.__get_rule_key_by_name(rule_name=self.__rule_name)

        # Check if rule exists
        if rule_obj:

            operation = 'edit'
            rule_changed = self.__check_rule_has_changed(rule_obj)

        else:
            operation = 'add'

        # Check if anything has changed when editing
        if operation == 'add' or (operation == 'edit' and rule_changed is True):

            rule = vim.cluster.VmHostRuleInfo()

            # Check if already rule exists
            if rule_obj:
                # This need to be set in order to edit a existing rule
                rule.key = rule_obj.key

            rule.enabled = self.__enabled
            rule.mandatory = self.__mandatory
            rule.name = self.__rule_name

            if self.__affinity_rule:
                rule.affineHostGroupName = self.__host_group_name
            else:
                rule.antiAffineHostGroupName = self.__host_group_name

            rule.vmGroupName = self.__vm_group_name

            rule_spec = vim.cluster.RuleSpec(info=rule, operation=operation)
            config_spec = vim.cluster.ConfigSpecEx(rulesSpec=[rule_spec])

            if not self.module.check_mode:

                task = self.__cluster_obj.ReconfigureEx(config_spec, modify=True)
                wait_for_task(task)

            self.__changed = True

        rule_obj = self.__get_rule_key_by_name(rule_name=self.__rule_name)
        self.__result = self.__normalize_vm_host_rule_spec(rule_obj)

        if operation == 'edit':
            self.__msg = "Updated DRS rule `%s` successfully" % (self.__rule_name)
        else:
            self.__msg = "Created DRS rule `%s` successfully" % (self.__rule_name)

    # Delete
    def delete(self, rule_name=None):
        """
        Function to delete VM-Host DRS rule using name
        """
        changed = False

        if rule_name is None:
            rule_name = self.__rule_name

        rule_obj = self.__get_rule_key_by_name(rule_name=rule_name)

        if rule_obj is not None:

            rule_key = int(rule_obj.key)
            rule_spec = vim.cluster.RuleSpec(removeKey=rule_key, operation='remove')
            config_spec = vim.cluster.ConfigSpecEx(rulesSpec=[rule_spec])

            if not self.module.check_mode:

                task = self.__cluster_obj.ReconfigureEx(config_spec, modify=True)
                wait_for_task(task)

            self.__changed = True

        if self.__changed:
            self.__msg = "Deleted DRS rule `%s` successfully" % (self.__rule_name)
        else:
            self.__msg = "DRS Rule `%s` does not exists or already deleted" % (self.__rule_name)


def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        vm_group_name=dict(type='str', required=True),
        host_group_name=dict(type='str', required=True),
        cluster_name=dict(type='str', required=True),
        datacenter=dict(type='str', required=False, aliases=['datacenter_name']),
        drs_rule_name=dict(type='str', required=True),
        enabled=dict(type='bool', default=False),
        mandatory=dict(type='bool', default=False),
        affinity_rule=dict(type='bool', default=True))
    )

    required_if = [
        ['state', 'present', ['vm_group_name'], ['host_group_name']],
    ]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    try:
        # Create instance of VmwareDrsGroupManager
        vm_host_drs = VmwareVmHostRuleDrs(module=module)

        if module.params['state'] == 'present':
            vm_host_drs.create()
        elif module.params['state'] == 'absent':
            vm_host_drs.delete()

        # Set results
        results = dict(msg=vm_host_drs.get_msg(),
                       failed=False,
                       changed=vm_host_drs.get_changed(),
                       result=vm_host_drs.get_result())

    except Exception as error:
        results = dict(failed=True, msg="Error: `%s`" % error)

    if results['failed']:
        module.fail_json(**results)
    else:
        module.exit_json(**results)


if __name__ == '__main__':
    main()
