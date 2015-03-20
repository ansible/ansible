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

import os
import time

DOCUMENTATION = '''
---
module: copy
version_added: "historical"
short_description: Copies files to remote locations.
description:
     - The M(copy) module copies a file on the local box to remote locations. Use the M(fetch) module to copy files from remote locations to the local box.
options:
  src:
    description:
      - Local path to a file to copy to the remote server; can be absolute or relative.
        If path is a directory, it is copied recursively. In this case, if path ends
        with "/", only inside contents of that directory are copied to destination.
        Otherwise, if it does not end with "/", the directory itself with all contents
        is copied. This behavior is similar to Rsync.
    required: false
    default: null
    aliases: []
  content:
    version_added: "1.1"
    description:
      - When used instead of 'src', sets the contents of a file directly to the specified value.
    required: false
    default: null
  dest:
    description:
      - Remote absolute path where the file should be copied to. If src is a directory,
        this must be a directory too.
    required: true
    default: null
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    version_added: "0.7"
    required: false
    choices: [ "yes", "no" ]
    default: "no"
  force:
    description:
      - the default is C(yes), which will replace the remote file when contents
        are different than the source.  If C(no), the file will only be transferred
        if the destination does not exist.
    version_added: "1.1"
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
    aliases: [ "thirsty" ]
  validate:
    description:
      - The validation command to run before copying into place.  The path to the file to
        validate is passed in via '%s' which must be present as in the visudo example below.
        The command is passed securely so shell features like expansion and pipes won't work.
    required: false
    default: ""
    version_added: "1.2"
  directory_mode:
    description:
      - When doing a recursive copy set the mode for the directories. If this is not set we will use the system
        defaults. The mode is only set on directories which are newly created, and will not affect those that
        already existed.
    required: false
    version_added: "1.5"
extends_documentation_fragment: files
author: Michael DeHaan
notes:
   - The "copy" module recursively copy facility does not scale to lots (>hundreds) of files.
     For alternative, see synchronize module, which is a wrapper around rsync.
'''

EXAMPLES = '''
# Example from Ansible Playbooks
- copy: src=/srv/myfiles/foo.conf dest=/etc/foo.conf owner=foo group=foo mode=0644

# The same example as above, but using a symbolic mode equivalent to 0644
- copy: src=/srv/myfiles/foo.conf dest=/etc/foo.conf owner=foo group=foo mode="u=rw,g=r,o=r"

# Another symbolic mode example, adding some permissions and removing others
- copy: src=/srv/myfiles/foo.conf dest=/etc/foo.conf owner=foo group=foo mode="u+rw,g-wx,o-rwx"

# Copy a new "ntp.conf file into place, backing up the original if it differs from the copied version
- copy: src=/mine/ntp.conf dest=/etc/ntp.conf owner=root group=root mode=644 backup=yes

# Copy a new "sudoers" file into place, after passing validation with visudo
- copy: src=/mine/sudoers dest=/etc/sudoers validate='visudo -cf %s'
'''

RETURN = '''
dest:
    description: destination file/path
    returned: success
    type: string
    sample: "/path/to/file.txt"
src:
    description: source file used for the copy on the target machine
    returned: changed
    type: string
    sample: "/home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source"
md5sum:
    description: md5 checksum of the file after running copy
    returned: when supported
    type: string
    sample: "2a5aeecc61dc98c4d780b14b330e3282"
checksum:
    description: checksum of the file after running copy
    returned: success
    type: string
    sample: "6e642bb8dd5c2e027bf21dd923337cbb4214f827"
backup_file:
    description: name of backup file created
    returned: changed and if backup=yes
    type: string
    sample: "/path/to/file.txt.2015-02-12@22:09~"
gid:
    description: group id of the file, after execution
    returned: success
    type: int
    sample: 100
group:
    description: group of the file, after execution
    returned: success
    type: string
    sample: "httpd"
owner:
    description: owner of the file, after execution
    returned: success
    type: string
    sample: "httpd"
uid:
    description: owner id of the file, after execution
    returned: success
    type: int
    sample: 100
mode:
    description: permissions of the target, after execution
    returned: success
    type: string
    sample: "0644"
size:
    description: size of the target, after execution
    returned: success
    type: int
    sample: 1220
state:
    description: permissions of the target, after execution
    returned: success
    type: string
    sample: "file"
'''

def split_pre_existing_dir(dirname):
    '''
    Return the first pre-existing directory and a list of the new directories that will be created.
    '''

    head, tail = os.path.split(dirname)
    if not os.path.exists(head):
        (pre_existing_dir, new_directory_list) = split_pre_existing_dir(head)
    else:
        return (head, [ tail ])
    new_directory_list.append(tail)
    return (pre_existing_dir, new_directory_list)


def adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed):
    '''
    Walk the new directories list and make sure that permissions are as we would expect
    '''

    if len(new_directory_list) > 0:
        working_dir = os.path.join(pre_existing_dir, new_directory_list.pop(0))
        directory_args['path'] = working_dir
        changed = module.set_fs_attributes_if_different(directory_args, changed)
        changed = adjust_recursive_directory_permissions(working_dir, new_directory_list, module, directory_args, changed)
    return changed


def main():

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec = dict(
            src               = dict(required=False),
            original_basename = dict(required=False), # used to handle 'dest is a directory' via template, a slight hack
            content           = dict(required=False, no_log=True),
            dest              = dict(required=True),
            backup            = dict(default=False, type='bool'),
            force             = dict(default=True, aliases=['thirsty'], type='bool'),
            validate          = dict(required=False, type='str'),
            directory_mode    = dict(required=False)
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    src    = os.path.expanduser(module.params['src'])
    dest   = os.path.expanduser(module.params['dest'])
    backup = module.params['backup']
    force  = module.params['force']
    original_basename = module.params.get('original_basename',None)
    validate = module.params.get('validate',None)
    follow = module.params['follow']

    if not os.path.exists(src):
        module.fail_json(msg="Source %s failed to transfer" % (src))
    if not os.access(src, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (src))

    checksum_src = module.sha1(src)
    checksum_dest = None
    # Backwards compat only.  This will be None in FIPS mode
    try:
        md5sum_src = module.md5(src)
    except ValueError:
        md5sum_src = None

    changed = False

    # Special handling for recursive copy - create intermediate dirs
    if original_basename and dest.endswith("/"):
        dest = os.path.join(dest, original_basename)
        dirname = os.path.dirname(dest)
        if not os.path.exists(dirname) and os.path.isabs(dirname):
            (pre_existing_dir, new_directory_list) = split_pre_existing_dir(dirname)
            os.makedirs(dirname)
            directory_args = module.load_file_common_arguments(module.params)
            directory_mode = module.params["directory_mode"]
            if directory_mode is not None:
                directory_args['mode'] = directory_mode
            else:
                directory_args['mode'] = None
            adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed)

    if os.path.exists(dest):
        if os.path.islink(dest) and follow:
            dest = os.path.realpath(dest)
        if not force:
            module.exit_json(msg="file already exists", src=src, dest=dest, changed=False)
        if (os.path.isdir(dest)):
            basename = os.path.basename(src)
            if original_basename:
                basename = original_basename
            dest = os.path.join(dest, basename)
        if os.access(dest, os.R_OK):
            checksum_dest = module.sha1(dest)
    else:
        if not os.path.exists(os.path.dirname(dest)):
            try:
                # os.path.exists() can return false in some
                # circumstances where the directory does not have
                # the execute bit for the current user set, in
                # which case the stat() call will raise an OSError 
                os.stat(os.path.dirname(dest))
            except OSError, e:
                if "permission denied" in str(e).lower():
                    module.fail_json(msg="Destination directory %s is not accessible" % (os.path.dirname(dest)))
            module.fail_json(msg="Destination directory %s does not exist" % (os.path.dirname(dest)))
    if not os.access(os.path.dirname(dest), os.W_OK):
        module.fail_json(msg="Destination %s not writable" % (os.path.dirname(dest)))

    backup_file = None
    if checksum_src != checksum_dest or os.path.islink(dest):
        try:
            if backup:
                if os.path.exists(dest):
                    backup_file = module.backup_local(dest)
            # allow for conversion from symlink.
            if os.path.islink(dest):
                os.unlink(dest)
                open(dest, 'w').close()
            if validate:
                if "%s" not in validate:
                    module.fail_json(msg="validate must contain %%s: %s" % (validate))
                (rc,out,err) = module.run_command(validate % src)
                if rc != 0:
                    module.fail_json(msg="failed to validate: rc:%s error:%s" % (rc,err))
            module.atomic_move(src, dest)
        except IOError:
            module.fail_json(msg="failed to copy: %s to %s" % (src, dest))
        changed = True
    else:
        changed = False

    res_args = dict(
        dest = dest, src = src, md5sum = md5sum_src, checksum = checksum_src, changed = changed
    )
    if backup_file:
        res_args['backup_file'] = backup_file

    module.params['dest'] = dest
    file_args = module.load_file_common_arguments(module.params)
    res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'])

    module.exit_json(**res_args)

# import module snippets
from ansible.module_utils.basic import *
main()
