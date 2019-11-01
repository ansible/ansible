#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Kairo Araujo <kairo@kairo.eti.br>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
author:
  - Kairo Araujo (@kairoaraujo)
module: aix_filesystem
short_description: Configure LVM and NFS file systems for AIX
description:
  - This module creates, removes, mount and unmount LVM and NFS file system for
    AIX using C(/etc/filesystems).
  - For LVM file systems is possible to resize a file system.
version_added: '2.8'
options:
  account_subsystem:
    description:
      - Specifies whether the file system is to be processed by the accounting subsystem.
    type: bool
    default: no
  attributes:
    description:
      - Specifies attributes for files system separated by comma.
    type: list
    default: agblksize='4096',isnapshot='no'
  auto_mount:
    description:
      - File system is automatically mounted at system restart.
    type: bool
    default: yes
  device:
    description:
      - Logical volume (LV) device name or remote export device to create a NFS file system.
      - It is used to create a file system on an already existing logical volume or the exported NFS file system.
      - If not mentioned a new logical volume name will be created following AIX standards (LVM).
    type: str
  fs_type:
    description:
      - Specifies the virtual file system type.
    type: str
    default: jfs2
  permissions:
    description:
      - Set file system permissions. C(rw) (read-write) or C(ro) (read-only).
    type: str
    choices: [ ro, rw ]
    default: rw
  mount_group:
    description:
      - Specifies the mount group.
    type: str
  filesystem:
    description:
      - Specifies the mount point, which is the directory where the file system will be mounted.
    type: str
    required: true
  nfs_server:
    description:
      - Specifies a Network File System (NFS) server.
    type: str
  rm_mount_point:
    description:
      - Removes the mount point directory when used with state C(absent).
    type: bool
    default: no
  size:
    description:
      - Specifies the file system size.
      - For already C(present) it will be resized.
      - 512-byte blocks, Megabytes or Gigabytes. If the value has M specified
        it will be in Megabytes. If the value has G specified it will be in
        Gigabytes.
      - If no M or G the value will be 512-byte blocks.
      - If "+" is specified in begin of value, the value will be added.
      - If "-" is specified in begin of value, the value will be removed.
      - If "+" or "-" is not specified, the total value will be the specified.
      - Size will respects the LVM AIX standards.
    type: str
  state:
    description:
      - Controls the file system state.
      - C(present) check if file system exists, creates or resize.
      - C(absent) removes existing file system if already C(unmounted).
      - C(mounted) checks if the file system is mounted or mount the file system.
      - C(unmounted) check if the file system is unmounted or unmount the file system.
    type: str
    required: true
    choices: [ absent, mounted, present, unmounted ]
    default: present
  vg:
    description:
      - Specifies an existing volume group (VG).
    type: str
notes:
  - For more C(attributes), please check "crfs" AIX manual.
'''

EXAMPLES = r'''
- name: Create filesystem in a previously defined logical volume.
  aix_filesystem:
    device: testlv
    filesystem: /testfs
    state: present

- name: Creating NFS filesystem from nfshost.
  aix_filesystem:
    device: /home/ftp
    nfs_server: nfshost
    filesystem: /home/ftp
    state: present

- name: Creating a new file system without a previously logical volume.
  aix_filesystem:
    filesystem: /newfs
    size: 1G
    state: present
    vg: datavg

- name: Unmounting /testfs.
  aix_filesystem:
    filesystem: /testfs
    state: unmounted

- name: Resizing /mksysb to +512M.
  aix_filesystem:
    filesystem: /mksysb
    size: +512M
    state: present

- name: Resizing /mksysb to 11G.
  aix_filesystem:
    filesystem: /mksysb
    size: 11G
    state: present

- name: Resizing /mksysb to -2G.
  aix_filesystem:
    filesystem: /mksysb
    size: -2G
    state: present

- name: Remove NFS filesystem /home/ftp.
  aix_filesystem:
    filesystem: /home/ftp
    rm_mount_point: yes
    state: absent

