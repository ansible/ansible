#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
#
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
module: vmware_dvswitch_pvlans
short_description: Manage Private VLAN configuration of a Distributed Switch
description:
    - This module can be used to configure Private VLANs (PVLANs) on a Distributed Switch.
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
    - Tested on vSphere 6.5 and 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch:
        description:
            - The name of the Distributed Switch.
        type: str
        required: True
        aliases: ['dvswitch']
    primary_pvlans:
        description:
            - A list of VLAN IDs that should be configured as Primary PVLANs.
            - If C(primary_pvlans) isn't specified, all PVLANs will be deleted if present.
            - Each member of the list requires primary_pvlan_id (int) set.
            - The secondary promiscuous PVLAN will be created automatically.
            - If C(secondary_pvlans) isn't specified, the primary PVLANs and each secondary promiscuous PVLAN will be created.
            - Please see examples for more information.
        type: list
        default: []
    secondary_pvlans:
        description:
            - A list of VLAN IDs that should be configured as Secondary PVLANs.
            - 'C(primary_pvlans) need to be specified to create any Secondary PVLAN.'
            - If C(primary_pvlans) isn't specified, all PVLANs will be deleted if present.
            - Each member of the list requires primary_pvlan_id (int), secondary_pvlan_id (int), and pvlan_type (str) to be set.
            - The type of the secondary PVLAN can be isolated or community. The secondary promiscuous PVLAN will be created automatically.
            - Please see examples for more information.
        type: list
        default: []
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Create PVLANs on a Distributed Switch
  vmware_dvswitch_pvlans:
    hostname: '{{ inventory_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch: dvSwitch
    primary_pvlans:
      - primary_pvlan_id: 1
      - primary_pvlan_id: 4
    secondary_pvlans:
      - primary_pvlan_id: 1
        secondary_pvlan_id: 2
        pvlan_type: isolated
      - primary_pvlan_id: 1
        secondary_pvlan_id: 3
        pvlan_type: community
      - primary_pvlan_id: 4
        secondary_pvlan_id: 5
        pvlan_type: community
  delegate_to: localhost

- name: Create primary PVLAN and secondary promiscuous PVLAN on a Distributed Switch
  vmware_dvswitch_pvlans:
    hostname: '{{ inventory_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch: dvSwitch
    primary_pvlans:
      - primary_pvlan_id: 1
  delegate_to: localhost

