#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Fabrizio Colonna <colofabrix@tin.it>
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

from ansible.module_utils.basic import AnsibleModule
import locale
import math
import re
import os


DOCUMENTATION = '''
---
author:
 - "Fabrizio Colonna (@ColOfAbRiX)"
module: parted
short_description: Configure block device partitions
version_added: "2.3"
description:
  - This module allows configuring block device partition using the C(parted)
    command line tool. For a full description of the fields and the options
    check the GNU parted manual.
notes:
  - When fetching information about a new disk and when the version of parted
    installed on the system is before version 3.1, the module queries the kernel
    through C(/sys/) to obtain disk information. In this case the units CHS and
    CYL are not supported.
requirements:
  - This module requires parted version >= 3.1 or, if parted version < 3.1,
    then it requires a Linux version running the sysfs file system C(/sys/).
options:
  device:
    description: The block device (disk) where to operate.
    required: True
  align:
    description: Set alignment for newly created partitions.
    choices: ['none', 'cylinder', 'minimal', 'optimal']
    default: optimal
  number:
    description:
     - The number of the partition to work with or the number of the partition
       that will be created. Required when performing any action on the disk,
       except fetching information.
  unit:
    description:
     - Selects the current default unit that Parted will use to display
       locations and capacities on the disk and to interpret those given by the
       user if they are not suffixed by an unit. When fetching information about
       a disk, it is always recommended to specify a unit.
    choices: [
       's', 'B', 'KB', 'KiB', 'MB', 'MiB', 'GB', 'GiB', 'TB', 'TiB', '%', 'cyl',
       'chs', 'compact'
    ]
    default: KiB
  label:
    description: Creates a new disk label.
    choices: [
       'aix', 'amiga', 'bsd', 'dvh', 'gpt', 'loop', 'mac', 'msdos', 'pc98',
       'sun', ''
    ]
    default: msdos
  part_type:
    description:
     - Is one of 'primary', 'extended' or 'logical' and may be specified only
       with 'msdos' or 'dvh' partition tables. A name must be specified for a
       'gpt' partition table. Neither part-type nor name may be used with a
       'sun' partition table.
    choices: ['primary', 'extended', 'logical']
  part_start:
    description:
     - Where the partition will start as offset from the beginning of the disk,
       that is, the "distance" from the start of the disk.
    default: 0%
  part_end :
    description:
     - Where the partition will end as offset from the beginning of the disk,
       that is, the "distance" from the start of the disk.
    default: 100%
  name:
    description:
     - Sets the name for the partition number (GPT, Mac, MIPS and PC98 only).
  flags:
    description: A list of the flags that has to be set on the partition.
  state:
    description:
     - If to create or delete a partition. If not present the module will return
       only the device information.
    choices: ['present', 'absent']
    default: present
'''

RETURN = '''
partition_info:
  description: Current partition information
  returned: success
  type: dict
  contains:
    device:
      description: Generic device information.
      type: dict
    partitions:
      description: List of device partitions.
      type: list
    sample: >
      {
        "disk": {
          "dev": "/dev/sdb",
          "logical_block": 512,
          "model": "VMware Virtual disk",
          "physical_block": 512,
          "size": 5.0,
          "table": "msdos",
          "unit": "gib"
        },
        "partitions": [{
          "begin": 0.0,
          "end": 1.0,
          "flags": ["boot", "lvm"],
          "fstype": null,
          "num": 1,
          "size": 1.0
        }, {
          "begin": 1.0,
          "end": 5.0,
          "flags": [],
          "fstype": null,
          "num": 2,
          "size": 4.0
        }],
        "script": "unit 'GiB' print"
      }
'''

EXAMPLES = """
# Create a new primary partition
- parted:
    device: /dev/sdb
    number: 1
    state: present

# Remove partition number 1
- parted:
    device: /dev/sdb
    number: 1
    state: absent

# Create a new primary partition with a size of 1GiB
- parted:
    device: /dev/sdb
    number: 1
    state: present
    part_end: 1GiB

# Create a new primary partition for LVM
- parted:
    device: /dev/sdb
    number: 2
    flags: [ lvm ]
    state: present
    part_start: 1GiB

# Read device information (always use unit when probing)
- parted: device=/dev/sdb unit=MiB
  register: sdb_info

# Remove all partitions from disk
- parted:
    device: /dev/sdb
    number: "{{ item.num }}"
    state: absent
  with_items:
   - "{{ sdb_info.partitions }}"
"""


