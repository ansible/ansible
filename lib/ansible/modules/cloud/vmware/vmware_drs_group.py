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
  - "This module can be used to create VM/Host groups in a given cluster. Creates a vm group if C(vms) is set. Creates a host group if C(hosts) is set."
extends_documentation_fragment: vmware.documentation
module: vmware_drs_group
notes:
  - "Tested on vSphere 6.5 and 6.7"
options:
  cluster_name:
    description:
      - "Cluster to create vm/host group."
    required: true
  datacenter:
    aliases:
      - datacenter_name
    description:
      - "Datacenter to search for given cluster. If not set, we use first cluster we encounter with C(cluster_name)."
    required: false
  group_name:
    description:
      - "The name of the group to create or remove."
    required: true
  hosts:
    description:
      - "List of hosts to create in group."
      - "Required only if C(vms) is not set."
    required: false
  state:
    choices:
      - present
      - absent
    default: present
    description:
      - "If set to C(present) and the group doesn't exists then the group will be created."
      - "If set to C(absent) and the group exists then the groupwill be deleted."
    required: true
  vms:
    description:
      - "List of vms to create in group."
      - "Required only if C(hosts) is not set."
    required: false
requirements:
  - "python >= 2.6"
  - PyVmomi
short_description: "Creates vm/host group in a given cluster."
version_added: "2.8"
'''

EXAMPLES = r'''
---
- name: "Create DRS VM group"
  delegate_to: localhost
  vmware_drs_group:
    hostname: "{{ vcenter_hostname }}"
    password: "{{ vcenter_password }}"
    username: "{{ vcenter_username }}"
    cluster_name: DC0_C0
    datacenter_name: DC0
    group_name: TEST_VM_01
    vms:
      - DC0_C0_RP0_VM0
      - DC0_C0_RP0_VM1
    state: present

- name: "Create DRS Host group"
  delegate_to: localhost
  vmware_drs_group:
    hostname: "{{ vcenter_hostname }}"
    password: "{{ vcenter_password }}"
    username: "{{ vcenter_username }}"
    cluster_name: DC0_C0
    datacenter_name: DC0
    group_name: TEST_HOST_01
    hosts:
      - DC0_C0_H0
      - DC0_C0_H1
      - DC0_C0_H2
    state: absent

- name: "Delete DRS Host group"
  delegate_to: localhost
  vmware_drs_group:
    hostname: "{{ vcenter_hostname }}"
    password: "{{ vcenter_password }}"
    username: "{{ vcenter_username }}"
    cluster_name: DC0_C0
    datacenter_name: DC0
    group_name: TEST_HOST_01
    state: absent

'''

RETURN = r'''
drs_group_facts:
    description: Metadata about DRS group created
    returned: always
    type: dict
    sample:
        "drs_group_facts": {
        "changed": true,
        "failed": false,
        "msg": "Created host group TEST_HOST_01 successfully",
        "result": {
            "DC0_C0": [
                {
                    "group_name": "TEST_HOST_01",
                    "hosts": [
                        "DC0_C0_H0",
                        "DC0_C0_H1",
                        "DC0_C0_H2"
                    ],
                    "type": "host"
                }
            ]
        }
    }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec,
                                         wait_for_task, find_cluster_by_name,
                                         find_vm_by_id, find_datacenter_by_name, find_vm_by_name)