- name: Remove all PVLANs from a Distributed Switch
  vmware_dvswitch_pvlans:
    hostname: '{{ inventory_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch: dvSwitch
    primary_pvlans: []
    secondary_pvlans: []
  delegate_to: localhost
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: str
    sample: {
        "changed": true,
        "dvswitch": "dvSwitch",
        "private_vlans": [
            {
                "primary_pvlan_id": 1,
                "pvlan_type": "promiscuous",
                "secondary_pvlan_id": 1
            },
            {
                "primary_pvlan_id": 1,
                "pvlan_type": "isolated",
                "secondary_pvlan_id": 2
            },
            {
                "primary_pvlan_id": 1,
                "pvlan_type": "community",
                "secondary_pvlan_id": 3
            }
        ],
        "private_vlans_previous": [],
        "result": "All private VLANs added"
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (
    PyVmomi, TaskError, find_dvs_by_name, vmware_argument_spec, wait_for_task
)


class VMwareDvSwitchPvlans(PyVmomi):
    """Class to manage Private VLANs on a Distributed Virtual Switch"""

    def __init__(self, module):
        super(VMwareDvSwitchPvlans, self).__init__(module)
        self.switch_name = self.module.params['switch']
        if self.module.params['primary_pvlans']:
            self.primary_pvlans = self.module.params['primary_pvlans']
            if self.module.params['secondary_pvlans']:
                self.secondary_pvlans = self.module.params['secondary_pvlans']
            else:
                self.secondary_pvlans = None
            self.do_pvlan_sanity_checks()
        else:
            self.primary_pvlans = None
            self.secondary_pvlans = None
        self.dvs = find_dvs_by_name(self.content, self.switch_name)
        if self.dvs is None:
            self.module.fail_json(msg="Failed to find DVS %s" % self.switch_name)

    def do_pvlan_sanity_checks(self):
        """Do sanity checks for primary and secondary PVLANs"""
        # Check if primary PVLANs are unique
        for primary_vlan in self.primary_pvlans:
            count = 0
            primary_pvlan_id = self.get_primary_pvlan_option(primary_vlan)
            for primary_vlan_2 in self.primary_pvlans:
                primary_pvlan_id_2 = self.get_primary_pvlan_option(primary_vlan_2)
                if primary_pvlan_id == primary_pvlan_id_2:
                    count += 1
            if count > 1:
                self.module.fail_json(
                    msg="The primary PVLAN ID '%s' must be unique!" % primary_pvlan_id
                )
        if self.secondary_pvlans:
            # Check if secondary PVLANs are unique
            for secondary_pvlan in self.secondary_pvlans:
                count = 0
                result = self.get_secondary_pvlan_options(secondary_pvlan)
                for secondary_pvlan_2 in self.secondary_pvlans:
                    result_2 = self.get_secondary_pvlan_options(secondary_pvlan_2)
                    if result[0] == result_2[0]:
                        count += 1
                if count > 1:
                    self.module.fail_json(
                        msg="The secondary PVLAN ID '%s' must be unique!" % result[0]
                    )
            # Check if secondary PVLANs are already used as primary PVLANs
            for primary_vlan in self.primary_pvlans:
                primary_pvlan_id = self.get_primary_pvlan_option(primary_vlan)
                for secondary_pvlan in self.secondary_pvlans:
                    result = self.get_secondary_pvlan_options(secondary_pvlan)
                    if primary_pvlan_id == result[0]:
                        self.module.fail_json(
                            msg="The secondary PVLAN ID '%s' is already used as a primary PVLAN!" %
                            result[0]
                        )
            # Check if a primary PVLAN is present for every secondary PVLANs
            for secondary_pvlan in self.secondary_pvlans:
                primary_pvlan_found = False
                result = self.get_secondary_pvlan_options(secondary_pvlan)
                for primary_vlan in self.primary_pvlans:
                    primary_pvlan_id = self.get_primary_pvlan_option(primary_vlan)
                    if result[1] == primary_pvlan_id:
                        primary_pvlan_found = True
                        break
                if not primary_pvlan_found:
                    self.module.fail_json(
                        msg="The primary PVLAN ID '%s' isn't defined for the secondary PVLAN ID '%s'!" %
                        (result[1], result[0])
                    )

    def ensure(self):
        """Manage Private VLANs"""
        changed = False
        results = dict(changed=changed)
        results['dvswitch'] = self.switch_name
        changed_list_add = []
        changed_list_remove = []

        config_spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
        # Use the same version in the new spec; The version will be increased by one by the API automatically
        config_spec.configVersion = self.dvs.config.configVersion

        # Check Private VLANs
        results['private_vlans'] = None
        if self.primary_pvlans:
            desired_pvlan_list = []
            for primary_vlan in self.primary_pvlans:
                primary_pvlan_id = self.get_primary_pvlan_option(primary_vlan)
                temp_pvlan = dict()
                temp_pvlan['primary_pvlan_id'] = primary_pvlan_id
                temp_pvlan['secondary_pvlan_id'] = primary_pvlan_id
                temp_pvlan['pvlan_type'] = 'promiscuous'
                desired_pvlan_list.append(temp_pvlan)
            if self.secondary_pvlans:
                for secondary_pvlan in self.secondary_pvlans:
                    (secondary_pvlan_id,
                     secondary_vlan_primary_vlan_id,
                     pvlan_type) = self.get_secondary_pvlan_options(secondary_pvlan)
                    temp_pvlan = dict()
                    temp_pvlan['primary_pvlan_id'] = secondary_vlan_primary_vlan_id
                    temp_pvlan['secondary_pvlan_id'] = secondary_pvlan_id
                    temp_pvlan['pvlan_type'] = pvlan_type
                    desired_pvlan_list.append(temp_pvlan)
            results['private_vlans'] = desired_pvlan_list
            if self.dvs.config.pvlanConfig:
                pvlan_spec_list = []
                # Check if desired PVLANs are configured
                for primary_vlan in self.primary_pvlans:
                    primary_pvlan_id = self.get_primary_pvlan_option(primary_vlan)
                    promiscuous_found = other_found = False
                    for pvlan_object in self.dvs.config.pvlanConfig:
                        if pvlan_object.primaryVlanId == primary_pvlan_id and pvlan_object.pvlanType == 'promiscuous':
                            promiscuous_found = True
                            break
                    if not promiscuous_found:
                        changed = True
                        changed_list_add.append('promiscuous (%s, %s)' % (primary_pvlan_id, primary_pvlan_id))
                        pvlan_spec_list.append(
                            self.create_pvlan_config_spec(
                                operation='add',
                                primary_pvlan_id=primary_pvlan_id,
                                secondary_pvlan_id=primary_pvlan_id,
                                pvlan_type='promiscuous'
                            )
                        )
                    if self.secondary_pvlans:
                        for secondary_pvlan in self.secondary_pvlans:
                            (secondary_pvlan_id,
                             secondary_vlan_primary_vlan_id,
                             pvlan_type) = self.get_secondary_pvlan_options(secondary_pvlan)
                            if primary_pvlan_id == secondary_vlan_primary_vlan_id:
                                for pvlan_object_2 in self.dvs.config.pvlanConfig:
                                    if (pvlan_object_2.primaryVlanId == secondary_vlan_primary_vlan_id
                                            and pvlan_object_2.secondaryVlanId == secondary_pvlan_id
                                            and pvlan_object_2.pvlanType == pvlan_type):
                                        other_found = True
                                        break
                                if not other_found:
                                    changed = True
                                    changed_list_add.append(
                                        '%s (%s, %s)' % (pvlan_type, primary_pvlan_id, secondary_pvlan_id)
                                    )
                                    pvlan_spec_list.append(
                                        self.create_pvlan_config_spec(
                                            operation='add',
                                            primary_pvlan_id=primary_pvlan_id,
                                            secondary_pvlan_id=secondary_pvlan_id,
                                            pvlan_type=pvlan_type
                                        )
                                    )
                # Check if a PVLAN needs to be removed
                for pvlan_object in self.dvs.config.pvlanConfig:
                    promiscuous_found = other_found = False
                    if (pvlan_object.primaryVlanId == pvlan_object.secondaryVlanId
                            and pvlan_object.pvlanType == 'promiscuous'):
                        for primary_vlan in self.primary_pvlans:
                            primary_pvlan_id = self.get_primary_pvlan_option(primary_vlan)
                            if pvlan_object.primaryVlanId == primary_pvlan_id and pvlan_object.pvlanType == 'promiscuous':
                                promiscuous_found = True
                                break
                        if not promiscuous_found:
                            changed = True
                            changed_list_remove.append(
                                'promiscuous (%s, %s)' % (pvlan_object.primaryVlanId, pvlan_object.secondaryVlanId)
                            )
                            pvlan_spec_list.append(
                                self.create_pvlan_config_spec(
                                    operation='remove',
                                    primary_pvlan_id=pvlan_object.primaryVlanId,
                                    secondary_pvlan_id=pvlan_object.secondaryVlanId,
                                    pvlan_type='promiscuous'
                                )
                            )
                    elif self.secondary_pvlans:
                        for secondary_pvlan in self.secondary_pvlans:
                            (secondary_pvlan_id,
                             secondary_vlan_primary_vlan_id,
                             pvlan_type) = self.get_secondary_pvlan_options(secondary_pvlan)
                            if (pvlan_object.primaryVlanId == secondary_vlan_primary_vlan_id
                                    and pvlan_object.secondaryVlanId == secondary_pvlan_id
                                    and pvlan_object.pvlanType == pvlan_type):
                                other_found = True
                                break
                        if not other_found:
                            changed = True
                            changed_list_remove.append(
                                '%s (%s, %s)' % (
                                    pvlan_object.pvlanType, pvlan_object.primaryVlanId, pvlan_object.secondaryVlanId
                                )
                            )
                            pvlan_spec_list.append(
                                self.create_pvlan_config_spec(
                                    operation='remove',
                                    primary_pvlan_id=pvlan_object.primaryVlanId,
                                    secondary_pvlan_id=pvlan_object.secondaryVlanId,
                                    pvlan_type=pvlan_object.pvlanType
                                )
                            )
                    else:
                        changed = True
                        changed_list_remove.append(
                            '%s (%s, %s)' % (
                                pvlan_object.pvlanType, pvlan_object.primaryVlanId, pvlan_object.secondaryVlanId
                            )
                        )
                        pvlan_spec_list.append(
                            self.create_pvlan_config_spec(
                                operation='remove',
                                primary_pvlan_id=pvlan_object.primaryVlanId,
                                secondary_pvlan_id=pvlan_object.secondaryVlanId,
                                pvlan_type=pvlan_object.pvlanType
                            )
                        )
            else:
                changed = True
                changed_list_add.append('All private VLANs')
                pvlan_spec_list = []
                for primary_vlan in self.primary_pvlans:
                    # the first secondary VLAN's type is always promiscuous
                    primary_pvlan_id = self.get_primary_pvlan_option(primary_vlan)
                    pvlan_spec_list.append(
                        self.create_pvlan_config_spec(
                            operation='add',
                            primary_pvlan_id=primary_pvlan_id,
                            secondary_pvlan_id=primary_pvlan_id,
                            pvlan_type='promiscuous'
                        )
                    )
                    if self.secondary_pvlans:
                        for secondary_pvlan in self.secondary_pvlans:
                            (secondary_pvlan_id,
                             secondary_vlan_primary_vlan_id,
                             pvlan_type) = self.get_secondary_pvlan_options(secondary_pvlan)
                            if primary_pvlan_id == secondary_vlan_primary_vlan_id:
                                pvlan_spec_list.append(
                                    self.create_pvlan_config_spec(
                                        operation='add',
                                        primary_pvlan_id=primary_pvlan_id,
                                        secondary_pvlan_id=secondary_pvlan_id,
                                        pvlan_type=pvlan_type
                                    )
                                )
        else:
            # Remove PVLAN configuration if present
            if self.dvs.config.pvlanConfig:
                changed = True
                changed_list_remove.append('All private VLANs')
                pvlan_spec_list = []
                for pvlan_object in self.dvs.config.pvlanConfig:
                    pvlan_spec_list.append(
                        self.create_pvlan_config_spec(
                            operation='remove',
                            primary_pvlan_id=pvlan_object.primaryVlanId,
                            secondary_pvlan_id=pvlan_object.secondaryVlanId,
                            pvlan_type=pvlan_object.pvlanType
                        )
                    )

        if changed:
            message_add = message_remove = None
            if changed_list_add:
                message_add = self.build_change_message('add', changed_list_add)
            if changed_list_remove:
                message_remove = self.build_change_message('remove', changed_list_remove)
            if message_add and message_remove:
                message = message_add + '. ' + message_remove + '.'
            elif message_add:
                message = message_add
            elif message_remove:
                message = message_remove
            current_pvlan_list = []
            for pvlan_object in self.dvs.config.pvlanConfig:
                temp_pvlan = dict()
                temp_pvlan['primary_pvlan_id'] = pvlan_object.primaryVlanId
                temp_pvlan['secondary_pvlan_id'] = pvlan_object.secondaryVlanId
                temp_pvlan['pvlan_type'] = pvlan_object.pvlanType
                current_pvlan_list.append(temp_pvlan)
            results['private_vlans_previous'] = current_pvlan_list
            config_spec.pvlanConfigSpec = pvlan_spec_list
            if not self.module.check_mode:
                try:
                    task = self.dvs.ReconfigureDvs_Task(config_spec)
                    wait_for_task(task)
                except TaskError as invalid_argument:
                    self.module.fail_json(
                        msg="Failed to update DVS : %s" % to_native(invalid_argument)
                    )
        else:
            message = "PVLANs already configured properly"
        results['changed'] = changed
        results['result'] = message

        self.module.exit_json(**results)

    def get_primary_pvlan_option(self, primary_vlan):
        """Get Primary PVLAN option"""
        primary_pvlan_id = primary_vlan.get('primary_pvlan_id', None)
        if primary_pvlan_id is None:
            self.module.fail_json(
                msg="Please specify primary_pvlan_id in primary_pvlans options as it's a required parameter"
            )
        if primary_pvlan_id in (0, 4095):
            self.module.fail_json(msg="The VLAN IDs of 0 and 4095 are reserved and cannot be used as a primary PVLAN.")
        return primary_pvlan_id

    def get_secondary_pvlan_options(self, secondary_pvlan):
        """Get Secondary PVLAN option"""
        secondary_pvlan_id = secondary_pvlan.get('secondary_pvlan_id', None)
        if secondary_pvlan_id is None:
            self.module.fail_json(
                msg="Please specify secondary_pvlan_id in secondary_pvlans options as it's a required parameter"
            )
        primary_pvlan_id = secondary_pvlan.get('primary_pvlan_id', None)
        if primary_pvlan_id is None:
            self.module.fail_json(
                msg="Please specify primary_pvlan_id in secondary_pvlans options as it's a required parameter"
            )
        if secondary_pvlan_id in (0, 4095) or primary_pvlan_id in (0, 4095):
            self.module.fail_json(
                msg="The VLAN IDs of 0 and 4095 are reserved and cannot be used as a primary or secondary PVLAN."
            )
        pvlan_type = secondary_pvlan.get('pvlan_type', None)
        supported_pvlan_types = ['isolated', 'community']
        if pvlan_type is None:
            self.module.fail_json(msg="Please specify pvlan_type in secondary_pvlans options as it's a required parameter")
        elif pvlan_type not in supported_pvlan_types:
            self.module.fail_json(msg="The specified PVLAN type '%s' isn't supported!" % pvlan_type)
        return secondary_pvlan_id, primary_pvlan_id, pvlan_type

    @staticmethod
    def create_pvlan_config_spec(operation, primary_pvlan_id, secondary_pvlan_id, pvlan_type):
        """
            Create PVLAN config spec
            operation: add, edit, or remove
            Returns: PVLAN config spec
        """
        pvlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.PvlanConfigSpec()
        pvlan_spec.operation = operation
        pvlan_spec.pvlanEntry = vim.dvs.VmwareDistributedVirtualSwitch.PvlanMapEntry()
        pvlan_spec.pvlanEntry.primaryVlanId = primary_pvlan_id
        pvlan_spec.pvlanEntry.secondaryVlanId = secondary_pvlan_id
        pvlan_spec.pvlanEntry.pvlanType = pvlan_type
        return pvlan_spec

    def build_change_message(self, operation, changed_list):
        """Build the changed message"""
        if operation == 'add':
            changed_operation = 'added'
        elif operation == 'remove':
            changed_operation = 'removed'
        if self.module.check_mode:
            changed_suffix = ' would be %s' % changed_operation
        else:
            changed_suffix = ' %s' % changed_operation
        if len(changed_list) > 2:
            message = ', '.join(changed_list[:-1]) + ', and ' + str(changed_list[-1])
        elif len(changed_list) == 2:
            message = ' and '.join(changed_list)
        elif len(changed_list) == 1:
            message = changed_list[0]
        message += changed_suffix
        return message


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            switch=dict(required=True, aliases=['dvswitch']),
            primary_pvlans=dict(type='list', default=list(), required=False),
            secondary_pvlans=dict(type='list', default=list(), required=False),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_dvswitch_pvlans = VMwareDvSwitchPvlans(module)
    vmware_dvswitch_pvlans.ensure()


if __name__ == '__main__':
    main()
