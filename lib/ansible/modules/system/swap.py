#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Pawel Szatkowski <pszatkowski.byd@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: swap

author:
    - Pawel Szatkowski (@pszatkowski)

short_description: Creates and activates swap, controls swap mounts in fstab.

description:
    - This module creates and activates swap, controls swap mounts in fstab.

version_added: "1.1"

options:
    device:
        description:
            - Device name that can be passed as path (/dev/sdx), uuid
              (UUID=440bb410-6b02-4ed6-81a8-68513761e772) or label
              (LABEL=swap01).
        required: true
    state:
        description:
            - If 'present', device will be swap formated, activated and added
              to fstab.
            - If 'absent', device will be de-activated and removed from fstab.
        choices: ['present', 'absent']
        required: true
    force:
        description:
            - If 'yes', overrides current device filesystem.
        choices: ['yes', 'no']
        default: 'no'
    options:
        description:
            - Mount options for fstab entry.
        default: 'none swap defaults 0 0'
    backup:
        description:
            - If 'yes', backup fstab file before change.
        choices: ['yes', 'no']
        default: 'no'
'''

EXAMPLES = '''
# Create swap on device /dev/sdx
- swap:
    device: /dev/sdx
    state: present

# Create swap on device that uuid is '440bb410-6b02-4ed6-81a8-68513761e772'.
- swap:
    device: UUID=440bb410-6b02-4ed6-81a8-68513761e772
    state: present

# Create swap on device labeled as 'swap01'
- swap:
    device: LABEL=swap01
    state: present

# Create swap on device /dev/sdx with custom fstab options and force filesystem
# override.
- swap:
    device: /dev/sdx
    state: present
    options: none swap sw 0 0
    force: yes

# Delete swap device /dev/sdx (do fstab backup before modification).
- swap:
    device: /dev/sdx
    state: present
    backup: yes