def parse_partition_info(output, unit):
    """
    Parses the output of parted and transforms the data into
    a dictionary.

    Parted Machine Parseable Output:
    See: https://lists.alioth.debian.org/pipermail/parted-devel/2006-December/00
    0573.html
     - All lines end with a semicolon (;)
     - The first line indicates the units in which the output is expressed.
       CHS, CYL and BYT stands for CHS, Cylinder and Bytes respectively.
     - The second line is made of disk information in the following format:
       "path":"size":"transport-type":"logical-sector-size":"physical-sector-siz
       e":"partition-table-type":"model-name";
     - If the first line was either CYL or CHS, the next line will contain
       information on no. of cylinders, heads, sectors and cylinder size.
     - Partition information begins from the next line. This is of the format:
       (for BYT)
       "number":"begin":"end":"size":"filesystem-type":"partition-name":"flags-s
       et";
       (for CHS/CYL)
       "number":"begin":"end":"filesystem-type":"partition-name":"flags-set";
    """
    lines = output.split('\n')
    generic_params = lines[1].rstrip(';').split(':')
    size, unit = parse_unit(generic_params[1], unit)

    generic = {
        'dev':   generic_params[0],
        'size':  size,
        'unit':  unit,
        'table': generic_params[5],
        'model': generic_params[6],
        'logical_block':  int(generic_params[3]),
        'physical_block': int(generic_params[4])
    }

    parts = []
    for line in lines[2:]:
        line = line.strip().rstrip(';')
        if not line:
            continue

        part_params = line.split(':')
        flags = [f for f in part_params[6].split(', ') if f != '']

        parts.append({
            'num':    int(part_params[0]),
            'begin':  parse_unit(part_params[1], unit)[0],
            'end':    parse_unit(part_params[2], unit)[0],
            'size':   parse_unit(part_params[3], unit)[0],
            'fstype': part_params[4] or None,
            'flags':  flags,
        })

    return {'generic': generic, 'partitions': parts}


def format_disk_size(size_bytes, unit, sector_size):
    """
    Formats a size in bytes into a different unit, like parted does. It doesn't
    manage CYL and CHS formats, though.
    This function has been adapted from https://github.com/Distrotech/parted/blo
    b/279d9d869ff472c52b9ec2e180d568f0c99e30b0/libparted/unit.c
    """
    unit = unit.lower()

    # Shortcut
    if size_bytes == 0:
        return 0.0

    # Reference prefixes (International System of Units and IEC)
    units_si  = ['b', 'kb',  'mb',  'gb',  'tb',  'pb',  'eb',  'zb',  'yb']
    units_iec = ['b', 'kib', 'mib', 'gib', 'tib', 'pib', 'eib', 'zib', 'yib']

    # Cases where we default to 'compact'
    if unit in ['', 'compact', 'cyl', 'chs']:
        index = max(0, int(
            (math.log10(size_bytes) - 1.0) / 3.0
        ))
        unit = 'b'
        if index < len(units_si):
            unit = units_si[index]

    # Find the appropriate multiplier
    multiplier = 1.0
    if unit in units_si:
        multiplier = 1000.0 ** units_si.index(unit)
    elif unit in units_iec:
        multiplier = 1024.0 ** units_iec.index(unit)

    output = size_bytes / multiplier * (1 + 1E-16)

    # Corrections to round up as per IEEE754 standard
    if output < 10:    w = output + 0.005
    elif output < 100: w = output + 0.05
    else:              w = output + 0.5

    if w < 10:    precision = 2
    elif w < 100: precision = 1
    else:         precision = 0

    # Round and return
    return round(output, precision), unit


def read_record(file_path, default=None):
    """
    Reads the first line of a file and returns it.
    """
    try:
        f = open(file_path, 'r')
        try:
            return f.readline().strip()
        finally:
            f.close()
    except IOError:
        return default