- name: Remove /newfs.
  aix_filesystem:
    filesystem: /newfs
    rm_mount_point: yes
    state: absent
'''

RETURN = r'''
changed:
  description: Return changed for aix_filesystems actions as true or false.
  returned: always
  type: bool
msg:
  description: Return message regarding the action.
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ismount import ismount
import re


def _fs_exists(module, filesystem):
    """
    Check if file system already exists on /etc/filesystems.

    :param module: Ansible module.
    :param filesystem: filesystem name.
    :return: True or False.
    """
    lsfs_cmd = module.get_bin_path('lsfs', True)
    rc, lsfs_out, err = module.run_command("%s -l %s" % (lsfs_cmd, filesystem))
    if rc == 1:
        if re.findall("No record matching", err):
            return False

        else:
            module.fail_json(msg="Failed to run lsfs. Error message: %s" % err)

    else:

        return True


def _check_nfs_device(module, nfs_host, device):
    """
    Validate if NFS server is exporting the device (remote export).

    :param module: Ansible module.
    :param nfs_host: nfs_host parameter, NFS server.
    :param device: device parameter, remote export.
    :return: True or False.
    """
    showmount_cmd = module.get_bin_path('showmount', True)
    rc, showmount_out, err = module.run_command(
        "%s -a %s" % (showmount_cmd, nfs_host))
    if rc != 0:
        module.fail_json(msg="Failed to run showmount. Error message: %s" % err)
    else:
        showmount_data = showmount_out.splitlines()
        for line in showmount_data:
            if line.split(':')[1] == device:
                return True

        return False


def _validate_vg(module, vg):
    """
    Check the current state of volume group.

    :param module: Ansible module argument spec.
    :param vg: Volume Group name.
    :return: True (VG in varyon state) or False (VG in varyoff state) or
             None (VG does not exist), message.
    """
    lsvg_cmd = module.get_bin_path('lsvg', True)
    rc, current_active_vgs, err = module.run_command("%s -o" % lsvg_cmd)
    if rc != 0:
        module.fail_json(msg="Failed executing %s command." % lsvg_cmd)

    rc, current_all_vgs, err = module.run_command("%s" % lsvg_cmd)
    if rc != 0:
        module.fail_json(msg="Failed executing %s command." % lsvg_cmd)

    if vg in current_all_vgs and vg not in current_active_vgs:
        msg = "Volume group %s is in varyoff state." % vg
        return False, msg
    elif vg in current_active_vgs:
        msg = "Volume group %s is in varyon state." % vg
        return True, msg
    else:
        msg = "Volume group %s does not exist." % vg
        return None, msg


def resize_fs(module, filesystem, size):
    """ Resize LVM file system. """

    chfs_cmd = module.get_bin_path('chfs', True)
    if not module.check_mode:
        rc, chfs_out, err = module.run_command('%s -a size="%s" %s' % (chfs_cmd, size, filesystem))

        if rc == 28:
            changed = False
            return changed, chfs_out
        elif rc != 0:
            if re.findall('Maximum allocation for logical', err):
                changed = False
                return changed, err
            else:
                module.fail_json(msg="Failed to run chfs. Error message: %s" % err)

        else:
            if re.findall('The filesystem size is already', chfs_out):
                changed = False
            else:
                changed = True

            return changed, chfs_out
    else:
        changed = True
        msg = ''

        return changed, msg


