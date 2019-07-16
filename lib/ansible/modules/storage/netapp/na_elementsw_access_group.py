#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Element Software Access Group Manager
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_access_group

short_description: NetApp Element Software Manage Access Groups
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, destroy, or update access groups on Element Software Cluster.

options:

    state:
        description:
        - Whether the specified access group should exist or not.
        required: true
        choices: ['present', 'absent']

    from_name:
        description:
        - ID or Name of the access group to rename.
        - Required to create a new access group called 'name' by renaming 'from_name'.
        version_added: '2.8'

    name:
        description:
        - Name for the access group for create, modify and delete operations.
        required: True
        aliases:
        - src_access_group_id

    initiators:
        description:
        - List of initiators to include in the access group. If unspecified, the access group will start out without configured initiators.

    volumes:
        description:
        - List of volumes to initially include in the volume access group. If unspecified, the access group will start without any volumes.
        - It accepts either volume_name or volume_id

    account_id:
        description:
        - Account ID for the owner of this volume.
        - It accepts either account_name or account_id
        - if account_id is digit, it will consider as account_id
        - If account_id is string, it will consider as account_name
        version_added: '2.8'

    virtual_network_id:
        description:
        - The ID of the Element SW Software Cluster Virtual Network ID to associate the access group with.

    virtual_network_tags:
        description:
        - The ID of the VLAN Virtual Network Tag to associate the access group with.

    attributes:
        description: List of Name/Value pairs in JSON object format.

