#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Alain Dejoux <adejoux@djouxtech.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
    - Alain Dejoux (@adejoux)
module: aix_lvol
short_description: Configure AIX LVM logical volumes
description:
  - This module creates, removes or resizes AIX logical volumes. Inspired by lvol module.
version_added: "2.4"
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
    - The type of the logical volume.
    default: jfs2
  size:
    description:
    - The size of the logical volume with one of the [MGT] units.
  copies:
    description:
    - The number of copies of the logical volume. Maximum copies are 3.
    default: '1'
  policy:
    choices: [ maximum, minimum ]
    default: maximum
    description:
    - Sets the interphysical volume allocation policy. C(maximum) allocates logical partitions across the maximum number of physical volumes.
      C(minimum) allocates logical partitions across the minimum number of physical volumes.
  state:
    choices: [ absent, present ]
    default: present
    description:
    - Control if the logical volume exists. If C(present) and the
      volume does not already exist then the C(size) option is required.
  opts:
    description:
    - Free-form options to be passed to the mklv command.
  pvs:
    description:
    - Comma separated list of physical volumes e.g. C(hdisk1,hdisk2).
'''

EXAMPLES = r'''
- name: Create a logical volume of 512M
  aix_lvol:
    vg: testvg
    lv: testlv
    size: 512M

- name: Create a logical volume of 512M with disks hdisk1 and hdisk2
  aix_lvol:
    vg: testvg
    lv: test2lv
    size: 512M
    pvs: hdisk1,hdisk2

- name: Create a logical volume of 512M mirrored
  aix_lvol:
    vg: testvg
    lv: test3lv
    size: 512M
    copies: 2

- name: Create a logical volume of 1G with a minimum placement policy
  aix_lvol:
    vg: rootvg
    lv: test4lv
    size: 1G
    policy: minimum

- name: Create a logical volume with special options like mirror pool
  aix_lvol:
    vg: testvg
    lv: testlv
    size: 512M
    opts: -p copy1=poolA -p copy2=poolB

- name: Extend the logical volume to 1200M
  aix_lvol:
    vg: testvg
    lv: test4lv
    size: 1200M

- name: Remove the logical volume
  aix_lvol:
    vg: testvg
    lv: testlv
    state: absent
'''

RETURN = r'''
msg:
  type: string
  description: A friendly message describing the task result.
  returned: always
  sample: Logical volume testlv created.
