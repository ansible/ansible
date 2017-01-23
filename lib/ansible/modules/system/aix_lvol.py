#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Alain Dejoux ²adejoux@djouxtech.net>
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
author:
    - "Alain Dejoux (@adejoux)"
module: aix_lvol
short_description: Configure AIX LVM logical volumes
description:
  - This module creates, removes or resizes AIX logical volumes. Inspired by lvol module.
version_added: "2.3"
options:
  vg:
    description:
    - The volume group this logical volume is part of.
    required: true
  lv:
    description:
    - The name of the logical volume.
    required: true
  lv_type:
    description:
    - The type of the logical volume. Default to jfs2.
    required: false
  size:
    description:
    - The size of the logical volume, size by default in megabytes or optionally with one of the [MGT] units.
  copies:
    description:
    - the number of copies of the logical volume. By default, 1 copy. Maximum copies are 3.
    required: false
  policy:
    choices: [ "maximum", "minimum" ]
    default: maximum
    description:
    - Sets the interphysical volume allocation policy. "maximum" allocates logical partitions across the maximum number of physical volumes.
      "minimum" allocates logical partitions across the minimum number of physical volumes.
    required: false
  state:
    choices: [ "present", "absent" ]
    default: present
    description:
    - Control if the logical volume exists. If C(present) and the
      volume does not already exist then the C(size) option is required.
    required: false
  opts:
    description:
    - Free-form options to be passed to the mklv command
  pvs:
    description:
    - Comma separated list of physical volumes e.g. hdisk1,hdisk2
    required: false
'''

EXAMPLES = '''
# Create a logical volume of 512M.
- aix_lvol:
    vg: testvg
    lv: testlv
    size: 512M

# Create a logical volume of 512M with disks hdisk1 and hdisk2
- aix_lvol:
    vg: testvg
    lv: test2lv
    size: 512M
    pvs: hdisk1,hdisk2

# Create a logical volume of 512M mirrored.
- aix_lvol:
    vg: testvg
    lv: test3lv
    size: 512M
    copies: 2

# Create a logical volume of 1G with a minimum placement policy .
- aix_lvol:
    vg: rootvg
    lv: test4lv
    size: 1G
    policy: minimum

# Create a logical volume with special options like mirror pool
- aix_lvol:
    vg: testvg
    lv: testlv
    size: 512M
    opts: -p copy1=poolA -p copy2=poolB

# Extend the logical volume to 1200M.
- aix_lvol:
    vg: testvg
    lv: test4lv
    size: 1200M


# Remove the logical volume.
- aix_lvol:
    vg: testvg
    lv: testlv
    state: absent
