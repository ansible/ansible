#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: sf_volume_access_group_manager

short_description: Manage SolidFire Volume Access Groups
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)
description:
- Create, destroy, or update volume access groups on SolidFire

options:

    state:
        description:
        - Whether the specified volume access group should exist or not.
        required: true
        choices: ['present', 'absent']

    name:
        description:
        - Name of the volume access group. It is not required to be unique, but recommended.
        required: true

    initiators:
        description:
        - List of initiators to include in the volume access group. If unspecified, the access group will start out without configured initiators.
        required: false
        default: None

    volumes:
        description:
        - List of volumes to initially include in the volume access group. If unspecified, the access group will start without any volumes.
        required: false
        default: None

    virtual_network_id:
        description:
        - The ID of the SolidFire Virtual Network ID to associate the volume access group with.
        required: false
        default: None

    virtual_network_tags:
        description:
        - The ID of the VLAN Virtual Network Tag to associate the volume access group with.
        required: false
        default: None

    attributes:
        description: List of Name/Value pairs in JSON object format.
        required: false
        default: None

    volume_access_group_id:
        description:
        - The ID of the volume access group to modify or delete.
        required: false
        default: None

'''

EXAMPLES = """
   - name: Create Volume Access Group
     sf_volume_access_group_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       name: AnsibleVolumeAccessGroup
       volumes: [7,8]

   - name: Modify Volume Access Group
     sf_volume_access_group_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       volume_access_group_id: 1
       name: AnsibleVolumeAccessGroup-Renamed
       attributes: {"volumes": [1,2,3], "virtual_network_id": 12345}

   - name: Delete Volume Access Group
     sf_volume_access_group_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: absent
       volume_access_group_id: 1
"""

RETURN = """


"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class SolidFireVolumeAccessGroup(object):

    def __init__(self):

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            volume_access_group_id=dict(required=False, type='int', default=None),

            initiators=dict(required=False, type='list', default=None),
            volumes=dict(required=False, type='list', default=None),
            virtual_network_id=dict(required=False, type='list', default=None),
            virtual_network_tags=dict(required=False, type='list', default=None),
            attributes=dict(required=False, type='dict', default=None),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.volume_access_group_id = p['volume_access_group_id']

        self.initiators = p['initiators']
        self.volumes = p['volumes']
        self.virtual_network_id = p['virtual_network_id']
        self.virtual_network_tags = p['virtual_network_tags']
        self.attributes = p['attributes']

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def get_volume_access_group(self):
        access_groups_list = self.sfe.list_volume_access_groups()

        for group in access_groups_list.volume_access_groups:
            if group.name == self.name:
                # Update self.volume_access_group_id:
                if self.volume_access_group_id is not None:
                    if group.volume_access_group_id == self.volume_access_group_id:
                        return group
                else:
                    self.volume_access_group_id = group.volume_access_group_id
                    return group
        return None

    def create_volume_access_group(self):
        try:
            self.sfe.create_volume_access_group(name=self.name,
                                                initiators=self.initiators,
                                                volumes=self.volumes,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                attributes=self.attributes)
        except Exception as e:
            self.module.fail_json(msg="Error creating volume access group %s: %s" %
                                  (self.name, to_native(e)), exception=traceback.format_exc())

    def delete_volume_access_group(self):
        try:
            self.sfe.delete_volume_access_group(volume_access_group_id=self.volume_access_group_id)

        except Exception as e:
            self.module.fail_json(msg="Error deleting volume access group %s: %s" %
                                  (self.volume_access_group_id, to_native(e)),
                                  exception=traceback.format_exc())

    def update_volume_access_group(self):
        try:
            self.sfe.modify_volume_access_group(volume_access_group_id=self.volume_access_group_id,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                name=self.name,
                                                initiators=self.initiators,
                                                volumes=self.volumes,
                                                attributes=self.attributes)
        except Exception as e:
            self.module.fail_json(msg="Error updating volume access group %s: %s" %
                                  (self.volume_access_group_id, to_native(e)), exception=traceback.format_exc())

    def apply(self):
        changed = False
        group_exists = False
        update_group = False
        group_detail = self.get_volume_access_group()

        if group_detail:
            group_exists = True

            if self.state == 'absent':
                changed = True

            elif self.state == 'present':
                # Check if we need to update the group
                if self.volumes is not None and group_detail.volumes != self.volumes:
                    update_group = True
                    changed = True
                elif self.initiators is not None and group_detail.initiators != self.initiators:
                    update_group = True
                    changed = True
                elif self.virtual_network_id is not None or self.virtual_network_tags is not None or \
                        self.attributes is not None:
                    update_group = True
                    changed = True

        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not group_exists:
                        self.create_volume_access_group()
                    elif update_group:
                        self.update_volume_access_group()

                elif self.state == 'absent':
                    self.delete_volume_access_group()

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireVolumeAccessGroup()
    v.apply()

if __name__ == '__main__':
    main()
