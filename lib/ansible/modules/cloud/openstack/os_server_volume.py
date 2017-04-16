#!/usr/bin/python
#coding: utf-8 -*-

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_server_volume
short_description: Attach/Detach Volumes from OpenStack VM's
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
   - Attach or Detach volumes from OpenStack VM's
options:
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
     required: false
   server:
     description:
       - Name or ID of server you want to attach a volume to
     required: true
   volume:
     description:
      - Name or id of volume you want to attach to a server
     required: true
   device:
     description:
      - Device you want to attach. Defaults to auto finding a device name.
     required: false
     default: None
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Attaches a volume to a compute host
- name: attach a volume
  hosts: localhost
  tasks:
  - name: attach volume to host
    os_server_volume:
      state: present
      cloud: mordred
      server: Mysql-server
      volume: mysql-data
      device: /dev/vdb
'''

try:
    import shade
    from shade import meta
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def _system_state_change(state, device):
    """Check if system state would change."""
    if state == 'present':
        if device:
            return False
        return True
    if state == 'absent':
        if device:
            return True
        return False
    return False

def main():
    argument_spec = openstack_full_argument_spec(
        server=dict(required=True),
        volume=dict(required=True),
        device=dict(default=None),  # None == auto choose device name
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    wait = module.params['wait']
    timeout = module.params['timeout']

    try:
        cloud = shade.openstack_cloud(**module.params)
        server = cloud.get_server(module.params['server'])
        volume = cloud.get_volume(module.params['volume'])
        dev = cloud.get_volume_attach_device(volume, server.id)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(state, dev))

        if state == 'present':
            if dev:
                # Volume is already attached to this server
                module.exit_json(changed=False)

            cloud.attach_volume(server, volume, module.params['device'],
                                wait=wait, timeout=timeout)

            server = cloud.get_server(module.params['server'])  # refresh
            volume = cloud.get_volume(module.params['volume'])  # refresh
            hostvars = meta.get_hostvars_from_server(cloud, server)

            module.exit_json(
                changed=True,
                id=volume['id'],
                attachments=volume['attachments'],
                openstack=hostvars
            )

        elif state == 'absent':
            if not dev:
                # Volume is not attached to this server
                module.exit_json(changed=False)

            cloud.detach_volume(server, volume, wait=wait, timeout=timeout)
            module.exit_json(
                changed=True,
                result='Detached volume from server'
            )

    except (shade.OpenStackCloudException, shade.OpenStackCloudTimeout) as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_utils/common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
