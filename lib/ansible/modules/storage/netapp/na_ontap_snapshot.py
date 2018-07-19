#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_snapshot
short_description: Manage NetApp Sanpshots
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author:
- Chris Archibald (carchi@netapp.com), Kevin Hutton (khutton@netapp.com)
description:
- Create/Modify/Delete Ontap snapshots
options:
  state:
    description:
    - If you want to create/modify a snapshot, or delete it.
    choices: ['present', 'absent']
    default: present
  snapshot:
    description:
      Name of the snapshot to be managed.
      The maximum string length is 256 characters.
    required: true
  volume:
    description:
    - Name of the volume on which the snapshot is to be created.
    required: true
  async_bool:
    description:
    - If true, the snapshot is to be created asynchronously.
    type: bool
  comment:
    description:
      A human readable comment attached with the snapshot.
      The size of the comment can be at most 255 characters.
  snapmirror_label:
    description:
      A human readable SnapMirror Label attached with the snapshot.
      Size of the label can be at most 31 characters.
  ignore_owners:
    description:
    - if this field is true, snapshot will be deleted
      even if some other processes are accessing it.
    type: bool
  snapshot_instance_uuid:
    description:
    - The 128 bit unique snapshot identifier expressed in the form of UUID.
  vserver:
    description:
    - The Vserver name
  new_comment:
    description:
      A human readable comment attached with the snapshot.
      The size of the comment can be at most 255 characters.
      This will replace the existing comment
