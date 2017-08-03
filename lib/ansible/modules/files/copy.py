#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: copy
version_added: "historical"
short_description: Copies files to remote locations
description:
    - The C(copy) module copies a file from the local or remote machine to a location on the remote machine.
      Use the M(fetch) module to copy files from remote locations to the local box.
      If you need variable interpolation in copied files, use the M(template) module.
    - For Windows targets, use the M(win_copy) module instead.
options:
  src:
    description:
      - Local path to a file to copy to the remote server; can be absolute or relative.
        If path is a directory, it is copied recursively. In this case, if path ends
        with "/", only inside contents of that directory are copied to destination.
        Otherwise, if it does not end with "/", the directory itself with all contents
        is copied. This behavior is similar to Rsync.
  content:
    description:
      - When used instead of 'src', sets the contents of a file directly to the specified value.
        For anything advanced or with formatting also look at the template module.
    version_added: "1.1"
  dest:
    description:
      - Remote absolute path where the file should be copied to. If C(src) is a directory,
        this must be a directory too.
    required: yes
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: 'no'
    version_added: "0.7"
  force:
    description:
      - the default is C(yes), which will replace the remote file when contents
        are different than the source. If C(no), the file will only be transferred
        if the destination does not exist.
    type: bool
    default: 'yes'
    aliases: [ "thirsty" ]
    version_added: "1.1"
  directory_mode:
    description:
      - When doing a recursive copy set the mode for the directories. If this is not set we will use the system
        defaults. The mode is only set on directories which are newly created, and will not affect those that
        already existed.
    version_added: "1.5"
  remote_src:
    description:
      - If C(no), it will search for src at originating/master machine.
      - If C(yes), it will go to the remote/target machine for the src. Default is False.
      - Currently C(remote_src) does not support recursive copying.
    type: bool
    default: 'no'
    version_added: "2.0"
  follow:
    description:
      - This flag indicates that filesystem links in the destination, if they exist, should be followed.
    type: bool
    default: 'no'
    version_added: "1.8"
  local_follow:
    description:
      - This flag indicates that filesystem links in the source tree, if they exist, should be followed.
    type: bool
    default: 'yes'
    version_added: "2.4"
extends_documentation_fragment:
    - files
    - validate
    - decrypt
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
notes:
   - The "copy" module recursively copy facility does not scale to lots (>hundreds) of files.
     For alternative, see synchronize module, which is a wrapper around rsync.
   - For Windows targets, use the M(win_copy) module instead.
'''

EXAMPLES = r'''
# Example from Ansible Playbooks
- copy:
    src: /srv/myfiles/foo.conf
    dest: /etc/foo.conf
    owner: foo
    group: foo
    mode: 0644

# The same example as above, but using a symbolic mode equivalent to 0644
- copy:
    src: /srv/myfiles/foo.conf
    dest: /etc/foo.conf
    owner: foo
    group: foo
    mode: u=rw,g=r,o=r

# Another symbolic mode example, adding some permissions and removing others
- copy:
    src: /srv/myfiles/foo.conf
    dest: /etc/foo.conf
    owner: foo
    group: foo
    mode: u+rw,g-wx,o-rwx

# Copy a new "ntp.conf file into place, backing up the original if it differs from the copied version
- copy:
    src: /mine/ntp.conf
    dest: /etc/ntp.conf
    owner: root
    group: root
    mode: 0644
    backup: yes

# Copy a new "sudoers" file into place, after passing validation with visudo
- copy:
    src: /mine/sudoers
    dest: /etc/sudoers
    validate: /usr/sbin/visudo -cf %s

# Copy a "sudoers" file on the remote machine for editing
- copy:
    src: /etc/sudoers
    dest: /etc/sudoers.edit
    remote_src: yes
    validate: /usr/sbin/visudo -cf %s

# Create a CSV file from your complete inventory using an inline template
- hosts: all
  tasks:
  - copy:
      content: |
        HOSTNAME;IPADDRESS;FQDN;OSNAME;OSVERSION;PROCESSOR;ARCHITECTURE;MEMORY;
        {% for host in hostvars %}
        {%   set vars = hostvars[host|string] %}
        {{ vars.ansible_hostname }};{{ vars.remote_host }};{{ vars.ansible_fqdn }};{{ vars.ansible_distribution }};{{ vars.ansible_distribution_version }};{{ vars.ansible_processor[1] }};{{ vars.ansible_architecture }};{{ (vars.ansible_memtotal_mb/1024)|round|int }};  # NOQA
        {% endfor %}
      dest: /some/path/systems.csv
      backup: yes
    run_once: yes
    delegate_to: localhost
'''

RETURN = r'''
dest:
    description: destination file/path
    returned: success
    type: string
    sample: /path/to/file.txt
src:
    description: source file used for the copy on the target machine
    returned: changed
    type: string
    sample: /home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source
md5sum:
    description: md5 checksum of the file after running copy
    returned: when supported
    type: string
    sample: 2a5aeecc61dc98c4d780b14b330e3282
checksum:
    description: sha1 checksum of the file after running copy
    returned: success
    type: string
    sample: 6e642bb8dd5c2e027bf21dd923337cbb4214f827
backup_file:
    description: name of backup file created
    returned: changed and if backup=yes
    type: string
    sample: /path/to/file.txt.2015-02-12@22:09~
