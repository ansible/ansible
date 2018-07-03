#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: file
version_added: "historical"
short_description: Sets attributes of files
extends_documentation_fragment: files
description:
     - Sets attributes of files, symlinks, and directories, or removes
       files/symlinks/directories. Many other modules support the same options as
       the C(file) module - including M(copy), M(template), and M(assemble).
     - For Windows targets, use the M(win_file) module instead.
notes:
    - For Windows targets, use the M(win_file) module instead.
    - See also M(copy), M(template), M(assemble)
author:
    - Ansible Core Team
    - Michael DeHaan
options:
  path:
    description:
      - Path to the file being managed.
    required: true
    aliases: [ dest, name ]
  state:
    description:
      - If C(directory), all intermediate subdirectories will be created if they
        do not exist. Since Ansible 1.7 they will be created with the supplied permissions.
        If C(file), the file will NOT be created if it does not exist; see the C(touch)
        value or the M(copy) or M(template) module if you want that behavior.  If C(link), the
        symbolic link will be created or changed. Use C(hard) for hardlinks. If C(absent),
        directories will be recursively deleted, and files or symlinks will be unlinked.
        Note that C(absent) will not cause C(file) to fail if the C(path) does not exist
        as the state did not change.
        If C(touch) (new in 1.4), an empty file will be created if the C(path) does not
        exist, while an existing file or directory will receive updated file access and
        modification times (similar to the way `touch` works from the command line).
    default: file
    choices: [ absent, directory, file, hard, link, touch ]
  src:
    description:
      - path of the file to link to (applies only to C(state=link) and C(state=hard)). Will accept
        absolute, relative and nonexisting paths. Relative paths are relative to the file being
        created (C(path)) which is how the UNIX command C(ln -s SRC DEST) treats relative paths.
  recurse:
    description:
      - recursively set the specified file attributes (applies only to directories)
    type: bool
    default: 'no'
    version_added: "1.1"
  force:
    description:
      - 'force the creation of the symlinks in two cases: the source file does
        not exist (but will appear later); the destination exists and is a file (so, we need to unlink the
        "path" file and create symlink to the "src" file in place of it).'
    type: bool
    default: 'no'
  follow:
    description:
      - 'This flag indicates that filesystem links, if they exist, should be followed.'
      - 'Previous to Ansible 2.5, this was C(no) by default.'
    type: bool
    default: 'yes'
    version_added: "1.8"
'''

EXAMPLES = '''
# change file ownership, group and mode. When specifying mode using octal numbers, first digit should always be 0.
- file:
    path: /etc/foo.conf
    owner: foo
    group: foo
    mode: 0644
- file:
    path: /work
    owner: root
    group: root
    mode: 01777
- file:
    src: /file/to/link/to
    dest: /path/to/symlink
    owner: foo
    group: foo
    state: link
- file:
    src: '/tmp/{{ item.src }}'
    dest: '{{ item.dest }}'
    state: link
  with_items:
    - { src: 'x', dest: 'y' }
    - { src: 'z', dest: 'k' }

# touch a file, using symbolic modes to set the permissions (equivalent to 0644)
- file:
    path: /etc/foo.conf
    state: touch
    mode: "u=rw,g=r,o=r"

# touch the same file, but add/remove some permissions
- file:
    path: /etc/foo.conf
    state: touch
    mode: "u+rw,g-wx,o-rwx"

