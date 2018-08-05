#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Remy Mudingay <remy.mudingay@esss.se>
# Copyright: (c) 2018, Stephane Armanet <stephane.armanet@esss.se>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: zpool
short_description: Manage zfs zpools
version_added: "2.7"
description:
  - Manage virtual storage pools using zfs zpools
options:
  name:
    description:
      - Pool name
    required: true
  add:
    description:
      -  Add devices (spare or mirror to an existing zpool)
    type: bool
    default: false
  raid_level:
    description:
      - type of pool
    choices: [ none, mirror, raidz, raidz1, raidz2 ]
  vdev:
    description:
      - number of devices in a vdev
    type: int
  devices:
    description:
      - full path to list of block devices such as hdd, nvme or nvme
  spare:
    description:
      - full path to list of block devices such as hdd, nvme or nvme
  state:
    description:
      - Create or delete the pool
    choices: [ absent, present ]
    required: true
author:
- Remy Mudingay
"""

EXAMPLES = """
- name: Create a new raidz zpool
  zpool:
    name: rpool
    devices:
      - /dev/sdc
      - /dev/sdd
      - /dev/sde
    raid_level: raidz
    state: present

- name: Create a new raid 0 stripe zpool
  zpool:
    name: rpool
    devices:
      - /dev/sdb
      - /dev/sdc
      - /dev/sdd
      - /dev/sde
      - /dev/sdf
    raid_level: none
    state: present

- name: Create a new mirror zpool
  zpool:
    name: rpool
    devices:
      - /dev/sdc
      - /dev/sdd
    raid_level: mirror
    state: present

- name: Create a new mirror zpool with a spare drive
  zpool:
    name: rpool
    devices:
      - /dev/sdc
      - /dev/sdd
    raid_level: mirror
    spare:
      - /dev/sde
    state: present

- name: Add devices to an existing zpool
  zpool:
    name: rpool
    add: true
    devices:
    - /dev/sdf
    - /dev/sdg
    raid_level: mirror
    state: present

- name: Add spare dev to an existing zpool
  zpool:
    name: rpool
    add: true
    spare:
    - /dev/sdf
    state: present

- name: Destroy an existing zpool
  zpool:
    name: rpool
    state: absent
"""

import os

from ansible.module_utils.basic import AnsibleModule


class Zpool(object):

    def __init__(self, module, name, state, raid_level, devices, spare, add, vdev):
        self.module = module
        self.name = name
        self.raid_level = raid_level
        self.devices = devices
        self.spare = spare
        self.state = state
        self.add = add
        self.vdev = vdev
        self.changed = False
        self.zpool_cmd = module.get_bin_path('zpool', True)

    def exists(self):
        cmd = [self.zpool_cmd, 'list', self.name]
        (rc, out, err) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            return True
        else:
            return False

    def create(self):
        if self.module.check_mode:
            self.changed = True
            return
        cmd = [self.zpool_cmd]
        if self.add is True:
            action = 'add'
        else:
            action = 'create'
        cmd.append(action)
        cmd.append(self.name)
        cmd.append(self.devices)
        cmd.append(self.spare)
        (rc, out, err) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            self.changed = True
        else:
            self.module.fail_json(msg=err)

    def destroy(self):
        if self.module.check_mode:
            self.changed = True
            return
        cmd = [self.zpool_cmd, 'destroy', self.name]
        (rc, out, err) = self.module.run_command(' '.join(cmd))
        if rc == 0:
            self.changed = True
        else:
            self.module.fail_json(msg=err)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', required=True, choices=['absent', 'present']),
            raid_level=dict(type='str', required=False, choices=['none', 'mirror', 'raidz', 'raidz1', 'raidz2', 'raidz3']),
            vdev=dict(type='int', require=False),
            devices=dict(type='list', default=None),
            spare=dict(type='list', default=None),
            add=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        required_together=[
                    ['raid_level', 'vdev']
                            ]
    )

    name = module.params.get('name')
    state = module.params.get('state')
    add = module.params.get('add')
    raid_level = module.params.get('raid_level')
    devices = module.params.get('devices')
    spare = module.params.get('spare')
    vdev = module.params.get('vdev')

    if raid_level is False or 'none' in raid_level:
        raid_level = ''

    if devices is False or not devices:
        devices = ''
    else:
        if vdev is not False:
            device = ''
            for i in range(0, len(devices), vdev):
                temp = ' ' + raid_level + ' ' + ' '.join(devices[i:i+vdev])
                device += temp
            devices = device
    if spare is False or not spare:
        spare = ''
        spares = spare
    else:
        spares = ' '.join(spare)
        spare = 'spare ' + spares

    result = dict(
        name=name,
        state=state,
        raid_level=raid_level,
        devices=devices,
        spare=spare,
        vdev=vdev,
    )

    zpool = Zpool(module, name, state, raid_level, devices, spare, add, vdev)

    if state == 'present':
        if (zpool.exists() is True and add is True) or zpool.exists() is False:
            zpool.create()
    elif state == 'absent':
        if zpool.exists():
            zpool.destroy()

    result['changed'] = zpool.changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
