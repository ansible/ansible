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
author: NetApp Ansible Team (ng-ansibleteam@netapp.com)
description:
- Create, destroy, or update access groups on Element Software Cluster.

options:

    state:
        description:
        - Whether the specified access group should exist or not.
        required: true
        choices: ['present', 'absent']

    src_access_group_id:
        description:
        - ID or Name of the access group to modify or delete.
        - Required for delete and modify operations.

    new_name:
        description:
        - New name for the access group for create and modify operation.
        - Required for create operation.

    initiators:
        description:
        - List of initiators to include in the access group. If unspecified, the access group will start out without configured initiators.
        required: false

    volumes:
        description:
        - List of volumes to initially include in the volume access group. If unspecified, the access group will start without any volumes.

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
       new_name: AnsibleAccessGroup
       volumes: [7,8]

   - name: Modify Access Group
     na_elementsw_access_group:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       src_access_group_id: AnsibleAccessGroup
       new_name: AnsibleAccessGroup-Renamed
       attributes: {"volumes": [1,2,3], "virtual_network_id": 12345}

   - name: Delete Access Group
     na_elementsw_access_group:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: absent
       src_access_group_id: 1
"""


RETURN = """

msg:
    description: Success message
    returned: success
    type: string

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
            src_access_group_id=dict(required=False, type='str'),
            new_name=dict(required=False, type='str'),
            initiators=dict(required=False, type='list'),
            volumes=dict(required=False, type='list'),
            virtual_network_id=dict(required=False, type='list'),
            virtual_network_tags=dict(required=False, type='list'),
            attributes=dict(required=False, type='dict'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        input_params = self.module.params

        # Set up state variables
        self.state = input_params['state']
        self.src_access_group_id = input_params['src_access_group_id']
        self.new_name = input_params['new_name']
        self.initiators = input_params['initiators']
        self.volumes = input_params['volumes']
        self.virtual_network_id = input_params['virtual_network_id']
        self.virtual_network_tags = input_params['virtual_network_tags']
        self.attributes = input_params['attributes']

        if self.state == "absent" and self.src_access_group_id is None:
            self.module.fail_json(msg="For delete operation, src_access_group_id parameter is required")

        if self.state == 'present' and self.new_name is None and self.src_access_group_id is None:
            self.module.fail_json(msg="new_name parameter or src_access_group is required parameter")

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

    def get_access_group(self):
        """
        Get Access Group
            :description: Get Access Group object for a given src_access_group_id

            :return: object (Group object)
            :rtype: object (Group object)
        """
        access_groups_list = self.sfe.list_volume_access_groups()
        self.new_name_exists = False
        group_obj = None

        for group in access_groups_list.volume_access_groups:
            # Check  and get access_group object for a given src_access_group_id
            if self.src_access_group_id is not None and group_obj is None:
                if str(group.volume_access_group_id) == self.src_access_group_id:
                    group_obj = group
                elif group.name == self.src_access_group_id:
                    self.src_access_group_id = group.volume_access_group_id
                    group_obj = group
            # Check if new_name exists on the list
            if group_obj is not None and self.new_name is None:
                return group_obj
            elif group.name == self.new_name:
                self.new_name_exists = True
                return group_obj
        return group_obj

    def create_access_group(self):
        """
        Create the Access Group
        """
        try:
            self.sfe.create_volume_access_group(name=self.new_name,
                                                initiators=self.initiators,
                                                volumes=self.volumes,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                attributes=self.attributes)
        except Exception as e:
            self.module.fail_json(msg="Error creating volume access group %s: %s" %
                                  (self.name, to_native(e)), exception=traceback.format_exc())

    def delete_access_group(self):
        """
        Delete the Access Group
        """
        try:
            self.sfe.delete_volume_access_group(volume_access_group_id=self.src_access_group_id)

        except Exception as e:
            self.module.fail_json(msg="Error deleting volume access group %s: %s" %
                                  (self.src_access_group_id, to_native(e)),
                                  exception=traceback.format_exc())

    def update_access_group(self):
        """
        Update the Access Group
        """
        try:
            self.sfe.modify_volume_access_group(volume_access_group_id=self.src_access_group_id,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                name=self.new_name,
                                                initiators=self.initiators,
                                                volumes=self.volumes,
                                                attributes=self.attributes)
        except Exception as e:
            self.module.fail_json(msg="Error updating volume access group %s: %s" %
                                  (self.src_access_group_id, to_native(e)), exception=traceback.format_exc())

    def apply(self):
        """
        Process the access group operation on the Element Software Cluster
        """
        changed = False
        group_exists = False
        update_group = False
        group_detail = self.get_access_group()

        if self.module.check_mode is False and group_detail is not None:
            group_exists = True

            if self.state == "absent":
                self.delete_access_group()
                changed = True
            else:
                # Check if we need to update the group
                if self.new_name is not None and self.new_name_exists is False:
                    update_group = True
                    changed = True

                elif self.volumes is not None and group_detail.volumes != self.volumes:
                    update_group = True
                    changed = True

                elif self.initiators is not None and group_detail.initiators != self.initiators:
                    update_group = True
                    changed = True

                elif self.virtual_network_id is not None or self.virtual_network_tags is not None or \
                        self.attributes is not None:
                    update_group = True
                    changed = True

                if update_group:
                    self.update_access_group()

        elif self.module.check_mode is False and self.new_name_exists is False and self.new_name is not None and self.state == 'present':
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
