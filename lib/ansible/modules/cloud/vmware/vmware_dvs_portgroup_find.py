#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
module: vmware_dvs_portgroup_find
short_description: Find portgroup(s) in a VMware environment
description:
- Find portgroup(s) based on different criteria such as distributed vSwitch, VLAN id or a string in the name.
version_added: 2.9
author:
- David Martinez (@dx0xm)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.7
- PyVmomi
options:
  dvswitch:
    description:
    - Name of a distributed vSwitch to look for.
    type: str
  vlanid:
    description:
    - VLAN id can be any number between 1 and 4094.
    - This search criteria will looks into VLAN ranges to find possible matches.
    required: false
    type: int
  name:
    description:
    - string to check inside the name of the portgroup.
    - Basic containment check using python C(in) operation.
    type: str
  show_uplink:
    description:
    - Show or hide uplink portgroups.
    - Only relevant when C(vlanid) is supplied.
    type: bool
    default: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Get all portgroups in dvswitch vDS
  vmware_dvs_portgroup_find:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    dvswitch: 'vDS'
    validate_certs: no
  delegate_to: localhost

- name: Confirm if vlan 15 is present
  vmware_dvs_portgroup_find:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    vlanid: '15'
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
dvs_portgroups:
    description: basic details of portgroups found
    returned: on success
    type: list
    sample: [
        {
            "dvswitch": "vDS",
            "name": "N-51",
            "pvlan": true,
            "trunk": true,
            "vlan_id": "0"
        }
    ]
'''

try:
    from pyVmomi import vim
except ImportError as e:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, find_dvs_by_name


class DVSPortgroupFindManager(PyVmomi):
    def __init__(self, module):
        super(DVSPortgroupFindManager, self).__init__(module)
        self.dvs_name = self.params['dvswitch']
        self.vlan = self.params['vlanid']
        self.cmp_vlans = True if self.vlan else False
        self.pgs = self.find_portgroups_by_name(self.content, self.module.params['name'])

        if self.dvs_name:
            self.pgs = self.find_portgroups_by_dvs(self.pgs, self.dvs_name)

    def find_portgroups_by_name(self, content, name=None):
        vimtype = [vim.dvs.DistributedVirtualPortgroup]
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        if not name:
            obj = container.view
        else:
            obj = []
            for c in container.view:
                if name in c.name:
                    obj.append(c)

        return obj

    def find_portgroups_by_dvs(self, pgl, dvs):
        obj = []
        for c in pgl:
            if dvs in c.config.distributedVirtualSwitch.name:
                obj.append(c)

        return obj

    def vlan_match(self, pgup, userup, vlanlst):
        res = False
        if pgup and userup:
            return True

        for ln in vlanlst:
            if '-' in ln:
                arr = ln.split('-')
                if arr[0] < self.vlan and self.vlan < arr[1]:
                    res = True
            elif ln == str(self.vlan):
                res = True

        return res

    def get_dvs_portgroup(self):
        pgroups = self.pgs

        pglist = []
        for pg in pgroups:
            trunk = False
            pvlan = False
            vlanInfo = pg.config.defaultPortConfig.vlan
            cl1 = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec
            cl2 = vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec
            vlan_id_list = []
            if isinstance(vlanInfo, cl1):
                trunk = True
                for item in vlanInfo.vlanId:
                    if item.start == item.end:
                        vlan_id_list.append(str(item.start))
                    else:
                        vlan_id_list.append(str(item.start) + '-' + str(item.end))
            elif isinstance(vlanInfo, cl2):
                pvlan = True
                vlan_id_list.append(str(vlanInfo.pvlanId))
            else:
                vlan_id_list.append(str(vlanInfo.vlanId))

            if self.cmp_vlans:
                if self.vlan_match(pg.config.uplink, self.module.params['show_uplink'], vlan_id_list):
                    pglist.append(dict(
                        name=pg.name,
                        trunk=trunk,
                        pvlan=pvlan,
                        vlan_id=','.join(vlan_id_list),
                        dvswitch=pg.config.distributedVirtualSwitch.name))
            else:
                pglist.append(dict(
                    name=pg.name,
                    trunk=trunk,
                    pvlan=pvlan,
                    vlan_id=','.join(vlan_id_list),
                    dvswitch=pg.config.distributedVirtualSwitch.name))

        return pglist


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dvswitch=dict(type='str', required=False),
        vlanid=dict(type='int', required=False),
        name=dict(type='str', required=False),
        show_uplink=dict(type='bool', default=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['show_uplink', 'True', 'vlanid']
        ]
    )

    dvs_pg_mgr = DVSPortgroupFindManager(module)
    module.exit_json(changed=False,
                     dvs_portgroups=dvs_pg_mgr.get_dvs_portgroup())


if __name__ == "__main__":
    main()