'''

import os
from ansible.module_utils.basic import AnsibleModule


class SwapModuleError(Exception):
    """
    Exception class for SwapModule.

    Attributes:
        msg (str): The error message.
        cmd (str): The OS command.
        rc (str): Command's return code.
        out (str): Command's standard output.
        err (str): Command's standard error.

    """

    def __init__(self, msg, cmd=None, rc=None, out=None, err=None):
        """
        Construct SwapModuleError object.

        Parameters:
            msg (str): The error message.
            cmd (str): The OS command.
            rc (str): The return code.
            out (str): Command's standard output.
            err (str): Command's standard error.

        """
        super(Exception, self).__init__(msg)
        self.msg = msg
        self.cmd = cmd
        self.rc = rc
        self.out = out
        self.err = err


class SwapModule():
    """
    Class provides code to create and delete swap space.

    Attributes:
        SWAPS (str): Path to swaps file.
        FSTAB (str): Path to fstab file.
        module (AnsibleModule): The helper class object.
        blkid_cmd (str): The blkid binary path.
        mkswap_cmd (str): The mkswap binary path.
        swapon_cmd (str): The swapon binary path.
        swapoff_cmd (str): The swapoff binary Path.
        cache (list): The cache for storing fstab lines.
        device (str): The device name (path, UUID or LABEL).
        device_path (str): The real path of a device.
        force (str): The 'yes/no' option for filesystem override.
        backup (str): The 'yes/no' option for fstab backup creation.
        options (str): The wihtespace separated fields (2-6) of fstab entry.

    """

    SWAPS = '/proc/swaps'
    FSTAB = '/etc/fstab'

    def __init__(self, module):
        """
        Construct SwapModule class object.

        Parameters:
            module (AnsibleModule): The helper class object.

        """
        self.module = module
        self.blkid_cmd = module.get_bin_path('blkid', required=True)
        self.mkswap_cmd = module.get_bin_path('mkswap', required=True)
        self.swapon_cmd = module.get_bin_path('swapon', required=True)
        self.swapoff_cmd = module.get_bin_path('swapoff', required=True)
        self.cache = None
        self.device = module.params['device']
        self.device_path = self.get_real_path()
        self.force = module.params['force']
        self.backup = module.params['backup']
        self.options = None

        self.read_fstab()
        self.get_options()

    def read_fstab(self):
        """Read fstab and write to 'cache' attribute."""
        try:
            with open(self.FSTAB, 'r') as fstab:
                self.cache = fstab.readlines()
        except IOError as io_error:
            raise SwapModuleError('%s' % io_error)

    def write_fstab(self):
        """Write 'cache' attribute to fstab."""
        try:
            with open(self.FSTAB, 'w') as fstab:
                for line in self.cache:
                    fstab.write(line)
        except IOError as io_error:
            raise SwapModuleError('%s' % io_error)

    def get_options(self):
        """Process options and write to 'options' attribute."""
        opts = self.module.params['options'].split()
        if len(opts) != 5:
            raise SwapModuleError(
                'Wrong fields specified! Required: fs_file, '
                'fs_vfstype, fs_mntops, fs_freq and fs_passno. See man '
                'fstab(5) for details.')
        self.options = [self.device] + opts

    def get_line_nr(self):
        """
        Check all fs_spec from cached fstab (1st fields) if match device.

        Comparision is done by real path of devices. If match, it records line
        number.

        Returns:
            list: Line numbers of matching fs_spec fields.

        """
        nr = []
        for index, line in enumerate(self.cache):
            try:
                in_fstab_device_path = self.get_real_path(line.split()[0])
            except SwapModuleError:
                # Path doesn't exist, so set empty string.
                in_fstab_device_path = ''
            if in_fstab_device_path == self.device_path:
                nr.append(index)
        return nr

    def get_real_path(self, device=None):
        """
        Get device real path.

        If device is not provided, class attribute 'device' is being used.
        Method supports device specified as a path, UUID or LABEL.

        Returns:
            str: Device real path.

        """
        if not device:
            device = self.device

        if 'UUID' in device:
            cmd = '%s %s %s' % (
                self.blkid_cmd, '-c /dev/null -U',
                # Ger rid off quotation marks to avoid open/close quotation
                # problems.
                device.split('=')[1].strip('\'\"'))
            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                raise SwapModuleError(
                    msg='Device with %s not found!' % (device),
                    cmd=cmd, rc=rc, err=err, out=out)
            return os.path.realpath(out.strip())
        elif 'LABEL' in device:
            cmd = '%s %s %s' % (
                self.blkid_cmd, '-c /dev/null -L',
                # Ger rid off quotation marks to avoid open/close quotation
                # problems.
                device.split('=')[1].strip('\'\"'))
            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                raise SwapModuleError(
                    msg='Device with %s not found!' % (device),
                    cmd=cmd, rc=rc, err=err, out=out)
            return os.path.realpath(out.strip())
        else:
            # Here device must be a path, otherwise it means that device syntax
            # is wrong.
            if not device.startswith('/'):
                raise SwapModuleError(
                    msg='Syntax error! Please check if '
                    'device %s is properly defined.' % (device))
            path = os.path.realpath(device)
            if not os.path.exists(path):
                raise SwapModuleError(msg='Device %s not found!' % (device))
            return path

    def get_fstype(self):
        """
        Get device filesystem type.

        Returns:
            str: Filesystem type.

        """
        cmd = '%s %s %s' % (
            self.blkid_cmd, '-c /dev/null -o value -s TYPE', self.device_path)
        rc, out, err = self.module.run_command(cmd)
        if rc == 0:
            return out.strip()
        # Command blkid returns 2 for not formated image files. If device path
        # is regular file, return None. Otherwise raise an error.
        elif rc == 2 and os.path.isfile(self.device_path):
            return None
        else:
            raise SwapModuleError(
                msg='Cannot identify fstype on %s!' % (self.device_path),
                cmd=cmd, rc=rc, stdout=out, stderr=err)

    def is_enabled(self):
        """
        Check if swapping is activated on device.

        Returns:
            bool: True if swap is enabled, otherwise False.

        """
        try:
            with open(self.SWAPS, 'r') as swaps:
                for line in swaps:
                    if self.device_path in line:
                        return True
        except IOError as e:
            raise SwapModuleError('%s' % e)
        return False

    def mkswap(self):
        """
        Make swap on device.

        If device is swap formated do nothing. If device has other filesystem
        type, check 'force' attribute first. If 'force' equals 'yes' then
        proceed, otherwise raise an error. Method supports ansible dry run.

        Returns:
            bool: True if change was/would be done, otherwise False.

        """
        changed = False
        fstype = self.get_fstype()
        if fstype == 'swap':
            changed = False
        elif not fstype:
            changed = True
            cmd = '%s %s' % (self.mkswap_cmd, self.device_path)
        elif fstype and self.force == 'yes':
            changed = True
            cmd = '%s %s %s' % (self.mkswap_cmd, '-f', self.device_path)
        elif fstype and self.force == 'no':
            raise SwapModuleError(
                msg='Device %s is already formatted as %s! Please use '
                'force=yes to overwrite.' % (self.device_path, fstype))

        if changed and not self.module.check_mode:
            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                raise SwapModuleError(
                    msg='Cannot set up swap area on %s!' % (self.device_path),
                    cmd=cmd, rc=rc, err=err, out=out)
        return changed

    def swapon(self):
        """
        Enable swapping on device.

        Method supports ansible dry run.

        Returns:
            bool: True if swap was/would be enabled, otherwise False.

        """
        changed = False
        if not self.is_enabled():
            changed = True

        if changed and not self.module.check_mode:
            cmd = '%s %s' % (self.swapon_cmd, self.device)
            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                raise SwapModuleError(
                    msg='Cannot enable swapping on %s!' % (self.device_path),
                    cmd=cmd, rc=rc, err=err, out=out)
        return changed

    def swapoff(self):
        """
        Disable swapping on device.

        Method supports ansible dry run.

        Returns:
            bool: True if swap was/would be disabled, otherwise False.

        """
        changed = False
        if self.is_enabled():
            changed = True

        if changed and not self.module.check_mode:
            cmd = '%s %s' % (self.swapoff_cmd, self.device_path)
            rc, out, err = self.module.run_command(cmd)
            if rc != 0:
                raise SwapModuleError(
                    msg='Cannot disable swapping on %s!' % (self.device_path),
                    cmd=cmd, rc=rc, err=err, out=out)
        return changed

    def fstab_add(self):
        """
        Add entry to fstab.

        If device is already in fstab, then check if match 'options' attribute
        and correct accordingly. In case of dupplicates, first line that match
        remains, the others are skipped and warning message is raised. Method
        supports ansible dry run.

        Returns:
            bool: True if entry was/would be added, otherwise False.

        """
        changed = False
        nr = self.get_line_nr()
        if len(nr) == 0:
            changed = True
            self.cache.append('%s\n' % ('\t'.join(self.options)))
        else:
            for x, y in zip(self.options, self.cache[nr[0]].split()):
                if x != y:
                    changed = True
                    self.cache[nr[0]] = '%s\n' % ('\t'.join(self.options))
            if len(nr) > 1:
                changed = True
                # First line recorded shoud remain, so skip first element in
                # slice.
                nr = nr[1:]
                # Pop operation makes that all indexes below removed item are
                # changed. Line numbers must be sorted in descending order to
                # make sure that lines will be removed from "the bottom".
                nr.sort(reverse=True)
                for idx in nr:
                    self.cache.pop(idx)
                self.module.warn(
                    'Removed duplicated entries of %s from %s'
                    % (self.device, self.FSTAB))

        if changed and not self.module.check_mode:
            if self.backup == 'yes':
                self.module.backup_local(self.FSTAB)
            self.write_fstab()
        return changed

    def fstab_rm(self):
        """
        Remove entry from fstab.

        Method supports ansible dry run.

        Returns:
            True if entry was/would be removed, otherwise False.

        """
        changed = False
        if len(self.get_line_nr()) > 0:
            changed = True

        if changed and not self.module.check_mode:
            if self.backup == 'yes':
                self.module.backup_local(self.FSTAB)
            new_fstab = []
            for line in self.cache:
                try:
                    in_fstab_device_path = self.get_real_path(
                        line.split()[0])
                except SwapModuleError:
                    # Path doesn't exist, so set empty string.
                    in_fstab_device_path = ''
                if self.device_path != in_fstab_device_path:
                    new_fstab.append(line)
            self.cache = new_fstab
            self.write_fstab()
        return changed


def main():
    """Execute main code."""
    module_args = dict(
        device=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], required=True),
        force=dict(type='str', choices=['yes', 'no'], default='no'),
        backup=dict(type='str', choices=['yes', 'no'], default='no'),
        options=dict(type='str', default='none swap defaults 0 0')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(changed=False)
    results = []

    try:
        swap_module = SwapModule(module)
        if module.params['state'] == 'present':
            results.append(swap_module.mkswap())
            results.append(swap_module.swapon())
            results.append(swap_module.fstab_add())
        elif module.params['state'] == 'absent':
            results.append(swap_module.swapoff())
            results.append(swap_module.fstab_rm())
    except SwapModuleError as error:
        module.fail_json(
            msg=error.msg, cmd=error.cmd, rc=error.rc, stdout=error.out,
            stderr=error.err)

    if True in results:
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
