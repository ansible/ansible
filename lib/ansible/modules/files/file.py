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
      - 'path to the file being managed.  Aliases: I(dest), I(name)'
    required: true
    aliases: [ dest, name ]
  state:
    description:
      - If C(directory), all immediate subdirectories will be created if they
        do not exist, since 1.7 they will be created with the supplied permissions.
        If C(file), the file will NOT be created if it does not exist, see the M(copy)
        or M(template) module if you want that behavior.  If C(link), the symbolic
        link will be created or changed. Use C(hard) for hardlinks. If C(absent),
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
      - path of the file to link to (applies only to C(state=link) and C(state=hard)). Will accept absolute,
        relative and nonexisting paths. Relative paths are not expanded.
  recurse:
    description:
      - recursively set the specified file attributes (applies only to state=directory)
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
import time

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import b
from ansible.module_utils._text import to_bytes, to_native


def get_state(b_path):
    ''' Find out current state '''

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


def recursive_set_attributes(module, b_path, follow, file_args):
    changed = False
    for b_root, b_dirs, b_files in os.walk(b_path):
        for b_fsobj in b_dirs + b_files:
            b_fsname = os.path.join(b_root, b_fsobj)
            if not os.path.islink(b_fsname):
                tmp_file_args = file_args.copy()
                tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
            else:
                tmp_file_args = file_args.copy()
                tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
                if follow:
                    b_fsname = os.path.join(b_root, os.readlink(b_fsname))
                    if os.path.isdir(b_fsname):
                        changed |= recursive_set_attributes(module, b_fsname, follow, file_args)
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path'] = to_native(b_fsname, errors='surrogate_or_strict')
                    changed |= module.set_fs_attributes_if_different(tmp_file_args, changed, expand=False)
    return changed


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['file', 'directory', 'link', 'hard', 'touch', 'absent'], default=None),
            path=dict(aliases=['dest', 'name'], required=True, type='path'),
            original_basename=dict(required=False),  # Internal use only, for recursive ops
            recurse=dict(default=False, type='bool'),
            force=dict(required=False, default=False, type='bool'),
            follow=dict(required=False, default=False, type='bool'),
            diff_peek=dict(default=None),  # Internal use only, for internal checks in the action plugins
            validate=dict(required=False, default=None),  # Internal use only, for template and copy
            src=dict(required=False, default=None, type='path'),
        ),
        add_file_common_args=True,
        supports_check_mode=True
    )

    params = module.params
    state = params['state']
    recurse = params['recurse']
    force = params['force']
    diff_peek = params['diff_peek']
    src = params['src']
    b_src = to_bytes(src, errors='surrogate_or_strict')
    follow = params['follow']

    # modify source as we later reload and pass, specially relevant when used by other modules.
    path = params['path']
    b_path = to_bytes(path, errors='surrogate_or_strict')

    # short-circuit for diff_peek
    if diff_peek is not None:
        appears_binary = False
        try:
            f = open(b_path, 'rb')
            head = f.read(8192)
            f.close()
            if b("\x00") in head:
                appears_binary = True
        except:
            pass
        module.exit_json(path=path, changed=False, appears_binary=appears_binary)

    prev_state = get_state(b_path)

    # state should default to file, but since that creates many conflicts,
    # default to 'current' when it exists.
    if state is None:
        if prev_state != 'absent':
            state = prev_state
        elif recurse:
            state = 'directory'
        else:
            state = 'file'

    # source is both the source of a symlink or an informational passing of the src for a template module
    # or copy module, even if this module never uses it, it is needed to key off some things
    if src is None:
        if state in ('link', 'hard'):
            if follow and state == 'link':
                # use the current target of the link as the source
                src = to_native(os.path.realpath(b_path), errors='strict')
                b_src = to_bytes(os.path.realpath(b_path), errors='strict')
            else:
                module.fail_json(msg='src and dest are required for creating links')

    # original_basename is used by other modules that depend on file.
    if state not in ("link", "absent") and os.path.isdir(b_path):
        basename = None
        if params['original_basename']:
            basename = params['original_basename']
        elif src is not None:
            basename = os.path.basename(src)
        if basename:
            params['path'] = path = os.path.join(path, basename)
            b_path = to_bytes(path, errors='surrogate_or_strict')
            prev_state = get_state(b_path)

    # make sure the target path is a directory when we're doing a recursive operation
    if recurse and state != 'directory':
        module.fail_json(path=path, msg="recurse option requires state to be 'directory'")

    file_args = module.load_file_common_arguments(params)

    changed = False
    diff = {'before': {'path': path},
            'after': {'path': path},
            }

    state_change = False
    if prev_state != state:
        diff['before']['state'] = prev_state
        diff['after']['state'] = state
        state_change = True

    if state == 'absent':
        if state_change:
            if not module.check_mode:
                if prev_state == 'directory':
                    try:
                        shutil.rmtree(b_path, ignore_errors=False)
                    except Exception as e:
                        module.fail_json(msg="rmtree failed: %s" % to_native(e))
                else:
                    try:
                        os.unlink(b_path)
                    except Exception as e:
                        module.fail_json(path=path, msg="unlinking failed: %s " % to_native(e))
            module.exit_json(path=path, changed=True, diff=diff)
        else:
            module.exit_json(path=path, changed=False)

    elif state == 'file':

        if state_change:
            if follow and prev_state == 'link':
                # follow symlink and operate on original
                b_path = os.path.realpath(b_path)
                path = to_native(b_path, errors='strict')
                prev_state = get_state(b_path)
                file_args['path'] = path

        if prev_state not in ('file', 'hard'):
            # file is not absent and any other state is a conflict
            module.fail_json(path=path, msg='file (%s) is %s, cannot continue' % (path, prev_state))

        changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
        module.exit_json(path=path, changed=changed, diff=diff)

    elif state == 'directory':
        if follow and prev_state == 'link':
            b_path = os.path.realpath(b_path)
            path = to_native(b_path, errors='strict')
            prev_state = get_state(b_path)

        if prev_state == 'absent':
            if module.check_mode:
                module.exit_json(changed=True, diff=diff)
            changed = True
            curpath = ''

            try:
                # Split the path so we can apply filesystem attributes recursively
                # from the root (/) directory for absolute paths or the base path
                # of a relative path.  We can then walk the appropriate directory
                # path to apply attributes.
                for dirname in path.strip('/').split('/'):
                    curpath = '/'.join([curpath, dirname])
                    # Remove leading slash if we're creating a relative path
                    if not os.path.isabs(path):
                        curpath = curpath.lstrip('/')
                    b_curpath = to_bytes(curpath, errors='surrogate_or_strict')
                    if not os.path.exists(b_curpath):
                        try:
                            os.mkdir(b_curpath)
                        except OSError as ex:
                            # Possibly something else created the dir since the os.path.exists
                            # check above. As long as it's a dir, we don't need to error out.
                            if not (ex.errno == errno.EEXIST and os.path.isdir(b_curpath)):
                                raise
                        tmp_file_args = file_args.copy()
                        tmp_file_args['path'] = curpath
                        changed = module.set_fs_attributes_if_different(tmp_file_args, changed, diff, expand=False)
            except Exception as e:
                module.fail_json(path=path, msg='There was an issue creating %s as requested: %s' % (curpath, to_native(e)))

        # We already know prev_state is not 'absent', therefore it exists in some form.
        elif prev_state != 'directory':
            module.fail_json(path=path, msg='%s already exists as a %s' % (path, prev_state))

        changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)

        if recurse:
            changed |= recursive_set_attributes(module, to_bytes(file_args['path'], errors='surrogate_or_strict'), follow, file_args)

        module.exit_json(path=path, changed=changed, diff=diff)

    elif state in ('link', 'hard'):

        if not os.path.islink(b_path) and os.path.isdir(b_path):
            relpath = path
        else:
            b_relpath = os.path.dirname(b_path)
            relpath = to_native(b_relpath, errors='strict')

        absrc = os.path.join(relpath, src)
        b_absrc = to_bytes(absrc, errors='surrogate_or_strict')
        if not force and not os.path.exists(b_absrc):
            module.fail_json(path=path, src=src, msg='src file does not exist, use "force=yes" if you really want to create the link: %s' % absrc)

        if state == 'hard':
            if not os.path.isabs(b_src):
                module.fail_json(msg="absolute paths are required")
        elif prev_state == 'directory':
            if not force:
                module.fail_json(path=path, msg='refusing to convert between %s and %s for %s' % (prev_state, state, path))
            elif os.listdir(b_path):
                # refuse to replace a directory that has files in it
                module.fail_json(path=path, msg='the directory %s is not empty, refusing to convert it' % path)
        elif prev_state in ('file', 'hard') and not force:
            module.fail_json(path=path, msg='refusing to convert between %s and %s for %s' % (prev_state, state, path))

        if prev_state == 'absent':
            changed = True
        elif prev_state == 'link':
            b_old_src = os.readlink(b_path)
            if b_old_src != b_src:
                diff['before']['src'] = to_native(b_old_src, errors='strict')
                diff['after']['src'] = src
                changed = True
        elif prev_state == 'hard':
            if not (state == 'hard' and os.stat(b_path).st_ino == os.stat(b_src).st_ino):
                changed = True
                if not force:
                    module.fail_json(dest=path, src=src, msg='Cannot link, different hard link exists at destination')
        elif prev_state == 'file':
            changed = True
            if not force:
                module.fail_json(dest=path, src=src, msg='Cannot link, %s exists at destination' % prev_state)
        elif prev_state == 'directory':
            changed = True
            if os.path.exists(b_path):
                if state == 'hard' and os.stat(b_path).st_ino == os.stat(b_src).st_ino:
                    module.exit_json(path=path, changed=False)
                elif not force:
                    module.fail_json(dest=path, src=src, msg='Cannot link, different hard link exists at destination')
        else:
            module.fail_json(dest=path, src=src, msg='unexpected position reached')

        if changed and not module.check_mode:
            if prev_state != 'absent':
                # try to replace atomically
                b_tmppath = to_bytes(os.path.sep).join(
                    [os.path.dirname(b_path), to_bytes(".%s.%s.tmp" % (os.getpid(), time.time()))]
                )
                try:
                    if prev_state == 'directory' and state == 'link':
                        os.rmdir(b_path)
                    elif prev_state == 'directory' and state == 'hard':
                        if os.path.exists(b_path):
                            os.remove(b_path)
                    if state == 'hard':
                        os.link(b_src, b_tmppath)
                    else:
                        os.symlink(b_src, b_tmppath)
                    os.rename(b_tmppath, b_path)
                except OSError as e:
                    if os.path.exists(b_tmppath):
                        os.unlink(b_tmppath)
                    module.fail_json(path=path, msg='Error while replacing: %s' % to_native(e, nonstring='simplerepr'))
            else:
                try:
                    if state == 'hard':
                        os.link(b_src, b_path)
                    else:
                        os.symlink(b_src, b_path)
                except OSError as e:
                    module.fail_json(path=path, msg='Error while linking: %s' % to_native(e, nonstring='simplerepr'))

        if module.check_mode and not os.path.exists(b_path):
            module.exit_json(dest=path, src=src, changed=changed, diff=diff)

        changed = module.set_fs_attributes_if_different(file_args, changed, diff, expand=False)
        module.exit_json(dest=path, src=src, changed=changed, diff=diff)

    elif state == 'touch':
        if not module.check_mode:

            if prev_state == 'absent':
                try:
                    open(b_path, 'wb').close()
                except (OSError, IOError) as e:
                    module.fail_json(path=path, msg='Error, could not touch target: %s' % to_native(e, nonstring='simplerepr'))
            elif prev_state in ('file', 'directory', 'hard'):
                try:
                    os.utime(b_path, None)
                except OSError as e:
                    module.fail_json(path=path, msg='Error while touching existing target: %s' % to_native(e, nonstring='simplerepr'))
            else:
                module.fail_json(msg='Cannot touch other than files, directories, and hardlinks (%s is %s)' % (path, prev_state))
            try:
                module.set_fs_attributes_if_different(file_args, True, diff, expand=False)
            except SystemExit as e:
                if e.code:
                    # We take this to mean that fail_json() was called from
                    # somewhere in basic.py
                    if prev_state == 'absent':
                        # If we just created the file we can safely remove it
                        os.remove(b_path)
                raise e

        module.exit_json(dest=path, changed=True, diff=diff)

    module.fail_json(path=path, msg='unexpected position reached')

if __name__ == '__main__':
    main()
