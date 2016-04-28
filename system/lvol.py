#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>, Alexander Bulimov <lazywolf0@gmail.com>
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

DOCUMENTATION = '''
---
author:
    - "Jeroen Hoekx (@jhoekx)"
    - "Alexander Bulimov (@abulimov)"
module: lvol
short_description: Configure LVM logical volumes
description:
  - This module creates, removes or resizes logical volumes.
version_added: "1.1"
options:
  vg:
    description:
    - The volume group this logical volume is part of.
    required: true
  lv:
    description:
    - The name of the logical volume.
    required: true
  size:
    description:
    - The size of the logical volume, according to lvcreate(8) --size, by
      default in megabytes or optionally with one of [bBsSkKmMgGtTpPeE] units; or
      according to lvcreate(8) --extents as a percentage of [VG|PVS|FREE];
      Float values must begin with a digit.
      Resizing using percentage values was not supported prior to 2.1.
  state:
    choices: [ "present", "absent" ]
    default: present
    description:
    - Control if the logical volume exists. If C(present) the C(size) option
      is required.
    required: false
  force:
    version_added: "1.5"
    choices: [ "yes", "no" ]
    default: "no"
    description:
    - Shrink or remove operations of volumes requires this switch. Ensures that
      that filesystems get never corrupted/destroyed by mistake.
    required: false
  opts:
    version_added: "2.0"
    description:
    - Free-form options to be passed to the lvcreate command
  snapshot:
    version_added: "2.1"
    description:
    - The name of the snapshot volume
    required: false
  pvs:
    version_added: "2.2"
    description:
    - Comma separated list of physical volumes e.g. /dev/sda,/dev/sdb
    required: false
notes:
  - Filesystems on top of the volume are not resized.
'''

EXAMPLES = '''
# Create a logical volume of 512m.
- lvol: vg=firefly lv=test size=512

# Create a logical volume of 512m with disks /dev/sda and /dev/sdb
- lvol: vg=firefly lv=test size=512 pvs=/dev/sda,/dev/sdb

# Create cache pool logical volume
- lvol: vg=firefly lv=lvcache size=512m opts='--type cache-pool'

# Create a logical volume of 512g.
- lvol: vg=firefly lv=test size=512g

# Create a logical volume the size of all remaining space in the volume group
- lvol: vg=firefly lv=test size=100%FREE

# Create a logical volume with special options
- lvol: vg=firefly lv=test size=512g opts="-r 16"

# Extend the logical volume to 1024m.
- lvol: vg=firefly lv=test size=1024

# Extend the logical volume to consume all remaining space in the volume group
- lvol: vg=firefly lv=test size=+100%FREE

# Extend the logical volume to take all remaining space of the PVs
- lvol: vg=firefly lv=test size=100%PVS

# Resize the logical volume to % of VG
- lvol: vg-firefly lv=test size=80%VG force=yes

# Reduce the logical volume to 512m
- lvol: vg=firefly lv=test size=512 force=yes

# Remove the logical volume.
- lvol: vg=firefly lv=test state=absent force=yes

# Create a snapshot volume of the test logical volume.
- lvol: vg=firefly lv=test snapshot=snap1 size=100m
'''

import re

decimal_point = re.compile(r"(\d+)")

def mkversion(major, minor, patch):
    return (1000 * 1000 * int(major)) + (1000 * int(minor)) + int(patch)

def parse_lvs(data):
    lvs = []
    for line in data.splitlines():
        parts = line.strip().split(';')
        lvs.append({
            'name': parts[0].replace('[','').replace(']',''),
            'size': int(decimal_point.match(parts[1]).group(1))
        })
    return lvs

def parse_vgs(data):
    vgs = []
    for line in data.splitlines():
        parts = line.strip().split(';')
        vgs.append({
            'name': parts[0],
            'size': int(decimal_point.match(parts[1]).group(1)),
            'free': int(decimal_point.match(parts[2]).group(1)),
            'ext_size': int(decimal_point.match(parts[3]).group(1))
        })
    return vgs