# create a directory if it doesn't exist
- file:
    path: /etc/some_directory
    state: directory
    mode: 0755
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

    # Make sure that src makes sense with the state
    if params['src'] and params['state'] not in ('link', 'hard'):
        params['src'] = None
        module.warn("The src option requires state to be 'link' or 'hard'.  This will become an"
                    " error in Ansible 2.10")

        # In 2.10, switch to this
        # raise ParameterError(results={"msg": "src option requires state to be 'link' or 'hard'",
        #                               "path": params["path"]})


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
def recursive_set_attributes(b_path, follow, file_args):
    changed = False
    for b_root, b_dirs, b_files in os.walk(b_path):
        for b_fsobj in b_dirs + b_files:
            b_fsname = os.path.join(b_root, b_fsobj)
            if not os.path.islink(b_fsname):
                tmp_file_args = file_args.copy()
                tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
            else:
                # Change perms on the link
                tmp_file_args = file_args.copy()
                tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)

                if follow:
                    b_fsname = os.path.join(b_root, os.readlink(b_fsname))
                    # The link target could be nonexistent
                    if os.path.exists(b_fsname):
                        if os.path.isdir(b_fsname):
                            # Link is a directory so change perms on the directory's contents
                            changed |= recursive_set_attributes(b_fsname, follow, file_args)

                        # Change perms on the file pointed to by the link
                        tmp_file_args = file_args.copy()
                        tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                        changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
    return changed


def initial_diff(path, state, prev_state):
    diff = {'before': {'path': path},
            'after': {'path': path},
            }

    if prev_state != state:
        diff['before']['state'] = prev_state
        diff['after']['state'] = state

    return diff

#
# States
#


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

        diff = initial_diff(path, 'absent', prev_state)
        result.update({'path': path, 'changed': True, 'diff': diff})
    else:
        result.update({'path': path, 'changed': False})

    return result


def execute_touch(path, follow):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    prev_state = get_state(b_path)

    # Unfortunately, touch always changes the file because it updates file's timestamp
    result = {'dest': path, 'changed': True}

    if not module.check_mode:
        if prev_state == 'absent':
            # Create an empty file if the filename did not already exist
            try:
                open(b_path, 'wb').close()
            except (OSError, IOError) as e:
                raise AnsibleModuleError(results={'msg': 'Error, could not touch target: %s'
                                                         % to_native(e, nonstring='simplerepr'),
                                                  'path': path})

        elif prev_state in ('file', 'directory', 'hard'):
            # Update the timestamp if the file already existed
            try:
                os.utime(b_path, None)
            except OSError as e:
                raise AnsibleModuleError(results={'msg': 'Error while touching existing target: %s'
                                                         % to_native(e, nonstring='simplerepr'),
                                                  'path': path})

        elif prev_state == 'link' and follow:
            # Update the timestamp of the pointed to file
            b_link_target = os.readlink(b_path)
            try:
                os.utime(b_link_target, None)
            except OSError as e:
                raise AnsibleModuleError(results={'msg': 'Error while touching existing target: %s'
                                                         % to_native(e, nonstring='simplerepr'),
                                                  'path': path})

        else:
            raise AnsibleModuleError(results={'msg': 'Can only touch files, directories, and'
                                                     ' hardlinks (%s is %s)' % (path, prev_state)})

        # Update the attributes on the file
        diff = initial_diff(path, 'touch', prev_state)
        file_args = module.load_file_common_arguments(module.params)
        try:
            module.set_fs_attributes_if_different(file_args, True, diff, expand=False)
        except SystemExit as e:
            if e.code:
                # We take this to mean that fail_json() was called from
                # somewhere in basic.py
                if prev_state == 'absent':
                    # If we just created the file we can safely remove it
                    os.remove(b_path)
            raise

        result['diff'] = diff
    return result


def ensure_file_attributes(path, follow):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)

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
                                          'path': path})

    diff = initial_diff(path, 'file', prev_state)
    changed = module.set_fs_attributes_if_different(file_args, False, diff, expand=False)
    return {'path': path, 'changed': changed, 'diff': diff}


def ensure_directory(path, follow, recurse):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)

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
            return {'changed': True, 'diff': diff}
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

    if recurse:
        changed |= recursive_set_attributes(b_path, follow, file_args)

    return {'path': path, 'changed': changed, 'diff': diff}


