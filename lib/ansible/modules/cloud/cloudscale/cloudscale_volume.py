#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# Copyright (c) 2019, René Moser <mail@renemoser.net>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudscale_volume
short_description: Manages volumes on the cloudscale.ch IaaS service.
description:
  - Create, attach/detach, update and delete volumes on the cloudscale.ch IaaS service.
notes:
  - To create a new volume at least the I(name) and I(size_gb) options
    are required.
  - A volume can be created and attached to a server in the same task.
version_added: '2.8'
author:
  - Gaudenz Steinlin (@gaudenz)
  - René Moser (@resmo)
options:
  state:
    description:
      - State of the volume.
    default: present
    choices: [ present, absent ]
    type: str
  name:
    description:
      - Name of the volume. Either name or UUID must be present to change an
        existing volume.
    type: str
  uuid:
    description:
      - UUID of the volume. Either name or UUID must be present to change an
        existing volume.
    type: str
  size_gb:
    description:
      - Size of the volume in GB.
    type: int
  type:
    description:
      - Type of the volume. Cannot be changed after creating the volume.
        Defaults to C(ssd) on volume creation.
    choices: [ ssd, bulk ]
    type: str
  server_uuids:
    description:
      - UUIDs of the servers this volume is attached to. Set this to C([]) to
        detach the volume. Currently a volume can only be attached to a
        single server.
    aliases: [ server_uuid ]
    type: list
  tags:
    description:
      - Tags associated with the volume. Set this to C({}) to clear any tags.
    type: dict
    version_added: '2.9'
extends_documentation_fragment: cloudscale
'''

EXAMPLES = '''
# Create a new SSD volume
- name: Create an SSD volume
  cloudscale_volume:
    name: my_ssd_volume
    size_gb: 50
    api_token: xxxxxx
  register: my_ssd_volume

# Attach an existing volume to a server
- name: Attach volume to server
  cloudscale_volume:
    uuid: my_ssd_volume.uuid
    server_uuids:
      - ea3b39a3-77a8-4d0b-881d-0bb00a1e7f48
    api_token: xxxxxx

# Create and attach a volume to a server
- name: Create and attach volume to server
  cloudscale_volume:
    name: my_ssd_volume
    size_gb: 50
    server_uuids:
      - ea3b39a3-77a8-4d0b-881d-0bb00a1e7f48
    api_token: xxxxxx

# Detach volume from server
- name: Detach volume from server
  cloudscale_volume:
    uuid: my_ssd_volume.uuid
    server_uuids: []
    api_token: xxxxxx

# Delete a volume
- name: Delete volume
  cloudscale_volume:
    name: my_ssd_volume
    state: absent
    api_token: xxxxxx
'''

RETURN = '''
href:
  description: The API URL to get details about this volume.
  returned: state == present
  type: str
  sample: https://api.cloudscale.ch/v1/volumes/2db69ba3-1864-4608-853a-0771b6885a3a
uuid:
  description: The unique identifier for this volume.
  returned: state == present
  type: str
  sample: 2db69ba3-1864-4608-853a-0771b6885a3a
name:
  description: The display name of the volume.
  returned: state == present
  type: str
  sample: my_ssd_volume
size_gb:
  description: The size of the volume in GB.
  returned: state == present
  type: str
  sample: 50
type:
  description: The type of the volume.
  returned: state == present
  type: str
  sample: bulk
server_uuids:
  description: The UUIDs of the servers this volume is attached to.
  returned: state == present
  type: list
  sample: ['47cec963-fcd2-482f-bdb6-24461b2d47b1']
state:
  description: The current status of the volume.
  returned: success
  type: str
  sample: present
tags:
  description: Tags associated with the volume.
  returned: state == present
  type: dict
  sample: { 'project': 'my project' }
  version_added: '2.9'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudscale import (AnsibleCloudscaleBase,
                                             cloudscale_argument_spec,
                                             )


class AnsibleCloudscaleVolume(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleVolume, self).__init__(module)
        self._info = {}

    def _init_container(self):
        return {
            'uuid': self._module.params.get('uuid') or self._info.get('uuid'),
            'name': self._module.params.get('name') or self._info.get('name'),
            'state': 'absent',
        }

    def _create(self, volume):
        # Fail when missing params for creation
        self._module.fail_on_missing_params(['name', 'size_gb'])

        # Fail if a user uses a UUID and state=present but the volume was not found.
        if self._module.params.get('uuid'):
            self._module.fail_json(msg="The volume with UUID '%s' was not found "
                                   "and we would create a new one with different UUID, "
                                   "this is probably not want you have asked for." % self._module.params.get('uuid'))

        self._result['changed'] = True
        data = {
            'name': self._module.params.get('name'),
            'type': self._module.params.get('type'),
            'size_gb': self._module.params.get('size_gb') or 'ssd',
            'server_uuids': self._module.params.get('server_uuids') or [],
            'tags': self._module.params.get('tags'),
        }
        if not self._module.check_mode:
            volume = self._post('volumes', data)
        return volume

    def _update(self, volume):
        update_params = (
            'name',
            'size_gb',
            'server_uuids',
            'tags',
        )
        updated = False
        for param in update_params:
            updated = self._param_updated(param, volume) or updated

        # Refresh if resource was updated in live mode
        if updated and not self._module.check_mode:
            volume = self.get_volume()
        return volume

    def get_volume(self):
        self._info = self._init_container()

        uuid = self._info.get('uuid')
        if uuid is not None:
            volume = self._get('volumes/%s' % uuid)
            if volume:
                self._info.update(volume)
                self._info['state'] = 'present'

        else:
            name = self._info.get('name')
            matching_volumes = []
            for volume in self._get('volumes'):
                if volume['name'] == name:
                    matching_volumes.append(volume)

            if len(matching_volumes) > 1:
                self._module.fail_json(msg="More than one volume with name exists: '%s'. "
                                       "Use the 'uuid' parameter to identify the volume." % name)
            elif len(matching_volumes) == 1:
                self._info.update(matching_volumes[0])
                self._info['state'] = 'present'
        return self._info

    def present(self):
        volume = self.get_volume()
        if volume.get('state') == 'absent':
            volume = self._create(volume)
        else:
            volume = self._update(volume)
        return volume

    def absent(self):
        volume = self.get_volume()
        if volume.get('state') != 'absent':
            self._result['changed'] = True
            if not self._module.check_mode:
                volume['state'] = "absent"
                self._delete('volumes/%s' % volume['uuid'])
        return volume


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=('present', 'absent')),
        name=dict(),
        uuid=dict(),
        size_gb=dict(type='int'),
        type=dict(choices=('ssd', 'bulk')),
        server_uuids=dict(type='list', aliases=['server_uuid']),
        tags=dict(type='dict'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid'),),
        supports_check_mode=True,
    )

    cloudscale_volume = AnsibleCloudscaleVolume(module)

    if module.params['state'] == 'absent':
        server_group = cloudscale_volume.absent()
    else:
        server_group = cloudscale_volume.present()

    result = cloudscale_volume.get_result(server_group)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