'''
EXAMPLES = """
    - name: create SnapShot
      tags:
        - create
      na_ontap_snapshot:
        state=present
        snapshot={{ snapshot name }}
        volume={{ vol name }}
        comment="i am a comment"
        vserver={{ vserver name }}
        username={{ netapp username }}
        password={{ netapp password }}
        hostname={{ netapp hostname }}
    - name: delete SnapShot
      tags:
        - delete
      na_ontap_snapshot:
        state=absent
        snapshot={{ snapshot name }}
        volume={{ vol name }}
        vserver={{ vserver name }}
        username={{ netapp username }}
        password={{ netapp password }}
        hostname={{ netapp hostname }}
    - name: modify SnapShot
      tags:
        - modify
      na_ontap_snapshot:
        state=present
        snapshot={{ snapshot name }}
        new_comment="New comments are great"
        volume={{ vol name }}
        vserver={{ vserver name }}
        username={{ netapp username }}
        password={{ netapp password }}
        hostname={{ netapp hostname }}
"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapSnapshot(object):
    """
    Creates, modifies, and deletes a Snapshot
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            snapshot=dict(required=True, type="str"),
            volume=dict(required=True, type="str"),
            async_bool=dict(required=False, type="bool", default=False),
            comment=dict(required=False, type="str"),
            snapmirror_label=dict(required=False, type="str"),
            ignore_owners=dict(required=False, type="bool", default=False),
            snapshot_instance_uuid=dict(required=False, type="str"),
            vserver=dict(required=True, type="str"),
            new_comment=dict(required=False, type="str"),

        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up state variables
        # These are the required variables
        self.state = parameters['state']
        self.snapshot = parameters['snapshot']
        self.vserver = parameters['vserver']
        # these are the optional variables for creating a snapshot
        self.volume = parameters['volume']
        self.async_bool = parameters['async_bool']
        self.comment = parameters['comment']
        self.snapmirror_label = parameters['snapmirror_label']
        # these are the optional variables for deleting a snapshot\
        self.ignore_owners = parameters['ignore_owners']
        self.snapshot_instance_uuid = parameters['snapshot_instance_uuid']
        # These are the optional for Modify.
        # You can NOT change a snapcenter name
        self.new_comment = parameters['new_comment']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.vserver)
        return

    def create_snapshot(self):
        """
        Creates a new snapshot
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-create")

        # set up required variables to create a snapshot
        snapshot_obj.add_new_child("snapshot", self.snapshot)
        snapshot_obj.add_new_child("volume", self.volume)
        # Set up optional variables to create a snapshot
        if self.async_bool:
            snapshot_obj.add_new_child("async", self.async_bool)
        if self.comment:
            snapshot_obj.add_new_child("comment", self.comment)
        if self.snapmirror_label:
            snapshot_obj.add_new_child(
                "snapmirror-label", self.snapmirror_label)
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating snapshot %s: %s' %
                                  (self.snapshot, to_native(error)),
                                  exception=traceback.format_exc())

    def delete_snapshot(self):
        """
        Deletes an existing snapshot
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-delete")

        # Set up required variables to delete a snapshot
        snapshot_obj.add_new_child("snapshot", self.snapshot)
        snapshot_obj.add_new_child("volume", self.volume)
        # set up optional variables to delete a snapshot
        if self.ignore_owners:
            snapshot_obj.add_new_child("ignore-owners", self.ignore_owners)
        if self.snapshot_instance_uuid:
            snapshot_obj.add_new_child(
                "snapshot-instance-uuid", self.snapshot_instance_uuid)
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting snapshot %s: %s' %
                                  (self.snapshot, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_snapshot(self):
        """
        Modify an existing snapshot
        :return:
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-modify-iter")
        # Create query object, this is the existing object
        query = netapp_utils.zapi.NaElement("query")
        snapshot_info_obj = netapp_utils.zapi.NaElement("snapshot-info")
        snapshot_info_obj.add_new_child("name", self.snapshot)
        query.add_child_elem(snapshot_info_obj)
        snapshot_obj.add_child_elem(query)

        # this is what we want to modify in the snapshot object
        attributes = netapp_utils.zapi.NaElement("attributes")
        snapshot_info_obj = netapp_utils.zapi.NaElement("snapshot-info")
        snapshot_info_obj.add_new_child("name", self.snapshot)
        snapshot_info_obj.add_new_child("comment", self.new_comment)
        attributes.add_child_elem(snapshot_info_obj)
        snapshot_obj.add_child_elem(attributes)
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying snapshot %s: %s' %
                                  (self.snapshot, to_native(error)),
                                  exception=traceback.format_exc())

    def does_snapshot_exist(self):
        """
        Checks to see if a snapshot exists or not
        :return: Return True if a snapshot exists, false if it dosn't
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-get-iter")
        desired_attr = netapp_utils.zapi.NaElement("desired-attributes")
        snapshot_info = netapp_utils.zapi.NaElement('snapshot-info')
        comment = netapp_utils.zapi.NaElement('comment')
        # add more desired attributes that are allowed to be modified
        snapshot_info.add_child_elem(comment)
        desired_attr.add_child_elem(snapshot_info)
        snapshot_obj.add_child_elem(desired_attr)
        # compose query
        query = netapp_utils.zapi.NaElement("query")
        snapshot_info_obj = netapp_utils.zapi.NaElement("snapshot-info")
        snapshot_info_obj.add_new_child("name", self.snapshot)
        snapshot_info_obj.add_new_child("volume", self.volume)
        query.add_child_elem(snapshot_info_obj)
        snapshot_obj.add_child_elem(query)
        result = self.server.invoke_successfully(snapshot_obj, True)
        return_value = None
        # TODO: Snapshot with the same name will mess this up,
        # need to fix that later
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            attributes_list = result.get_child_by_name('attributes-list')
            snap_info = attributes_list.get_child_by_name('snapshot-info')
            return_value = {'comment': snap_info.get_child_content('comment')}
        return return_value

    def apply(self):
        """
        Check to see which play we should run
        """
        changed = False
        comment_changed = False
        netapp_utils.ems_log_event("na_ontap_snapshot", self.server)
        existing_snapshot = self.does_snapshot_exist()
        if existing_snapshot is not None:
            if self.state == 'absent':
                changed = True
            elif self.state == 'present' and self.new_comment:
                if existing_snapshot['comment'] != self.new_comment:
                    comment_changed = True
                    changed = True
        else:
            if self.state == 'present':
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not existing_snapshot:
                        self.create_snapshot()
                    elif comment_changed:
                        self.modify_snapshot()
                elif self.state == 'absent':
                    if existing_snapshot:
                        self.delete_snapshot()

        self.module.exit_json(changed=changed)


def main():
    """
    Creates, modifies, and deletes a Snapshot
    """

    obj = NetAppOntapSnapshot()
    obj.apply()


if __name__ == '__main__':
    main()