def ensure_symlink(path, src, follow, force):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    b_src = to_bytes(src, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)

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

    if prev_state == 'absent':
        changed = True
    elif prev_state == 'link':
        b_old_src = os.readlink(b_path)
        if b_old_src != b_src:
            diff['before']['src'] = to_native(b_old_src, errors='strict')
            diff['after']['src'] = src
            changed = True
    elif prev_state == 'hard':
        changed = True
        if not force:
            raise AnsibleModuleError(results={'msg': 'Cannot link because a hard link exists at destination',
                                              'dest': path, 'src': src})
    elif prev_state == 'file':
        changed = True
        if not force:
            raise AnsibleModuleError(results={'msg': 'Cannot link because a file exists at destination',
                                              'dest': path, 'src': src})
    elif prev_state == 'directory':
        changed = True
        if os.path.exists(b_path):
            if not force:
                raise AnsibleModuleError(results={'msg': 'Cannot link because a file exists at destination',
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

    # Whenever we create a link to a nonexistent target we know that the nonexistent target
    # cannot have any permissions set on it.  Skip setting those and emit a warning (the user
    # can set follow=False to remove the warning)
    if follow and os.path.islink(b_path) and not os.path.exists(file_args['path']):
        module.warn('Cannot set fs attributes on a non-existent symlink target. follow should be'
                    ' set to False to avoid this.')
    else:
        changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)

    return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}


def ensure_hardlink(path, src, follow, force):
    b_path = to_bytes(path, errors='surrogate_or_strict')
    b_src = to_bytes(src, errors='surrogate_or_strict')
    prev_state = get_state(b_path)
    file_args = module.load_file_common_arguments(module.params)

    # src is the source of a hardlink.  We require it if we are creating a new hardlink
    if src is None and not os.path.exists(b_path):
        raise AnsibleModuleError(results={'msg': 'src and dest are required for creating new hardlinks'})

    # Toshio: Begin suspect block
    # I believe that this block of code is wrong for hardlinks.
    # src may be relative.
    # If it is relative, it should be relative to the cwd (so just use abspath).
    # This is different from symlinks where src is relative to the symlink's path.

    # Why must src be an absolute path?
    if not os.path.isabs(b_src):
        raise AnsibleModuleError(results={'msg': "src must be an absolute path"})

    # If this is a link, then it can't be a dir so why is it in the conditional?
    if not os.path.islink(b_path) and os.path.isdir(b_path):
        relpath = path
    else:
        b_relpath = os.path.dirname(b_path)
        relpath = to_native(b_relpath, errors='strict')

    # Why? This does nothing because src was checked to be absolute above?
    absrc = os.path.join(relpath, src)
    b_absrc = to_bytes(absrc, errors='surrogate_or_strict')
    if not force and not os.path.exists(b_absrc):
        raise AnsibleModuleError(results={'msg': 'src file does not exist, use "force=yes" if you'
                                                 ' really want to create the link: %s' % absrc,
                                          'path': path, 'src': src})
    # Toshio: end suspect block

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

    return {'dest': path, 'src': src, 'changed': changed, 'diff': diff}


def main():

    global module

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['file', 'directory', 'link', 'hard', 'touch', 'absent'], default=None),
            path=dict(aliases=['dest', 'name'], required=True, type='path'),
            _original_basename=dict(required=False),  # Internal use only, for recursive ops
            recurse=dict(default=False, type='bool'),
            force=dict(required=False, default=False, type='bool'),  # Note: Should not be in file_common_args in future
            follow=dict(required=False, default=True, type='bool'),  # Note: Different default than file_common_args
            _diff_peek=dict(default=None),  # Internal use only, for internal checks in the action plugins
            src=dict(required=False, default=None, type='path'),  # Note: Should not be in file_common_args in future
        ),
        add_file_common_args=True,
        supports_check_mode=True
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

    # short-circuit for diff_peek
    if params['_diff_peek'] is not None:
        appears_binary = execute_diff_peek(to_bytes(path, errors='surrogate_or_strict'))
        module.exit_json(path=path, changed=False, appears_binary=appears_binary)

    if state == 'file':
        result = ensure_file_attributes(path, follow)
    elif state == 'directory':
        result = ensure_directory(path, follow, recurse)
    elif state == 'link':
        result = ensure_symlink(path, src, follow, force)
    elif state == 'hard':
        result = ensure_hardlink(path, src, follow, force)
    elif state == 'touch':
        result = execute_touch(path, follow)
    elif state == 'absent':
        result = ensure_absent(path)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
