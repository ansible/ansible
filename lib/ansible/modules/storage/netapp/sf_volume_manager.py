#!/usr/bin/python

# (c) 2017, NetApp, Inc
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''

module: sf_volume_manager

short_description: Manage SolidFire volumes
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)
description:
- Create, destroy, or update volumes on SolidFire

options:

    state:
        required: true
        description:
        - Whether the specified volume should exist or not.
        choices: ['present', 'absent']

    name:
        required: true
        description:
        - The name of the volume to manage

    account_id:
        required: true
        type: int
        description:
        - account_id for the owner of this volume

    512emulation:
        required: false
        type: bool
        description:
        - Should the volume provide 512-byte sector emulation?
        - required when C(state=present)

    qos:
        required: false
        type: QoS object
        description: Initial quality of service settings for this volume.
        default: None

    attributes:
        required: false
        type: dict
        description: List of Name/Value pairs in JSON object format.
        default: None

    volume_id:
        required: false
        description:
        - The ID of the volume to manage or update.
        - In order to create multiple volumes with the same name, but different volume_ids, please declare the volume_id
          parameter with an arbitary value. However, the specified volume_id will not be assigned to the newly created
          volume (since it's an auto-generated property).
        default: None

    size:
        required: false
        description:
        - The size of the volume in (size_unit)
        - required when C(state = present)

    size_unit:
        required: false
        description:
        - The unit used to interpret the size parameter
        choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
        default: 'gb'

    access:
        required: false
        description:
        - Access allowed for the volume
        choices: ['readOnly', 'readWrite', 'locked', 'replicationTarget']
        access_type_description:
        - readOnly: Only read operations are allowed.
        - readWrite: Reads and writes are allowed.
        - locked: No reads or writes are allowed.
        - replicationTarget: Identify a volume as the target volume for a paired set of volumes. If the volume is not paired, the access status is locked.
        - If unspecified, the access settings of the clone will be the same as the source.
        default: None

'''

EXAMPLES = """
   - name: Create Volume
     sf_volume_manager:
       hostname: "{{ solidfire_hostname }}"
       username: "{{ solidfire_username }}"
       password: "{{ solidfire_password }}"
       state: present
       name: AnsibleVol
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


"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
import ansible.module_utils.netapp as netapp_utils

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class SolidFireVolume(object):

    def __init__(self):

        self._size_unit_map = dict(

            # Management GUI displays 1024 ** 3 as 1.1 GB, thus use 1000.
            bytes=1,
            b=1,
            kb=1000,
            mb=1000 ** 2,
            gb=1000 ** 3,
            tb=1000 ** 4,
            pb=1000 ** 5,
            eb=1000 ** 6,
            zb=1000 ** 7,
            yb=1000 ** 8
        )

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            account_id=dict(required=True, type='int'),

            enable512e=dict(type='bool'),
            qos=dict(required=False, type='str', default=None),
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

        except:
            err = get_exception()
            self.module.fail_json(msg="Error provisioning volume %s of size %s" % (self.name, self.size),
                                  exception=str(err))

    def delete_volume(self):
        try:
            self.sfe.delete_volume(volume_id=self.volume_id)

        except:
            err = get_exception()
            self.module.fail_json(msg="Error deleting volume %s" % self.volume_id,
                                  exception=str(err))

    def update_volume(self):
        try:
            self.sfe.modify_volume(self.volume_id,
                                   account_id=self.account_id,
                                   access=self.access,
                                   qos=self.qos,
                                   total_size=self.size,
                                   attributes=self.attributes)

        except:
            err = get_exception()
            self.module.fail_json(msg="Error updating volume %s" % self.name,
                                  exception=str(err))

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
                    if size_difference/self.size > 0.001:
                        update_volume = True
                        changed = True

                elif volume_detail.attributes is not None and self.attributes is not None and \
                        volume_detail.attributes != self.attributes:
                    update_volume = True
                    changed = True
        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not volume_exists:
                        self.create_volume()
                    elif update_volume:
                            self.update_volume()

                elif self.state == 'absent':
                    self.delete_volume()

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireVolume()
    v.apply()

if __name__ == '__main__':
    main()

