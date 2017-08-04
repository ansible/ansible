#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Pavol Ipoth <pavol.ipoth@gmail.com>
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
    - "Pavol Ipoth <pavol.ipoth@gmail.com>"
module: lvol_thin
short_description: Configure Thin LVM logical volumes
description:
  - This module creates, removes or resizes, converts thin logical volumes.
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
    - The size of the logical volume, by
      default in megabytes or optionally with one of [bBsSkKmMgGtTpPeE] units; or
      as a percentage of [VG|PVS|FREE]; +size is not implemented, as it is by
      design not indempodent
      Float values must begin with a digit.
  state:
    choices: [ "present", "absent" ]
    default: present
    description:
    - Control if the logical volume exists. If C(present) the C(size) option
      is required.
    required: false
  force:
    choices: [ "yes", "no" ]
    default: "no"
    description:
    - Shrink/extend/remove/conversion operations of volumes requires this switch. Ensures that
      that filesystems get never corrupted/destroyed by mistake.
    - this flag always means that data on lvol will be destroyed
    required: false
  opts:
    description:
    - Free-form options to be passed to the lvcreate command
  pvs:
    description:
    - Comma separated list of physical volumes /dev/sda,/dev/sdc
  type:
    choices: ["thin", "thin-pool", "normal"]
    default: normal
    description:
    - Type of logical volume, thin is thind lvol, thin-pool is thin pool
      supplying thind lvol, normal is lvol without any type. To create thin
      lvol, thin pool must already exist
  pool:
    description:
    - This value is used when type is thin, specifies which thin pool will
      be caching data for thin lvol. Must be in format vg/lv. Thin pool lvol
      and thin lvol must be from same vg (this is restriction of lvm2).
notes:
  - Filesystems on top of the volume are not resized.
'''

EXAMPLES = '''
# Create a logical volume of 512m.
- lvol: vg=firefly lv=test size=512m

# Create a logical volume of 512g.
- lvol: vg=firefly lv=test size=512g

# Create a logical volume the size of all remaining space in the volume group
- lvol: vg=firefly lv=test size=100%FREE

# Create a logical volume with special options
- lvol: vg=firefly lv=test size=512g opts="-r 16"

# Extend the logical volume to 1024m.
- lvol: vg=firefly lv=test size=1024m

# Extend the logical volume to take all remaining space of the PVs
- lvol: vg=firefly lv=test size=100%PVS

# Resize the logical volume to % of VG
- lvol: vg=firefly lv=test size=80%VG force=yes

# Reduce the logical volume to 512m
- lvol: vg=firefly lv=test size=512m force=yes

# Remove the logical volume.
- lvol: vg=firefly lv=test state=absent force=yes

# Create thin pool logical volume of 512m.
- lvol: vg=firefly lv=testpool size=512m type=thin-pool

# Create thin lvol testthind with thin pool firefly/testpool,
# thin pool must already exist
- lvol: vg=firefly lv=testthind size=1g type=thin pool=firefly/testpool

# Extend thin pool to 2g,
- lvol: vg=firefly lv=testpool size=2g type=thin-pool

# Extend thin lvol to 5g
- lvol: vg=firefly lv=testthind size=5g type=thin pool=firefly/testpool

# Convert thin lvol to normal lvol
- lvol: vg=firefly lv=testthind size=5g type=normal force=yes

# Convert normal lvol to thin pool
- lvol: vg=firefly lv=testthind size=5g type=thin-pool force=yes

# Convert thin pool lvol to thin lvol, you should notice that firefly/testpool
# still exists
- lvol: vg=firefly lv=testthind size=5g type=thin pool=firefly/testpool force=yes

