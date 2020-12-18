#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: file
version_added: historical
short_description: Manage files and file properties
extends_documentation_fragment: files
description:
- Set attributes of files, symlinks or directories.
- Alternatively, remove files, symlinks or directories.
- Many other modules support the same options as the C(file) module - including M(ansible.builtin.copy),
  M(ansible.builtin.template), and M(ansible.builtin.assemble).
- For Windows targets, use the M(ansible.windows.win_file) module instead.
options:
  path:
    description:
    - Path to the file being managed.
    type: path
    required: yes
    aliases: [ dest, name ]
  state:
    description:
    - If C(absent), directories will be recursively deleted, and files or symlinks will
      be unlinked. In the case of a directory, if C(diff) is declared, you will see the files and folders deleted listed
      under C(path_contents). Note that C(absent) will not cause C(file) to fail if the C(path) does
      not exist as the state did not change.
    - If C(directory), all intermediate subdirectories will be created if they
      do not exist. Since Ansible 1.7 they will be created with the supplied permissions.
    - If C(file), without any other options this works mostly as a 'stat' and will return the current state of C(path).
      Even with other options (i.e C(mode)), the file will be modified but will NOT be created if it does not exist;
      see the C(touch) value or the M(ansible.builtin.copy) or M(ansible.builtin.template) module if you want that behavior.
    - If C(hard), the hard link will be created or changed.
    - If C(link), the symbolic link will be created or changed.
    - If C(touch) (new in 1.4), an empty file will be created if the C(path) does not
      exist, while an existing file or directory will receive updated file access and
      modification times (similar to the way C(touch) works from the command line).
    type: str
    default: file
    choices: [ absent, directory, file, hard, link, touch ]
  src:
    description:
    - Path of the file to link to.
    - This applies only to C(state=link) and C(state=hard).
    - For C(state=link), this will also accept a non-existing path.
    - Relative paths are relative to the file being created (C(path)) which is how
      the Unix command C(ln -s SRC DEST) treats relative paths.
    type: path
  recurse:
    description:
    - Recursively set the specified file attributes on directory contents.
    - This applies only when C(state) is set to C(directory).
    type: bool
    default: no
    version_added: '1.1'
  force:
    description:
    - >
      Force the creation of the symlinks in two cases: the source file does
      not exist (but will appear later); the destination exists and is a file (so, we need to unlink the
      C(path) file and create symlink to the C(src) file in place of it).
    type: bool
    default: no
  follow:
    description:
    - This flag indicates that filesystem links, if they exist, should be followed.
    - Previous to Ansible 2.5, this was C(no) by default.
    type: bool
    default: yes
    version_added: '1.8'
  modification_time:
    description:
    - This parameter indicates the time the file's modification time should be set to.
    - Should be C(preserve) when no modification is required, C(YYYYMMDDHHMM.SS) when using default time format, or C(now).
    - Default is None meaning that C(preserve) is the default for C(state=[file,directory,link,hard]) and C(now) is default for C(state=touch).
    type: str
    version_added: "2.7"
  modification_time_format:
    description:
    - When used with C(modification_time), indicates the time format that must be used.
    - Based on default Python format (see time.strftime doc).
    type: str
    default: "%Y%m%d%H%M.%S"
    version_added: '2.7'
  access_time:
    description:
    - This parameter indicates the time the file's access time should be set to.
    - Should be C(preserve) when no modification is required, C(YYYYMMDDHHMM.SS) when using default time format, or C(now).
    - Default is C(None) meaning that C(preserve) is the default for C(state=[file,directory,link,hard]) and C(now) is default for C(state=touch).
    type: str
    version_added: '2.7'
  access_time_format:
    description:
    - When used with C(access_time), indicates the time format that must be used.
    - Based on default Python format (see time.strftime doc).
    type: str
    default: "%Y%m%d%H%M.%S"
    version_added: '2.7'
seealso:
- module: ansible.builtin.assemble
- module: ansible.builtin.copy
- module: ansible.builtin.stat
- module: ansible.builtin.template
- module: ansible.windows.win_file
notes:
- Supports C(check_mode).
author:
- Ansible Core Team
- Michael DeHaan
'''

EXAMPLES = r'''
- name: Change file ownership, group and permissions
  ansible.builtin.file:
    path: /etc/foo.conf
    owner: foo
    group: foo
    mode: '0644'