'''

import re

def convert_size(size):
    base_size = None
    size_factor = None

    match = re.search("(\d+)", size)
    if match is not None:
        base_size = int(match.group(1))

    match = re.search("(\w)", size)
    if match is not None:

        if match.group(1) == "G":
            size_factor=1024
        if match.group(1) == "G":
            size_factor=1024*1024

    if base_size is None:
        return None

    if size_factor is None:
        return base_size

    return base_size * base_factor

def round_ppsize(x, base=16):
    new_size = int(base * round(float(x)/base))
    if new_size < x:
        new_size += base
    return new_size


def parse_lv(data):
    name=None

    for line in data.splitlines():
        match = re.search("LOGICAL VOLUME:\s+(\w+)\s+VOLUME GROUP:\s+(\w+)", line)
        if match is not None:
            name = match.group(1)
            vg = match.group(2)
            continue
        match = re.search("LPs:\s+(\d+).*PPs", line)
        if match is not None:
            lps = int(match.group(1))
            continue
        match = re.search("PP SIZE:\s+(\d+)", line)
        if match is not None:
            pp_size = int(match.group(1))
            continue
        match = re.search("INTER-POLICY:\s+(\w+)", line)
        if match is not None:
            policy = match.group(1)
            continue

    if not name:
        return None

    size = lps * pp_size

    return {'name': name, 'vg': vg, 'size': size, 'policy': policy}

def parse_vg(data):

    for line in data.splitlines():

        match = re.search("VOLUME GROUP:\s+(\w+)", line)
        if match is not None:
            name = match.group(1)
            continue

        match = re.search("TOTAL PP.*\((\d+)", line)
        if match is not None:
            size = int(match.group(1))
            continue

        match = re.search("PP SIZE:\s+(\d+)", line)
        if match is not None:
            pp_size = int(match.group(1))
            continue

        match = re.search("FREE PP.*\((\d+)", line)
        if match is not None:
            free = int(match.group(1))
            continue

    return {'name': name, 'size': size, 'free': free, 'pp_size': pp_size}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(required=True),
            lv=dict(required=True),
            lv_type=dict(required=False),
            size=dict(type='str'),
            opts=dict(type='str'),
            copies=dict(type='str'),
            state=dict(choices=["absent", "present"], default='present'),
            policy=dict(choices=["maximum", "minimum"], default='maximum'),
            pvs=dict(type='str')
        ),
        supports_check_mode=True,
    )

    vg = module.params['vg']
    lv = module.params['lv']
    lv_type = module.params['lv_type']
    size = module.params['size']
    opts = module.params['opts']
    copies = module.params['copies']
    policy = module.params['policy']
    state = module.params['state']
    pvs = module.params['pvs']

    if pvs is None:
        pvs = ""
    else:
        pvs = pvs.replace(",", " ")

    if opts is None:
        opts = ""

    if copies is None:
        copies = "1"

    if lv_type is None:
        lv_type = "jfs2"

    if policy == "maximum":
        lv_policy="x"
    else:
        lv_policy="m"

    # Add --test option when running in check-mode
    if module.check_mode:
        test_opt = 'echo '
    else:
        test_opt = ''


    # Get information on volume group requested
    lsvg_cmd = module.get_bin_path("lsvg", required=True)
    rc, vg_info, err = module.run_command(
        "%s %s" % (lsvg_cmd, vg))

    if rc != 0:
        if state == 'absent':
            module.exit_json(changed=False, msg="Volume group %s does not exist." % vg)
        else:
            module.fail_json(msg="Volume group %s does not exist." % vg, rc=rc, err=err)

    this_vg = parse_vg(vg_info)


    if size is not None:
        # Calculate pp size and round it up based on pp size.
        lv_size = round_ppsize(convert_size(size), base=this_vg['pp_size'])

    # Get information on logical volume requested
    lslv_cmd = module.get_bin_path("lslv", required=True)
    rc, lv_info, err = module.run_command(
        "%s %s" % (lslv_cmd, lv))

    if rc != 0:
        if state == 'absent':
            module.exit_json(changed=False, msg="Logical Volume %s does not exist." % lv)

    changed = False

    this_lv = parse_lv(lv_info)

    if state == 'present' and not size:
        if this_lv is None:
            module.fail_json(msg="No size given.")

    msg=''
    if this_lv is None:
        if state == 'present':
            if lv_size > this_vg['free']:
                module.fail_json(msg="Not enough free space in volume group %s: %sM free." % (this_vg['name'], this_vg['free']))

            ### create LV
            mklv_cmd = module.get_bin_path("mklv", required=True)

            cmd = "%s %s -t %s -y %s -c %s  -e %s %s %s %sM %s" % (test_opt, mklv_cmd, lv_type, lv, copies, lv_policy, opts, vg, lv_size, pvs)
            rc, _, err = module.run_command(cmd)
            if rc == 0:
                changed = True
                msg = "Logical volume %s created." % lv
            else:
                module.fail_json(msg="Creating logical volume '%s' failed" % lv, rc=rc, err=err)
    else:
        if state == 'absent':
            ### remove LV
            rmlv_cmd = module.get_bin_path("rmlv", required=True)
            rc, _, err = module.run_command("%s %s -f %s" % (test_opt, rmlv_cmd, this_lv['name']))
            if rc == 0:
                changed = True
                msg = "Logical volume %s deleted." % lv
            else:
                module.fail_json(msg="Failed to remove logical volume %s" % (lv), rc=rc, err=err)
        else:
            if this_lv['policy'] != policy:
                ### change lv allocation policy
                chlv_cmd = module.get_bin_path("chlv", required=True)
                rc, _, err = module.run_command("%s %s -e %s %s" % (test_opt, chlv_cmd, lv_policy, this_lv['name']))
                if rc == 0:
                    changed = True
                    msg = "Logical volume %s policy changed: %s." % (lv, policy)
            if not size:
                pass
            if vg != this_lv['vg']:
                module.fail_json(msg="Logical volume %s already exist in volume group %s" % (lv, this_lv['vg']))

            ### resize LV based on absolute values
            if int(lv_size) > this_lv['size']:
                extendlv_cmd = module.get_bin_path("extendlv", required=True)
                cmd = "%s %s %sM" % (extendlv_cmd, lv, lv_size - this_lv['size'])
                rc, out, err = module.run_command(cmd)
                if rc == 0:
                    changed = True
                    msg += "Logical volume %s size extended to %sMB." % (lv, lv_size)
                else:
                    module.fail_json(msg="Unable to resize %s to %sMB" % (lv, lv_size), rc=rc, err=err)
            elif lv_size < this_lv['size']:
                module.fail_json(msg="No shrinking of Logical Volume %s permitted. Current size: %s MB" % (lv, this_lv['size']))
            else:
                msg += "Logical volume %s size is already %sMB." % (lv, lv_size)

    module.exit_json(changed=changed, msg=msg)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
