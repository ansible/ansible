#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Karsten Kaj Jakobsen <kj@patientsky.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['deprecated'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
deprecated:
  removed_in: '2.13'
  why: Deprecated in favour of C(_info) module.
  alternative: Use M(vmware_drs_group_info) instead.
author:
  - "Karsten Kaj Jakobsen (@karstenjakobsen)"
description:
  - "This module can be used to gather facts about DRS VM/HOST groups from the given cluster."
extends_documentation_fragment: vmware.documentation
module: vmware_drs_group_facts
notes:
  - "Tested on vSphere 6.5 and 6.7"
options:
  cluster_name:
    description:
      - "Cluster to search for VM/Host groups."
      - "If set, facts of DRS groups belonging this cluster will be returned."
      - "Not needed if C(datacenter) is set."
    required: false
    type: str
  datacenter:
    aliases:
      - datacenter_name
    description:
      - "Datacenter to search for DRS VM/Host groups."
    required: true
    type: str
requirements:
  - "python >= 2.6"
  - PyVmomi
short_description: "Gathers facts about DRS VM/Host groups on the given cluster"
version_added: "2.8"
'''

EXAMPLES = r'''
---
- name: "Gather DRS facts about given Cluster"
  register: cluster_drs_group_facts
  vmware_drs_group_facts:
    hostname: "{{ vcenter_hostname }}"
    password: "{{ vcenter_password }}"
    username: "{{ vcenter_username }}"
    cluster_name: "{{ cluster_name }}"
    datacenter: "{{ datacenter }}"
  delegate_to: localhost

- name: "Gather DRS group facts about all clusters in given datacenter"
  register: cluster_drs_group_facts
  vmware_drs_group_facts:
    hostname: "{{ vcenter_hostname }}"
    password: "{{ vcenter_password }}"
    username: "{{ vcenter_username }}"
    datacenter: "{{ datacenter }}"
  delegate_to: localhost
'''

RETURN = r'''
drs_group_facts:
    description: Metadata about DRS group from given cluster / datacenter
    returned: always
    type: dict
    sample:
        "drs_group_facts": {
            "DC0_C0": [
                {
                    "group_name": "GROUP_HOST_S01",
                    "hosts": [
                        "vm-01.zone",
                        "vm-02.zone"
                    ],
                    "type": "host"
                },
                {
                    "group_name": "GROUP_HOST_S02",
                    "hosts": [
                        "vm-03.zone",
                        "vm-04.zone"
                    ],
                    "type": "host"
                },
                {
                    "group_name": "GROUP_VM_S01",
                    "type": "vm",
                    "vms": [
                        "test-node01"
                    ]
                },
                {
                    "group_name": "GROUP_VM_S02",
                    "type": "vm",
                    "vms": [
                        "test-node02"
                    ]
                }
            ],
            "DC0_C1": []
        }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, find_datacenter_by_name, get_all_objs


class VmwareDrsGroupFactManager(PyVmomi):

    def __init__(self, module, datacenter_name, cluster_name=None):
        """
        Doctring: Init
        """

        super(VmwareDrsGroupFactManager, self).__init__(module)

        self.__datacenter_name = datacenter_name
        self.__datacenter_obj = None
        self.__cluster_name = cluster_name
        self.__cluster_obj = None
        self.__msg = 'Nothing to see here...'
        self.__result = dict()
        self.__changed = False

        if datacenter_name:

            datacenter_obj = find_datacenter_by_name(self.content, datacenter_name=datacenter_name)
            self.cluster_obj_list = []

            if datacenter_obj:
                folder = datacenter_obj.hostFolder
                self.cluster_obj_list = get_all_objs(self.content, [vim.ClusterComputeResource], folder)
            else:
                raise Exception("Datacenter '%s' not found" % self.__datacenter_name)

        if cluster_name:

            cluster_obj = self.find_cluster_by_name(cluster_name=self.__cluster_name)

            if cluster_obj is None:
                raise Exception("Cluster '%s' not found" % self.__cluster_name)
            else:
                self.cluster_obj_list = [cluster_obj]

    def get_result(self):
        """
        Docstring
        """
        return self.__result

    def __set_result(self, result):
        """
        Sets result
        Args:
            result: drs group result list

        Returns: None

        """
        self.__result = result

    def __get_all_from_group(self, group_obj, host_group=False):
        """
        Return all VM / Host names using given group
        Args:
            group_obj: Group object
            host_group: True if we want only host name from group

        Returns: List of VM / Host names belonging to given group object

        """
        obj_name_list = []

        if not all([group_obj]):
            return obj_name_list

        if not host_group and isinstance(group_obj, vim.cluster.VmGroup):
            obj_name_list = [vm.name for vm in group_obj.vm]
        elif host_group and isinstance(group_obj, vim.cluster.HostGroup):
            obj_name_list = [host.name for host in group_obj.host]

        return obj_name_list

    def __normalize_group_data(self, group_obj):
        """
        Return human readable group spec
        Args:
            group_obj: Group object

        Returns: Dictionary with DRS groups

        """
        if not all([group_obj]):
            return {}

        # Check if group is a host group
        if hasattr(group_obj, 'host'):
            return dict(
                group_name=group_obj.name,
                hosts=self.__get_all_from_group(group_obj=group_obj, host_group=True),
                type="host"
            )
        else:
            return dict(
                group_name=group_obj.name,
                vms=self.__get_all_from_group(group_obj=group_obj),
                type="vm"
            )

    def gather_facts(self):
        """
        Gather DRS group facts about given cluster
        Returns: Dictionary of clusters with DRS groups

        """
        cluster_group_facts = dict()

        for cluster_obj in self.cluster_obj_list:

            cluster_group_facts[cluster_obj.name] = []

            for drs_group in cluster_obj.configurationEx.group:
                cluster_group_facts[cluster_obj.name].append(self.__normalize_group_data(drs_group))

        self.__set_result(cluster_group_facts)


def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        datacenter=dict(type='str', required=False, aliases=['datacenter_name']),
        cluster_name=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['cluster_name', 'datacenter']],
        mutually_exclusive=[['cluster_name', 'datacenter']],
    )

    try:
        # Create instance of VmwareDrsGroupManager
        vmware_drs_group_facts = VmwareDrsGroupFactManager(module=module,
                                                           datacenter_name=module.params.get('datacenter'),
                                                           cluster_name=module.params.get('cluster_name', None))

        vmware_drs_group_facts.gather_facts()

        # Set results
        results = dict(failed=False,
                       drs_group_facts=vmware_drs_group_facts.get_result())

    except Exception as error:
        results = dict(failed=True, msg="Error: %s" % error)

    if results['failed']:
        module.fail_json(**results)
    else:
        module.exit_json(**results)


if __name__ == "__main__":
    main()