def get_lvm_version(module):
    ver_cmd = module.get_bin_path("lvm", required=True)
    rc, out, err = module.run_command("%s version" % (ver_cmd))
    if rc != 0:
        return None
    m = re.search("LVM version:\s+(\d+)\.(\d+)\.(\d+).*(\d{4}-\d{2}-\d{2})", out)
    if not m:
        return None
    return mkversion(m.group(1), m.group(2), m.group(3))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(required=True),
            lv=dict(required=True),
            size=dict(type='str'),
            opts=dict(type='str'),
            state=dict(choices=["absent", "present"], default='present'),
            force=dict(type='bool', default='no'),
            snapshot=dict(type='str', default=None),
            pvs=dict(type='str')
        ),
        supports_check_mode=True,
    )

    # Determine if the "--yes" option should be used
    version_found = get_lvm_version(module)
    if version_found == None:
        module.fail_json(msg="Failed to get LVM version number")
    version_yesopt = mkversion(2, 2, 99) # First LVM with the "--yes" option
    if version_found >= version_yesopt:
        yesopt = "--yes"
    else:
        yesopt = ""

    vg = module.params['vg']
    lv = module.params['lv']
    size = module.params['size']
    opts = module.params['opts']
    state = module.params['state']
    force = module.boolean(module.params['force'])
    size_opt = 'L'
    size_unit = 'm'
    snapshot = module.params['snapshot']
    pvs = module.params['pvs']

    if pvs is None:
        pvs = ""
    else:
        pvs = pvs.replace(",", " ")

    if opts is None:
        opts = ""

    if size:
        # LVCREATE(8) -l --extents option with percentage
        if '%' in size:
            size_parts = size.split('%', 1)
            size_percent = int(size_parts[0])
            if size_percent > 100:
                module.fail_json(msg="Size percentage cannot be larger than 100%")
            size_whole = size_parts[1]
            if size_whole == 'ORIGIN':
                module.fail_json(msg="Snapshot Volumes are not supported")
            elif size_whole not in ['VG', 'PVS', 'FREE']:
                module.fail_json(msg="Specify extents as a percentage of VG|PVS|FREE")
            size_opt = 'l'
            size_unit = ''

        if not '%' in size:
        # LVCREATE(8) -L --size option unit
            if size[-1].lower() in 'bskmgtpe':
               size_unit = size[-1].lower()
               size = size[0:-1]

            try:
               float(size)
               if not size[0].isdigit(): raise ValueError()
            except ValueError:
               module.fail_json(msg="Bad size specification of '%s'" % size)

    # when no unit, megabytes by default
    if size_opt == 'l':
        unit = 'm'
    else:
        unit = size_unit

    # Get information on volume group requested
    vgs_cmd = module.get_bin_path("vgs", required=True)
    rc, current_vgs, err = module.run_command(
        "%s --noheadings -o vg_name,size,free,vg_extent_size --units %s --separator ';' %s" % (vgs_cmd, unit, vg))

    if rc != 0:
        if state == 'absent':
            module.exit_json(changed=False, stdout="Volume group %s does not exist." % vg, stderr=False)
        else:
            module.fail_json(msg="Volume group %s does not exist." % vg, rc=rc, err=err)

    vgs = parse_vgs(current_vgs)
    this_vg = vgs[0]

    # Get information on logical volume requested
    lvs_cmd = module.get_bin_path("lvs", required=True)
    rc, current_lvs, err = module.run_command(
        "%s -a --noheadings --nosuffix -o lv_name,size --units %s --separator ';' %s" % (lvs_cmd, unit, vg))

    if rc != 0:
        if state == 'absent':
            module.exit_json(changed=False, stdout="Volume group %s does not exist." % vg, stderr=False)
        else:
            module.fail_json(msg="Volume group %s does not exist." % vg, rc=rc, err=err)

    changed = False

    lvs = parse_lvs(current_lvs)

    if snapshot is None:
        check_lv = lv
    else:
        check_lv = snapshot
    for test_lv in lvs:
        if test_lv['name'] == check_lv:
            this_lv = test_lv
            break
    else:
        this_lv = None

    if state == 'present' and not size:
        if this_lv is None:
            module.fail_json(msg="No size given.")
        else:
            module.exit_json(changed=False, vg=vg, lv=this_lv['name'], size=this_lv['size'])

    msg = ''
    if this_lv is None:
        if state == 'present':
            ### create LV
            if module.check_mode:
                changed = True
            else:
                lvcreate_cmd = module.get_bin_path("lvcreate", required=True)
                if snapshot is not None:
                    cmd = "%s %s -%s %s%s -s -n %s %s %s/%s" % (lvcreate_cmd, yesopt, size_opt, size, size_unit, snapshot, opts, vg, lv)
                else:
                    cmd = "%s %s -n %s -%s %s%s %s %s %s" % (lvcreate_cmd, yesopt, lv, size_opt, size, size_unit, opts, vg, pvs)
                rc, _, err = module.run_command(cmd)
                if rc == 0:
                    changed = True
                else:
                    module.fail_json(msg="Creating logical volume '%s' failed" % lv, rc=rc, err=err)
    else:
        if state == 'absent':
            ### remove LV
            if module.check_mode:
                module.exit_json(changed=True)
            if not force:
                module.fail_json(msg="Sorry, no removal of logical volume %s without force=yes." % (this_lv['name']))
            lvremove_cmd = module.get_bin_path("lvremove", required=True)
            rc, _, err = module.run_command("%s --force %s/%s" % (lvremove_cmd, vg, this_lv['name']))
            if rc == 0:
                module.exit_json(changed=True)
            else:
                module.fail_json(msg="Failed to remove logical volume %s" % (lv), rc=rc, err=err)

        elif size_opt == 'l':
            ### Resize LV based on % value
            tool = None
            size_free = this_vg['free']
            if size_whole == 'VG' or size_whole == 'PVS':
                size_requested = size_percent * this_vg['size'] / 100
            else: # size_whole == 'FREE':
                size_requested = size_percent * this_vg['free'] / 100
            if '+' in size:
                size_requested += this_lv['size']
            if this_lv['size'] < size_requested:
                if (size_free > 0)  and (('+' not in size) or (size_free >= (size_requested -  this_lv['size']))):
                    tool = module.get_bin_path("lvextend", required=True)
                else:
                    module.fail_json(msg="Logical Volume %s could not be extended. Not enough free space left (%s%s required / %s%s available)" % (this_lv['name'], (size_requested -  this_lv['size']), unit, size_free, unit))
            elif this_lv['size'] > size_requested + this_vg['ext_size']:  # more than an extent too large
                if size_requested == 0:
                    module.fail_json(msg="Sorry, no shrinking of %s to 0 permitted." % (this_lv['name']))
                elif not force:
                    module.fail_json(msg="Sorry, no shrinking of %s without force=yes" % (this_lv['name']))
                else:
                    tool = module.get_bin_path("lvreduce", required=True)
                    tool = '%s %s' % (tool, '--force')

            if tool:
                if module.check_mode:
                    changed = True
                else:
                    cmd = "%s -%s %s%s %s/%s %s" % (tool, size_opt, size, size_unit, vg, this_lv['name'], pvs)
                    rc, out, err = module.run_command(cmd)
                    if "Reached maximum COW size" in out:
                        module.fail_json(msg="Unable to resize %s to %s%s" % (lv, size, size_unit), rc=rc, err=err, out=out)
                    elif rc == 0:
                        changed = True
                        msg="Volume %s resized to %s%s" % (this_lv['name'], size_requested, unit)
                    elif "matches existing size" in err:
                        module.exit_json(changed=False, vg=vg, lv=this_lv['name'], size=this_lv['size'])
                    else:
                        module.fail_json(msg="Unable to resize %s to %s%s" % (lv, size, size_unit), rc=rc, err=err)

        else:
            ### resize LV based on absolute values
            tool = None
            if int(size) > this_lv['size']:
                tool = module.get_bin_path("lvextend", required=True)
            elif int(size) < this_lv['size']:
                if int(size) == 0:
                    module.fail_json(msg="Sorry, no shrinking of %s to 0 permitted." % (this_lv['name']))
                if not force:
                    module.fail_json(msg="Sorry, no shrinking of %s without force=yes." % (this_lv['name']))
                else:
                    tool = module.get_bin_path("lvreduce", required=True)
                    tool = '%s %s' % (tool, '--force')

            if tool:
                if module.check_mode:
                    changed = True
                else:
                    cmd = "%s -%s %s%s %s/%s %s" % (tool, size_opt, size, size_unit, vg, this_lv['name'], pvs)
                    rc, out, err = module.run_command(cmd)
                    if "Reached maximum COW size" in out:
                        module.fail_json(msg="Unable to resize %s to %s%s" % (lv, size, size_unit), rc=rc, err=err, out=out)
                    elif rc == 0:
                        changed = True
                    elif "matches existing size" in err:
                        module.exit_json(changed=False, vg=vg, lv=this_lv['name'], size=this_lv['size'])
                    else:
                        module.fail_json(msg="Unable to resize %s to %s%s" % (lv, size, size_unit), rc=rc, err=err)

    module.exit_json(changed=changed, msg=msg)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
