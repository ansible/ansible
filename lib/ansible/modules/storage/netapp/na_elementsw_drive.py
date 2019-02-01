#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

'''
Element Software Node Drives
'''
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_drive

short_description: NetApp Element Software Manage Node Drives
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
    - Add, Erase or Remove drive for nodes on Element Software Cluster.

options:
    drive_id:
        description:
        - Drive ID or Serial Name of Node drive.
        - If not specified, add and remove action will be performed on all drives of node_id

    state:
        description:
        - Element SW Storage Drive operation state.
        - present - To add drive of node to participate in cluster data storage.
        - absent  - To remove the drive from being part of active cluster.
        - clean   - Clean-up any residual data persistent on a *removed* drive in a secured method.
        choices: ['present', 'absent', 'clean']
        default: 'present'

    node_id:
        description:
        - ID or Name of cluster node.
        required: true

    force_during_upgrade:
        description:
        - Flag to force drive operation during upgrade.
        type: 'bool'

    force_during_bin_sync:
        description:
        - Flag to force during a bin sync operation.
        type: 'bool'
'''

EXAMPLES = """
   - name: Add drive with status available to cluster
     tags:
     - elementsw_add_drive
     na_element_drive:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       drive_id: scsi-SATA_SAMSUNG_MZ7LM48S2UJNX0J3221807
       force_during_upgrade: false
       force_during_bin_sync: false
       node_id: sf4805-meg-03

   - name: Remove active drive from cluster
     tags:
     - elementsw_remove_drive
     na_element_drive:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: absent
       force_during_upgrade: false
       node_id: sf4805-meg-03
       drive_id: scsi-SATA_SAMSUNG_MZ7LM48S2UJNX0J321208

   - name: Secure Erase drive
     tags:
     - elemensw_clean_drive
     na_elementsw_drive:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: clean
       drive_id: scsi-SATA_SAMSUNG_MZ7LM48S2UJNX0J432109
       node_id: sf4805-meg-03

   - name: Add all the drives of a node to cluster
     tags:
     - elementsw_add_node
     na_elementsw_drive:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       force_during_upgrade: false
       force_during_bin_sync: false
       node_id: sf4805-meg-03

"""


RETURN = """

msg:
    description: Success message
    returned: success
    type: str

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class ElementSWDrive(object):
    """
    Element Software Storage Drive operations
    """

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent', 'clean'], default='present'),
            drive_id=dict(required=False, type='str'),
            node_id=dict(required=True, type='str'),
            force_during_upgrade=dict(required=False, type='bool'),
            force_during_bin_sync=dict(required=False, type='bool')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        input_params = self.module.params

        self.state = input_params['state']
        self.drive_id = input_params['drive_id']
        self.node_id = input_params['node_id']
        self.force_during_upgrade = input_params['force_during_upgrade']
        self.force_during_bin_sync = input_params['force_during_bin_sync']

        if HAS_SF_SDK is False:
            self.module.fail_json(
                msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def get_node_id(self):
        """
            Get Node ID
            :description: Find and retrieve node_id from the active cluster

            :return: node_id (None if not found)
            :rtype: node_id
        """
        if self.node_id is not None:
            list_nodes = self.sfe.list_active_nodes()
            for current_node in list_nodes.nodes:
                if self.node_id == str(current_node.node_id):
                    return current_node.node_id
                elif current_node.name == self.node_id:
                    self.node_id = current_node.node_id
                    return current_node.node_id
        self.node_id = None
        return self.node_id

    def get_drives_listby_status(self):
        """
            Capture list of drives based on status for a given node_id
            :description: Capture list of active, failed and available drives from a given node_id

            :return: None
        """
        if self.node_id is not None:
            list_drives = self.sfe.list_drives()
            for drive in list_drives.drives:
                if drive.node_id == self.node_id:
                    if drive.status in ['active', 'failed']:
                        self.active_drives[drive.serial] = drive.drive_id
                    elif drive.status == "available":
                        self.available_drives[drive.serial] = drive.drive_id
        return None

    def get_active_drives(self, drive_id=None):
        """
        return a list of active drives
        if drive_id is specified, only [] or [drive_id] is returned
        else all available drives for this node are returned
        """
        action_list = list()
        if self.drive_id is not None:
            if self.drive_id in self.active_drives.values():
                action_list.append(int(self.drive_id))
            if self.drive_id in self.active_drives:
                action_list.append(self.active_drives[self.drive_id])
        else:
            action_list.extend(self.active_drives.values())

        return action_list

    def get_available_drives(self, drive_id=None):
        """
        return a list of available drives (not active)
        if drive_id is specified, only [] or [drive_id] is returned
        else all available drives for this node are returned
        """
        action_list = list()
        if self.drive_id is not None:
            if self.drive_id in self.available_drives.values():
                action_list.append(int(self.drive_id))
            if self.drive_id in self.available_drives:
                action_list.append(self.available_drives[self.drive_id])
        else:
            action_list.extend(self.available_drives.values())

        return action_list

    def add_drive(self, drives=None):
        """
        Add Drive available for Cluster storage expansion
        """
        try:
            self.sfe.add_drives(drives,
                                force_during_upgrade=self.force_during_upgrade,
                                force_during_bin_sync=self.force_during_bin_sync)
        except Exception as exception_object:
            self.module.fail_json(msg='Error add drive to cluster  %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def remove_drive(self, drives=None):
        """
        Remove Drive active in Cluster
        """
        try:
            self.sfe.remove_drives(drives,
                                   force_during_upgrade=self.force_during_upgrade)
        except Exception as exception_object:
            self.module.fail_json(msg='Error remove drive from cluster  %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def secure_erase(self, drives=None):
        """
        Secure Erase any residual data existing on a drive
        """
        try:
            self.sfe.secure_erase_drives(drives)
        except Exception as exception_object:
            self.module.fail_json(msg='Error clean data from drive %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Check, process and initiate Drive operation
        """
        changed = False
        result_message = None
        self.active_drives = {}
        self.available_drives = {}
        action_list = []
        self.get_node_id()
        self.get_drives_listby_status()

        if self.module.check_mode is False and self.node_id is not None:
            if self.state == "present":
                action_list = self.get_available_drives(self.drive_id)
                if len(action_list) > 0:
                    self.add_drive(action_list)
                    changed = True
                elif self.drive_id is not None and (self.drive_id in self.active_drives.values() or self.drive_id in self.active_drives):
                    changed = False  # No action, so setting changed to false
                elif self.drive_id is None and len(self.active_drives) > 0:
                    changed = False  # No action, so setting changed to false
                else:
                    self.module.fail_json(msg='Error - no drive(s) in available state on node to be included in cluster')

            elif self.state == "absent":
                action_list = self.get_active_drives(self.drive_id)
                if len(action_list) > 0:
                    self.remove_drive(action_list)
                    changed = True

            elif self.state == "clean":
                action_list = self.get_available_drives(self.drive_id)
                if len(action_list) > 0:
                    self.secure_erase(action_list)
                    changed = True
                else:
                    self.module.fail_json(msg='Error - no drive(s) in available state on node to be cleaned')

        else:
            result_message = "Skipping changes, No change requested"
        self.module.exit_json(changed=changed, msg=result_message)


def main():
    """
    Main function
    """

    na_elementsw_drive = ElementSWDrive()
    na_elementsw_drive.apply()


if __name__ == '__main__':
    main()