# Remove thin pool lvol, this also changes thin lvol to normal
- lvol: vg=firefly lv=testpool size=2g type=thin-pool state=absent force=yes
'''

import re
# import module snippets
from ansible.module_utils.basic import *

decimal_point = re.compile(r"(\d+\.?\d+)")

class Vg(object):

    name = ''
    size = None
    unit = 'm'
    free = None
    vg_extent_size = None
    module = None

    def __init__(self, module, vg_name, unit):
        self.module = module
        vg_info = self.get_vg_info(vg_name, unit)

        self.name = vg_info['name']
        self.size = vg_info['size']
        self.unit = unit
        self.free = vg_info['free']
        self.vg_extent_size = vg_info['vg_extent_size']

    def get_vg_info(self, vg_name, unit):
        vgs_cmd = self.module.get_bin_path("vgs", required=True)
        cmd = "%s --noheadings -o vg_name,size,free,vg_extent_size --units %s --separator ';' %s" % (vgs_cmd, unit, vg_name)

        rc, current_vgs, err = self.module.run_command(cmd)

        if rc != 0:
            self.module.fail_json(msg="Volume group %s does not exist." % vg_name, rc=rc, err=err)

        parts = current_vgs.strip().split(';')

        return {
            'name': parts[0],
            'size': float(decimal_point.match(parts[1]).group(1)),
            'free': float(decimal_point.match(parts[2]).group(1)),
            'vg_extent_size': float(decimal_point.match(parts[3]).group(1))
        }

class Lvol(object):

    name = ''
    size = None
    unit = 'm'
    pool_lv = ''
    vg = None
    yes_opt = ""
    module = None

    def __init__(self, module, vg_name, lv_name, unit, opts, pvs):
        self.vg = Vg(module, vg_name, unit)
        self.module = module

        lv_info = self.get_lv_info(vg_name, lv_name, unit)

        self.name = lv_info['name']
        self.pool_lv = lv_info['pool_lv']
        self.size = lv_info['size']
        self.unit = unit
        self.opts = opts
        self.pvs = pvs
        
        self.yes_opt = self.get_yes_opt(module)

    @classmethod
    def exists(cls, module, vg_name, lv_name):
        exists = False
        lvs_cmd = module.get_bin_path("lvs", required=True)

        rc, current_lv, err = module.run_command(
            "%s -a %s/%s" % (lvs_cmd, vg_name, lv_name)
        )

        if rc == 0:
            exists = True
        elif rc == 5 and "Failed to find logical volume" in err:
            exists = False
        else:
            module.fail_json(msg="Unexpected error", rc=rc, err=err)

        return exists

    @classmethod
    def is_thin_pool(cls, module, vg_name, lv_name):
        is_thin_pool = False
        lvs_cmd = module.get_bin_path("lvs", required=True)

        rc, current_lv, err = module.run_command(
            "%s -a --noheadings --nosuffix -o lv_layout --separator ';' %s/%s" % (lvs_cmd, vg_name, lv_name)
        )

        if rc != 0:
            module.fail_json(msg="Error", rc=rc, err=err)

        parts = current_lv.strip().split(';')

        if 'thin,pool' in parts[0]:
            is_thin_pool = True

        return is_thin_pool

    @classmethod
    def is_thin_lv(cls, module, vg_name, lv_name):
        is_thin_lv = False
        lvs_cmd = module.get_bin_path("lvs", required=True)

        rc, current_lv, err = module.run_command(
            "%s -a --noheadings --nosuffix -o lv_layout --separator ';' %s/%s" % (lvs_cmd, vg_name, lv_name)
        )

        if rc != 0:
            module.fail_json(msg="Error", rc=rc, err=err)

        parts = current_lv.strip().split(';')

        if 'thin' in parts[0] and 'pool' not in parts[0]:
            is_thin_lv = True

        return is_thin_lv

    @classmethod
    def mkversion(cls, major, minor, patch):
        return (1000 * 1000 * int(major)) + (1000 * int(minor)) + int(patch)

    @classmethod
    def get_lvm_version(cls, module):
        ver_cmd = module.get_bin_path("lvm", required=True)
        rc, out, err = module.run_command("%s version" % (ver_cmd))

        if rc != 0:
            return None

        m = re.search("LVM version:\s+(\d+)\.(\d+)\.(\d+).*(\d{4}-\d{2}-\d{2})", out)

        if not m:
            return None

        return cls.mkversion(m.group(1), m.group(2), m.group(3))

    def get_lv_info(self, vg_name, lv_name, unit):
        lvs_cmd = self.module.get_bin_path("lvs", required=True)

        rc, current_lvs, err = self.module.run_command(
            "%s -a --noheadings --nosuffix -o lv_name,size,pool_lv,cachemode --units %s --separator ';' %s/%s" % (lvs_cmd, unit, vg_name, lv_name)
        )

        if rc != 0:
            self.module.fail_json(msg="Volume group or lvol does not exist." % vg_name, rc=rc, err=err)

        parts = current_lvs.strip().split(';')

        return {
            'name': parts[0].replace('[','').replace(']',''),
            'size': float(decimal_point.match(parts[1]).group(1)),
            'pool_lv': parts[2].replace('[','').replace(']',''),
            'cachemode': parts[3]
        }

    @classmethod
    def get_yes_opt(cls, module):
        # Determine if the "--yes" option should be used
        version_found = cls.get_lvm_version(module)

        if version_found == None:
            module.fail_json(msg="Failed to get LVM version number")

        version_yesopt = cls.mkversion(2, 2, 99) # First LVM with the "--yes" option

        if version_found >= version_yesopt:
            yesopt = "--yes"
        else:
            yesopt = ""

        return yesopt

    @classmethod
    def get_size_opt(cls, requested_size):
        if '%' in requested_size:
            return 'l'
        else:
            return 'L'

    @classmethod
    def calculate_size(cls, vg_free, vg_size, lv_size, size):
        if '%' in size:
            parts = size.split('%', 1)
            size_percent = parts[0]

            size_whole = parts[1]

            if size_whole == 'VG' or size_whole == 'PVS':
               size_requested = float(size_percent) * float(vg_size) / 100
            else: # size_whole == 'FREE':
               size_requested = float(size_percent) * float(vg_free) / 100

            if '+' in size:
               size_requested += float(lv_size)
        else:
            size_requested = float(size[0:-1])

            if '+' in size:
               size_requested += float(lv_size)

        return size_requested

    @classmethod
    def create_lv(cls, module, requested_size, unit, opts, vg_name, lv_name, pvs):
        yes_opt = cls.get_yes_opt(module)
        
        lvcreate_cmd = module.get_bin_path("lvcreate", required=True)

        cmd = "%s %s -n %s -L %s%s %s %s %s" % (lvcreate_cmd, yes_opt, lv_name, requested_size, unit, opts, vg_name, pvs)

        rc, _, err = module.run_command(cmd)

        if rc != 0:
            module.fail_json(msg="Creating logical volume '%s' failed" % lv_name, rc=rc, err=err)

    @classmethod
    def delete_lv(cls, module, force, vg_name, lv_name):
        if not force:
            module.fail_json(msg="Sorry, no removal of logical volume %s without force=yes." % (lv_name))

        lvremove_cmd = module.get_bin_path("lvremove", required=True)
        rc, _, err = module.run_command("%s --force %s/%s" % (lvremove_cmd, vg_name, lv_name))

        if rc !=0 :
            module.fail_json(msg="Failed to remove logical volume %s/%s" % (vg_name, lv_name), rc=rc, err=err)

    def resize_common(self, tool, requested_size, pvs):
        cmd = "%s -L %s%s %s/%s %s" % (tool, requested_size, self.unit, self.vg.name, self.name, pvs)

        rc, out, err = self.module.run_command(cmd)

        if rc != 0:
            if "Reached maximum COW size" in out:
                self.module.fail_json(msg="Unable to resize %s to %s%s" % (self.name, requested_size, self.unit), rc=rc, err=err, out=out)
            elif "matches existing size" in err:
                self.module.exit_json(changed=False, vg=self.vg.name, lv=self.name, size=self.size)
            else:
                self.module.fail_json(msg="Unable to resize %s to %s%s" % (self.name, requested_size, self.unit), rc=rc, err=err)

    def shrink_lv(self, force, requested_size, pvs):
        if requested_size == 0:
            self.module.fail_json(msg="Sorry, no shrinking of %s to 0 permitted." % (self.name))
        elif not force:
            self.module.fail_json(msg="Sorry, no shrinking of %s without force=yes" % (self.name))
        else:
            tool = self.module.get_bin_path("lvreduce", required=True)
            tool = '%s %s' % (tool, '--force')

        self.resize_common(tool, requested_size, pvs)

    def extend_lv(self, requested_size, pvs):
        if (self.vg.free > 0)  and self.vg.free >= (requested_size - self.size):
            tool = self.module.get_bin_path("lvextend", required=True)
        else:
            self.module.fail_json(
                msg="Logical Volume %s could not be extended. Not enough free space left (%s%s required / %s%s available)"
                % (self.name, (requested_size -  self.size), self.unit, self.vg.free, self.unit)
            )

        self.resize_common(tool, requested_size, pvs)

    def resize_lv(self, force, requested_size, pvs):
        if self.size < requested_size:
            self.extend_lv(requested_size, pvs)
        elif self.size > requested_size + self.vg.vg_extent_size:  # more than an extent too large
            self.shrink_lv(force, requested_size, pvs)

        self.__init__(self.module, self.vg.name, self.name, self.unit, self.opts, self.pvs)

    def convert_to_thin(self, pool):
        lvconvert_cmd = self.module.get_bin_path("lvconvert", required=True)

        rc, out, err = self.module.run_command(
            "%s --type thin --thinpool %s %s/%s" % (lvconvert_cmd, pool, self.vg.name, self.name)
        )

        if rc != 0:
            self.module.fail_json(msg="Converting logical volume to thin LV '%s' failed" % self.name, rc=rc, err=err)

        return ThinLvol(self.module, self.vg.name, self.name, self.unit, self.opts, self.pvs)

    def convert_to_thin_pool(self, force):
        lvconvert_cmd = self.module.get_bin_path("lvconvert", required=True)
        yes_opt = self.get_yes_opt(self.module)

        if not force:
            self.module.fail_json(msg="Sorry, no conversion of %s to thin-pool without force=yes." % (self.name))

        rc, out, err = self.module.run_command(
            "%s %s --type thin-pool %s/%s" % (lvconvert_cmd, yes_opt, self.vg.name, self.name)
        )

        if rc != 0:
            self.module.fail_json(msg="Converting logical volume to thin pool '%s' failed" % self.name, rc=rc, err=err)

        return ThinPoolLvol(self.module, self.vg.name, self.name, self.unit, self.opts, self.pvs)

class ThinPoolLvol(Lvol):

    @classmethod
    def create_lv(cls, module, requested_size, unit, opts, vg_name, lv_name, pvs):
        opts += " --type thin-pool"
        
        super(ThinPoolLvol, cls).create_lv(module, requested_size, unit, opts, vg_name, lv_name, pvs)

    def get_thin_lvol_name(self):
        thin_lvol_info = None
        lvs_cmd = self.module.get_bin_path("lvs", required=True)

        rc, current_lvs, err = self.module.run_command(
            "%s -a --noheadings --nosuffix -o lv_name,size,pool_lv,lv_layout --units %s --separator ';' %s" % (lvs_cmd, self.unit, self.vg.name))

        if rc != 0:
            if state == 'absent':
                self.module.exit_json(changed=False, stdout="Volume group %s does not exist." % self.vg.name, stderr=False)
            else:
                self.module.fail_json(msg="Volume group %s does not exist." % self.vg.name, rc=rc, err=err)

        for line in current_lvs.splitlines():
            parts = line.strip().split(';')
            pool = parts[2].replace('[','').replace(']','')

            if pool == self.name:
                thin_lvol_info = parts[0].replace('[','').replace(']','')

        return thin_lvol_info

    def convert_to_thin(self, force, opts, pvs, pool):
        self.delete_lv(self.module, force, self.vg.name, self.name)
        ThinLvol.create_lv(self.module, self.size, self.unit, opts, self.vg.name, self.name, pvs, pool)
        
        return ThinLvol(self.module, self.vg.name, self.name, self.unit, self.opts, self.pvs)

    def convert_to_normal(self, force, opts, pvs):
        self.delete_lv(self.module, force, self.vg.name, self.name)
        Lvol.create_lv(self.module, self.size, self.unit, opts, self.vg.name, self.name, pvs)

        return Lvol(self.module, self.vg.name, self.name, self.unit, self.opts, self.pvs)

    def shrink_lv(self, force, requested_size, pvs):
        self.delete_lv(self.module, force, self.vg.name, self.name)
        self.create_lv(self.module, self.size, self.unit, self.opts, self.vg.name, self.name, self.pvs)
        
        self.__init__(self.module, self.vg.name, self.name, self.unit, self.opts, self.pvs)

        return self
    
class ThinLvol(Lvol):

    @classmethod
    def create_lv(cls, module, requested_size, unit, opts, vg_name, lv_name, pvs, pool):
        yes_opt = cls.get_yes_opt(module)
        opts += ' --thin-pool %s' % (pool)
        pvs = ''
        
        lvcreate_cmd = module.get_bin_path("lvcreate", required=True)

        cmd = "%s %s -n %s -V %s%s %s %s %s" % (lvcreate_cmd, yes_opt, lv_name, requested_size, unit, opts, vg_name, pvs)

        rc, _, err = module.run_command(cmd)

        if rc != 0:
            module.fail_json(msg="Creating logical volume '%s' failed" % lv_name, rc=rc, err=err)
            
    def convert_to_normal(self, force, opts, pvs):
        self.delete_lv(self.module, force, self.vg.name, self.name)
        Lvol.create_lv(self.module, self.size, self.unit, opts, self.vg.name, self.name, pvs)

        return Lvol(self.module, self.vg.name, self.name, self.unit, self.opts, self.pvs)

    def convert_to_thin_pool(self, force):
        lvol = self.convert_to_normal(force, self.opts, self.pvs)
        thinPoolLvol = lvol.convert_to_thin_pool(force)

        return thinPoolLvol

    def change_pool(self, pool, force, opts, pvs):
        lvol = self.convert_to_normal(force, opts, pvs)
        lvol.convert_to_thin(pool)

        self.__init__(self.module, self.vg.name, self.name, self.unit, self.opts, self.pvs)

def validate_size(module, size):
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

    if not '%' in size:
        if size[-1].lower() in 'bskmgtpe':
           size = size[0:-1]
        else:
            module.fail_json(msg="Invalid units for size: %s" % size)

        try:
           float(size)
           if not size[0].isdigit(): raise ValueError()
        except ValueError:
           module.fail_json(msg="Bad size specification of '%s'" % size)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(required=True),
            lv=dict(required=True),
            size=dict(type='str'),
            opts=dict(type='str'),
            state=dict(choices=["absent", "present"], default='present'),
            force=dict(type='bool', default='no'),
            pvs=dict(type='str'),
            type=dict(choices=["thin", "thin-pool", "normal"], default="normal"),
            pool=dict(type='str')
        ),
        supports_check_mode=True,
    )

    vg = module.params['vg']
    lv = module.params['lv']
    size = module.params['size']
    opts = module.params['opts']
    state = module.params['state']
    force = module.boolean(module.params['force'])
    pvs = module.params['pvs']
    type = module.params['type']
    pool = module.params['pool']

    if size: validate_size(module, size)

    if pvs is None:
        pvs = ""
    else:
        pvs = pvs.replace(",", " ")

    if opts is None:
        opts = ""

    # when no unit, megabytes by default
    if '%' in size:
        unit = 'm'
    else:
        unit = size[-1].lower()

    changed = False
    msg = ''

    if type == 'thin' and not pool:
        module.fail_json(msg="You must specify also pool when type is thin")

    if state == 'present' and not size:
        if not Lvol.exists(module, vg, lv):
            module.fail_json(msg="No size given.")
        else:
            module.exit_json(changed=False, vg=vg, lv=lv, size=vg)

    vg_obj = Vg(module, vg, unit)

    if not Lvol.exists(module, vg, lv):
        if state == 'present':
            if module.check_mode:
                changed = True
            else:
                requested_size = Lvol.calculate_size(vg_obj.free, vg_obj.size, 0, size)

                if type != "normal":
                    if type == 'thin':
                        ThinLvol.create_lv(module, requested_size, unit, opts, vg, lv, pvs, pool)
                    elif type == 'thin-pool':
                        ThinPoolLvol.create_lv(module, requested_size, unit, opts, vg, lv, pvs)
                else:
                    Lvol.create_lv(module, requested_size, unit, opts, vg, lv, pvs)

                changed = True
                msg="Volume %s/%s created" % (vg, lv)
    else:
        if state == 'absent':
            if module.check_mode:
                module.exit_json(changed=True)
            else:
                if Lvol.is_thin_lv(module, vg, lv):
                    thinLvol = ThinLvol(module, vg, lv, unit, opts, pvs)
                    lvol = thinLvol.convert_to_normal(force, opts, pvs)

                    changed = True
                    msg = "Volume %s converted to normal LV to %s." % (lv, size)

                Lvol.delete_lv(module, force, vg, lv)

                changed = True
                msg += "Volume %s/%s deleted." % (vg, lv)
        else:
            if module.check_mode:
                changed = True
            else:
                if type != "normal":
                    if type == 'thin':
                        if not Lvol.is_thin_lv(module, vg, lv):
                            if Lvol.is_thin_pool(module, vg, lv):
                                thinPoolLvol = ThinPoolLvol(module, vg, lv, unit, opts, pvs)
                                thinLvol = thinPoolLvol.convert_to_thin(force, opts, pvs, pool)
                            else:
                                lvol = Lvol(module, vg, lv, unit, opts, pvs)
                                thinLvol = lvol.convert_to_thin(pool)

                            changed = True
                            msg = "Volume %s converted to thin LV to %s." % (lv, size)
                        else:
                            thinLvol = ThinLvol(module, vg, lv, unit, opts, pvs)

                        requested_size = thinLvol.calculate_size(vg_obj.free, vg_obj.size, thinLvol.size, size)
                        lvol_size_min = thinLvol.size - vg_obj.vg_extent_size
                        lvol_size_max = thinLvol.size + vg_obj.vg_extent_size

                        current_pool = "%s/%s" % (thinLvol.vg.name, thinLvol.pool_lv)

                        if pool != current_pool:
                            thinLvol.change_pool(pool, force, opts, pvs)

                            changed = True
                            msg += "Changed pool of %s to %s." % (lv, pool)

                        if not (lvol_size_min <= requested_size <= lvol_size_max):
                            thinLvol.resize_lv(force, requested_size, pvs)

                            changed = True
                            msg += "Volume %s resized to %s." % (lv, size)

                    elif type == 'thin-pool':
                        if not Lvol.is_thin_pool(module, vg, lv):
                            if Lvol.is_thin_lv(module, vg, lv):
                                thinLvol = ThinLvol(module, vg, lv, unit, opts, pvs)
                                thinPoolLvol = thinLvol.convert_to_thin_pool(force)
                            else:
                                lvol = Lvol(module, vg, lv, unit, opts, pvs)
                                thinPoolLvol = lvol.convert_to_thin_pool(force)

                            changed = True
                            msg = "Volume %s converted to thin pool to %s." % (lv, size)
                        else:
                            thinPoolLvol = ThinPoolLvol(module, vg, lv, unit, opts, pvs)

                        requested_size = thinPoolLvol.calculate_size(vg_obj.free, vg_obj.size, thinPoolLvol.size, size)
                        lvol_size_min = thinPoolLvol.size - vg_obj.vg_extent_size
                        lvol_size_max = thinPoolLvol.size + vg_obj.vg_extent_size

                        if not (lvol_size_min <= requested_size <= lvol_size_max):
                            thinPoolLvol.resize_lv(force, requested_size, pvs)

                            changed = True
                            msg += "Volume %s resized to %s." % (lv, size)
                else:
                    if Lvol.is_thin_lv(module, vg, lv):
                            thinLvol = ThinLvol(module, vg, lv, unit, opts, pvs)
                            lvol = thinLvol.convert_to_normal(force, opts, pvs)

                            changed = True
                            msg = "Volume %s converted to normal LV to %s." % (lv, size)
                    elif Lvol.is_thin_pool(module, vg, lv):
                            thinPoolLvol = ThinPoolLvol(module, vg, lv, unit, opts, pvs)
                            thin_lvol_name = thinPoolLvol.get_thin_lvol_name()

                            if thin_lvol_name is not None:
                                thinLvol = ThinLvol(module, vg, thin_lvol_name, unit, opts, pvs)
                                lvol = thinLvol.convert_to_normal(force, opts, pvs)
                            else:
                                lvol = thinPoolLvol.convert_to_normal(force, opts, pvs)

                            changed = True
                            msg += "Volume %s converted to normal LV to %s." % (lv, size)
                    else:
                        lvol = Lvol(module, vg, lv, unit, opts, pvs)

                    requested_size = lvol.calculate_size(vg_obj.free, vg_obj.size, lvol.size, size)
                    lvol_size_min = lvol.size - vg_obj.vg_extent_size
                    lvol_size_max = lvol.size + vg_obj.vg_extent_size

                    if not (lvol_size_min <= requested_size <= lvol_size_max):
                        lvol.resize_lv(force, requested_size, pvs)

                        changed = True
                        msg += "Volume %s resized to %s." % (lv, size)

    module.exit_json(changed=changed, msg=msg)

if __name__ == '__main__':
    main()