'''

import re

from ansible.module_utils.basic import AnsibleModule


def convert_size(module, size):
    unit = size[-1].upper()
    units = ['M', 'G', 'T']
    try:
        multiplier = 1024 ** units.index(unit)
    except ValueError:
        module.fail_json(msg="No valid size unit specified.")

    return int(size[:-1]) * multiplier


def round_ppsize(x, base=16):
    new_size = int(base * round(float(x) / base))
    if new_size < x:
        new_size += base
    return new_size


def parse_lv(data):
    name = None

    for line in data.splitlines():
        match = re.search(r"LOGICAL VOLUME:\s+(\w+)\s+VOLUME GROUP:\s+(\w+)", line)
        if match is not None:
            name = match.group(1)
            vg = match.group(2)
            continue
        match = re.search(r"LPs:\s+(\d+).*PPs", line)
        if match is not None:
            lps = int(match.group(1))
            continue
        match = re.search(r"PP SIZE:\s+(\d+)", line)
        if match is not None:
            pp_size = int(match.group(1))
            continue
        match = re.search(r"INTER-POLICY:\s+(\w+)", line)
        if match is not None:
            policy = match.group(1)
            continue

    if not name:
        return None

    size = lps * pp_size

    return {'name': name, 'vg': vg, 'size': size, 'policy': policy}


def parse_vg(data):

    for line in data.splitlines():

        match = re.search(r"VOLUME GROUP:\s+(\w+)", line)
        if match is not None:
            name = match.group(1)
            continue

        match = re.search(r"TOTAL PP.*\((\d+)", line)
        if match is not None:
            size = int(match.group(1))
            continue

        match = re.search(r"PP SIZE:\s+(\d+)", line)
        if match is not None:
            pp_size = int(match.group(1))
            continue

        match = re.search(r"FREE PP.*\((\d+)", line)
        if match is not None:
            free = int(match.group(1))
            continue

    return {'name': name, 'size': size, 'free': free, 'pp_size': pp_size}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(type='str', required=True),
            lv=dict(type='str', required=True),
            lv_type=dict(type='str', default='jfs2'),
            size=dict(type='str'),
            opts=dict(type='str', default=''),
            copies=dict(type='str', default='1'),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            policy=dict(type='str', default='maximum', choices=['maximum', 'minimum']),
            pvs=dict(type='list', default=list())
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

    pv_list = ' '.join(pvs)

    if policy == 'maximum':
        lv_policy = 'x'
    else:
        lv_policy = 'm'

    # Add echo command when running in check-mode
    if module.check_mode:
        test_opt = 'echo '
    else:
        test_opt = ''

    # check if system commands are available
    lsvg_cmd = module.get_bin_path("lsvg", required=True)
    lslv_cmd = module.get_bin_path("lslv", required=True)

    # Get information on volume group requested
    rc, vg_info, err = module.run_command("%s %s" % (lsvg_cmd, vg))

    if rc != 0:
        if state == 'absent':
            module.exit_json(changed=False, msg="Volume group %s does not exist." % vg)
        else:
            module.fail_json(msg="Volume group %s does not exist." % vg, rc=rc, out=vg_info, err=err)

    this_vg = parse_vg(vg_info)

    if size is not None:
        # Calculate pp size and round it up based on pp size.
        lv_size = round_ppsize(convert_size(module, size), base=this_vg['pp_size'])

    # Get information on logical volume requested
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

    if this_lv is None:
        if state == 'present':
            if lv_size > this_vg['free']:
                module.fail_json(msg="Not enough free space in volume group %s: %s MB free." % (this_vg['name'], this_vg['free']))

            # create LV
            mklv_cmd = module.get_bin_path("mklv", required=True)

            cmd = "%s %s -t %s -y %s -c %s  -e %s %s %s %sM %s" % (test_opt, mklv_cmd, lv_type, lv, copies, lv_policy, opts, vg, lv_size, pv_list)
            rc, out, err = module.run_command(cmd)
            if rc == 0:
                module.exit_json(changed=True, msg="Logical volume %s created." % lv)
            else:
                module.fail_json(msg="Creating logical volume %s failed." % lv, rc=rc, out=out, err=err)
    else:
        if state == 'absent':
            # remove LV
            rmlv_cmd = module.get_bin_path("rmlv", required=True)
            rc, out, err = module.run_command("%s %s -f %s" % (test_opt, rmlv_cmd, this_lv['name']))
            if rc == 0:
                module.exit_json(changed=True, msg="Logical volume %s deleted." % lv)
            else:
                module.fail_json(msg="Failed to remove logical volume %s." % lv, rc=rc, out=out, err=err)
        else:
            if this_lv['policy'] != policy:
                # change lv allocation policy
                chlv_cmd = module.get_bin_path("chlv", required=True)
                rc, out, err = module.run_command("%s %s -e %s %s" % (test_opt, chlv_cmd, lv_policy, this_lv['name']))
                if rc == 0:
                    module.exit_json(changed=True, msg="Logical volume %s policy changed: %s." % (lv, policy))
                else:
                    module.fail_json(msg="Failed to change logical volume %s policy." % lv, rc=rc, out=out, err=err)

            if vg != this_lv['vg']:
                module.fail_json(msg="Logical volume %s already exist in volume group %s" % (lv, this_lv['vg']))

            # from here the last remaining action is to resize it, if no size parameter is passed we do nothing.
            if not size:
                module.exit_json(changed=False, msg="Logical volume %s already exist." % (lv))

            # resize LV based on absolute values
            if int(lv_size) > this_lv['size']:
                extendlv_cmd = module.get_bin_path("extendlv", required=True)
                cmd = "%s %s %s %sM" % (test_opt, extendlv_cmd, lv, lv_size - this_lv['size'])
                rc, out, err = module.run_command(cmd)
                if rc == 0:
                    module.exit_json(changed=True, msg="Logical volume %s size extended to %sMB." % (lv, lv_size))
                else:
                    module.fail_json(msg="Unable to resize %s to %sMB." % (lv, lv_size), rc=rc, out=out, err=err)
            elif lv_size < this_lv['size']:
                module.fail_json(msg="No shrinking of Logical Volume %s permitted. Current size: %s MB" % (lv, this_lv['size']))
            else:
                module.exit_json(changed=False, msg="Logical volume %s size is already %sMB." % (lv, lv_size))


if __name__ == '__main__':
    main()