def create_fs(
        module, fs_type, filesystem, vg, device, size, mount_group, auto_mount,
        account_subsystem, permissions, nfs_server, attributes):
    """ Create LVM file system or NFS remote mount point. """

    attributes = ' -a '.join(attributes)

    # Parameters definition.
    account_subsys_opt = {
        True: '-t yes',
        False: '-t no'
    }

    if nfs_server is not None:
        auto_mount_opt = {
            True: '-A',
            False: '-a'
        }

    else:
        auto_mount_opt = {
            True: '-A yes',
            False: '-A no'
        }

    if size is None:
        size = ''
    else:
        size = "-a size=%s" % size

    if device is None:
        device = ''
    else:
        device = "-d %s" % device

    if vg is None:
        vg = ''
    else:
        vg_state, msg = _validate_vg(module, vg)
        if vg_state:
            vg = "-g %s" % vg
        else:
            changed = False

            return changed, msg

    if mount_group is None:
        mount_group = ''

    else:
        mount_group = "-u %s" % mount_group

    auto_mount = auto_mount_opt[auto_mount]
    account_subsystem = account_subsys_opt[account_subsystem]

    if nfs_server is not None:
        # Creates a NFS file system.
        mknfsmnt_cmd = module.get_bin_path('mknfsmnt', True)
        if not module.check_mode:
            rc, mknfsmnt_out, err = module.run_command('%s -f "%s" %s -h "%s" -t "%s" "%s" -w "bg"' % (
                mknfsmnt_cmd, filesystem, device, nfs_server, permissions, auto_mount))
            if rc != 0:
                module.fail_json(msg="Failed to run mknfsmnt. Error message: %s" % err)
            else:
                changed = True
                msg = "NFS file system %s created." % filesystem

                return changed, msg
        else:
            changed = True
            msg = ''

            return changed, msg

    else:
        # Creates a LVM file system.
        crfs_cmd = module.get_bin_path('crfs', True)
        if not module.check_mode:
            cmd = "%s -v %s -m %s %s %s %s %s %s -p %s %s -a %s" % (
                crfs_cmd, fs_type, filesystem, vg, device, mount_group, auto_mount, account_subsystem, permissions, size, attributes)
            rc, crfs_out, err = module.run_command(cmd)

            if rc == 10:
                module.exit_json(
                    msg="Using a existent previously defined logical volume, "
                        "volume group needs to be empty. %s" % err)

            elif rc != 0:
                module.fail_json(msg="Failed to run %s. Error message: %s" % (cmd, err))

            else:
                changed = True
                return changed, crfs_out
        else:
            changed = True
            msg = ''

            return changed, msg


def remove_fs(module, filesystem, rm_mount_point):
    """ Remove an LVM file system or NFS entry. """

    # Command parameters.
    rm_mount_point_opt = {
        True: '-r',
        False: ''
    }

    rm_mount_point = rm_mount_point_opt[rm_mount_point]

    rmfs_cmd = module.get_bin_path('rmfs', True)
    if not module.check_mode:
        cmd = "%s -r %s %s" % (rmfs_cmd, rm_mount_point, filesystem)
        rc, rmfs_out, err = module.run_command(cmd)
        if rc != 0:
            module.fail_json(msg="Failed to run %s. Error message: %s" % (cmd, err))
        else:
            changed = True
            msg = rmfs_out
            if not rmfs_out:
                msg = "File system %s removed." % filesystem

            return changed, msg
    else:
        changed = True
        msg = ''

        return changed, msg


def mount_fs(module, filesystem):
    """ Mount a file system. """
    mount_cmd = module.get_bin_path('mount', True)

    if not module.check_mode:
        rc, mount_out, err = module.run_command(
            "%s %s" % (mount_cmd, filesystem))
        if rc != 0:
            module.fail_json(msg="Failed to run mount. Error message: %s" % err)
        else:
            changed = True
            msg = "File system %s mounted." % filesystem

            return changed, msg
    else:
        changed = True
        msg = ''

        return changed, msg


