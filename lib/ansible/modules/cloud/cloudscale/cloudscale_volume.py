#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudscale_volume
short_description: Manages volumes on the cloudscale.ch IaaS service
description:
  - Create, attach/detach and delete volumes on the cloudscale.ch IaaS service.
notes:
  - To create a new volume at least the I(name) and I(size_gb) options
    are required.
  - A volume can be created and attached to a server in the same task.
version_added: 2.8
author: "Gaudenz Steinlin (@gaudenz)"
options:
  state:
    description:
      - State of the volume.
    default: present
    choices: [ present, absent ]
  name:
    description:
      - Name of the volume. Either name or UUID must be present to change an
        existing volume.
  uuid:
    description:
      - UUID of the volume. Either name or UUID must be present to change an
        existing volume.
  size_gb:
    description:
      - Size of the volume in GB.
  type:
    description:
      - Type of the volume. Cannot be changed after creating the volume.
        Defaults to ssd on volume creation.
    choices: [ ssd, bulk ]
  server_uuids:
    description:
      - UUIDs of the servers this volume is attached to. Set this to [] to
        detach the volume. Currently a volume can only be attached to a
        single server.
    aliases: [ server_uuid ]
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
  returned: success when state == present
  type: str
  sample: https://api.cloudscale.ch/v1/volumes/2db69ba3-1864-4608-853a-0771b6885a3a
uuid:
  description: The unique identifier for this volume.
  returned: success when state == present
  type: str
  sample: 2db69ba3-1864-4608-853a-0771b6885a3a
name:
  description: The display name of the volume.
  returned: success when state == present
  type: str
  sample: my_ssd_volume
size_gb:
  description: The size of the volume in GB.
  returned: success when state == present
  type: str
  sample: 50
type:
  description: "The type of the volume. There are currently two options:
                ssd (default) or bulk."
  returned: success when state == present
  type: str
  sample: bulk
server_uuids:
  description: The UUIDs of the servers this volume is attached to.
  returned: success when state == present
  type: list
  sample: ['47cec963-fcd2-482f-bdb6-24461b2d47b1']
state:
  description: The current status of the volume.
  returned: success
  type: str
  sample: present
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudscale import (AnsibleCloudscaleBase,
                                             cloudscale_argument_spec,
                                             )


class AnsibleCloudscaleVolume(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleVolume, self).__init__(module)
        params = self._module.params
        self.info = {
            'name': params['name'],
            'uuid': params['uuid'],
            'state': 'absent',
        }
        self.changed = False
        if params['uuid'] is not None:
            vol = self._get('volumes/%s' % params['uuid'])
            if vol is None and params['state'] == 'present':
                self._module.fail_json(
                    msg='Volume with UUID %s does not exist. Can\'t create a '
                        'volume with a predefined UUID.' % params['uuid'],
                )
            elif vol is not None:
                self.info = vol
                self.info['state'] = 'present'
        else:
            resp = self._get('volumes')
            volumes = [vol for vol in resp if vol['name'] == params['name']]
            if len(volumes) == 1:
                self.info = volumes[0]
                self.info['state'] = 'present'
            elif len(volumes) > 1:
                self._module.fail_json(
                    msg='More than 1 volume with name "%s" exists.'
                        % params['name'],
                )

    def create(self):
        params = self._module.params

        # check for required parameters to create a volume
        missing_parameters = []
        for p in ('name', 'size_gb'):
            if p not in params or not params[p]:
                missing_parameters.append(p)

        if len(missing_parameters) > 0:
            self._module.fail_json(
                msg='Missing required parameter(s) to create a volume: %s.'
                    % ' '.join(missing_parameters),
            )

        data = {
            'name': params['name'],
            'size_gb': params['size_gb'],
            'type': params['type'] or 'ssd',
            'server_uuids': params['server_uuids'] or [],
        }

        self.info = self._post('volumes', data)
        self.info['state'] = 'present'
        self.changed = True

    def delete(self):
        self._delete('volumes/%s' % self.info['uuid'])
        self.info = {
            'name': self.info['name'],
            'uuid': self.info['uuid'],
            'state': 'absent',
        }
        self.changed = True

    def update(self, param):
        self._patch(
            'volumes/%s' % self.info['uuid'],
            {param: self._module.params[param]},
        )
        self.info[param] = self._module.params[param]
        self.changed = True


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=('present', 'absent')),
        name=dict(),
        uuid=dict(),
        size_gb=dict(type='int'),
        type=dict(choices=('ssd', 'bulk')),
        server_uuids=dict(type='list', aliases=['server_uuid']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid'),),
        mutually_exclusive=(('name', 'uuid'),),
        supports_check_mode=True,
    )

    volume = AnsibleCloudscaleVolume(module)
    if module.check_mode:
        changed = False
        for param, conv in (('state', str),
                            ('server_uuids', set),
                            ('size_gb', int)):
            if module.params[param] is None:
                continue

            if conv(volume.info[param]) != conv(module.params[param]):
                changed = True
                break

        module.exit_json(changed=changed,
                         **volume.info)

    if (volume.info['state'] == 'absent'
       and module.params['state'] == 'present'):
        volume.create()
    elif (volume.info['state'] == 'present'
          and module.params['state'] == 'absent'):
        volume.delete()

    if module.params['state'] == 'present':
        if (module.params['type'] is not None
           and volume.info['type'] != module.params['type']):
            module.fail_json(
                msg='Cannot change type of an existing volume.',
            )

        for param, conv in (('server_uuids', set), ('size_gb', int)):
            if module.params[param] is None:
                continue
            if conv(volume.info[param]) != conv(module.params[param]):
                volume.update(param)

    module.exit_json(changed=volume.changed, **volume.info)


if __name__ == '__main__':
    main()