def get_unlabeled_device_info(device, unit):
    """
    Fetches device information directly from the kernel and it is used when
    parted cannot work because of a missing label. It always returns a 'unknown'
    label.
    """
    device_name = os.path.basename(device)
    base = "/sys/block/{0}".format(device_name)

    vendor      = read_record(base + "/device/vendor", "Unknown")
    model       = read_record(base + "/device/model", "model")
    logic_block = int(read_record(base + "/queue/logical_block_size", 0))
    phys_block  = int(read_record(base + "/queue/physical_block_size", 0))
    size_bytes  = int(read_record(base + "/size", 0)) * logic_block

    size, unit  = format_disk_size(size_bytes, unit, logic_block)

    return {
        'generic': {
            'dev':            device,
            'table':          "unknown",
            'size':           size,
            'unit':           unit,
            'logical_block':  logic_block,
            'physical_block': phys_block,
            'model':          "{0} {1}".format(vendor, model),
        },
        'partitions': []
    }


def get_device_info(device, unit):
    """
    Fetches information about a disk and its partitions and it returns a
    dictionary.
    """
    global module

    # If parted complains about missing labels, it means there are no partitions.
    # In this case only, use a custom function to fetch information and emulate
    # parted formats for the unit.
    label_needed = check_parted_label(device)
    if label_needed:
        return get_unlabeled_device_info(device, unit)

    command = "parted -s -m {0} -- unit '{1}' print".format(device, unit)
    rc, out, err = module.run_command(command)
    if rc != 0 and 'unrecognised disk label' not in err:
        module.fail_json(msg=(
            "Error while getting device information with parted "
            "script: '{0}'".format(command)),
             rc=rc, out=out, err=err
        )

    return parse_partition_info(out, unit)


def check_parted_label(device):
    """
    Determines if parted needs a label to complete its duties. Versions prior
    to 3.1 don't return data when there is no label. For more information see:
    http://upstream.rosalinux.ru/changelogs/libparted/3.1/changelog.html
    """
    # Check the version
    parted_major, parted_minor = parted_version()
    if (parted_major == 3 and parted_minor >= 1) or parted_major > 3:
        return False

    # Older parted versions return a message in the stdout and RC > 0.
    rc, out, err = module.run_command("parted -s -m {0} print".format(device))
    if rc != 0 and 'unrecognised disk label' in out.lower():
        return True

    return False


def parted_version():
    """
    Returns the major and minor version of parted installed on the system.
    """
    global module

    rc, out, err = module.run_command("parted --version")
    if rc != 0:
        module.fail_json(
            msg="Failed to get parted version.", rc=rc, out=out, err=err
        )

    lines = out.split('\n')
    if len(lines) == 0:
        module.fail_json(msg="Failed to get parted version.", rc=0, out=out)

    matches = re.search(r'^parted.+(\d+)\.(\d+)$', lines[0])
    if len(matches.groups()) != 2:
        module.fail_json(msg="Failed to get parted version.", rc=0, out=out)

    major = int(matches.group(1))
    minor = int(matches.group(2))

    return major, minor


def parted(script, device, align):
    """
    Runs a parted script.
    """
    global module

    if script and not module.check_mode:
        command = "parted -s -m -a {0} {1} -- {2}".format(align, device, script)
        rc, out, err = module.run_command(command)

        if rc != 0:
            module.fail_json(
                msg="Error while running parted script: '{0}'".format(
                    command.strip()
                ),
                rc=rc, out=out, err=err
            )


def part_exists(partitions, attribute, number):
    """
    Looks if a partition that has a specific value for a specific attribute
    actually exists.
    """
    return any(
        part[attribute] and
        part[attribute] == number for part in partitions
    )


def parse_unit(size_str, unit, ceil=True):
    """
    Converts '123.1unit' string into ints. If ceil is True it will be rounded up
    (124) and and down (123) if ceil is False.
    """
    matches = re.search(r'^([\d.]+)(\w+)?$', size_str)
    if matches is None:
        module.fail_json(msg="Error interpreting the size of the disk given by parted.")

    size = locale.atof(matches.group(1))
    if len(matches.groups()) == 2:
        unit = matches.group(2).lower()

    size = math.floor(size)
    if ceil:
        math.ceil(size)

    return size, unit