class VmwareDrsGroupManager(PyVmomi):
    """
    Class to manage DRS groups
    """

    def __init__(self, module, cluster_name, group_name, state,
                 datacenter_name=None, vm_list=None, host_list=None):
        """
        Init
        """

        super(VmwareDrsGroupManager, self).__init__(module)

        self.__datacenter_name = datacenter_name
        self.__datacenter_obj = None
        self.__cluster_name = cluster_name
        self.__cluster_obj = None
        self.__group_name = group_name
        self.__group_obj = None
        self.__operation = None
        self.__vm_list = vm_list
        self.__vm_obj_list = []
        self.__host_list = host_list
        self.__host_obj_list = []
        self.__msg = 'Nothing to see here...'
        self.__result = dict()
        self.__changed = False
        self.__state = state

        if datacenter_name is not None:

            self.__datacenter_obj = find_datacenter_by_name(self.content, self.__datacenter_name)

            if self.__datacenter_obj is None and module.check_mode is False:
                raise Exception("Datacenter '%s' not found" % self.__datacenter_name)

        self.__cluster_obj = find_cluster_by_name(content=self.content,
                                                  cluster_name=self.__cluster_name,
                                                  datacenter=self.__datacenter_obj)

        # Throw error if cluster does not exist
        if self.__cluster_obj is None:
            if module.check_mode is False:
                raise Exception("Cluster '%s' not found" % self.__cluster_name)
        else:
            # get group
            self.__group_obj = self.__get_group_by_name()
            # Set result here. If nothing is to be updated, result is already set
            self.__set_result(self.__group_obj)

        # Dont populate lists if we are deleting group
        if state == 'present':

            if self.__group_obj:
                self.__operation = 'edit'
            else:
                self.__operation = 'add'

            if self.__vm_list is not None:
                self.__set_vm_obj_list(vm_list=self.__vm_list)

            if self.__host_list is not None:
                self.__set_host_obj_list(host_list=self.__host_list)
        else:
            self.__operation = 'remove'

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

    def __set_result(self, group_obj):
        """
        Creates result for successful run
        Args:
            group_obj: group object

        Returns: None

        """
        self.__result = dict()

        if (self.__cluster_obj is not None) and (group_obj is not None):
            self.__result[self.__cluster_obj.name] = []
            self.__result[self.__cluster_obj.name].append(self.__normalize_group_data(group_obj))

    def get_changed(self):
        """
        Returns if anything changed
        Args: none

        Returns: boolean
        """
        return self.__changed

    def __set_vm_obj_list(self, vm_list=None, cluster_obj=None):
        """
        Function pupulate vm object list from list of vms
        Args:
            vm_list: List of vm names

        Returns: None

        """

        if vm_list is None:
            vm_list = self.__vm_list

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        if vm_list is not None:

            for vm in vm_list:

                if self.module.check_mode is False:

                    # Get host data
                    vm_obj = find_vm_by_id(content=self.content, vm_id=vm,
                                           vm_id_type='vm_name', cluster=cluster_obj)

                    if vm_obj is None:
                        raise Exception("VM %s does not exist in cluster %s" % (vm,
                                                                                self.__cluster_name))

                    self.__vm_obj_list.append(vm_obj)

    def __set_host_obj_list(self, host_list=None):
        """
        Function pupulate host object list from list of hostnames
        Args:
            host_list: List of host names

        Returns: None

        """

        if host_list is None:
            host_list = self.__host_list

        if host_list is not None:

            for host in host_list:

                if self.module.check_mode is False:

                    # Get host data
                    host_obj = self.find_hostsystem_by_name(host)

                    if host_obj is None and self.module.check_mode is False:
                        raise Exception("ESXi host %s does not exist in cluster %s" % (host, self.__cluster_name))

                    self.__host_obj_list.append(host_obj)

    def __get_group_by_name(self, group_name=None, cluster_obj=None):
        """
        Function to get group by name
        Args:
            group_name: Name of group
            cluster_obj: vim Cluster object

        Returns: Group Object if found or None

        """

        if group_name is None:
            group_name = self.__group_name

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        # Allow for group check even if dry run
        if self.module.check_mode and cluster_obj is None:
            return None

        for group in cluster_obj.configurationEx.group:
            if group.name == group_name:
                return group

        # No group found
        return None

    def __populate_vm_host_list(self, group_name=None, cluster_obj=None, host_group=False):
        """
        Return all VM/Host names using given group name
        Args:
            group_name: group name
            cluster_obj: Cluster managed object
            host_group: True if we want only host name from group

        Returns: List of VM/Host names belonging to given group object

        """
        obj_name_list = []

        if group_name is None:
            group_name = self.__group_name

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        if not all([group_name, cluster_obj]):
            return obj_name_list

        group = self.__group_obj

        if not host_group and isinstance(group, vim.cluster.VmGroup):
            obj_name_list = [vm.name for vm in group.vm]

        elif host_group and isinstance(group, vim.cluster.HostGroup):
            obj_name_list = [host.name for host in group.host]

        return obj_name_list

    def __check_if_vms_hosts_changed(self, group_name=None, cluster_obj=None, host_group=False):
        """
        Function to check if VMs/Hosts changed
        Args:
            group_name: Name of group
            cluster_obj: vim Cluster object
            host_group: True if we want to check hosts, else check vms

        Returns: Bool

        """

        if group_name is None:
            group_name = self.__group_name

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        list_a = self.__host_list if host_group else self.__vm_list
        list_b = self.__populate_vm_host_list(host_group=host_group)

        # By casting lists as a set, you remove duplicates and order doesn't count. Comparing sets is also much faster and more efficient than comparing lists.
        if set(list_a) == set(list_b):
            return False
        else:
            return True

    def __create_host_group(self):

        # Check if anything has changed when editing
        if self.__operation == 'add' or (self.__operation == 'edit' and self.__check_if_vms_hosts_changed(host_group=True)):

            group = vim.cluster.HostGroup()
            group.name = self.__group_name
            group.host = self.__host_obj_list

            group_spec = vim.cluster.GroupSpec(info=group, operation=self.__operation)
            config_spec = vim.cluster.ConfigSpecEx(groupSpec=[group_spec])

            if not self.module.check_mode:
                task = self.__cluster_obj.ReconfigureEx(config_spec, modify=True)
                wait_for_task(task)

            # Set new result since something changed
            self.__set_result(group)
            self.__changed = True

        if self.__operation == 'edit':
            self.__msg = "Updated host group %s successfully" % (self.__group_name)
        else:
            self.__msg = "Created host group %s successfully" % (self.__group_name)

    def __create_vm_group(self):

        # Check if anything has changed when editing
        if self.__operation == 'add' or (self.__operation == 'edit' and self.__check_if_vms_hosts_changed()):

            group = vim.cluster.VmGroup()

            group.name = self.__group_name
            group.vm = self.__vm_obj_list

            group_spec = vim.cluster.GroupSpec(info=group, operation=self.__operation)
            config_spec = vim.cluster.ConfigSpecEx(groupSpec=[group_spec])

            # Check if dry run
            if not self.module.check_mode:
                task = self.__cluster_obj.ReconfigureEx(config_spec, modify=True)
                wait_for_task(task)

            self.__set_result(group)
            self.__changed = True

        if self.__operation == 'edit':
            self.__msg = "Updated vm group %s successfully" % (self.__group_name)
        else:
            self.__msg = "Created vm group %s successfully" % (self.__group_name)

    def __normalize_group_data(self, group_obj):
        """
        Return human readable group spec
        Args:
            group_obj: Group object

        Returns: DRS group object fact

        """
        if not all([group_obj]):
            return {}

        # Check if group is a host group
        if hasattr(group_obj, 'host'):
            return dict(
                group_name=group_obj.name,
                hosts=self.__host_list,
                type="host"
            )
        else:
            return dict(
                group_name=group_obj.name,
                vms=self.__vm_list,
                type="vm"
            )

    def create_drs_group(self):
        """
        Function to create a DRS host/vm group
        """

        if self.__vm_list is None:
            self.__create_host_group()
        elif self.__host_list is None:
            self.__create_vm_group()
        else:
            raise Exception('Failed, no hosts or vms defined')

    def delete_drs_group(self):
        """
        Function to delete a DRS host/vm group
        """

        if self.__group_obj is not None:

            self.__changed = True

            # Check if dry run
            if not self.module.check_mode:

                group_spec = vim.cluster.GroupSpec(removeKey=self.__group_name, operation=self.__operation)
                config_spec = vim.cluster.ConfigSpecEx(groupSpec=[group_spec])

                task = self.__cluster_obj.ReconfigureEx(config_spec, modify=True)
                wait_for_task(task)

        # Dont throw error if group does not exist. Simply set changed = False
        if self.__changed:
            self.__msg = "Deleted group `%s` successfully" % (self.__group_name)
        else:
            self.__msg = "DRS group `%s` does not exists or already deleted" % (self.__group_name)


