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

RETURN = ''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, find_datacenter_by_name, get_all_objs


class VmwareDrsGroupFactManager(PyVmomi):

    def __init__(self, module):

        super(VmwareDrsGroupFactManager, self).__init__(module)

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

    def get_all_from_group(self, group_obj, hostgroup=False):
        """
        Return all VM / Host names using given group
        Args:
            group_obj: Group object
            hostgroup: True if we want only host name from group

        Returns: List of VM / Host names belonging to given group object

        """
        obj_name_list = []

        if not all([group_obj]):
            return obj_name_list

        if not hostgroup and isinstance(group_obj, vim.cluster.VmGroup):
            obj_name_list = [vm.name for vm in group_obj.vm]
        elif hostgroup and isinstance(group_obj, vim.cluster.HostGroup):
            obj_name_list = [host.name for host in group_obj.host]

        return obj_name_list

    def normalize_group_data(self, group_obj):
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
                hosts=self.get_all_from_group(group_obj=group_obj, hostgroup=True),
                type="host"
            )
        else:
            return dict(
                group_name=group_obj.name,
                vms=self.get_all_from_group(group_obj=group_obj),
                type="vm"
            )

    def gather_drs_group_facts(self):
        """
        Gather DRS group facts about given cluster
        Returns: Dictionary of clusters with DRS groups

        """
        cluster_group_facts = dict()

        for cluster_obj in self.cluster_obj_list:

            cluster_group_facts[cluster_obj.name] = []

            for drs_group in cluster_obj.configurationEx.group:
                cluster_group_facts[cluster_obj.name].append(self.normalize_group_data(drs_group))

        return cluster_group_facts


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
        ],
        supports_check_mode=True,
    )

    vmware_drs_group_facts = VmwareDrsGroupFactManager(module)

    module.exit_json(changed=False, drs_group_facts=vmware_drs_group_facts.gather_drs_group_facts())


if __name__ == "__main__":
    main()
