#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

'''
Element OS Software Snapshot Manager
'''
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_snapshot

short_description: NetApp Element Software Manage Snapshots
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
    - Create, Modify or Delete Snapshot on Element OS Cluster.

options:
    name:
        description:
        - Name of new snapshot create.
        - If unspecified, date and time when the snapshot was taken is used.

    state:
        description:
        - Whether the specified snapshot should exist or not.
        choices: ['present', 'absent']
        default: 'present'

    src_volume_id:
        description:
        - ID or Name of active volume.
        required: true

    account_id:
        description:
        - Account ID or Name of Parent/Source Volume.
        required: true

    retention:
        description:
        - Retention period for the snapshot.
        - Format is 'HH:mm:ss'.

    src_snapshot_id:
        description:
        - ID or Name of an existing snapshot.
        - Required when C(state=present), to modify snapshot properties.
        - Required when C(state=present), to create snapshot from another snapshot in the volume.
        - Required when C(state=absent), to delete snapshot.

    enable_remote_replication:
        description:
        - Flag, whether to replicate the snapshot created to a remote replication cluster.
        - To enable specify 'true' value.
        type: bool

    snap_mirror_label:
        description:
        - Label used by SnapMirror software to specify snapshot retention policy on SnapMirror endpoint.

    expiration_time:
        description:
        - The date and time (format ISO 8601 date string) at which this snapshot will expire.

    password:
        description:
        - Element OS access account password
        aliases:
        - pass

    username:
        description:
        - Element OS access account user-name
        aliases:
        - user

