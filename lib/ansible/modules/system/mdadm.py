#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Anthony ARNAUD <anthony.arnaud@corp.ovh.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
author:
  - Anthony ARNAUD  (@bluelogon)
module: mdadm
short_description: Configure software RAID devices
description:
  - This module creates, removes software RAID devices.
    WARNING This module does not support "check mode" to prevent r/w on array.
version_added: "2.10"
options:
  name:
    type: str
    description:
    - Array name.
    required: true
  devices:
    type: list
    description:
    - Define disk devices to assign to array.
  raid_devices:
    type: int
    description:
    - Specify the number of active devices in the array. Default is the total devices
  level:
    type: str
    description:
    - Define the array raid level
    choices: ['linear','stripe','raid0','raid1','raid4','raid5','raid6','raid10','multipath','faulty','container']
    default: "raid10"
  metadata:
    type: str
    description:
    - Declare the style of RAID metadata (superblock) to be used
    choices: ['0','0.90','1.0','1.1','1.2']
    default: "1.2"
  state:
    type: str
    description:
    - Control if the MD exists. If C(present) and the
      MD does not already exist then the C(devices) option is required.
    choices: [ absent, present, info ]
    default: present
  opts:
    type: str
    description:
    - Free-form options to be passed to the mdadm command at creation.
'''

EXAMPLES = '''
- name: Create a RAID1 /dev/md/myraid1
  mdadm:
    name: myraid1
    devices:
      - /dev/sda1
      - /dev/sdb1
    level: raid1
    state: present

- name: Create a RAID5 with on spare
  mdadm:
    name: 0
    devices:
      - /dev/sda1
      - /dev/sdb1
      - /dev/sdc1
      - /dev/sdd1
    level: raid5
    raid_devices: 3
    state: present

- name: Destroy /dev/md0
  mdadm:
    name: 0
    state: absent
'''

RETURN = '''
changed:
  description: Return changed for mdadm actions as true or false.
  returned: always
  type: bool
active:
  description: soft-raid is active.
  returned: success
  type: bool
degraded:
  description: soft-raid is degraded.
  returned: success
  type: bool
dev:
  description: "The soft-raid device (ex: /dev/md0)."
  returned: success
  type: str
devices:
  description: The devices that compose the array.
  returned: success
  type: list
level:
  description: Raid level (raid0, raid1...).
  returned: success
  type: str
metadata:
  description: mdadm metadata version.
  returned: success
  type: str
name:
  description: Array name.
  returned: success
  type: str
num_devices:
  description: Number of devices active in the array.
  returned: success
  type: str
state:
  description: Array state return by mdadm.
  returned: success
  type: str
uuid:
  description: Array UUID.
  returned: success
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
import os
import re


class MDArray:
    def __init__(self, name, dev, uuid, metadata, level, devices, num_devices, ansmod):
        self.name = name
        self.dev = dev
        self.uuid = uuid
        self.metadata = metadata
        self.level = level
        self.sparses = 0
        self.num_devices = num_devices
        if devices is None:
            self.devices = []
        else:
            self.devices = devices
        self.active = False
        # Ansible module: to run command or return error
        self._ansmod = ansmod
        self.state = "unknown"
        self.degraded = False

    def __str__(self):
        return self.name

    def refresh_state(self):
        if not self.active:
            self.assemble()
        real_dev_name = os.path.basename(self.get_real_dev())
        # Check degraded only if supported (not with raid0)
        degraded_status_file = "/sys/block/%s/md/degraded" % real_dev_name
        if os.path.exists(degraded_status_file):
            with open(degraded_status_file, 'r') as f:
                if '1' in f.read().rstrip("\n"):
                    self.degraded = True
                else:
                    self.degraded = False

        with open("/sys/block/%s/md/array_state" % real_dev_name, 'r') as f:
            self.state = f.read().rstrip("\n")

    def get_real_dev(self):
        # /dev/md/name => /dev/mdXXX
        if os.path.islink(self.dev):
            return os.path.realpath(self.dev)
        return self.dev

    def is_readonly(self):
        real_dev_name = os.path.basename(self.get_real_dev())
        with open("/sys/block/%s/md/array_state" % real_dev_name, 'r') as f:
            if 'readonly' in f.read().rstrip("\n"):
                return True
        return False

    def disable_readonly(self):
        mdadm_cmd = self._ansmod.get_bin_path("mdadm", required=True)
        self._ansmod.run_command(
            "%s --readwrite %s" % (mdadm_cmd, self.dev),
            check_rc=True
        )

    def assemble(self, readonly=True):
        mdadm_cmd = self._ansmod.get_bin_path("mdadm", required=True)
        if readonly:
            readonly = "--readonly"
        if not self.active:
            self._ansmod.run_command(
                "%s --assemble --scan --uuid=%s %s" % (mdadm_cmd, self.uuid, readonly),
                check_rc=True
            )
            self.active = True

    def stop(self):
        mdadm_cmd = self._ansmod.get_bin_path("mdadm", required=True)
        if self.active:
            self._ansmod.run_command("%s --stop %s" % (mdadm_cmd, self.dev), check_rc=True)
            self.active = False

    def add_device(self, device):
        mdadm_cmd = self._ansmod.get_bin_path("mdadm", required=True)
        self._ansmod.run_command("%s %s --add %s" % (mdadm_cmd, self.dev, device), check_rc=True)

    def remove_device(self, device):
        mdadm_cmd = self._ansmod.get_bin_path("mdadm", required=True)

        # Force device to faulty before remove it
        self._ansmod.run_command("%s %s --fail %s" % (mdadm_cmd, self.dev, device), check_rc=True)

        # Remove device
        self._ansmod.run_command("%s %s --remove %s" % (mdadm_cmd, self.dev, device), check_rc=True)

        # Erase superblock to prevent disk assembling
        self._ansmod.run_command("%s --zero-superblock %s" % (mdadm_cmd, device), check_rc=True)

    def delete(self):
        mdadm_cmd = self._ansmod.get_bin_path("mdadm", required=True)

        if self.active:
            self.stop()

        for device in self.devices:
            # Erase superblock to prevent disk assembling
            self._ansmod.run_command("%s --zero-superblock %s" % (mdadm_cmd, device), check_rc=True)


