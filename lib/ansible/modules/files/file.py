#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import shutil
import stat
import grp
import pwd
try:
    import selinux
    HAVE_SELINUX=True
except ImportError:
    HAVE_SELINUX=False

DOCUMENTATION = '''
---
module: file
version_added: "historical"
short_description: Sets attributes of files
extends_documentation_fragment: files
description: 
     - Sets attributes of files, symlinks, and directories, or removes
       files/symlinks/directories. Many other modules support the same options as
       the M(file) module - including M(copy), M(template), and M(assemble).
notes:
    - See also M(copy), M(template), M(assemble)
requirements: [ ]
author: Michael DeHaan
options:
  path:
    description:
      - 'path to the file being managed.  Aliases: I(dest), I(name)'
    required: true
    default: []
    aliases: ['dest', 'name'] 
  state:
    description:
      - If C(directory), all immediate subdirectories will be created if they
        do not exist, since 1.7 they will be created with the supplied permissions.
        If C(file), the file will NOT be created if it does not exist, see the M(copy)
        or M(template) module if you want that behavior.  If C(link), the symbolic
        link will be created or changed. Use C(hard) for hardlinks. If C(absent),
        directories will be recursively deleted, and files or symlinks will be unlinked.
        If C(touch) (new in 1.4), an empty file will be created if the c(path) does not
        exist, while an existing file or directory will receive updated file access and
        modification times (similar to the way `touch` works from the command line).
    required: false
    default: file
    choices: [ file, link, directory, hard, touch, absent ]
  src:
    required: false
    default: null
    choices: []
    description:
      - path of the file to link to (applies only to C(state=link)). Will accept absolute,
        relative and nonexisting paths. Relative paths are not expanded.
  recurse:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    version_added: "1.1"
    description:
      - recursively set the specified file attributes (applies only to state=directory)
  force:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    description:
      - 'force the creation of the symlinks in two cases: the source file does 
        not exist (but will appear later); the destination exists and is a file (so, we need to unlink the
        "path" file and create symlink to the "src" file in place of it).'
'''

EXAMPLES = '''
# change file ownership, group and mode. When specifying mode using octal numbers, first digit should always be 0.
- file: path=/etc/foo.conf owner=foo group=foo mode=0644
- file: src=/file/to/link/to dest=/path/to/symlink owner=foo group=foo state=link
- file: src=/tmp/{{ item.path }} dest={{ item.dest }} state=link
  with_items:
    - { path: 'x', dest: 'y' }
    - { path: 'z', dest: 'k' }

# touch a file, using symbolic modes to set the permissions (equivalent to 0644)
- file: path=/etc/foo.conf state=touch mode="u=rw,g=r,o=r"

# touch the same file, but add/remove some permissions
- file: path=/etc/foo.conf state=touch mode="u+rw,g-wx,o-rwx"

'''


def get_state(path):
    ''' Find out current state '''

    if os.path.lexists(path):
        if os.path.islink(path):
            return 'link'
        elif os.path.isdir(path):
            return 'directory'
        elif os.stat(path).st_nlink > 1:
            return 'hard'
        else:
            # could be many other things, but defaulting to file
            return 'file'

    return 'absent'

def recursive_set_attributes(module, path, follow, file_args):
    changed = False
    for root, dirs, files in os.walk(path):
        for fsobj in dirs + files:
            fsname = os.path.join(root, fsobj)
            if not os.path.islink(fsname):
                tmp_file_args = file_args.copy()
                tmp_file_args['path']=fsname
                changed |= module.set_fs_attributes_if_different(tmp_file_args, changed)
            else:
                tmp_file_args = file_args.copy()
                tmp_file_args['path']=fsname
                changed |= module.set_fs_attributes_if_different(tmp_file_args, changed)
                if follow:
                    fsname = os.path.join(root, os.readlink(fsname))
                    if os.path.isdir(fsname):
                        changed |= recursive_set_attributes(module, fsname, follow, file_args)
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path']=fsname
                    changed |= module.set_fs_attributes_if_different(tmp_file_args, changed)
    return changed