- name: Give insecure permissions to an existing file
  ansible.builtin.file:
    path: /work
    owner: root
    group: root
    mode: '1777'

- name: Create a symbolic link
  ansible.builtin.file:
    src: /file/to/link/to
    dest: /path/to/symlink
    owner: foo
    group: foo
    state: link

- name: Create two hard links
  ansible.builtin.file:
    src: '/tmp/{{ item.src }}'
    dest: '{{ item.dest }}'
    state: hard
  loop:
    - { src: x, dest: y }
    - { src: z, dest: k }

- name: Touch a file, using symbolic modes to set the permissions (equivalent to 0644)
  ansible.builtin.file:
    path: /etc/foo.conf
    state: touch
    mode: u=rw,g=r,o=r

- name: Touch the same file, but add/remove some permissions
  ansible.builtin.file:
    path: /etc/foo.conf
    state: touch
    mode: u+rw,g-wx,o-rwx

- name: Touch again the same file, but do not change times this makes the task idempotent
  ansible.builtin.file:
    path: /etc/foo.conf
    state: touch
    mode: u+rw,g-wx,o-rwx
    modification_time: preserve
    access_time: preserve

- name: Create a directory if it does not exist
  ansible.builtin.file:
    path: /etc/some_directory
    state: directory
    mode: '0755'

- name: Update modification and access time of given file
  ansible.builtin.file:
    path: /etc/some_file
    state: file
    modification_time: now
    access_time: now

- name: Set access time based on seconds from epoch value
  ansible.builtin.file:
    path: /etc/another_file
    state: file
    access_time: '{{ "%Y%m%d%H%M.%S" | strftime(stat_var.stat.atime) }}'

- name: Recursively change ownership of a directory
  ansible.builtin.file:
    path: /etc/foo
    state: directory
    recurse: yes
    owner: foo
    group: foo

- name: Remove file (delete file)
  ansible.builtin.file:
    path: /etc/foo.txt
    state: absent

- name: Recursively remove directory
  ansible.builtin.file:
    path: /etc/foo
    state: absent

'''
RETURN = r'''
dest:
    description: Destination file/path, equal to the value passed to I(path).
    returned: state=touch, state=hard, state=link
    type: str
    sample: /path/to/file.txt
path:
    description: Destination file/path, equal to the value passed to I(path).
    returned: state=absent, state=directory, state=file
    type: str
    sample: /path/to/file.txt
