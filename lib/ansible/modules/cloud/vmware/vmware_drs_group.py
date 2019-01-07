#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Karsten Kaj Jakobsen <kj@patientsky.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# - name: Create DRS VM/Host group
#   vmware_drs_group:
#     # Login creds
#     hostname: '127.0.0.1'
#     username: 'administrator@vsphere.local'
#     password: 'password'
#     validate_certs: false
#     # Options
#     cluster_name: 'test'
#     group_name: TEST_S1
#     vms:
#       - vm-01-node01
#       - vm-01-node02
#     state: present
#   delegate_to: localhost

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
'''

EXAMPLES = r'''
'''

RETURN = r'''
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec,
                                         wait_for_task, find_cluster_by_name, find_vm_by_id)

class VmwareDrsGroupManager(PyVmomi):
    """
    Docstring
    """

    def get_msg(self):
        """
        Message
        """
        return self.__msg

    def get_result(self):
        """
        Message
        """
        return self.__result

    def get_changed(self):
        """
        Message
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

                # Get host data
                vm_obj = find_vm_by_id(content=self.content, vm_id=vm,
                                       vm_id_type='vm_name', cluster=cluster_obj)

                if vm_obj is None:
                    raise Exception("VM %s does not exist in cluster %s" % (vm, self.__cluster_name))

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

                # Get host data
                host_obj = self.find_hostsystem_by_name(host)

                if host_obj is None:
                    raise Exception("ESXi host %s does not exist in cluster %s" % (host, self.__cluster_name))

                self.__host_obj_list.append(host_obj)

    def __init__(self, module, cluster_name, group_name, datacenter, vm_list=None, host_list=None):
        """
        Init
        """

        super(VmwareDrsGroupManager, self).__init__(module)

        self.__datacenter = datacenter
        self.__cluster_name = cluster_name
        self.__group_name = group_name
        self.__vm_list = vm_list
        self.__vm_obj_list = []
        self.__host_list = host_list
        self.__host_obj_list = []
        self.__msg = 'Nothing to see here...'
        self.__result = dict()
        self.__changed = False

        # Sanity checks
        self.__cluster_obj = find_cluster_by_name(content=self.content,
                                                  cluster_name=self.__cluster_name)

        # Dont check if dry run
        if not module.check_mode:

            # Throw error if cluster does not exist
            if self.__cluster_obj is None:
                raise Exception("Failed to find the cluster %s" % self.__cluster_name)

            if self.__vm_list is not None:
                 self.__set_vm_obj_list(vm_list=self.__vm_list)

            if self.__host_list is not None:
                self.__set_host_obj_list(host_list=self.__host_list)


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

    def __group_exists(self, group_name=None, cluster_obj=None):
        """
        Function to check if group already exists
        Args:
            group_name: Name of group
            cluster_obj: vim Cluster object

        Returns: Bool

        """

        if group_name is None:
            group_name = self.__group_name

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        group = self.__get_group_by_name(group_name=group_name, cluster_obj=cluster_obj)

        if group is None:
            return False
        else:
            return True

    def __check_if_vms_changed(self, group_name=None, cluster_obj=None):
        """
        Function to check if vms changed
        Args:
            group_name: Name of group
            cluster_obj: vim Cluster object

        Returns: Bool

        """

        if group_name is None:
            group_name = self.__group_name

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        # By casting lists as a set, you remove duplicates and order doesn't count. Comparing sets is also much faster and more efficient than comparing lists.
        # if set(self.__host_list) == set(group_list_b):
        #     return False
        # else:
        #     return True

        # TODO
        return True

    def __check_if_hosts_changed(self, group_name=None, cluster_obj=None):
        """
        Function to check if hosts changed
        Args:
            group_name: Name of group
            cluster_obj: vim Cluster object

        Returns: Bool

        """

        if group_name is None:
            group_name = self.__group_name

        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        # By casting lists as a set, you remove duplicates and order doesn't count. Comparing sets is also much faster and more efficient than comparing lists.
        # if set(self.__host_list) == set(group_list_b):
        #     return False
        # else:
        #     return True

        # TODO
        return True

    def __create_host_group(self):

        # Check if group exists
        if self.__group_exists():
            operation = 'edit'
        else:
            operation = 'add'

        # Check if anything has changed when editing
        if operation == 'add' or (operation == 'edit' and self.__check_if_hosts_changed()):

            group = vim.cluster.HostGroup()

            group.name = self.__group_name
            group.host = self.__host_obj_list

            group_spec = vim.cluster.GroupSpec(info=group, operation=operation)
            config_spec = vim.cluster.ConfigSpecEx(groupSpec=[group_spec])

            task = self.__cluster_obj.ReconfigureEx(config_spec, modify=True)
            wait_for_task(task) # Wait for given task using exponential back-off algorithm.

            self.__changed = True

        self.__msg = "Created host group %s successfully" % (self.__group_name)

    def __create_vm_group(self):

        # Check if group exists
        if self.__group_exists():
            operation = 'edit'
        else:
            operation = 'add'

        # Check if anything has changed when editing
        if operation == 'add' or (operation == 'edit' and self.__check_if_vms_changed()):

            # Check if dry run
            if not self.module.check_mode:

                group = vim.cluster.VmGroup()

                group.name = self.__group_name
                group.vm = self.__vm_obj_list

                group_spec = vim.cluster.GroupSpec(info=group, operation=operation)
                config_spec = vim.cluster.ConfigSpecEx(groupSpec=[group_spec])

                task = self.__cluster_obj.ReconfigureEx(config_spec, modify=True)
                wait_for_task(task) # Wait for given task using exponential back-off algorithm.

            self.__changed = True

        self.__msg = "Created vm group %s successfully" % (self.__group_name)

    # Create
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


    def __get_group_key_by_name(self, cluster_obj=None, group_name=None):
        """
        Function to get a specific DRS group key by name
        Args:
            group_name: Name of group
            cluster_obj: Cluster managed object

        Returns: Group Object if found or None

        """
        if cluster_obj is None:
            cluster_obj = self.__cluster_obj

        # Allow for group check even if dry run
        if self.module.check_mode and cluster_obj is None:
            return None

        if group_name is None:
            group_name = self.__group_name

        if group_name:
            groups_list = [group for group in cluster_obj.configurationEx.group if group.name == group_name]
            if groups_list:
                return groups_list[0]

        # No group found
        return None

    def delete_drs_group(self):
        """
        Function to delete a DRS host/vm group
        """

        group = self.__get_group_key_by_name()
        operation = 'remove'

        if group is not None:

            self.__changed = True

            # Check if dry run
            if not self.module.check_mode:

                group_spec = vim.cluster.GroupSpec(removeKey=self.__group_name, operation=operation)
                config_spec = vim.cluster.ConfigSpecEx(groupSpec=[group_spec])

                task = self.__cluster_obj.ReconfigureEx(config_spec, modify=True)
                wait_for_task(task)

        # Dont throw error if group does not exist. Simply set changed = False
        self.__msg = "Delete group %s successfully for operation %s" % (self.__group_name, operation)


def main():
    """
    Main function
    """

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        datacenter=dict(type='str', required=True),
        cluster_name=dict(type='str', required=True),
        group_name=dict(type='str', required=True),
        vms=dict(type='list'),
        hosts=dict(type='list')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['vms', 'hosts']],
        required_one_of=[['vms', 'hosts']],
    )

    try:
        # Create instance of VmwareDrsGroupManager
        vmware_drs_group = VmwareDrsGroupManager(module=module,
                                                 datacenter=module.params['datacenter'],
                                                 cluster_name=module.params['cluster_name'],
                                                 group_name=module.params['group_name'],
                                                 vm_list=module.params['vms'],
                                                 host_list=module.params['hosts'])

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
