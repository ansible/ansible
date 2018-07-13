#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Remy Mudingay <remy.mudingay@esss.se>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: zpool
short_description: Manage zfs zpools
description:
  - Manage virtual storage pools using zfs zpools
version_added: "0.1"
options:
  name:
    description:
      - Pool name
    required: true
  raid_level:
    description:
      - type of pool
    choices: [ mirror, raidz, raidz1, raidz2 ]
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
'''

EXAMPLES = '''
- name: Create a new raidz zpool
  zpool:
    name: rpool
    devices:
      - /dev/sdc
      - /dev/sdd
      - /dev/sde
    raid_level: raidz
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

- name: Destroy an existing zpool
  zpool:
    name: rpool
    state: absent
'''

import os

from ansible.module_utils.basic import AnsibleModule


class Zpool(object):

    def __init__(self, module, name, raid_level, devices, spare, state):
        self.module = module
        self.name = name
        self.changed = False
        self.zpool_cmd = module.get_bin_path('zpool', True)
        self.pool = name.split('/')[0]
        self.is_solaris = os.uname()[0] == 'SunOS'
        self.enhanced_sharing = self.check_enhanced_sharing()


    def check_enhanced_sharing(self):
        if self.is_solaris and not self.is_openzfs:
            cmd = [self.zpool_cmd]
            cmd.extend(['get', 'version'])
            cmd.append(self.pool)
            (rc, out, err) = self.module.run_command(cmd, check_rc=True)
            version = out.splitlines()[-1].split()[2]
            if int(version) >= 34:
                return True
        return False


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
        action = 'create'
        cmd.append(action)
        cmd.append(self.name)
        cmd.append(self.raid_level)
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
def is_even(x):
    if x % 2 == 0:
        return True
    else:
        return False


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', required=True, choices=['absent', 'present']),
            devices=dict(type='list', default=None),
            raid_level=dict(type='str', required=False, choices=['mirror','raidz', 'raidz1', 'raidz2']),
            spare=dict(type='list', default=None),
        ),
    )

    #parameters = self.module.params

    state = module.params.get('state')
    name = module.params.get('name')
    devices = module.params.get('devices')
    raid_level = module.params.get('raid_level')
    spare = module.params.get('spare')

    result = dict(
        name=name,
        state=state,
        devices=devices,
        raid_level=raid_level,
        spare=spare,
    )

    zpool = Zpool(module, name, state, raid_level, devices, spare)

    if raid_level  == 'mirror':
        if len(devices) >= 2 and is_even(len(devices)):
            device_count = len(devices)/2
            devcount = 0
            for index, item in enumerate(devices):
                dev1 = item[devcount]
                devcount += 1
                dev2 = item[devcount]
                devcount += 1
                devs = [ dev1, dev2 ]
                devicelist = ' '.join(devs)
        #returning a string instead of a list!
        devices = ' mirror ', devicelist

    elif raid_level == 'raidz':
        if len(devices) == 3:
            dev = ' '.join(devices)
            devices = 'raidz ', dev
    elif raid_level == 'raidz1':
        if len(devices) == 6:
            dev = ' '.join(devices)
            devices = 'raidz1 ', dev
    elif raid_level == 'raidz2':
        if len(devices) == 6:
            dev = ' '.join(devices)
            devices = 'raidz2 ', dev


    if devices is None:
        devices = []

    if spare is None:
        spare = []
        spares = spare
    else:
        spares = ' '.join(spare)
        spare = 'spare ', spares

    if state == 'present':
        if zpool.exists() is False:
            zpool.create()

    elif state == 'absent':
        if zpool.exists():
            zpool.destroy()

    result['changed'] = zpool.changed
    module.exit_json(**result)

if __name__ == '__main__':
    main()