gid:
    description: group id of the file, after execution
    returned: success
    type: int
    sample: 100
group:
    description: group of the file, after execution
    returned: success
    type: string
    sample: httpd
owner:
    description: owner of the file, after execution
    returned: success
    type: string
    sample: httpd
uid:
    description: owner id of the file, after execution
    returned: success
    type: int
    sample: 100
mode:
    description: permissions of the target, after execution
    returned: success
    type: string
    sample: 0644
size:
    description: size of the target, after execution
    returned: success
    type: int
    sample: 1220
state:
    description: state of the target, after execution
    returned: success
    type: string
    sample: file
'''

import os
import shutil
import tempfile
import traceback

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native


def split_pre_existing_dir(dirname):
    '''
    Return the first pre-existing directory and a list of the new directories that will be created.
    '''

    head, tail = os.path.split(dirname)
    b_head = to_bytes(head, errors='surrogate_or_strict')
    if not os.path.exists(b_head):
        (pre_existing_dir, new_directory_list) = split_pre_existing_dir(head)
    else:
        return (head, [tail])
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
        argument_spec=dict(
            src=dict(type='path'),
            original_basename=dict(type='str'),  # used to handle 'dest is a directory' via template, a slight hack
            content=dict(type='str', no_log=True),
            dest=dict(type='path', required=True),
            backup=dict(type='bool', default=False),
            force=dict(type='bool', default=True, aliases=['thirsty']),
            validate=dict(type='str'),
            directory_mode=dict(type='raw'),
            remote_src=dict(type='bool'),
            local_follow=dict(type='bool'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    src = module.params['src']
    b_src = to_bytes(src, errors='surrogate_or_strict')
    dest = module.params['dest']
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    backup = module.params['backup']
    force = module.params['force']
    original_basename = module.params.get('original_basename', None)
    validate = module.params.get('validate', None)
    follow = module.params['follow']
    mode = module.params['mode']
    remote_src = module.params['remote_src']

    if not os.path.exists(b_src):
        module.fail_json(msg="Source %s not found" % (src))
    if not os.access(b_src, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (src))
    if os.path.isdir(b_src):
        module.fail_json(msg="Remote copy does not support recursive copy of directory: %s" % (src))

    checksum_src = module.sha1(src)
    checksum_dest = None
    # Backwards compat only.  This will be None in FIPS mode
    try:
        md5sum_src = module.md5(src)
    except ValueError:
        md5sum_src = None

    changed = False

    # Special handling for recursive copy - create intermediate dirs
    if original_basename and dest.endswith(os.sep):
        dest = os.path.join(dest, original_basename)
        b_dest = to_bytes(dest, errors='surrogate_or_strict')
        dirname = os.path.dirname(dest)
        b_dirname = to_bytes(dirname, errors='surrogate_or_strict')
        if not os.path.exists(b_dirname) and os.path.isabs(b_dirname):
            (pre_existing_dir, new_directory_list) = split_pre_existing_dir(dirname)
            os.makedirs(b_dirname)
            directory_args = module.load_file_common_arguments(module.params)
            directory_mode = module.params["directory_mode"]
            if directory_mode is not None:
                directory_args['mode'] = directory_mode
            else:
                directory_args['mode'] = None
            adjust_recursive_directory_permissions(pre_existing_dir, new_directory_list, module, directory_args, changed)

    if os.path.isdir(b_dest):
        basename = os.path.basename(src)
        if original_basename:
            basename = original_basename
        dest = os.path.join(dest, basename)
        b_dest = to_bytes(dest, errors='surrogate_or_strict')

    if os.path.exists(b_dest):
        if os.path.islink(b_dest) and follow:
            b_dest = os.path.realpath(b_dest)
            dest = to_native(b_dest, errors='surrogate_or_strict')
        if not force:
            module.exit_json(msg="file already exists", src=src, dest=dest, changed=False)
        if os.access(b_dest, os.R_OK):
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
                    # FIXME: should we do the same for owner/group here too?
                    if mode is not None:
                        module.set_mode_if_different(src, mode, False)
                    if "%s" not in validate:
                        module.fail_json(msg="validate must contain %%s: %s" % (validate))
                    (rc, out, err) = module.run_command(validate % src)
                    if rc != 0:
                        module.fail_json(msg="failed to validate", exit_status=rc, stdout=out, stderr=err)
                b_mysrc = b_src
                if remote_src:
                    _, b_mysrc = tempfile.mkstemp(dir=os.path.dirname(b_dest))
                    shutil.copy2(b_src, b_mysrc)
                module.atomic_move(b_mysrc, dest, unsafe_writes=module.params['unsafe_writes'])
            except IOError:
                module.fail_json(msg="failed to copy: %s to %s" % (src, dest), traceback=traceback.format_exc())
        changed = True
    else:
        changed = False

    res_args = dict(
        dest=dest, src=src, md5sum=md5sum_src, checksum=checksum_src, changed=changed
    )
    if backup_file:
        res_args['backup_file'] = backup_file

    module.params['dest'] = dest
    if not module.check_mode:
        file_args = module.load_file_common_arguments(module.params)
        res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'])

    module.exit_json(**res_args)

if __name__ == '__main__':
    main()