def main():
    """
    Main function
    """

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        datacenter=dict(type='str', required=False, aliases=['datacenter_name']),
        cluster_name=dict(type='str', required=True),
        group_name=dict(type='str', required=True),
        vms=dict(type='list'),
        hosts=dict(type='list')
    )

    required_if = [
        ['state', 'absent', ['group_name']]
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
        mutually_exclusive=[['vms', 'hosts']],
        required_one_of=[['vms', 'hosts']]
    )

    try:
        # Create instance of VmwareDrsGroupManager
        vmware_drs_group = VmwareDrsGroupManager(module=module,
                                                 datacenter_name=module.params.get('datacenter', None),
                                                 cluster_name=module.params['cluster_name'],
                                                 group_name=module.params['group_name'],
                                                 vm_list=module.params['vms'],
                                                 host_list=module.params['hosts'],
                                                 state=module.params['state'])

        if module.params['state'] == 'present':
            # Add DRS group
            vmware_drs_group.create_drs_group()
        elif module.params['state'] == 'absent':
            # Delete DRS group
            vmware_drs_group.delete_drs_group()

        # Set results
        results = dict(msg=vmware_drs_group.get_msg(),
                       failed=False,
                       changed=vmware_drs_group.get_changed(),
                       result=vmware_drs_group.get_result())

    except Exception as error:
        results = dict(failed=True, msg="Error: %s" % error)

    if results['failed']:
        module.fail_json(**results)
    else:
        module.exit_json(**results)


if __name__ == "__main__":
    main()