class MDArrayDict(dict):
    def search_by_name(self, name):
        for uuid, raid in self.items():
            if raid.name == name:
                return raid
        return None


def mkversion(major, minor, patch):
    if patch is None:
        patch = 0
    return (1000 * 1000 * int(major)) + (1000 * int(minor)) + int(patch)


def get_mdadm_version(ansmod):
    ver_cmd = ansmod.get_bin_path("mdadm", required=True)
    rc, out, err = ansmod.run_command("%s --version" % ver_cmd)
    if rc != 0:
        return None
    m = re.search(r"mdadm\s+-\s+v(\d+)\.(\d+)(?:\.(\d+))?", err)
    if not m:
        return None
    return mkversion(m.group(1), m.group(2), m.group(3))


def get_mdadm_array(ansmod):
    re_examine = re.compile(r'^ARRAY\s+'
                            r'(?P<dev>[\/|\w|\-|_]+)\s+'
                            r'level=(?P<level>[\w]+)\s+'
                            r'metadata=(?P<metadata>[\d|\.]+)\s+'
                            r'num-devices=(?P<numdevices>[\d]+)\s+'
                            r'UUID=(?P<uuid>[\w+|:]+)\s+'
                            r'name=(?P<host>[\w|\.|-]+):(?P<name>[\w|\-|_]+)\n\s+'
                            r'(spares=(?P<spares>[\d]+)\s+)?'
                            r'devices=(?P<devices>[\/|\w|\-|_|,]+)', re.MULTILINE)

    re_detail = re.compile(r'^ARRAY\s+'
                           r'(?P<dev>[\/|\w|\-|_]+)\s+'
                           r'level=(?P<level>[\w]+)\s+'
                           r'num-devices=(?P<numdevices>[\d]+)\s+'
                           r'metadata=(?P<metadata>[\d|\.]+)\s+'
                           r'(spares=(?P<spares>[\d]+)\s+)?'
                           r'name=(?P<host>[\w|\.|-]+):(?P<name>[\w|\-|_]+)\s+'
                           r'UUID=(?P<uuid>[\w+|:]+)\n\s+'
                           r'devices=(?P<devices>[\/|\w|\-|_|,]+)', re.MULTILINE)

    # list all array detected by mdadm
    mdadm_cmd = ansmod.get_bin_path("mdadm", required=True)
    rc, stdout, err = ansmod.run_command(
        "%s --examine --brief --scan --verbose" % mdadm_cmd,
        check_rc=True
    )

    mdarray_list = MDArrayDict()
    for match in re_examine.finditer(stdout):
        devices = []
        for device in match.group('devices').split(','):
            devices.append(device)

        mdarray = MDArray(
            name=match.group('name'),
            dev=match.group('dev'),
            uuid=match.group('uuid'),
            level=match.group('level'),
            metadata=match.group('metadata'),
            devices=devices,
            num_devices=match.group('numdevices'),
            ansmod=ansmod)
        mdarray_list[mdarray.uuid] = mdarray

    # List all active array
    mdadm_cmd = ansmod.get_bin_path("mdadm", required=True)
    rc, stdout, err = ansmod.run_command(
        "%s --detail --brief --scan --verbose" % mdadm_cmd,
        check_rc=True
    )

    for match in re_detail.finditer(stdout):
        if match.group('uuid') in mdarray_list:
            mdarray_list[match.group('uuid')].active = True
            mdarray_list[match.group('uuid')].refresh_state()
            if match.group('spares'):
                mdarray_list[match.group('uuid')].sparses = match.group('spares')

    return mdarray_list


