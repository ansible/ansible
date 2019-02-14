#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Element Software Snapshot Restore
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_snapshot_restore

short_description:  NetApp Element Software Restore Snapshot
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Element OS Cluster restore snapshot to volume.

options:

    src_volume_id:
        description:
        - ID or Name of source active volume.
        required: true

    src_snapshot_id:
        description:
        - ID or Name of an existing snapshot.
        required: true

    dest_volume_name:
        description:
        - New Name of destination for restoring the snapshot
        required: true

    account_id:
        description:
        - Account ID or Name of Parent/Source Volume.
        required: true

'''

EXAMPLES = """
   - name: Restore snapshot to volume
     tags:
     - elementsw_create_snapshot_restore
     na_elementsw_snapshot_restore:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       account_id: ansible-1
       src_snapshot_id: snapshot_20171021
       src_volume_id: volume-playarea
       dest_volume_name: dest-volume-area

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


class ElementOSSnapshotRestore(object):
    """
    Element OS Restore from snapshot
    """

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            account_id=dict(required=True, type='str'),
            src_volume_id=dict(required=True, type='str'),
            dest_volume_name=dict(required=True, type='str'),
            src_snapshot_id=dict(required=True, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        input_params = self.module.params

        self.account_id = input_params['account_id']
        self.src_volume_id = input_params['src_volume_id']
        self.dest_volume_name = input_params['dest_volume_name']
        self.src_snapshot_id = input_params['src_snapshot_id']

        if HAS_SF_SDK is False:
            self.module.fail_json(
                msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

        self.elementsw_helper = NaElementSWModule(self.sfe)

        # add telemetry attributes
        self.attributes = self.elementsw_helper.set_element_attributes(source='na_elementsw_snapshot_restore')

    def get_account_id(self):
        """
            Get account id if found
        """
        try:
            # Update and return self.account_id
            self.account_id = self.elementsw_helper.account_exists(self.account_id)
            return self.account_id
        except Exception as err:
            self.module.fail_json(msg="Error: account_id %s does not exist" % self.account_id, exception=to_native(err))

    def get_snapshot_id(self):
        """
            Return snapshot details if found
        """
        src_snapshot = self.elementsw_helper.get_snapshot(self.src_snapshot_id, self.src_volume_id)
        # Update and return self.src_snapshot_id
        if src_snapshot:
            self.src_snapshot_id = src_snapshot.snapshot_id
            # Return self.src_snapshot_id
            return self.src_snapshot_id
        return None

    def restore_snapshot(self):
        """
        Restore Snapshot to Volume
        """
        try:
            self.sfe.clone_volume(volume_id=self.src_volume_id,
                                  name=self.dest_volume_name,
                                  snapshot_id=self.src_snapshot_id,
                                  attributes=self.attributes)
        except Exception as exception_object:
            self.module.fail_json(
                msg='Error restore snapshot %s' % (to_native(exception_object)),
                exception=traceback.format_exc())

    def apply(self):
        """
        Check, process and initiate restore snapshot to volume operation
        """
        changed = False
        result_message = None
        snapshot_detail = None
        self.get_account_id()
        src_vol_id = self.elementsw_helper.volume_exists(self.src_volume_id, self.account_id)

        if src_vol_id is not None:
            # Update self.src_volume_id
            self.src_volume_id = src_vol_id
            if self.get_snapshot_id() is not None:
                # Addressing idempotency by comparing volume does not exist with same volume name
                if self.elementsw_helper.volume_exists(self.dest_volume_name, self.account_id) is None:
                    self.restore_snapshot()
                    changed = True
                else:
                    result_message = "No changes requested, Skipping changes"
            else:
                self.module.fail_json(msg="Snapshot id not found %s" % self.src_snapshot_id)
        else:
            self.module.fail_json(msg="Volume id not found %s" % self.src_volume_id)

        self.module.exit_json(changed=changed, msg=result_message)


def main():
    """
    Main function
    """
    na_elementsw_snapshot_restore = ElementOSSnapshotRestore()
    na_elementsw_snapshot_restore.apply()


if __name__ == '__main__':
    main()
