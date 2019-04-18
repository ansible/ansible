#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_snapshot
short_description: NetApp ONTAP manage Snapshots
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create/Modify/Delete ONTAP snapshots
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
  from_name:
    description:
    - Name of the existing snapshot to be renamed to.
    version_added: '2.8'
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
'''
EXAMPLES = """
    - name: create SnapShot
      tags:
        - create
      na_ontap_snapshot:
        state: present
        snapshot: "{{ snapshot name }}"
        volume: "{{ vol name }}"
        comment: "i am a comment"
        vserver: "{{ vserver name }}"
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        hostname: "{{ netapp hostname }}"
    - name: delete SnapShot
      tags:
        - delete
      na_ontap_snapshot:
        state: absent
        snapshot: "{{ snapshot name }}"
        volume: "{{ vol name }}"
        vserver: "{{ vserver name }}"
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        hostname: "{{ netapp hostname }}"
    - name: modify SnapShot
      tags:
        - modify
      na_ontap_snapshot:
        state: present
        snapshot: "{{ snapshot name }}"
        comment: "New comments are great"
        volume: "{{ vol name }}"
        vserver: "{{ vserver name }}"
        username: "{{ netapp username }}"
        password: "{{ netapp password }}"
        hostname: "{{ netapp hostname }}"
"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp_module import NetAppModule
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
            from_name=dict(required=False, type='str'),
            snapshot=dict(required=True, type="str"),
            volume=dict(required=True, type="str"),
            async_bool=dict(required=False, type="bool", default=False),
            comment=dict(required=False, type="str"),
            snapmirror_label=dict(required=False, type="str"),
            ignore_owners=dict(required=False, type="bool", default=False),
            snapshot_instance_uuid=dict(required=False, type="str"),
            vserver=dict(required=True, type="str"),

        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(
                msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(
                module=self.module, vserver=self.parameters['vserver'])
        return

    def get_snapshot(self, snapshot_name=None):
        """
        Checks to see if a snapshot exists or not
        :return: Return True if a snapshot exists, False if it doesn't
        """
        if snapshot_name is None:
            snapshot_name = self.parameters['snapshot']
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-get-iter")
        desired_attr = netapp_utils.zapi.NaElement("desired-attributes")
        snapshot_info = netapp_utils.zapi.NaElement('snapshot-info')
        comment = netapp_utils.zapi.NaElement('comment')
        snapmirror_label = netapp_utils.zapi.NaElement('snapmirror-label')
        # add more desired attributes that are allowed to be modified
        snapshot_info.add_child_elem(comment)
        snapshot_info.add_child_elem(snapmirror_label)
        desired_attr.add_child_elem(snapshot_info)
        snapshot_obj.add_child_elem(desired_attr)
        # compose query
        query = netapp_utils.zapi.NaElement("query")
        snapshot_info_obj = netapp_utils.zapi.NaElement("snapshot-info")
        snapshot_info_obj.add_new_child("name", snapshot_name)
        snapshot_info_obj.add_new_child("volume", self.parameters['volume'])
        query.add_child_elem(snapshot_info_obj)
        snapshot_obj.add_child_elem(query)
        result = self.server.invoke_successfully(snapshot_obj, True)
        return_value = None
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) == 1:
            attributes_list = result.get_child_by_name('attributes-list')
            snap_info = attributes_list.get_child_by_name('snapshot-info')
            return_value = {'comment': snap_info.get_child_content('comment')}
            if snap_info.get_child_by_name('snapmirror-label'):
                return_value['snapmirror_label'] = snap_info.get_child_content('snapmirror-label')
            else:
                return_value['snapmirror_label'] = None
        return return_value

    def create_snapshot(self):
        """
        Creates a new snapshot
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-create")

        # set up required variables to create a snapshot
        snapshot_obj.add_new_child("snapshot", self.parameters['snapshot'])
        snapshot_obj.add_new_child("volume", self.parameters['volume'])
        # Set up optional variables to create a snapshot
        if self.parameters.get('async_bool'):
            snapshot_obj.add_new_child("async", self.parameters['async_bool'])
        if self.parameters.get('comment'):
            snapshot_obj.add_new_child("comment", self.parameters['comment'])
        if self.parameters.get('snapmirror_label'):
            snapshot_obj.add_new_child(
                "snapmirror-label", self.parameters['snapmirror_label'])
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error creating snapshot %s: %s' %
                                  (self.parameters['snapshot'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_snapshot(self):
        """
        Deletes an existing snapshot
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-delete")

        # Set up required variables to delete a snapshot
        snapshot_obj.add_new_child("snapshot", self.parameters['snapshot'])
        snapshot_obj.add_new_child("volume", self.parameters['volume'])
        # set up optional variables to delete a snapshot
        if self.parameters.get('ignore_owners'):
            snapshot_obj.add_new_child("ignore-owners", self.parameters['ignore_owners'])
        if self.parameters.get('snapshot_instance_uuid'):
            snapshot_obj.add_new_child("snapshot-instance-uuid", self.parameters['snapshot_instance_uuid'])
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting snapshot %s: %s' %
                                  (self.parameters['snapshot'], to_native(error)),
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
        snapshot_info_obj.add_new_child("name", self.parameters['snapshot'])
        query.add_child_elem(snapshot_info_obj)
        snapshot_obj.add_child_elem(query)

        # this is what we want to modify in the snapshot object
        attributes = netapp_utils.zapi.NaElement("attributes")
        snapshot_info_obj = netapp_utils.zapi.NaElement("snapshot-info")
        snapshot_info_obj.add_new_child("name", self.parameters['snapshot'])
        if self.parameters.get('comment'):
            snapshot_info_obj.add_new_child("comment", self.parameters['comment'])
        if self.parameters.get('snapmirror_label'):
            snapshot_info_obj.add_new_child("snapmirror-label", self.parameters['snapmirror_label'])
        attributes.add_child_elem(snapshot_info_obj)
        snapshot_obj.add_child_elem(attributes)
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying snapshot %s: %s' %
                                  (self.parameters['snapshot'], to_native(error)),
                                  exception=traceback.format_exc())

    def rename_snapshot(self):
        """
        Rename the sanpshot
        """
        snapshot_obj = netapp_utils.zapi.NaElement("snapshot-rename")

        # set up required variables to rename a snapshot
        snapshot_obj.add_new_child("current-name", self.parameters['from_name'])
        snapshot_obj.add_new_child("new-name", self.parameters['snapshot'])
        snapshot_obj.add_new_child("volume", self.parameters['volume'])
        try:
            self.server.invoke_successfully(snapshot_obj, True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error renaming snapshot %s to %s: %s' %
                                  (self.parameters['from_name'], self.parameters['snapshot'], to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Check to see which play we should run
        """
        current = self.get_snapshot()
        netapp_utils.ems_log_event("na_ontap_snapshot", self.server)
        rename, cd_action = None, None
        modify = {}
        if self.parameters.get('from_name'):
            current_old_name = self.get_snapshot(self.parameters['from_name'])
            rename = self.na_helper.is_rename_action(current_old_name, current)
            modify = self.na_helper.get_modified_attributes(current_old_name, self.parameters)
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
            if cd_action is None:
                modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_snapshot()
                if cd_action == 'create':
                    self.create_snapshot()
                elif cd_action == 'delete':
                    self.delete_snapshot()
                elif modify:
                    self.modify_snapshot()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Creates, modifies, and deletes a Snapshot
    """
    obj = NetAppOntapSnapshot()
    obj.apply()


if __name__ == '__main__':
    main()