def check_and_get_devices(devices, ansmod):
    checked_devices = []
    for device in devices:
        if not os.path.exists(device):
            ansmod.fail_json(msg="%s does not exist" % device)
        if os.path.islink(device):
            checked_devices.append(os.path.realpath(device))
        else:
            checked_devices.append(device)
    return checked_devices


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            devices=dict(type='list', default=[]),
            raid_devices=dict(type='int'),
            level=dict(type='str', default='raid10', choices=[
                'linear',
                'stripe',
                'raid0',
                'raid1',
                'raid4',
                'raid5',
                'raid6',
                'raid10',
                'multipath',
                'faulty',
                'container'
            ]),
            metadata=dict(type='str', default='1.2', choices=['0', '0.90', '1.0', '1.1', '1.2']),
            opts=dict(type='str'),
            state=dict(type='str', default='present', choices=['absent', 'present', 'info']),
        ),
        supports_check_mode=False,
    )

    # Determine if the "--yes" option should be used
    version_found = get_mdadm_version(module)
    if version_found is None:
        module.fail_json(msg="Failed to get mdadm version number")

    mdadm_cmd = module.get_bin_path("mdadm", required=True)
    name = module.params['name']
    devices = module.params['devices']
    raid_devices = module.params['raid_devices']
    level = module.params['level']
    metadata = module.params['metadata']
    opts = module.params['opts']
    state = module.params['state']

    checked_devices = check_and_get_devices(devices, module)
    mdarray_list = get_mdadm_array(module)
    mdarray = mdarray_list.search_by_name(name)

    if opts is None:
        opts = ""

    # Number of devices by default
    if raid_devices is None and mdarray is None:
        raid_devices = len(devices)
    elif raid_devices is None and mdarray is not None:
        raid_devices = mdarray.num_devices

    if mdarray is None:
        if state == 'absent':
            # No MD and state absent, nothing to do.
            module.exit_json(changed=False)
        elif state == 'present':
            if len(devices) == 0:
                module.fail_on_missing_params(['devices'])

            # Create MD
            spare_devices = len(checked_devices) - raid_devices
            if level in ['linear', 'strip', 'raid0']:
                # Does not support spare-devices
                create_cmd = "%s --create --verbose %s --metadata=%s --level=%s --raid-devices=%s %s %s"
                create_cmd_build = create_cmd % (mdadm_cmd, name, metadata, level,
                                                 raid_devices, opts, " ".join(checked_devices))
            else:
                create_cmd = "%s --create --verbose %s --metadata=%s " \
                             "--level=%s --raid-devices=%s --spare-devices=%s %s %s"
                create_cmd_build = create_cmd % (mdadm_cmd, name, metadata, level,
                                                 raid_devices, spare_devices, opts, " ".join(checked_devices))

            rc, dummy, err = module.run_command(create_cmd_build)
            if rc == 0:
                changed = True
                module.exit_json(changed=changed)
            else:
                module.fail_json(msg="Creating MD '%s' failed" % name, rc=rc, err=err)
        elif state == 'info':
            module.exit_json(changed=False, stdout="MD %s doesn't exist." % name)

    else:
        if state == 'absent':
            mdarray.delete()
            module.exit_json(changed=True)
        elif state == 'present':
            changed = False

            # Exception with different level
            if mdarray.level != level:
                module.fail_json(msg="Changing level is not supported. %s => %s" % (mdarray.level, level))

            # Exception with different num-devices
            if int(mdarray.num_devices) != int(raid_devices):
                module.fail_json(
                    msg="Changing active devices is not supported. %s => %s" % (mdarray.num_devices, raid_devices)
                )

            # device to add
            devices_to_add = []
            for device in checked_devices:
                if device not in mdarray.devices:
                    devices_to_add.append(device)

            # device to remove
            devices_to_remove = []
            for device in mdarray.devices:
                if device not in checked_devices:
                    devices_to_remove.append(device)

            # Make change
            for device in devices_to_add:
                changed = True
                mdarray.add_device(device)
            for device in devices_to_remove:
                changed = True
                mdarray.remove_device(device)

            module.exit_json(
                changed=changed,
                active=mdarray.active,
                degraded=mdarray.degraded,
                dev=mdarray.dev,
                devices=mdarray.devices,
                level=mdarray.level,
                metadata=mdarray.metadata,
                name=mdarray.name,
                num_devices=mdarray.num_devices,
                state=mdarray.state,
                uuid=mdarray.uuid,
            )
        elif state == 'info':
            module.exit_json(
                changed=False,
                active=mdarray.active,
                degraded=mdarray.degraded,
                dev=mdarray.dev,
                devices=mdarray.devices,
                level=mdarray.level,
                metadata=mdarray.metadata,
                name=mdarray.name,
                num_devices=mdarray.num_devices,
                state=mdarray.state,
                uuid=mdarray.uuid,
            )


if __name__ == '__main__':
    main()
