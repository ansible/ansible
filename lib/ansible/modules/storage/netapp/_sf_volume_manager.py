#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: sf_volume_manager
deprecated:
  removed_in: "2.11"
  why: This Module has been replaced
  alternative: please use M(na_elementsw_volume)
short_description: Manage SolidFire volumes
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.3'
author: Sumit Kumar (@timuster) <sumit4@netapp.com>
description:
- Create, destroy, or update volumes on SolidFire

options:

    state:
        description:
        - Whether the specified volume should exist or not.
        required: true
        choices: ['present', 'absent']

    name:
        description:
        - The name of the volume to manage.
        required: true

    account_id:
        description:
        - Account ID for the owner of this volume.
        required: true

    512emulation:
        description:
        - Should the volume provide 512-byte sector emulation?
        - Required when C(state=present)

    qos:
        description: Initial quality of service settings for this volume. Configure as dict in playbooks.

    attributes:
        description: A YAML dictionary of attributes that you would like to apply on this volume.

    volume_id:
        description:
        - The ID of the volume to manage or update.
        - In order to create multiple volumes with the same name, but different volume_ids, please declare the I(volume_id)
          parameter with an arbitrary value. However, the specified volume_id will not be assigned to the newly created
          volume (since it's an auto-generated property).

    size:
        description:
        - The size of the volume in (size_unit).
        - Required when C(state = present).

    size_unit:
        description:
        - The unit used to interpret the size parameter.
        choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
        default: 'gb'

    access:
        description:
        - "Access allowed for the volume."
        - "readOnly: Only read operations are allowed."
        - "readWrite: Reads and writes are allowed."
        - "locked: No reads or writes are allowed."
        - "replicationTarget: Identify a volume as the target volume for a paired set of volumes. If the volume is not paired, the access status is locked."
        - "If unspecified, the access settings of the clone will be the same as the source."
        choices: ['readOnly', 'readWrite', 'locked', 'replicationTarget']

'''

EXAMPLES = """
   - name: Create Volume
     sf_volume_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       name: AnsibleVol
       qos: {minIOPS: 1000, maxIOPS: 20000, burstIOPS: 50000}
       account_id: 3
       enable512e: False
       size: 1
       size_unit: gb

   - name: Update Volume
     sf_volume_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       name: AnsibleVol
       account_id: 3
       access: readWrite

   - name: Delete Volume
     sf_volume_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: absent
       name: AnsibleVol
       account_id: 2
"""

RETURN = """

msg:
    description: Success message
    returned: success
    type: str

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class SolidFireVolume(object):

    def __init__(self):

        self._size_unit_map = netapp_utils.SF_BYTE_MAP

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            account_id=dict(required=True, type='int'),

            enable512e=dict(type='bool', aliases=['512emulation']),
            qos=dict(required=False, type='dict', default=None),
            attributes=dict(required=False, type='dict', default=None),

            volume_id=dict(type='int', default=None),
            size=dict(type='int'),
            size_unit=dict(default='gb',
                           choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                    'pb', 'eb', 'zb', 'yb'], type='str'),

            access=dict(required=False, type='str', default=None, choices=['readOnly', 'readWrite',
                                                                           'locked', 'replicationTarget']),

        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['size', 'enable512e'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.account_id = p['account_id']
        self.enable512e = p['enable512e']
        self.qos = p['qos']
        self.attributes = p['attributes']

        self.volume_id = p['volume_id']
        self.size_unit = p['size_unit']
        if p['size'] is not None:
            self.size = p['size'] * self._size_unit_map[self.size_unit]
        else:
            self.size = None
        self.access = p['access']
        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def get_volume(self):
        """
            Return volume object if found

            :return: Details about the volume. None if not found.
            :rtype: dict
        """
        volume_list = self.sfe.list_volumes_for_account(account_id=self.account_id)
        for volume in volume_list.volumes:
            if volume.name == self.name:
                # Update self.volume_id
                if self.volume_id is not None:
                    if volume.volume_id == self.volume_id and str(volume.delete_time) == "":
                        return volume
                else:
                    if str(volume.delete_time) == "":
                        self.volume_id = volume.volume_id
                        return volume
        return None

    def create_volume(self):
        try:
            self.sfe.create_volume(name=self.name,
                                   account_id=self.account_id,
                                   total_size=self.size,
                                   enable512e=self.enable512e,
                                   qos=self.qos,
                                   attributes=self.attributes)

        except Exception as err:
            self.module.fail_json(msg="Error provisioning volume %s of size %s" % (self.name, self.size),
                                  exception=to_native(err))

    def delete_volume(self):
        try:
            self.sfe.delete_volume(volume_id=self.volume_id)

        except Exception as err:
            self.module.fail_json(msg="Error deleting volume %s" % self.volume_id,
                                  exception=to_native(err))

    def update_volume(self):
        try:
            self.sfe.modify_volume(self.volume_id,
                                   account_id=self.account_id,
                                   access=self.access,
                                   qos=self.qos,
                                   total_size=self.size,
                                   attributes=self.attributes)

        except Exception as err:
            self.module.fail_json(msg="Error updating volume %s" % self.name,
                                  exception=to_native(err))

    def apply(self):
        changed = False
        volume_exists = False
        update_volume = False
        volume_detail = self.get_volume()

        if volume_detail:
            volume_exists = True

            if self.state == 'absent':
                # Checking for state change(s) here, and applying it later in the code allows us to support
                # check_mode
                changed = True

            elif self.state == 'present':
                if volume_detail.access is not None and self.access is not None and volume_detail.access != self.access:
                    update_volume = True
                    changed = True

                elif volume_detail.account_id is not None and self.account_id is not None \
                        and volume_detail.account_id != self.account_id:
                    update_volume = True
                    changed = True

                elif volume_detail.qos is not None and self.qos is not None and volume_detail.qos != self.qos:
                    update_volume = True
                    changed = True

                elif volume_detail.total_size is not None and volume_detail.total_size != self.size:
                    size_difference = abs(float(volume_detail.total_size - self.size))
                    # Change size only if difference is bigger than 0.001
                    if size_difference / self.size > 0.001:
                        update_volume = True
                        changed = True

                elif volume_detail.attributes is not None and self.attributes is not None and \
                        volume_detail.attributes != self.attributes:
                    update_volume = True
                    changed = True
        else:
            if self.state == 'present':
                changed = True

        result_message = ""

        if changed:
            if self.module.check_mode:
                result_message = "Check mode, skipping changes"
            else:
                if self.state == 'present':
                    if not volume_exists:
                        self.create_volume()
                        result_message = "Volume created"
                    elif update_volume:
                        self.update_volume()
                        result_message = "Volume updated"

                elif self.state == 'absent':
                    self.delete_volume()
                    result_message = "Volume deleted"

        self.module.exit_json(changed=changed, msg=result_message)


def main():
    v = SolidFireVolume()
    v.apply()


if __name__ == '__main__':
    main()