def unmount_fs(module, filesystem):
    """ Unmount a file system."""
    unmount_cmd = module.get_bin_path('unmount', True)

    if not module.check_mode:
        rc, unmount_out, err = module.run_command("%s %s" % (unmount_cmd, filesystem))
        if rc != 0:
            module.fail_json(msg="Failed to run unmount. Error message: %s" % err)
        else:
            changed = True
            msg = "File system %s unmounted." % filesystem

            return changed, msg
    else:
        changed = True
        msg = ''

        return changed, msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_subsystem=dict(type='bool', default=False),
            attributes=dict(type='list', default=["agblksize='4096'", "isnapshot='no'"]),
            auto_mount=dict(type='bool', default=True),
            device=dict(type='str'),
            filesystem=dict(type='str', required=True),
            fs_type=dict(type='str', default='jfs2'),
            permissions=dict(type='str', default='rw', choices=['rw', 'ro']),
            mount_group=dict(type='str'),
            nfs_server=dict(type='str'),
            rm_mount_point=dict(type='bool', default=False),
            size=dict(type='str'),
            state=dict(type='str', default='present', choices=['absent', 'mounted', 'present', 'unmounted']),
            vg=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    account_subsystem = module.params['account_subsystem']
    attributes = module.params['attributes']
    auto_mount = module.params['auto_mount']
    device = module.params['device']
    fs_type = module.params['fs_type']
    permissions = module.params['permissions']
    mount_group = module.params['mount_group']
    filesystem = module.params['filesystem']
    nfs_server = module.params['nfs_server']
    rm_mount_point = module.params['rm_mount_point']
    size = module.params['size']
    state = module.params['state']
    vg = module.params['vg']

    result = dict(
        changed=False,
        msg='',
    )

    if state == 'present':
        fs_mounted = ismount(filesystem)
        fs_exists = _fs_exists(module, filesystem)

        # Check if fs is mounted or exists.
        if fs_mounted or fs_exists:
            result['msg'] = "File system %s already exists." % filesystem
            result['changed'] = False

            # If parameter size was passed, resize fs.
            if size is not None:
                result['changed'], result['msg'] = resize_fs(module, filesystem, size)

        # If fs doesn't exist, create it.
        else:
            # Check if fs will be a NFS device.
            if nfs_server is not None:
                if device is None:
                    result['msg'] = 'Parameter "device" is required when "nfs_server" is defined.'
                    module.fail_json(**result)
                else:
                    # Create a fs from NFS export.
                    if _check_nfs_device(module, nfs_server, device):
                        result['changed'], result['msg'] = create_fs(
                            module, fs_type, filesystem, vg, device, size, mount_group, auto_mount, account_subsystem, permissions, nfs_server, attributes)

            if device is None:
                if vg is None:
                    result['msg'] = 'Required parameter "device" and/or "vg" is missing for filesystem creation.'
                    module.fail_json(**result)
                else:
                    # Create a fs from
                    result['changed'], result['msg'] = create_fs(
                        module, fs_type, filesystem, vg, device, size, mount_group, auto_mount, account_subsystem, permissions, nfs_server, attributes)

            if device is not None and nfs_server is None:
                # Create a fs from a previously lv device.
                result['changed'], result['msg'] = create_fs(
                    module, fs_type, filesystem, vg, device, size, mount_group, auto_mount, account_subsystem, permissions, nfs_server, attributes)

    elif state == 'absent':
        if ismount(filesystem):
            result['msg'] = "File system %s mounted." % filesystem

        else:
            fs_status = _fs_exists(module, filesystem)
            if not fs_status:
                result['msg'] = "File system %s does not exist." % filesystem
            else:
                result['changed'], result['msg'] = remove_fs(module, filesystem, rm_mount_point)

    elif state == 'mounted':
        if ismount(filesystem):
            result['changed'] = False
            result['msg'] = "File system %s already mounted." % filesystem
        else:
            result['changed'], result['msg'] = mount_fs(module, filesystem)

    elif state == 'unmounted':
        if not ismount(filesystem):
            result['changed'] = False
            result['msg'] = "File system %s already unmounted." % filesystem
        else:
            result['changed'], result['msg'] = unmount_fs(module, filesystem)

    else:
        # Unreachable codeblock
        result['msg'] = "Unexpected state %s." % state
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
