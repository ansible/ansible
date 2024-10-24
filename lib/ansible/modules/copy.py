# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: copy
version_added: historical
short_description: Copy files to remote locations
description:
    - The M(ansible.builtin.copy) module copies a file or a directory structure from the local or remote machine to a location on the remote machine.
      File system meta-information (permissions, ownership, etc.) may be set, even when the file or directory already exists on the target system.
      Some meta-information may be copied on request.
    - Get meta-information with the M(ansible.builtin.stat) module.
    - Set meta-information with the M(ansible.builtin.file) module.
    - Use the M(ansible.builtin.fetch) module to copy files from remote locations to the local box.
    - If you need variable interpolation in copied files, use the M(ansible.builtin.template) module.
      Using a variable with the O(content) parameter produces unpredictable results.
    - For Windows targets, use the M(ansible.windows.win_copy) module instead.
options:
  src:
    description:
    - Local path to a file to copy to the remote server.
    - This can be absolute or relative.
    - If path is a directory, it is copied recursively. In this case, if path ends
      with C(/), only inside contents of that directory are copied to destination.
      Otherwise, if it does not end with C(/), the directory itself with all contents
      is copied. This behavior is similar to the C(rsync) command line tool.
    type: path
  content:
    description:
    - When used instead of O(src), sets the contents of a file directly to the specified value.
    - Works only when O(dest) is a file. Creates the file if it does not exist.
    - For advanced formatting or if O(content) contains a variable, use the
      M(ansible.builtin.template) module.
    type: str
    version_added: '1.1'
  dest:
    description:
    - Remote absolute path where the file should be copied to.
    - If O(src) is a directory, this must be a directory too.
    - If O(dest) is a non-existent path and if either O(dest) ends with C(/) or O(src) is a directory, O(dest) is created.
    - If O(dest) is a relative path, the starting directory is determined by the remote host.
    - If O(src) and O(dest) are files, the parent directory of O(dest) is not created and the task fails if it does not already exist.
    type: path
    required: yes
  backup:
    description:
    - Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
    version_added: '0.7'
  force:
    description:
    - Influence whether the remote file must always be replaced.
    - If V(true), the remote file will be replaced when contents are different than the source.
    - If V(false), the file will only be transferred if the destination does not exist.
    type: bool
    default: yes
    version_added: '1.1'
  mode:
    description:
    - The permissions of the destination file or directory.
    - For those used to C(/usr/bin/chmod) remember that modes are actually octal numbers.
      You must either add a leading zero so that Ansible's YAML parser knows it is an octal number
      (like V(0644) or V(01777)) or quote it (like V('644') or V('1777')) so Ansible receives a string
      and can do its own conversion from string into number. Giving Ansible a number without following
      one of these rules will end up with a decimal number which will have unexpected results.
    - As of Ansible 1.8, the mode may be specified as a symbolic mode (for example, V(u+rwx) or V(u=rw,g=r,o=r)).
    - As of Ansible 2.3, the mode may also be the special string V(preserve).
    - V(preserve) means that the file will be given the same permissions as the source file.
    - When doing a recursive copy, see also O(directory_mode).
    - If O(mode) is not specified and the destination file B(does not) exist, the default C(umask) on the system will be used
      when setting the mode for the newly created file.
    - If O(mode) is not specified and the destination file B(does) exist, the mode of the existing file will be used.
    - Specifying O(mode) is the best way to ensure files are created with the correct permissions.
      See CVE-2020-1736 for further details.
  directory_mode:
    description:
    - Set the access permissions of newly created directories to the given mode.
      Permissions on existing directories do not change.
    - See O(mode) for the syntax of accepted values.
    - The target system's defaults determine permissions when this parameter is not set.
    type: raw
    version_added: '1.5'
  remote_src:
    description:
    - Influence whether O(src) needs to be transferred or already is present remotely.
    - If V(false), it will search for O(src) on the controller node.
    - If V(true), it will search for O(src) on the managed (remote) node.
    - O(remote_src) supports recursive copying as of version 2.8.
    - O(remote_src) only works with O(mode=preserve) as of version 2.6.
    - Auto-decryption of files does not work when O(remote_src=yes).
    type: bool
    default: no
    version_added: '2.0'
  follow:
    description:
    - This flag indicates that filesystem links in the destination, if they exist, should be followed.
    type: bool
    default: no
    version_added: '1.8'
  local_follow:
    description:
    - This flag indicates that filesystem links in the source tree, if they exist, should be followed.
    type: bool
    version_added: '2.4'
  checksum:
    description:
    - SHA256 checksum of the file being transferred.
    - Used to validate that the copy of the file was successful.
    - If this is not provided, ansible will use the local calculated checksum of the src file.
    - Ansible 2.19 and onwards, SHA256 is default instead of SHA1.
    type: str
    version_added: '2.5'