'''

import errno
import os
import shutil
import sys
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native


# There will only be a single AnsibleModule object per module
module = None


class AnsibleModuleError(Exception):
    def __init__(self, results):
        self.results = results

    def __repr__(self):
        print('AnsibleModuleError(results={0})'.format(self.results))


class ParameterError(AnsibleModuleError):
    pass


class Sentinel(object):
    def __new__(cls, *args, **kwargs):
        return cls


def _ansible_excepthook(exc_type, exc_value, tb):
    # Using an exception allows us to catch it if the calling code knows it can recover
    if issubclass(exc_type, AnsibleModuleError):
        module.fail_json(**exc_value.results)
    else:
        sys.__excepthook__(exc_type, exc_value, tb)


def additional_parameter_handling(params):
    """Additional parameter validation and reformatting"""
    # When path is a directory, rewrite the pathname to be the file inside of the directory
    # TODO: Why do we exclude link?  Why don't we exclude directory?  Should we exclude touch?
    # I think this is where we want to be in the future:
    # when isdir(path):
    # if state == absent:  Remove the directory
    # if state == touch:   Touch the directory
    # if state == directory: Assert the directory is the same as the one specified
    # if state == file:    place inside of the directory (use _original_basename)
    # if state == link:    place inside of the directory (use _original_basename.  Fallback to src?)
    # if state == hard:    place inside of the directory (use _original_basename.  Fallback to src?)
    if (params['state'] not in ("link", "absent") and os.path.isdir(to_bytes(params['path'], errors='surrogate_or_strict'))):
        basename = None

        if params['_original_basename']:
            basename = params['_original_basename']
        elif params['src']:
            basename = os.path.basename(params['src'])

        if basename:
            params['path'] = os.path.join(params['path'], basename)

    # state should default to file, but since that creates many conflicts,
    # default state to 'current' when it exists.
    prev_state = get_state(to_bytes(params['path'], errors='surrogate_or_strict'))

    if params['state'] is None:
        if prev_state != 'absent':
            params['state'] = prev_state
        elif params['recurse']:
            params['state'] = 'directory'
        else:
            params['state'] = 'file'

    # make sure the target path is a directory when we're doing a recursive operation
    if params['recurse'] and params['state'] != 'directory':
        raise ParameterError(results={"msg": "recurse option requires state to be 'directory'",
                                      "path": params["path"]})

    # Fail if 'src' but no 'state' is specified
    if params['src'] and params['state'] not in ('link', 'hard'):
        raise ParameterError(results={'msg': "src option requires state to be 'link' or 'hard'",
                                      'path': params['path']})


def get_state(path):
    ''' Find out current state '''

    b_path = to_bytes(path, errors='surrogate_or_strict')
    try:
        if os.path.lexists(b_path):
            if os.path.islink(b_path):
                return 'link'
            elif os.path.isdir(b_path):
                return 'directory'
            elif os.stat(b_path).st_nlink > 1:
                return 'hard'

            # could be many other things, but defaulting to file
            return 'file'

        return 'absent'
    except OSError as e:
        if e.errno == errno.ENOENT:  # It may already have been removed
            return 'absent'
        else:
            raise


# This should be moved into the common file utilities
def recursive_set_attributes(b_path, follow, file_args, mtime, atime):
    changed = False

    try:
        for b_root, b_dirs, b_files in os.walk(b_path):
            for b_fsobj in b_dirs + b_files:
                b_fsname = os.path.join(b_root, b_fsobj)
                if not os.path.islink(b_fsname):
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                    changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
                    changed |= update_timestamp_for_file(tmp_file_args['path'], mtime, atime)

                else:
                    # Change perms on the link
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                    changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
                    changed |= update_timestamp_for_file(tmp_file_args['path'], mtime, atime)

                    if follow:
                        b_fsname = os.path.join(b_root, os.readlink(b_fsname))
                        # The link target could be nonexistent
                        if os.path.exists(b_fsname):
                            if os.path.isdir(b_fsname):
                                # Link is a directory so change perms on the directory's contents
                                changed |= recursive_set_attributes(b_fsname, follow, file_args, mtime, atime)

                            # Change perms on the file pointed to by the link
                            tmp_file_args = file_args.copy()
                            tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                            changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
                            changed |= update_timestamp_for_file(tmp_file_args['path'], mtime, atime)
    except RuntimeError as e:
        # on Python3 "RecursionError" is raised which is derived from "RuntimeError"
        # TODO once this function is moved into the common file utilities, this should probably raise more general exception
        raise AnsibleModuleError(
            results={'msg': "Could not recursively set attributes on %s. Original error was: '%s'" % (to_native(b_path), to_native(e))}
        )

    return changed


def initial_diff(path, state, prev_state):
    diff = {'before': {'path': path},
            'after': {'path': path},
            }

    if prev_state != state:
        diff['before']['state'] = prev_state
        diff['after']['state'] = state
        if state == 'absent' and prev_state == 'directory':
            walklist = {
                'directories': [],
                'files': [],
            }
            b_path = to_bytes(path, errors='surrogate_or_strict')
            for base_path, sub_folders, files in os.walk(b_path):
                for folder in sub_folders:
                    folderpath = os.path.join(base_path, folder)
                    walklist['directories'].append(folderpath)

                for filename in files:
                    filepath = os.path.join(base_path, filename)
                    walklist['files'].append(filepath)

            diff['before']['path_content'] = walklist

    return diff

#
# States
#


def get_timestamp_for_time(formatted_time, time_format):
    if formatted_time == 'preserve':
        return None
    elif formatted_time == 'now':
        return Sentinel
    else:
        try:
            struct = time.strptime(formatted_time, time_format)
            struct_time = time.mktime(struct)
        except (ValueError, OverflowError) as e:
            raise AnsibleModuleError(results={'msg': 'Error while obtaining timestamp for time %s using format %s: %s'
                                              % (formatted_time, time_format, to_native(e, nonstring='simplerepr'))})

        return struct_time


def update_timestamp_for_file(path, mtime, atime, diff=None):
    b_path = to_bytes(path, errors='surrogate_or_strict')

    try:
        # When mtime and atime are set to 'now', rely on utime(path, None) which does not require ownership of the file
        # https://github.com/ansible/ansible/issues/50943
        if mtime is Sentinel and atime is Sentinel:
            # It's not exact but we can't rely on os.stat(path).st_mtime after setting os.utime(path, None) as it may
            # not be updated. Just use the current time for the diff values
            mtime = atime = time.time()

            previous_mtime = os.stat(b_path).st_mtime
            previous_atime = os.stat(b_path).st_atime

            set_time = None
        else:
            # If both parameters are None 'preserve', nothing to do
            if mtime is None and atime is None:
                return False

            previous_mtime = os.stat(b_path).st_mtime
            previous_atime = os.stat(b_path).st_atime

            if mtime is None:
                mtime = previous_mtime
            elif mtime is Sentinel:
                mtime = time.time()

            if atime is None:
                atime = previous_atime
            elif atime is Sentinel:
                atime = time.time()

            # If both timestamps are already ok, nothing to do
            if mtime == previous_mtime and atime == previous_atime:
                return False

            set_time = (atime, mtime)

        os.utime(b_path, set_time)

        if diff is not None:
            if 'before' not in diff:
                diff['before'] = {}
            if 'after' not in diff:
                diff['after'] = {}
            if mtime != previous_mtime:
                diff['before']['mtime'] = previous_mtime
                diff['after']['mtime'] = mtime
            if atime != previous_atime:
                diff['before']['atime'] = previous_atime
                diff['after']['atime'] = atime
    except OSError as e:
        raise AnsibleModuleError(results={'msg': 'Error while updating modification or access time: %s'
                                          % to_native(e, nonstring='simplerepr'), 'path': path})
    return True


def keep_backward_compatibility_on_timestamps(parameter, state):
    if state in ['file', 'hard', 'directory', 'link'] and parameter is None:
        return 'preserve'
    elif state == 'touch' and parameter is None:
        return 'now'
    else:
        return parameter


def execute_diff_peek(path):
    """Take a guess as to whether a file is a binary file"""
    b_path = to_bytes(path, errors='surrogate_or_strict')
    appears_binary = False
    try:
        with open(b_path, 'rb') as f:
            head = f.read(8192)
    except Exception:
        # If we can't read the file, we're okay assuming it's text
        pass
    else:
        if b"\x00" in head:
            appears_binary = True

    return appears_binary


def ensure_absent(path):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    result = {}

    if prev_state != 'absent':
        diff = initial_diff(path, 'absent', prev_state)

        if not module.check_mode:
            if prev_state == 'directory':
                try:
                    shutil.rmtree(b_path, ignore_errors=False)
                except Exception as e:
                    raise AnsibleModuleError(results={'msg': "rmtree failed: %s" % to_native(e)})
            else:
                try:
                    os.unlink(b_path)
                except OSError as e:
                    if e.errno != errno.ENOENT:  # It may already have been removed
                        raise AnsibleModuleError(results={'msg': "unlinking failed: %s " % to_native(e),
                                                          'path': path})

        result.update({'path': path, 'changed': True, 'diff': diff, 'state': 'absent'})
    else:
        result.update({'path': path, 'changed': False, 'state': 'absent'})

    return result


def execute_touch(path, follow, timestamps):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    changed = False
    result = {'dest': path}
    mtime = get_timestamp_for_time(timestamps['modification_time'], timestamps['modification_time_format'])
    atime = get_timestamp_for_time(timestamps['access_time'], timestamps['access_time_format'])

    if not module.check_mode:
        if prev_state == 'absent':
            # Create an empty file if the filename did not already exist
            try:
                open(b_path, 'wb').close()
                changed = True
            except (OSError, IOError) as e:
                raise AnsibleModuleError(results={'msg': 'Error, could not touch target: %s'
                                                         % to_native(e, nonstring='simplerepr'),
                                                  'path': path})

        # Update the attributes on the file
        diff = initial_diff(path, 'touch', prev_state)
        file_args = module.load_file_common_arguments(module.params)
        try:
            changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
            changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)
        except SystemExit as e:
            if e.code:
                # We take this to mean that fail_json() was called from
                # somewhere in basic.py
                if prev_state == 'absent':
                    # If we just created the file we can safely remove it
                    os.remove(b_path)
            raise

        result['changed'] = changed
        result['diff'] = diff
    return result


def ensure_file_attributes(path, follow, timestamps):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)
    mtime = get_timestamp_for_time(timestamps['modification_time'], timestamps['modification_time_format'])
    atime = get_timestamp_for_time(timestamps['access_time'], timestamps['access_time_format'])

    if prev_state != 'file':
        if follow and prev_state == 'link':
            # follow symlink and operate on original
            b_path = os.path.realpath(b_path)
            path = to_native(b_path, errors='strict')
            prev_state = get_state(b_path)
            file_args['path'] = path

    if prev_state not in ('file', 'hard'):
        # file is not absent and any other state is a conflict
        raise AnsibleModuleError(results={'msg': 'file (%s) is %s, cannot continue' % (path, prev_state),
                                          'path': path, 'state': prev_state})

    diff = initial_diff(path, 'file', prev_state)
    changed = module.set_fs_attributes_if_different(file_args, False, diff, expand=False)
    changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)
    return {'path': path, 'changed': changed, 'diff': diff}


def ensure_directory(path, follow, recurse, timestamps):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)
    mtime = get_timestamp_for_time(timestamps['modification_time'], timestamps['modification_time_format'])
    atime = get_timestamp_for_time(timestamps['access_time'], timestamps['access_time_format'])

    # For followed symlinks, we need to operate on the target of the link
    if follow and prev_state == 'link':
        b_path = os.path.realpath(b_path)
        path = to_native(b_path, errors='strict')
        file_args['path'] = path
        prev_state = get_state(b_path)

    changed = False
    diff = initial_diff(path, 'directory', prev_state)

    if prev_state == 'absent':
        # Create directory and assign permissions to it
        if module.check_mode:
            return {'path': path, 'changed': True, 'diff': diff}
        curpath = ''

        try:
            # Split the path so we can apply filesystem attributes recursively
            # from the root (/) directory for absolute paths or the base path
            # of a relative path.  We can then walk the appropriate directory
            # path to apply attributes.
            # Something like mkdir -p with mode applied to all of the newly created directories
            for dirname in path.strip('/').split('/'):
                curpath = '/'.join([curpath, dirname])
                # Remove leading slash if we're creating a relative path
                if not os.path.isabs(path):
                    curpath = curpath.lstrip('/')
                b_curpath = to_bytes(curpath, errors='surrogate_or_strict')
                if not os.path.exists(b_curpath):
                    try:
                        os.mkdir(b_curpath)
                        changed = True
                    except OSError as ex:
                        # Possibly something else created the dir since the os.path.exists
                        # check above. As long as it's a dir, we don't need to error out.
                        if not (ex.errno == errno.EEXIST and os.path.isdir(b_curpath)):
                            raise
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path'] = curpath
                    changed = module.set_fs_attributes_if_different(tmp_file_args, changed, diff, expand=False)
                    changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)
        except Exception as e:
            raise AnsibleModuleError(results={'msg': 'There was an issue creating %s as requested:'
                                                     ' %s' % (curpath, to_native(e)),
                                              'path': path})
        return {'path': path, 'changed': changed, 'diff': diff}

    elif prev_state != 'directory':
        # We already know prev_state is not 'absent', therefore it exists in some form.
        raise AnsibleModuleError(results={'msg': '%s already exists as a %s' % (path, prev_state),
                                          'path': path})

    #
    # previous state == directory
    #

    changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
    changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)
    if recurse:
        changed |= recursive_set_attributes(b_path, follow, file_args, mtime, atime)

    return {'path': path, 'changed': changed, 'diff': diff}


def ensure_symlink(path, src, follow, force, timestamps):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    b_src = to_bytes(src, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    mtime = get_timestamp_for_time(timestamps['modification_time'], timestamps['modification_time_format'])
    atime = get_timestamp_for_time(timestamps['access_time'], timestamps['access_time_format'])
    # source is both the source of a symlink or an informational passing of the src for a template module
    # or copy module, even if this module never uses it, it is needed to key off some things
    if src is None:
        if follow:
            # use the current target of the link as the source
            src = to_native(os.path.realpath(b_path), errors='strict')
            b_src = to_bytes(src, errors='surrogate_or_strict')

    if not os.path.islink(b_path) and os.path.isdir(b_path):
        relpath = path
    else:
        b_relpath = os.path.dirname(b_path)
        relpath = to_native(b_relpath, errors='strict')

    absrc = os.path.join(relpath, src)
    b_absrc = to_bytes(absrc, errors='surrogate_or_strict')
    if not force and not os.path.exists(b_absrc):
        raise AnsibleModuleError(results={'msg': 'src file does not exist, use "force=yes" if you'
                                                 ' really want to create the link: %s' % absrc,
                                          'path': path, 'src': src})

    if prev_state == 'directory':
        if not force:
            raise AnsibleModuleError(results={'msg': 'refusing to convert from %s to symlink for %s'
                                                     % (prev_state, path),
                                              'path': path})
        elif os.listdir(b_path):
            # refuse to replace a directory that has files in it
            raise AnsibleModuleError(results={'msg': 'the directory %s is not empty, refusing to'
                                                     ' convert it' % path,
                                              'path': path})
    elif prev_state in ('file', 'hard') and not force:
        raise AnsibleModuleError(results={'msg': 'refusing to convert from %s to symlink for %s'
                                                 % (prev_state, path),
                                          'path': path})

    diff = initial_diff(path, 'link', prev_state)
    changed = False

    if prev_state in ('hard', 'file', 'directory', 'absent'):
        changed = True
    elif prev_state == 'link':
        b_old_src = os.readlink(b_path)
        if b_old_src != b_src:
            diff['before']['src'] = to_native(b_old_src, errors='strict')
            diff['after']['src'] = src
            changed = True
    else:
        raise AnsibleModuleError(results={'msg': 'unexpected position reached', 'dest': path, 'src': src})

    if changed and not module.check_mode:
        if prev_state != 'absent':
            # try to replace atomically
            b_tmppath = to_bytes(os.path.sep).join(
                [os.path.dirname(b_path), to_bytes(".%s.%s.tmp" % (os.getpid(), time.time()))]
            )
            try:
                if prev_state == 'directory':
                    os.rmdir(b_path)
                os.symlink(b_src, b_tmppath)
                os.rename(b_tmppath, b_path)
            except OSError as e:
                if os.path.exists(b_tmppath):
                    os.unlink(b_tmppath)
                raise AnsibleModuleError(results={'msg': 'Error while replacing: %s'
                                                         % to_native(e, nonstring='simplerepr'),
                                                  'path': path})
        else:
            try:
                os.symlink(b_src, b_path)
            except OSError as e:
                raise AnsibleModuleError(results={'msg': 'Error while linking: %s'
                                                         % to_native(e, nonstring='simplerepr'),
                                                  'path': path})

    if module.check_mode and not os.path.exists(b_path):
        return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}

    # Now that we might have created the symlink, get the arguments.
    # We need to do it now so we can properly follow the symlink if needed
    # because load_file_common_arguments sets 'path' according
    # the value of follow and the symlink existence.
    file_args = module.load_file_common_arguments(module.params)

    # Whenever we create a link to a nonexistent target we know that the nonexistent target
    # cannot have any permissions set on it.  Skip setting those and emit a warning (the user
    # can set follow=False to remove the warning)
    if follow and os.path.islink(b_path) and not os.path.exists(file_args['path']):
        module.warn('Cannot set fs attributes on a non-existent symlink target. follow should be'
                    ' set to False to avoid this.')
    else:
        changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
        changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)

    return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}


def ensure_hardlink(path, src, follow, force, timestamps):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    b_src = to_bytes(src, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)
    mtime = get_timestamp_for_time(timestamps['modification_time'], timestamps['modification_time_format'])
    atime = get_timestamp_for_time(timestamps['access_time'], timestamps['access_time_format'])

    # src is the source of a hardlink.  We require it if we are creating a new hardlink.
    # We require path in the argument_spec so we know it is present at this point.
    if src is None:
        raise AnsibleModuleError(results={'msg': 'src is required for creating new hardlinks'})

    if not os.path.exists(b_src):
        raise AnsibleModuleError(results={'msg': 'src does not exist', 'dest': path, 'src': src})

    diff = initial_diff(path, 'hard', prev_state)
    changed = False

    if prev_state == 'absent':
        changed = True
    elif prev_state == 'link':
        b_old_src = os.readlink(b_path)
        if b_old_src != b_src:
            diff['before']['src'] = to_native(b_old_src, errors='strict')
            diff['after']['src'] = src
            changed = True
    elif prev_state == 'hard':
        if not os.stat(b_path).st_ino == os.stat(b_src).st_ino:
            changed = True
            if not force:
                raise AnsibleModuleError(results={'msg': 'Cannot link, different hard link exists at destination',
                                                  'dest': path, 'src': src})
    elif prev_state == 'file':
        changed = True
        if not force:
            raise AnsibleModuleError(results={'msg': 'Cannot link, %s exists at destination' % prev_state,
                                              'dest': path, 'src': src})
    elif prev_state == 'directory':
        changed = True
        if os.path.exists(b_path):
            if os.stat(b_path).st_ino == os.stat(b_src).st_ino:
                return {'path': path, 'changed': False}
            elif not force:
                raise AnsibleModuleError(results={'msg': 'Cannot link: different hard link exists at destination',
                                                  'dest': path, 'src': src})
    else:
        raise AnsibleModuleError(results={'msg': 'unexpected position reached', 'dest': path, 'src': src})

    if changed and not module.check_mode:
        if prev_state != 'absent':
            # try to replace atomically
            b_tmppath = to_bytes(os.path.sep).join(
                [os.path.dirname(b_path), to_bytes(".%s.%s.tmp" % (os.getpid(), time.time()))]
            )
            try:
                if prev_state == 'directory':
                    if os.path.exists(b_path):
                        try:
                            os.unlink(b_path)
                        except OSError as e:
                            if e.errno != errno.ENOENT:  # It may already have been removed
                                raise
                os.link(b_src, b_tmppath)
                os.rename(b_tmppath, b_path)
            except OSError as e:
                if os.path.exists(b_tmppath):
                    os.unlink(b_tmppath)
                raise AnsibleModuleError(results={'msg': 'Error while replacing: %s'
                                                         % to_native(e, nonstring='simplerepr'),
                                                  'path': path})
        else:
            try:
                os.link(b_src, b_path)
            except OSError as e:
                raise AnsibleModuleError(results={'msg': 'Error while linking: %s'
                                                         % to_native(e, nonstring='simplerepr'),
                                                  'path': path})

    if module.check_mode and not os.path.exists(b_path):
        return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}

    changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
    changed |= update_timestamp_for_file(file_args['path'], mtime, atime, diff)

    return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}


def main():

    global module

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['absent', 'directory', 'file', 'hard', 'link', 'touch']),
            path=dict(type='path', required=True, aliases=['dest', 'name']),
            _original_basename=dict(type='str'),  # Internal use only, for recursive ops
            recurse=dict(type='bool', default=False),
            force=dict(type='bool', default=False),  # Note: Should not be in file_common_args in future
            follow=dict(type='bool', default=True),  # Note: Different default than file_common_args
            _diff_peek=dict(type='bool'),  # Internal use only, for internal checks in the action plugins
            src=dict(type='path'),  # Note: Should not be in file_common_args in future
            modification_time=dict(type='str'),
            modification_time_format=dict(type='str', default='%Y%m%d%H%M.%S'),
            access_time=dict(type='str'),
            access_time_format=dict(type='str', default='%Y%m%d%H%M.%S'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    # When we rewrite basic.py, we will do something similar to this on instantiating an AnsibleModule
    sys.excepthook = _ansible_excepthook
    additional_parameter_handling(module.params)
    params = module.params

    state = params['state']
    recurse = params['recurse']
    force = params['force']
    follow = params['follow']
    path = params['path']
    src = params['src']

    timestamps = {}
    timestamps['modification_time'] = keep_backward_compatibility_on_timestamps(params['modification_time'], state)
    timestamps['modification_time_format'] = params['modification_time_format']
    timestamps['access_time'] = keep_backward_compatibility_on_timestamps(params['access_time'], state)
    timestamps['access_time_format'] = params['access_time_format']

    # short-circuit for diff_peek
    if params['_diff_peek'] is not None:
        appears_binary = execute_diff_peek(to_bytes(path, errors='surrogate_or_strict'))
        module.exit_json(path=path, changed=False, appears_binary=appears_binary)

    if state == 'file':
        result = ensure_file_attributes(path, follow, timestamps)
    elif state == 'directory':
        result = ensure_directory(path, follow, recurse, timestamps)
    elif state == 'link':
        result = ensure_symlink(path, src, follow, force, timestamps)
    elif state == 'hard':
        result = ensure_hardlink(path, src, follow, force, timestamps)
    elif state == 'touch':
        result = execute_touch(path, follow, timestamps)
    elif state == 'absent':
        result = ensure_absent(path)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