def main():
    global module
    changed = False
    output_script = ""
    script = ""

    module = AnsibleModule(
        argument_spec={
            'device': {'required': True, 'type': 'str'},
            'align': {
                'default': 'optimal',
                'choices': ['none', 'cylinder', 'minimal', 'optimal'],
                'required': False,
                'type': 'str'
            },
            'number': {'default': None, 'type': 'int', 'required': False},

            # unit <unit> command
            'unit': {
                'default': 'KiB',
                'choices': [
                    's', 'B', 'KB', 'KiB', 'MB', 'MiB', 'GB', 'GiB', 'TB',
                    'TiB', '%', 'cyl', 'chs', 'compact'
                ],
                'required': False,
                'type': 'str'
            },

            # mklabel <label-type> command
            'label': {
                'choices': [
                    'aix', 'amiga', 'bsd', 'dvh', 'gpt', 'loop', 'mac', 'msdos',
                    'pc98', 'sun', ''
                ],
                'required': False,
                'type': 'str'
            },

            # mkpart <part-type> [<fs-type>] <start> <end> command
            'part_type': {
                'default': 'primary',
                'choices': ['primary', 'extended', 'logical'],
                'required': False,
                'type': 'str'
            },
            'part_start': {'default': '0%', 'type': 'str', 'required': False},
            'part_end': {'default': '100%', 'type': 'str', 'required': False},

            # name <partition> <name> command
            'name': {'type': 'str', 'required': False},

            # set <partition> <flag> <state> command
            'flags': {'type': 'list', 'required': False},

            # rm/mkpart command
            'state': {
                'choices': ['present', 'absent'],
                'required': False,
                'type': 'str'
            }
        },
        required_together=[
            ['number', 'state']
        ],
        supports_check_mode=True,
    )

    # Data extraction
    device      = module.params['device']
    align       = module.params['align'].lower()
    number      = module.params['number']
    unit        = module.params['unit']
    label       = module.params['label']
    part_type   = module.params['part_type'].lower()
    part_start  = module.params['part_start']
    part_end    = module.params['part_end']
    name        = module.params['name']
    state       = module.params['state']
    flags       = module.params['flags']

    # Conditioning
    if state:
        state = state.lower()
    if number and number < 0:
        module.fail_json(msg="The partition number must be non negative.")

    # Read the current disk information
    current_device = get_device_info(device, unit)
    current_parts = current_device['partitions']

    if state and state == 'present':
        # Default value for the label
        if not current_device['generic']['table'] or \
           current_device['generic']['table'] == 'unknown' and \
           not label:
            label = 'msdos'

        # Assign label if required
        if label:
            script += "mklabel {0} ".format(label)

        # Create partition if required
        if part_type and not part_exists(current_parts, 'num', number):
            script += "mkpart {0} {1} {2} ".format(
                part_type,
                part_start,
                part_end
            )

        # Set the unit of the run
        if unit and script:
            script = "unit {0} ".format(unit) + script

        # Execute the script and update the data structure.
        # This will create the partition for the next steps
        if script:
            output_script += script
            parted(script, device, align)
            changed = True
            script = ""

            current_parts = get_device_info(device, unit)['partitions']

        if part_exists(current_parts, 'num', number) or module.check_mode:
            # Assign name to the the partition
            if name and name in ['gpt', 'mac', 'mips', 'pc98']:
                script += "name {0} {1} ".format(number, name)

            # Manage flags
            if flags:
                partition = {'flags': []}
                if not module.check_mode:
                    partition = [p for p in current_parts if p['num'] == number][0]

                # Compute only the changes in flags status
                flags_off = list(set(partition['flags']) - set(flags))
                flags_on  = list(set(flags) - set(partition['flags']))

                for f in flags_on:
                    script += "set {0} {1} on ".format(number, f)

                for f in flags_off:
                    script += "set {0} {1} off ".format(number, f)

        # Set the unit of the run
        if unit and script:
            script = "unit {0} ".format(unit) + script

        # Execute the script
        if script:
            output_script += script
            changed = True
            parted(script, device, align)

    elif state and state == 'absent':
        # Remove the partition
        if part_exists(current_parts, 'num', number) or module.check_mode:
            script = "rm {0} ".format(number)
            output_script += script
            changed = True
            parted(script, device, align)

    elif not state:
        output_script = "unit '{0}' print ".format(unit)

    # Final status of the device
    final_device_status = get_device_info(device, unit)
    module.exit_json(
        changed=changed,
        disk=final_device_status['generic'],
        partitions=final_device_status['partitions'],
        script=output_script.strip()
    )


module = None

if __name__ == '__main__':
    main()
