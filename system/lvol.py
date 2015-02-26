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
author: Jeroen Hoekx
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
      resizing is not supported with percentages.
  state:
    choices: [ "present", "absent" ]
    default: present
    description:
    - Control if the logical volume exists.
    required: false
  force:
    version_added: "1.5"
    choices: [ "yes", "no" ]
    default: "no"
    description:
    - Shrink or remove operations of volumes requires this switch. Ensures that
      that filesystems get never corrupted/destroyed by mistake.
    required: false
notes:
  - Filesystems on top of the volume are not resized.
'''

EXAMPLES = '''
# Create a logical volume of 512m.
- lvol: vg=firefly lv=test size=512

# Create a logical volume of 512g.
- lvol: vg=firefly lv=test size=512g

# Create a logical volume the size of all remaining space in the volume group
- lvol: vg=firefly lv=test size=100%FREE

# Extend the logical volume to 1024m.
- lvol: vg=firefly lv=test size=1024

# Reduce the logical volume to 512m
- lvol: vg=firefly lv=test size=512 force=yes

# Remove the logical volume.
- lvol: vg=firefly lv=test state=absent force=yes
'''

import re

decimal_point = re.compile(r"(\.|,)")


def parse_lvs(data):
    lvs = []
    for line in data.splitlines():
        parts = line.strip().split(';')
        lvs.append({
            'name': parts[0],
            'size': int(decimal_point.split(parts[1])[0]),
        })
    return lvs


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(required=True),
            lv=dict(required=True),
            size=dict(),
            state=dict(choices=["absent", "present"], default='present'),
            force=dict(type='bool', default='no'),
        ),
        supports_check_mode=True,
    )

    vg = module.params['vg']
    lv = module.params['lv']
    size = module.params['size']
    state = module.params['state']
    force = module.boolean(module.params['force'])
    size_opt = 'L'
    size_unit = 'm'

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

        # LVCREATE(8) -L --size option unit
        elif size[-1].isalpha():
            if size[-1].lower() in 'bskmgtpe':
                size_unit = size[-1].lower()
                if size[0:-1].isdigit():
                    size = int(size[0:-1])
                else:
                    module.fail_json(msg="Bad size specification for unit %s" % size_unit)
                size_opt = 'L'
            else:
                module.fail_json(msg="Size unit should be one of [bBsSkKmMgGtTpPeE]")
        # when no unit, megabytes by default
        elif size.isdigit():
            size = int(size)
        else:
            module.fail_json(msg="Bad size specification")

    if size_opt == 'l':
        unit = 'm'
    else:
        unit = size_unit

    lvs_cmd = module.get_bin_path("lvs", required=True)
    rc, current_lvs, err = module.run_command(
        "%s --noheadings -o lv_name,size --units %s --separator ';' %s" % (lvs_cmd, unit, vg))

    if rc != 0:
        if state == 'absent':
            module.exit_json(changed=False, stdout="Volume group %s does not exist." % vg, stderr=False)
        else:
            module.fail_json(msg="Volume group %s does not exist." % vg, rc=rc, err=err)

    changed = False

    lvs = parse_lvs(current_lvs)

    for test_lv in lvs:
        if test_lv['name'] == lv:
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
                rc, _, err = module.run_command("%s -n %s -%s %s%s %s" % (lvcreate_cmd, lv, size_opt, size, size_unit, vg))
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
            module.exit_json(changed=False, msg="Resizing extents with percentage not supported.")
        else:
            ### resize LV
            tool = None
            if size > this_lv['size']:
                tool = module.get_bin_path("lvextend", required=True)
            elif size < this_lv['size']:
                if not force:
                    module.fail_json(msg="Sorry, no shrinking of %s without force=yes." % (this_lv['name']))
                tool = module.get_bin_path("lvextend", required=True)
                tool.append("--force")

            if tool:
                if module.check_mode:
                    changed = True
                else:
                    rc, _, err = module.run_command("%s -%s %s%s %s/%s" % (tool, size_opt, size, size_unit, vg, this_lv['name']))
                    if rc == 0:
                        changed = True
                    elif "matches existing size" in err:
                        module.exit_json(changed=False, vg=vg, lv=this_lv['name'], size=this_lv['size'])
                    else:
                        module.fail_json(msg="Unable to resize %s to %s%s" % (lv, size, size_unit), rc=rc, err=err)

    module.exit_json(changed=changed, msg=msg)

# import module snippets
from ansible.module_utils.basic import *

main()
