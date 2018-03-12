#!/usr/bin/python
# -*- coding: utf-8 -*-
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
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = """
module: efi_boot
version_added: "2.6"
short_description: Manage EFI boot entries
description: 
- Idempotent management of EFI boot loader entries via efibootmgr.
options:
  name:
    required: true
    description:
      - Name of the boot entry to add
  state:
    required: true
    description:
      - If set to 'present' ensures a bootloader entry booting the given
        config is present and active.
      - If set to 'absent' then deletes a bootloader entry based on the
        specified fields.
  device:
    required: false
    default: null
    description:
      - Path of the device the ESP partition is found on
  partition:
    required: false
    default: null
    description:
      - Number of the partition on the device that is the ESP partition.
  bootloader:
    required: false
    default: null
    description:
      - Path to bootloader on the specified ESP partition
  remove_name_conflicts:
    required: false
    default: false
    type: bool
    description:
      - If set to true, bootloaders with conflicting names but a different
        location to the one being added will be removed.
author: "w.rouesnel@gmail.com"
"""

RESULTS = """
"""

EXAMPLES = """
# install an entry for grub on partition 2 of /dev/sda as the new top EFI
# entry. Multiple calls like this will just keep adding new top entries.
- name: install EFI boot entry
  efi_boot:
    name: Grub
    device: /dev/sda
    partition: 2
    bootloader: \EFI\grub\grubx64.efi
    state: present
    
# install an entry for grub and remove any other entries named grub which don't
# point to this disk, partition and bootloader.
- name: install EFI boot entry
  efi_boot:
    name: Grub
    device: /dev/sda
    partition: 2
    bootloader: \EFI\grub\grubx64.efi
    state: present
    remove_name_conflicts: true

# remove any entries named Grub    
- name: remove Grub entries
  efi_boot:
    name: Grub
    state: absent
"""

import os
import subprocess
from ansible.module_utils.basic import AnsibleModule
"""Note: We also monkey-patch subprocess for python 2.6 to
give feature parity with later versions.
"""

if getattr(subprocess, 'check_output', None) is None:
    # python 2.6 doesn't include check_output
    # monkey patch it in!
    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:  # pragma: no cover
            raise ValueError('stdout argument not allowed, '
                             'it will be overridden.')
        process = subprocess.Popen(
            stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, _ = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd, output=output)
        return output

    subprocess.check_output = check_output

    # overwrite CalledProcessError due to `output`
    # keyword not being available (in 2.6)
    class CalledProcessError(Exception):
        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output

        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (
                self.cmd, self.returncode)

    subprocess.CalledProcessError = CalledProcessError


def parse_efibootmgr(output):
    # Build up a map of the boot entry numbers
    boot_entries = {}
    # Ignore the header lines
    output_lines = output.split("\n")[3:]
    for l in output_lines:
        l = l.strip()
        if len(l) == 0:
            continue
        if not l.startswith("Boot"):
            raise Exception("Line did not start with \"Boot\": %s" % (l, ))

        # Split into the name and location parts
        linetuple = l.split("\t")
        if len(linetuple) == 2:
            namepart, location = linetuple
        else:
            namepart = linetuple[0]
            location = ''

        # Get the name and the boot component.
        bootpart, name = namepart.split(" ", 1)

        # Get the boot entry number
        active = bootpart.find("*") != -1
        bootnum = bootpart.split("Boot")[1].replace("*", "")

        # Build the boot entries dictionary
        boot_entries[bootnum] = {
            'name': name,
            'location': location,
            'active': active
        }
    return boot_entries


def bootnums_with_location(boot_entries, location):
    """return a list of bootnums with a given location"""
    result = []
    for bootnum, bootdict in boot_entries.items():
        if bootdict['location'] == location:
            result.append(bootnum)
    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str', default=None),
            state=dict(required=True, type='str', default=None),
            device=dict(required=False, type='str', default=None),
            partition=dict(required=False, type='int', default=None),
            bootloader=dict(required=False, type='str', default=None),
            remove_name_conflicts=dict(
                required=False, type='bool', default=False),
        ),
        supports_check_mode=False)

    params = module.params
    name = params['name']
    state = params['state']
    device = params['device']
    partition = params['partition']
    bootloader = params['bootloader']
    remove_name_conflicts = params['remove_name_conflicts']

    if state not in ('present', 'absent'):
        module.fail_json(msg="state must be set to either present or absent")

    if remove_name_conflicts == True and state != 'present':
        module.fail_json(
            msg="remove_name_conflicts doesn't work with state=absent")

    if name == "":
        module.fail_json(msg="name cannot be blank")

    if device == "":
        module.fail_json(msg="device cannot be blank")

    if partition < 1 and partition is not None:
        module.fail_json(msg="partition numbering must start at 1.")

    if bootloader == "":
        module.fail_json(msg="bootloader cannot be blank.")

    FNULL = open(os.devnull, 'w')

    starting_entries = parse_efibootmgr(
        subprocess.check_output(["efibootmgr", "-v"], stderr=FNULL))

    result = {}

    if state == 'present':
        # Do the bootloader addition right away
        subprocess.check_call(
            [
                "efibootmgr", "-c", "-d", device, "-p",
                '%d' % (partition, ), "-L", name, "-l", bootloader
            ],
            stdout=FNULL,
            stderr=subprocess.STDOUT)
        # Get the entries after addition
        after_addition_entries = parse_efibootmgr(
            subprocess.check_output(["efibootmgr", "-v"], stderr=FNULL))
        # Should be exactly 1 new bootnumber
        added_bootnums = set(after_addition_entries.keys()).difference(
            set(starting_entries.keys()))
        if len(added_bootnums) > 1:
            module.fail_json(
                msg=
                "got more then 1 added bootnum after running single add command.",
                added_bootnums=added_bootnums)

        # Okay the goal is now to remove all the bootnums which match us in location
        # but don't remove the one we just added (which is at the head of the boot order)
        preserved_bootnum = added_bootnums.pop()
        preserved_location = after_addition_entries[preserved_bootnum][
            'location']

        # Find and remove any bootnums with the same location which aren't the one
        # we added which will be at the top of the order now.
        bootnums = bootnums_with_location(after_addition_entries,
                                          preserved_location)
        for b in bootnums:
            if b != preserved_bootnum:
                subprocess.check_call(
                    ["efibootmgr", "-B", "-b", b],
                    stdout=FNULL,
                    stderr=subprocess.STDOUT)
        result['added_boot_entry'] = {
            'bootnum': preserved_bootnum,
            'entry': after_addition_entries[preserved_bootnum]
        }
        result['changed'] = True

    elif state == 'absent':
        if device is not None or partition is not None or bootloader is not None:
            module.fail_json(
                msg=
                "state=absent not implemented for bootloader,device or partition matching"
            )

        result['removed_boot_entries'] = []

        for bootnum, bootdict in starting_entries.items():
            if bootdict['name'] == name:
                result['removed_boot_entries'].append({
                    'bootnum': bootnum,
                    'entry': bootdict
                })
                subprocess.check_call(
                    ["efibootmgr", "-B", "-b", bootnum],
                    stdout=FNULL,
                    stderr=subprocess.STDOUT)
                result['changed'] = True
    else:
        module.fail_json(msg="state must be set to either present or absent")

    module.exit_json(**result)


if __name__ == '__main__':
    main()