'''

EXAMPLES = """
   - name: Create Access Group
     na_elementsw_access_group:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       name: AnsibleAccessGroup
       volumes: [7,8]
       account_id: 1

   - name: Modify Access Group
     na_elementsw_access_group:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       name: AnsibleAccessGroup-Renamed
       account_id: 1
       attributes: {"volumes": [1,2,3], "virtual_network_id": 12345}

   - name: Rename Access Group
     na_elementsw_access_group:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       from_name: AnsibleAccessGroup
       name: AnsibleAccessGroup-Renamed

   - name: Delete Access Group
     na_elementsw_access_group:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: absent
       name: 1
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
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class ElementSWAccessGroup(object):
    """
    Element Software Volume Access Group
    """

    def __init__(self):

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            from_name=dict(required=False, type='str'),
            name=dict(required=True, aliases=["src_access_group_id"], type='str'),
            initiators=dict(required=False, type='list'),
            volumes=dict(required=False, type='list'),
            account_id=dict(required=False, type='str'),
            virtual_network_id=dict(required=False, type='list'),
            virtual_network_tags=dict(required=False, type='list'),
            attributes=dict(required=False, type='dict'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['account_id'])
            ],
            supports_check_mode=True
        )

        input_params = self.module.params

        # Set up state variables
        self.state = input_params['state']
        self.from_name = input_params['from_name']
        self.access_group_name = input_params['name']
        self.initiators = input_params['initiators']
        self.volumes = input_params['volumes']
        self.account_id = input_params['account_id']
        self.virtual_network_id = input_params['virtual_network_id']
        self.virtual_network_tags = input_params['virtual_network_tags']
        self.attributes = input_params['attributes']

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

        self.elementsw_helper = NaElementSWModule(self.sfe)

        # add telemetry attributes
        if self.attributes is not None:
            self.attributes.update(self.elementsw_helper.set_element_attributes(source='na_elementsw_access_group'))
        else:
            self.attributes = self.elementsw_helper.set_element_attributes(source='na_elementsw_access_group')

    def get_access_group(self, name):
        """
        Get Access Group
            :description: Get Access Group object for a given name

            :return: object (Group object)
            :rtype: object (Group object)
        """
        access_groups_list = self.sfe.list_volume_access_groups()
        group_obj = None

        for group in access_groups_list.volume_access_groups:
            # Check  and get access_group object for a given name
            if str(group.volume_access_group_id) == name:
                group_obj = group
            elif group.name == name:
                group_obj = group

        return group_obj

    def get_account_id(self):
        # Validate account id
        # Return account_id if found, None otherwise
        try:
            account_id = self.elementsw_helper.account_exists(self.account_id)
            return account_id
        except Exception:
            return None

    def get_volume_id(self):
        # Validate volume_ids
        # Return volume ids if found, fail if not found
        volume_ids = []
        for volume in self.volumes:
            volume_id = self.elementsw_helper.volume_exists(volume, self.account_id)
            if volume_id:
                volume_ids.append(volume_id)
            else:
                self.module.fail_json(msg='Specified volume %s does not exist' % volume)
        return volume_ids

    def create_access_group(self):
        """
        Create the Access Group
        """
        try:
            self.sfe.create_volume_access_group(name=self.access_group_name,
                                                initiators=self.initiators,
                                                volumes=self.volumes,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                attributes=self.attributes)
        except Exception as e:
            self.module.fail_json(msg="Error creating volume access group %s: %s" %
                                  (self.access_group_name, to_native(e)), exception=traceback.format_exc())

    def delete_access_group(self):
        """
        Delete the Access Group
        """
        try:
            self.sfe.delete_volume_access_group(volume_access_group_id=self.group_id)

        except Exception as e:
            self.module.fail_json(msg="Error deleting volume access group %s: %s" %
                                  (self.access_group_name, to_native(e)),
                                  exception=traceback.format_exc())

    def update_access_group(self):
        """
        Update the Access Group if the access_group already exists
        """
        try:
            self.sfe.modify_volume_access_group(volume_access_group_id=self.group_id,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                initiators=self.initiators,
                                                volumes=self.volumes,
                                                attributes=self.attributes)
        except Exception as e:
            self.module.fail_json(msg="Error updating volume access group %s: %s" %
                                  (self.access_group_name, to_native(e)), exception=traceback.format_exc())

    def rename_access_group(self):
        """
        Rename the Access Group to the new name
        """
        try:
            self.sfe.modify_volume_access_group(volume_access_group_id=self.from_group_id,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                name=self.access_group_name,
                                                initiators=self.initiators,
                                                volumes=self.volumes,
                                                attributes=self.attributes)
        except Exception as e:
            self.module.fail_json(msg="Error updating volume access group %s: %s" %
                                  (self.from_name, to_native(e)), exception=traceback.format_exc())

    def apply(self):
        """
        Process the access group operation on the Element Software Cluster
        """
        changed = False
        update_group = False

        if self.account_id is not None:
            self.account_id_valid = self.get_account_id()

        if self.state == 'present' and self.volumes is not None:
            if self.account_id_valid:
                self.volumes = self.get_volume_id()
            else:
                self.module.fail_json(msg='Error: Specified account id %s does not exist ' % self.account_id)

        group_detail = self.get_access_group(self.access_group_name)

        if group_detail is not None:
            # If access group found
            self.group_id = group_detail.volume_access_group_id

            if self.state == "absent":
                self.delete_access_group()
                changed = True
            else:
                # If state - present, check for any parameter of exising group needs modification.
                if self.volumes is not None and len(self.volumes) > 0:
                    # Compare the volume list
                    for volumeID in group_detail.volumes:
                        if volumeID not in self.volumes:
                            update_group = True
                            changed = True

                elif self.initiators is not None and group_detail.initiators != self.initiators:
                    update_group = True
                    changed = True

                elif self.virtual_network_id is not None or self.virtual_network_tags is not None:
                    update_group = True
                    changed = True

                if update_group:
                    self.update_access_group()

        else:
            # access_group does not exist
            if self.state == "present" and self.from_name is not None:
                group_detail = self.get_access_group(self.from_name)
                if group_detail is not None:
                    # If resource pointed by from_name exists, rename the access_group to name
                    self.from_group_id = group_detail.volume_access_group_id
                    self.rename_access_group()
                    changed = True
                else:
                    # If resource pointed by from_name does not exists, error out
                    self.module.fail_json(msg="Resource does not exist : %s" % self.from_name)
            elif self.state == "present":
                # If from_name is not defined, Create from scratch.
                self.create_access_group()
                changed = True

        self.module.exit_json(changed=changed)


def main():
    """
    Main function
    """
    na_elementsw_access_group = ElementSWAccessGroup()
    na_elementsw_access_group.apply()


if __name__ == '__main__':
    main()
