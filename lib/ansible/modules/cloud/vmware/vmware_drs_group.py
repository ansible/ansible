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
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec, wait_for_task,
                                         find_vm_by_id, find_cluster_by_name)

class VmwareDrsGroupManager(PyVmomi):
    """
    Docstring
    """

    def get_msg(self):
        """
        Message
        """
        return self.__msg

    def set_msg(self, msg):
        """
        Message
        """
        self.__msg = msg

    def get_result(self):
        """
        Message
        """
        return self.__result

    def set_result(self, result):
        """
        Message
        """
        self.__result = result

    def get_failed(self):
        """
        Message
        """
        return self.__failed

    def set_failed(self, failed):
        """
        Message
        """
        self.__failed = failed

    def __init__(self, module, cluster_name, group_name, datacenter, vm_list=None, host_list=None):
        """
        Message
        """

        super(VmwareDrsGroupManager, self).__init__(module)

        self.__datacenter = datacenter
        self.__cluster_name = cluster_name
        self.__group_name = group_name
        self.__vm_list = vm_list
        self.__host_list = host_list
        self.__msg = 'Nothing to see here...'
        self.__failed = True
        self.__result = dict()

    def __create_host_group(self):

        self.set_result(dict(type='host'))
        self.set_failed(False)
        self.set_msg("Create successfully %s" % self.__group_name )

        return None

    def __create_vm_group(self):

        self.set_result(dict(type='vm'))
        self.set_failed(False)
        self.set_msg("Create successfully %s" % self.__group_name )

        return None

    # Create
    def create_drs_group(self):
        """
        Function to create a DRS host group
        """

        if self.__vm_list is None:
            self.__create_host_group()
        elif self.__host_list is None:
            self.__create_vm_group()
        else:
            self.set_failed(True)
            self.set_msg('Failed, no hosts or vms defined')


    # Create
    def delete_drs_group(self):
        """
        Function to create a DRS host group
        """

        return None


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

    # Create instance of VmwareDrsGroupManager
    vmware_drs_group = VmwareDrsGroupManager(module=module,
                                             datacenter=module.params['datacenter'],
                                             cluster_name=module.params['cluster_name'],
                                             group_name=module.params['group_name'])

    if module.params['state'] == 'present':
        # Add DRS group
        vmware_drs_group.create_drs_group()
    elif module.params['state'] == 'absent':
        # Delete DRS group
        vmware_drs_group.delete_drs_group()

    # Set results
    results = dict(msg=vmware_drs_group.get_msg(),
                   failed=vmware_drs_group.get_failed(),
                   result=vmware_drs_group.get_result())

    if results['failed']:
        module.fail_json(**results)
    else:
        module.exit_json(**results)

if __name__ == "__main__":
    main()