extends_documentation_fragment:
    - decrypt
    - files
    - validate
    - action_common_attributes
    - action_common_attributes.files
    - action_common_attributes.flow
notes:
    - The M(ansible.builtin.copy) module recursively copy facility does not scale to lots (>hundreds) of files.
seealso:
    - module: ansible.builtin.assemble
    - module: ansible.builtin.fetch
    - module: ansible.builtin.file
    - module: ansible.builtin.template
    - module: ansible.posix.synchronize
    - module: ansible.windows.win_copy
author:
    - Ansible Core Team
    - Michael DeHaan
attributes:
  action:
    support: full
  async:
    support: none
  bypass_host_loop:
    support: none
  check_mode:
    support: full
  diff_mode:
    support: full
  platform:
    platforms: posix
  safe_file_operations:
      support: full
  vault:
    support: full
    version_added: '2.2'
"""

EXAMPLES = r"""
- name: Copy file with owner and permissions
  ansible.builtin.copy:
    src: /srv/myfiles/foo.conf
    dest: /etc/foo.conf
    owner: foo
    group: foo
    mode: '0644'

- name: Copy file with owner and permission, using symbolic representation
  ansible.builtin.copy:
    src: /srv/myfiles/foo.conf
    dest: /etc/foo.conf
    owner: foo
    group: foo
    mode: u=rw,g=r,o=r

- name: Another symbolic mode example, adding some permissions and removing others
  ansible.builtin.copy:
    src: /srv/myfiles/foo.conf
    dest: /etc/foo.conf
    owner: foo
    group: foo
    mode: u+rw,g-wx,o-rwx

- name: Copy a new "ntp.conf" file into place, backing up the original if it differs from the copied version
  ansible.builtin.copy:
    src: /mine/ntp.conf
    dest: /etc/ntp.conf
    owner: root
    group: root
    mode: '0644'
    backup: yes

- name: Copy a new "sudoers" file into place, after passing validation with visudo
  ansible.builtin.copy:
    src: /mine/sudoers
    dest: /etc/sudoers
    validate: /usr/sbin/visudo -csf %s

- name: Copy a "sudoers" file on the remote machine for editing
  ansible.builtin.copy:
    src: /etc/sudoers
    dest: /etc/sudoers.edit
    remote_src: yes
    validate: /usr/sbin/visudo -csf %s

- name: Copy using inline content
  ansible.builtin.copy:
    content: '# This file was moved to /etc/other.conf'
    dest: /etc/mine.conf

- name: If follow=yes, /path/to/file will be overwritten by contents of foo.conf
  ansible.builtin.copy:
    src: /etc/foo.conf
    dest: /path/to/link  # link to /path/to/file
    follow: yes

- name: If follow=no, /path/to/link will become a file and be overwritten by contents of foo.conf
  ansible.builtin.copy:
    src: /etc/foo.conf
    dest: /path/to/link  # link to /path/to/file
    follow: no
"""

RETURN = r"""
dest:
    description: Destination file/path.
    returned: success
    type: str
    sample: /path/to/file.txt
src:
    description: Source file used for the copy on the target machine.
    returned: changed
    type: str
    sample: /home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source