def main():

    module = AnsibleModule(
        argument_spec = dict(
            state = dict(choices=['file','directory','link','hard','touch','absent'], default=None),
            path  = dict(aliases=['dest', 'name'], required=True),
            original_basename = dict(required=False), # Internal use only, for recursive ops
            recurse  = dict(default='no', type='bool'),
            force = dict(required=False,default=False,type='bool'),
            diff_peek = dict(default=None),
            validate = dict(required=False, default=None),
            src = dict(required=False, default=None),
        ),
        add_file_common_args=True,
        supports_check_mode=True
    )

    params = module.params
    state  = params['state']
    force = params['force']
    diff_peek = params['diff_peek']
    src = params['src']
    follow = params['follow']

    # modify source as we later reload and pass, specially relevant when used by other modules.
    params['path'] = path = os.path.expanduser(params['path'])

    # short-circuit for diff_peek
    if diff_peek is not None:
        appears_binary = False
        try:
            f = open(path)
            b = f.read(8192)
            f.close()
            if "\x00" in b:
                appears_binary = True
        except:
            pass
        module.exit_json(path=path, changed=False, appears_binary=appears_binary)

    prev_state = get_state(path)

    # state should default to file, but since that creates many conflicts,
    # default to 'current' when it exists.
    if state is None:
        if prev_state != 'absent':
            state = prev_state
        else:
            state = 'file'

    # source is both the source of a symlink or an informational passing of the src for a template module
    # or copy module, even if this module never uses it, it is needed to key off some things
    if src is not None:
        src = os.path.expanduser(src)
    else:
        if state in ['link','hard']:
            if follow and state == 'link':
                # use the current target of the link as the source
                src = os.path.realpath(path)
            else:
                module.fail_json(msg='src and dest are required for creating links')

    # original_basename is used by other modules that depend on file.
    if os.path.isdir(path) and state not in ["link", "absent"]:
        basename = None
        if params['original_basename']:
            basename = params['original_basename']
        elif src is not None:
            basename = os.path.basename(src)
        if basename:
            params['path'] = path = os.path.join(path, basename)

    # make sure the target path is a directory when we're doing a recursive operation
    recurse = params['recurse']
    if recurse and state != 'directory':
        module.fail_json(path=path, msg="recurse option requires state to be 'directory'")

    file_args = module.load_file_common_arguments(params)
    changed = False

    if state == 'absent':
        if state != prev_state:
            if not module.check_mode:
                if prev_state == 'directory':
                    try:
                        shutil.rmtree(path, ignore_errors=False)
                    except Exception, e:
                        module.fail_json(msg="rmtree failed: %s" % str(e))
                else:
                    try:
                        os.unlink(path)
                    except Exception, e:
                        module.fail_json(path=path, msg="unlinking failed: %s " % str(e))
            module.exit_json(path=path, changed=True)
        else:
            module.exit_json(path=path, changed=False)

    elif state == 'file':

        if state != prev_state:
            if follow and prev_state == 'link':
                # follow symlink and operate on original
                path = os.path.realpath(path)
                prev_state = get_state(path)
                file_args['path'] = path

        if prev_state not in ['file','hard']:
            # file is not absent and any other state is a conflict
            module.fail_json(path=path, msg='file (%s) is %s, cannot continue' % (path, prev_state))

        changed = module.set_fs_attributes_if_different(file_args, changed)
        module.exit_json(path=path, changed=changed)

    elif state == 'directory':
        if follow and prev_state == 'link':
            path = os.path.realpath(path)
            prev_state = get_state(path)

        if prev_state == 'absent':
            if module.check_mode:
                module.exit_json(changed=True)
            changed = True
            curpath = ''
            # Split the path so we can apply filesystem attributes recursively
            # from the root (/) directory for absolute paths or the base path
            # of a relative path.  We can then walk the appropriate directory
            # path to apply attributes.
            for dirname in path.strip('/').split('/'):
                curpath = '/'.join([curpath, dirname])
                # Remove leading slash if we're creating a relative path
                if not os.path.isabs(path):
                    curpath = curpath.lstrip('/')
                if not os.path.exists(curpath):
                    os.mkdir(curpath)
                    tmp_file_args = file_args.copy()
                    tmp_file_args['path']=curpath
                    changed = module.set_fs_attributes_if_different(tmp_file_args, changed)

        # We already know prev_state is not 'absent', therefore it exists in some form.
        elif prev_state != 'directory':
            module.fail_json(path=path, msg='%s already exists as a %s' % (path, prev_state))

        changed = module.set_fs_attributes_if_different(file_args, changed)

        if recurse:
            changed |= recursive_set_attributes(module, file_args['path'], follow, file_args)

        module.exit_json(path=path, changed=changed)

    elif state in ['link','hard']:

        if os.path.isdir(path) and not os.path.islink(path):
            relpath = path
        else:
            relpath = os.path.dirname(path)

        absrc = os.path.join(relpath, src)
        if not os.path.exists(absrc) and not force:
            module.fail_json(path=path, src=src, msg='src file does not exist, use "force=yes" if you really want to create the link: %s' % absrc)

        if state == 'hard':
            if not os.path.isabs(src):
                module.fail_json(msg="absolute paths are required")
        elif prev_state == 'directory':
            if not force:
                module.fail_json(path=path, msg='refusing to convert between %s and %s for %s' % (prev_state, state, path))
            elif len(os.listdir(path)) > 0:
                # refuse to replace a directory that has files in it
                module.fail_json(path=path, msg='the directory %s is not empty, refusing to convert it' % path)
        elif prev_state in ['file', 'hard'] and not force:
            module.fail_json(path=path, msg='refusing to convert between %s and %s for %s' % (prev_state, state, path))

        if prev_state == 'absent':
            changed = True
        elif prev_state == 'link':
            old_src = os.readlink(path)
            if old_src != src:
                changed = True
        elif prev_state == 'hard':
            if not (state == 'hard' and os.stat(path).st_ino == os.stat(src).st_ino):
                changed = True
                if not force:
                    module.fail_json(dest=path, src=src, msg='Cannot link, different hard link exists at destination')
        elif prev_state in ['file', 'directory']:
            changed = True
            if not force:
                module.fail_json(dest=path, src=src, msg='Cannot link, %s exists at destination' % prev_state)
        else:
            module.fail_json(dest=path, src=src, msg='unexpected position reached')

        if changed and not module.check_mode:
            if prev_state != 'absent':
                # try to replace atomically
                tmppath = '/'.join([os.path.dirname(path), ".%s.%s.tmp" % (os.getpid(),time.time())])
                try:
                    if prev_state == 'directory' and (state == 'hard' or state == 'link'):
                        os.rmdir(path)
                    if state == 'hard':
                        os.link(src,tmppath)
                    else:
                        os.symlink(src, tmppath)
                    os.rename(tmppath, path)
                except OSError, e:
                    if os.path.exists(tmppath):
                        os.unlink(tmppath)
                    module.fail_json(path=path, msg='Error while replacing: %s' % str(e))
            else:
                try:
                    if state == 'hard':
                        os.link(src,path)
                    else:
                        os.symlink(src, path)
                except OSError, e:
                    module.fail_json(path=path, msg='Error while linking: %s' % str(e))

        if module.check_mode and not os.path.exists(path):
            module.exit_json(dest=path, src=src, changed=changed)

        changed = module.set_fs_attributes_if_different(file_args, changed)
        module.exit_json(dest=path, src=src, changed=changed)

    elif state == 'touch':
        if not module.check_mode:

            if prev_state == 'absent':
                try:
                    open(path, 'w').close()
                except OSError, e:
                    module.fail_json(path=path, msg='Error, could not touch target: %s' % str(e))
            elif prev_state in ['file', 'directory', 'hard']:
                try:
                    os.utime(path, None)
                except OSError, e:
                    module.fail_json(path=path, msg='Error while touching existing target: %s' % str(e))
            else:
                module.fail_json(msg='Cannot touch other than files, directories, and hardlinks (%s is %s)' % (path, prev_state))
            try:
                module.set_fs_attributes_if_different(file_args, True)
            except SystemExit, e:
                if e.code:
                    # We take this to mean that fail_json() was called from
                    # somewhere in basic.py
                    if prev_state == 'absent':
                        # If we just created the file we can safely remove it
                        os.remove(path)
                raise e

        module.exit_json(dest=path, changed=True)

    module.fail_json(path=path, msg='unexpected position reached')

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()