'''

EXAMPLES = """
   - name: Create snapshot
     tags:
     - elementsw_create_snapshot
     na_elementsw_snapshot:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       src_volume_id: 118
       account_id: sagarsh
       name: newsnapshot-1

   - name: Modify Snapshot
     tags:
     - elementsw_modify_snapshot
     na_elementsw_snapshot:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       src_volume_id: sagarshansivolume
       src_snapshot_id: test1
       account_id: sagarsh
       expiration_time: '2018-06-16T12:24:56Z'
       enable_remote_replication: false

   - name: Delete Snapshot
     tags:
     - elementsw_delete_snapshot
     na_elementsw_snapshot:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: absent
       src_snapshot_id: deltest1
       account_id: sagarsh
       src_volume_id: sagarshansivolume
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


class ElementOSSnapshot(object):
    """
    Element OS Snapshot Manager
    """

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            account_id=dict(required=True, type='str'),
            name=dict(required=False, type='str'),
            src_volume_id=dict(required=True, type='str'),
            retention=dict(required=False, type='str'),
            src_snapshot_id=dict(required=False, type='str'),
            enable_remote_replication=dict(required=False, type='bool'),
            expiration_time=dict(required=False, type='str'),
            snap_mirror_label=dict(required=False, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        input_params = self.module.params

        self.state = input_params['state']
        self.name = input_params['name']
        self.account_id = input_params['account_id']
        self.src_volume_id = input_params['src_volume_id']
        self.src_snapshot_id = input_params['src_snapshot_id']
        self.retention = input_params['retention']
        self.properties_provided = False

        self.expiration_time = input_params['expiration_time']
        if input_params['expiration_time'] is not None:
            self.properties_provided = True

        self.enable_remote_replication = input_params['enable_remote_replication']
        if input_params['enable_remote_replication'] is not None:
            self.properties_provided = True

        self.snap_mirror_label = input_params['snap_mirror_label']
        if input_params['snap_mirror_label'] is not None:
            self.properties_provided = True

        if self.state == 'absent' and self.src_snapshot_id is None:
            self.module.fail_json(
                msg="Please provide required parameter : snapshot_id")

        if HAS_SF_SDK is False:
            self.module.fail_json(
                msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

        self.elementsw_helper = NaElementSWModule(self.sfe)

        # add telemetry attributes
        self.attributes = self.elementsw_helper.set_element_attributes(source='na_elementsw_snapshot')

    def get_account_id(self):
        """
            Return account id if found
        """
        try:
            # Update and return self.account_id
            self.account_id = self.elementsw_helper.account_exists(self.account_id)
            return self.account_id
        except Exception as err:
            self.module.fail_json(msg="Error: account_id %s does not exist" % self.account_id, exception=to_native(err))

    def get_src_volume_id(self):
        """
            Return volume id if found
        """
        src_vol_id = self.elementsw_helper.volume_exists(self.src_volume_id, self.account_id)
        if src_vol_id is not None:
            # Update and return self.volume_id
            self.src_volume_id = src_vol_id
            # Return src_volume_id
            return self.src_volume_id
        return None

    def get_snapshot(self, name=None):
        """
            Return snapshot details if found
        """
        src_snapshot = None
        if name is not None:
            src_snapshot = self.elementsw_helper.get_snapshot(name, self.src_volume_id)
        elif self.src_snapshot_id is not None:
            src_snapshot = self.elementsw_helper.get_snapshot(self.src_snapshot_id, self.src_volume_id)
        if src_snapshot is not None:
            # Update self.src_snapshot_id
            self.src_snapshot_id = src_snapshot.snapshot_id
        # Return src_snapshot
        return src_snapshot

    def create_snapshot(self):
        """
        Create Snapshot
        """
        try:
            self.sfe.create_snapshot(volume_id=self.src_volume_id,
                                     snapshot_id=self.src_snapshot_id,
                                     name=self.name,
                                     enable_remote_replication=self.enable_remote_replication,
                                     retention=self.retention,
                                     snap_mirror_label=self.snap_mirror_label,
                                     attributes=self.attributes)
        except Exception as exception_object:
            self.module.fail_json(
                msg='Error creating snapshot %s' % (
                    to_native(exception_object)),
                exception=traceback.format_exc())

    def modify_snapshot(self):
        """
        Modify Snapshot Properties
        """
        try:
            self.sfe.modify_snapshot(snapshot_id=self.src_snapshot_id,
                                     expiration_time=self.expiration_time,
                                     enable_remote_replication=self.enable_remote_replication,
                                     snap_mirror_label=self.snap_mirror_label)
        except Exception as exception_object:
            self.module.fail_json(
                msg='Error modify snapshot %s' % (
                    to_native(exception_object)),
                exception=traceback.format_exc())

    def delete_snapshot(self):
        """
        Delete Snapshot
        """
        try:
            self.sfe.delete_snapshot(snapshot_id=self.src_snapshot_id)
        except Exception as exception_object:
            self.module.fail_json(
                msg='Error delete snapshot %s' % (
                    to_native(exception_object)),
                exception=traceback.format_exc())

    def apply(self):
        """
        Check, process and initiate snapshot operation
        """
        changed = False
        snapshot_delete = False
        snapshot_create = False
        snapshot_modify = False
        result_message = None
        self.get_account_id()

        # Dont proceed if source volume is not found
        if self.get_src_volume_id() is None:
            self.module.fail_json(msg="Volume id not found %s" % self.src_volume_id)

        # Get snapshot details using source volume
        snapshot_detail = self.get_snapshot()

        if snapshot_detail:
            if self.properties_provided:
                if self.expiration_time != snapshot_detail.expiration_time:
                    changed = True
                else:   # To preserve value in case  parameter expiration_time is not defined/provided.
                    self.expiration_time = snapshot_detail.expiration_time

                if self.enable_remote_replication != snapshot_detail.enable_remote_replication:
                    changed = True
                else:   # To preserve value in case  parameter enable_remote_Replication is not defined/provided.
                    self.enable_remote_replication = snapshot_detail.enable_remote_replication

                if self.snap_mirror_label != snapshot_detail.snap_mirror_label:
                    changed = True
                else:   # To preserve value in case  parameter snap_mirror_label is not defined/provided.
                    self.snap_mirror_label = snapshot_detail.snap_mirror_label

        if self.account_id is None or self.src_volume_id is None or self.module.check_mode:
            changed = False
            result_message = "Check mode, skipping changes"
        elif self.state == 'absent' and snapshot_detail is not None:
            self.delete_snapshot()
            changed = True
        elif self.state == 'present' and snapshot_detail is not None:
            if changed:
                self.modify_snapshot()   # Modify Snapshot properties
            elif not self.properties_provided:
                if self.name is not None:
                    snapshot = self.get_snapshot(self.name)
                    # If snapshot with name already exists return without performing any action
                    if snapshot is None:
                        self.create_snapshot()  # Create Snapshot using parent src_snapshot_id
                        changed = True
                else:
                    self.create_snapshot()
                    changed = True
        elif self.state == 'present':
            if self.name is not None:
                snapshot = self.get_snapshot(self.name)
                # If snapshot with name already exists return without performing any action
                if snapshot is None:
                    self.create_snapshot()  # Create Snapshot using parent src_snapshot_id
                    changed = True
            else:
                self.create_snapshot()
                changed = True
        else:
            changed = False
            result_message = "No changes requested, skipping changes"

        self.module.exit_json(changed=changed, msg=result_message)


def main():
    """
    Main function
    """

    na_elementsw_snapshot = ElementOSSnapshot()
    na_elementsw_snapshot.apply()


if __name__ == '__main__':
    main()