md5sum:
    description: MD5 checksum of the file after running copy.
    returned: when supported
    type: str
    sample: 2a5aeecc61dc98c4d780b14b330e3282
checksum:
    description: SHA256 checksum of the file after running copy.
    returned: success
    type: str
    sample: e1ace7b1f177f35749523ce34721d2b1e1ad0b1e3196754f476a69730d24cb53
backup_file:
    description: Name of backup file created.
    returned: changed and if backup=yes
    type: str
    sample: /path/to/file.txt.2015-02-12@22:09~
gid:
    description: Group id of the file, after execution.
    returned: success
    type: int
    sample: 100
group:
    description: Group of the file, after execution.
    returned: success
    type: str
    sample: httpd
owner:
    description: Owner of the file, after execution.
    returned: success
    type: str
    sample: httpd
uid:
    description: Owner id of the file, after execution.
    returned: success
    type: int
    sample: 100
mode:
    description: Permissions of the target, after execution.
    returned: success
    type: str
    sample: '0644'
size:
    description: Size of the target, after execution.
    returned: success
    type: int
    sample: 1220
state:
    description: State of the target, after execution.
    returned: success
    type: str
    sample: file
"""

import errno
import filecmp
import grp
import os
import os.path
import pwd
import shutil
import stat
import tempfile
import traceback

from ansible.module_utils.common.text.converters import to_bytes, to_native
from ansible.module_utils.basic import AnsibleModule


class AnsibleModuleError(Exception):
    def __init__(self, results):
        self.results = results


def split_pre_existing_dir(dirname):
    """
    Return the first pre-existing directory and a list of the new directories that will be created.
    """
    head, tail = os.path.split(dirname)
    b_head = to_bytes(head, errors='surrogate_or_strict')
    if head == '':
        return ('.', [tail])
    if not os.path.exists(b_head):
        if head == '/':
            raise AnsibleModuleError(results={'msg': "The '/' directory doesn't exist on this machine."})
        (pre_existing_dir, new_directory_list) = split_pre_existing_dir(head)
    else:
        return (head, [tail])
    new_directory_list.append(tail)
    return (pre_existing_dir, new_directory_list)


def adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed):
    """
    Walk the new directories list and make sure that permissions are as we would expect
    """

    if new_directory_list:
        working_dir = os.path.join(pre_existing_dir, new_directory_list.pop(0))
        directory_args['path'] = working_dir
        changed = module.set_fs_attributes_if_different(directory_args, changed)
        changed = adjust_recursive_directory_permissions(working_dir, new_directory_list, module, directory_args, changed)
    return changed


def chown_recursive(path, module):
    changed = False
    owner = module.params['owner']
    group = module.params['group']

    if owner is not None:
        if not module.check_mode:
            for dirpath, dirnames, filenames in os.walk(path):
                owner_changed = module.set_owner_if_different(dirpath, owner, False)
                if owner_changed is True:
                    changed = owner_changed
                for dir in [os.path.join(dirpath, d) for d in dirnames]:
                    owner_changed = module.set_owner_if_different(dir, owner, False)
                    if owner_changed is True:
                        changed = owner_changed
                for file in [os.path.join(dirpath, f) for f in filenames]:
                    owner_changed = module.set_owner_if_different(file, owner, False)
                    if owner_changed is True:
                        changed = owner_changed
        else:
            uid = pwd.getpwnam(owner).pw_uid
            for dirpath, dirnames, filenames in os.walk(path):
                owner_changed = (os.stat(dirpath).st_uid != uid)
                if owner_changed is True:
                    changed = owner_changed
                for dir in [os.path.join(dirpath, d) for d in dirnames]:
                    owner_changed = (os.stat(dir).st_uid != uid)
                    if owner_changed is True:
                        changed = owner_changed
                for file in [os.path.join(dirpath, f) for f in filenames]:
                    owner_changed = (os.stat(file).st_uid != uid)
                    if owner_changed is True:
                        changed = owner_changed
    if group is not None:
        if not module.check_mode:
            for dirpath, dirnames, filenames in os.walk(path):
                group_changed = module.set_group_if_different(dirpath, group, False)
                if group_changed is True:
                    changed = group_changed
                for dir in [os.path.join(dirpath, d) for d in dirnames]:
                    group_changed = module.set_group_if_different(dir, group, False)
                    if group_changed is True:
                        changed = group_changed
                for file in [os.path.join(dirpath, f) for f in filenames]:
                    group_changed = module.set_group_if_different(file, group, False)
                    if group_changed is True:
                        changed = group_changed
        else:
            gid = grp.getgrnam(group).gr_gid
            for dirpath, dirnames, filenames in os.walk(path):
                group_changed = (os.stat(dirpath).st_gid != gid)
                if group_changed is True:
                    changed = group_changed
                for dir in [os.path.join(dirpath, d) for d in dirnames]:
                    group_changed = (os.stat(dir).st_gid != gid)
                    if group_changed is True:
                        changed = group_changed
                for file in [os.path.join(dirpath, f) for f in filenames]:
                    group_changed = (os.stat(file).st_gid != gid)
                    if group_changed is True:
                        changed = group_changed

    return changed


def copy_diff_files(src, dest, module):
    """Copy files that are different between `src` directory and `dest` directory."""

    changed = False
    owner = module.params['owner']
    group = module.params['group']
    local_follow = module.params['local_follow']
    diff_files = filecmp.dircmp(src, dest).diff_files
    if len(diff_files):
        changed = True
    if not module.check_mode:
        for item in diff_files:
            src_item_path = os.path.join(src, item)
            dest_item_path = os.path.join(dest, item)
            b_src_item_path = to_bytes(src_item_path, errors='surrogate_or_strict')
            b_dest_item_path = to_bytes(dest_item_path, errors='surrogate_or_strict')
            if os.path.islink(b_src_item_path) and local_follow is False:
                linkto = os.readlink(b_src_item_path)
                os.symlink(linkto, b_dest_item_path)
            else:
                shutil.copyfile(b_src_item_path, b_dest_item_path)
                shutil.copymode(b_src_item_path, b_dest_item_path)

            if owner is not None:
                module.set_owner_if_different(b_dest_item_path, owner, False)
            if group is not None:
                module.set_group_if_different(b_dest_item_path, group, False)
            changed = True
    return changed


def copy_left_only(src, dest, module):
    """Copy files that exist in `src` directory only to the `dest` directory."""

    changed = False
    owner = module.params['owner']
    group = module.params['group']
    local_follow = module.params['local_follow']
    left_only = filecmp.dircmp(src, dest).left_only
    if len(left_only):
        changed = True
    if not module.check_mode:
        for item in left_only:
            src_item_path = os.path.join(src, item)
            dest_item_path = os.path.join(dest, item)
            b_src_item_path = to_bytes(src_item_path, errors='surrogate_or_strict')
            b_dest_item_path = to_bytes(dest_item_path, errors='surrogate_or_strict')

            if os.path.islink(b_src_item_path) and os.path.isdir(b_src_item_path) and local_follow is True:
                shutil.copytree(b_src_item_path, b_dest_item_path, symlinks=not local_follow)
                chown_recursive(b_dest_item_path, module)

            if os.path.islink(b_src_item_path) and os.path.isdir(b_src_item_path) and local_follow is False:
                linkto = os.readlink(b_src_item_path)
                os.symlink(linkto, b_dest_item_path)

            if os.path.islink(b_src_item_path) and os.path.isfile(b_src_item_path) and local_follow is True:
                shutil.copyfile(b_src_item_path, b_dest_item_path)
                if owner is not None:
                    module.set_owner_if_different(b_dest_item_path, owner, False)
                if group is not None:
                    module.set_group_if_different(b_dest_item_path, group, False)

            if os.path.islink(b_src_item_path) and os.path.isfile(b_src_item_path) and local_follow is False:
                linkto = os.readlink(b_src_item_path)
                os.symlink(linkto, b_dest_item_path)

            if not os.path.islink(b_src_item_path) and os.path.isfile(b_src_item_path):
                shutil.copyfile(b_src_item_path, b_dest_item_path)
                shutil.copymode(b_src_item_path, b_dest_item_path)

                if owner is not None:
                    module.set_owner_if_different(b_dest_item_path, owner, False)
                if group is not None:
                    module.set_group_if_different(b_dest_item_path, group, False)

            if not os.path.islink(b_src_item_path) and os.path.isdir(b_src_item_path):
                shutil.copytree(b_src_item_path, b_dest_item_path, symlinks=not local_follow)
                chown_recursive(b_dest_item_path, module)

            changed = True
    return changed


def copy_common_dirs(src, dest, module):
    changed = False
    common_dirs = filecmp.dircmp(src, dest).common_dirs
    for item in common_dirs:
        src_item_path = os.path.join(src, item)
        dest_item_path = os.path.join(dest, item)
        b_src_item_path = to_bytes(src_item_path, errors='surrogate_or_strict')
        b_dest_item_path = to_bytes(dest_item_path, errors='surrogate_or_strict')
        diff_files_changed = copy_diff_files(b_src_item_path, b_dest_item_path, module)
        left_only_changed = copy_left_only(b_src_item_path, b_dest_item_path, module)
        if diff_files_changed or left_only_changed:
            changed = True

        # recurse into subdirectory
        changed = copy_common_dirs(os.path.join(src, item), os.path.join(dest, item), module) or changed
    return changed


def main():

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            src=dict(type='path'),
            _original_basename=dict(type='str'),  # used to handle 'dest is a directory' via template, a slight hack
            content=dict(type='str', no_log=True),
            dest=dict(type='path', required=True),
            backup=dict(type='bool', default=False),
            force=dict(type='bool', default=True),
            validate=dict(type='str'),
            directory_mode=dict(type='raw'),
            remote_src=dict(type='bool', default=False),
            local_follow=dict(type='bool'),
            checksum=dict(type='str'),
            follow=dict(type='bool', default=False),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    src = module.params['src']
    b_src = to_bytes(src, errors='surrogate_or_strict')
    dest = module.params['dest']
    # Make sure we always have a directory component for later processing
    if os.path.sep not in dest:
        dest = '.{0}{1}'.format(os.path.sep, dest)
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    backup = module.params['backup']
    force = module.params['force']
    _original_basename = module.params.get('_original_basename', None)
    validate = module.params.get('validate', None)
    follow = module.params['follow']
    local_follow = module.params['local_follow']
    mode = module.params['mode']
    owner = module.params['owner']
    group = module.params['group']
    remote_src = module.params['remote_src']
    checksum = module.params['checksum']

    if not os.path.exists(b_src):
        module.fail_json(msg="Source %s not found" % (src))
    if not os.access(b_src, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (src))

    # Preserve is usually handled in the action plugin but mode + remote_src has to be done on the
    # remote host
    if module.params['mode'] == 'preserve':
        module.params['mode'] = '0%03o' % stat.S_IMODE(os.stat(b_src).st_mode)
    mode = module.params['mode']

    changed = False

    checksum_dest = None
    checksum_src = None
    md5sum_src = None

    if os.path.isfile(src):
        try:
            checksum_src = module.sha256(src)
        except (OSError, IOError) as e:
            module.warn(f"Unable to calculate src checksum, assuming change: {to_native(e)}")
        try:
            # Backwards compat only.  This will be None in FIPS mode
            md5sum_src = module.md5(src)
        except ValueError:
            pass
    elif remote_src and not os.path.isdir(src):
        module.fail_json("Cannot copy invalid source '%s': not a file" % to_native(src))

    if checksum and checksum_src != checksum:
        module.fail_json(
            msg='Copied file does not match the expected checksum. Transfer failed.',
            checksum=checksum_src,
            expected_checksum=checksum
        )

    # Special handling for recursive copy - create intermediate dirs
    if dest.endswith(os.sep):
        if _original_basename:
            dest = os.path.join(dest, _original_basename)
        b_dest = to_bytes(dest, errors='surrogate_or_strict')
        dirname = os.path.dirname(dest)
        b_dirname = to_bytes(dirname, errors='surrogate_or_strict')
        if not os.path.exists(b_dirname):
            try:
                (pre_existing_dir, new_directory_list) = split_pre_existing_dir(dirname)
            except AnsibleModuleError as e:
                e.result['msg'] += ' Could not copy to {0}'.format(dest)
                module.fail_json(**e.results)

            if module.check_mode:
                module.exit_json(msg='dest directory %s would be created' % dirname, changed=True, src=src)
            os.makedirs(b_dirname)
            changed = True
            directory_args = module.load_file_common_arguments(module.params)
            directory_mode = module.params["directory_mode"]
            if directory_mode is not None:
                directory_args['mode'] = directory_mode
            else:
                directory_args['mode'] = None
            adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed)

    if os.path.isdir(b_dest):
        basename = os.path.basename(src)
        if _original_basename:
            basename = _original_basename
        dest = os.path.join(dest, basename)
        b_dest = to_bytes(dest, errors='surrogate_or_strict')

    if os.path.exists(b_dest):
        if os.path.islink(b_dest) and follow:
            b_dest = os.path.realpath(b_dest)
            dest = to_native(b_dest, errors='surrogate_or_strict')
        if not force:
            module.exit_json(msg="file already exists", src=src, dest=dest, changed=False)
        if os.access(b_dest, os.R_OK) and os.path.isfile(b_dest):
            checksum_dest = module.sha1(dest)
    else:
        if not os.path.exists(os.path.dirname(b_dest)):
            try:
                # os.path.exists() can return false in some
                # circumstances where the directory does not have
                # the execute bit for the current user set, in
                # which case the stat() call will raise an OSError
                os.stat(os.path.dirname(b_dest))
            except OSError as e:
                if "permission denied" in to_native(e).lower():
                    module.fail_json(msg="Destination directory %s is not accessible" % (os.path.dirname(dest)))
            module.fail_json(msg="Destination directory %s does not exist" % (os.path.dirname(dest)))

    if not os.access(os.path.dirname(b_dest), os.W_OK) and not module.params['unsafe_writes']:
        module.fail_json(msg="Destination %s not writable" % (os.path.dirname(dest)))

    backup_file = None
    if checksum_src != checksum_dest or os.path.islink(b_dest):

        if not module.check_mode:
            try:
                if backup:
                    if os.path.exists(b_dest):
                        backup_file = module.backup_local(dest)
                # allow for conversion from symlink.
                if os.path.islink(b_dest):
                    os.unlink(b_dest)
                    open(b_dest, 'w').close()
                if validate:
                    # if we have a mode, make sure we set it on the temporary
                    # file source as some validations may require it
                    if mode is not None:
                        module.set_mode_if_different(src, mode, False)
                    if owner is not None:
                        module.set_owner_if_different(src, owner, False)
                    if group is not None:
                        module.set_group_if_different(src, group, False)
                    if "%s" not in validate:
                        module.fail_json(msg="validate must contain %%s: %s" % (validate))
                    (rc, out, err) = module.run_command(validate % src)
                    if rc != 0:
                        module.fail_json(msg="failed to validate", exit_status=rc, stdout=out, stderr=err)

                b_mysrc = b_src
                if remote_src and os.path.isfile(b_src):

                    dummy, b_mysrc = tempfile.mkstemp(dir=os.path.dirname(b_dest))

                    shutil.copyfile(b_src, b_mysrc)
                    try:
                        shutil.copystat(b_src, b_mysrc)
                    except OSError as err:
                        if err.errno == errno.ENOSYS and mode == "preserve":
                            module.warn("Unable to copy stats {0}".format(to_native(b_src)))
                        else:
                            raise

                # at this point we should always have tmp file
                module.atomic_move(b_mysrc, dest, unsafe_writes=module.params['unsafe_writes'], keep_dest_attrs=not remote_src)

            except (IOError, OSError):
                module.fail_json(msg="failed to copy: %s to %s" % (src, dest), traceback=traceback.format_exc())
        changed = True

    # If neither have checksums, both src and dest are directories.
    if checksum_src is None and checksum_dest is None:
        if remote_src and os.path.isdir(module.params['src']):
            b_src = to_bytes(module.params['src'], errors='surrogate_or_strict')
            b_dest = to_bytes(module.params['dest'], errors='surrogate_or_strict')

            if src.endswith(os.path.sep) and os.path.isdir(module.params['dest']):
                diff_files_changed = copy_diff_files(b_src, b_dest, module)
                left_only_changed = copy_left_only(b_src, b_dest, module)
                common_dirs_changed = copy_common_dirs(b_src, b_dest, module)
                owner_group_changed = chown_recursive(b_dest, module)
                if diff_files_changed or left_only_changed or common_dirs_changed or owner_group_changed:
                    changed = True

            if src.endswith(os.path.sep) and not os.path.exists(module.params['dest']):
                b_basename = to_bytes(os.path.basename(src), errors='surrogate_or_strict')
                b_dest = to_bytes(os.path.join(b_dest, b_basename), errors='surrogate_or_strict')
                b_src = to_bytes(os.path.join(module.params['src'], ""), errors='surrogate_or_strict')
                if not module.check_mode:
                    shutil.copytree(b_src, b_dest, symlinks=not local_follow)
                chown_recursive(dest, module)
                changed = True

            if not src.endswith(os.path.sep) and os.path.isdir(module.params['dest']):
                b_basename = to_bytes(os.path.basename(src), errors='surrogate_or_strict')
                b_dest = to_bytes(os.path.join(b_dest, b_basename), errors='surrogate_or_strict')
                b_src = to_bytes(os.path.join(module.params['src'], ""), errors='surrogate_or_strict')
                if not module.check_mode and not os.path.exists(b_dest):
                    shutil.copytree(b_src, b_dest, symlinks=not local_follow)
                    changed = True
                    chown_recursive(dest, module)
                if module.check_mode and not os.path.exists(b_dest):
                    changed = True
                if os.path.exists(b_dest):
                    diff_files_changed = copy_diff_files(b_src, b_dest, module)
                    left_only_changed = copy_left_only(b_src, b_dest, module)
                    common_dirs_changed = copy_common_dirs(b_src, b_dest, module)
                    owner_group_changed = chown_recursive(b_dest, module)
                    if diff_files_changed or left_only_changed or common_dirs_changed or owner_group_changed:
                        changed = True

            if not src.endswith(os.path.sep) and not os.path.exists(module.params['dest']):
                b_basename = to_bytes(os.path.basename(module.params['src']), errors='surrogate_or_strict')
                b_dest = to_bytes(os.path.join(b_dest, b_basename), errors='surrogate_or_strict')
                if not module.check_mode and not os.path.exists(b_dest):
                    os.makedirs(b_dest)
                    changed = True
                    b_src = to_bytes(os.path.join(module.params['src'], ""), errors='surrogate_or_strict')
                    diff_files_changed = copy_diff_files(b_src, b_dest, module)
                    left_only_changed = copy_left_only(b_src, b_dest, module)
                    common_dirs_changed = copy_common_dirs(b_src, b_dest, module)
                    owner_group_changed = chown_recursive(b_dest, module)
                if module.check_mode and not os.path.exists(b_dest):
                    changed = True

    res_args = dict(
        dest=dest, src=src, md5sum=md5sum_src, checksum=checksum_src, changed=changed
    )
    if backup_file:
        res_args['backup_file'] = backup_file

    file_args = module.load_file_common_arguments(module.params, path=dest)
    res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'])

    module.exit_json(**res_args)


if __name__ == '__main__':
    main()
