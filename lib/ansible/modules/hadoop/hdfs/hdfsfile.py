#!/usr/bin/python
# -*- coding: utf-8 -*-

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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: hdfsfile
short_description: Sets attributes of hdfs files
extends_documentation_fragment: hdfs
description:
     - Sets attributes of HDFS files and directories, or removes
       files/directories.
version_added: "2.8"
requirements: [ pywhdfs ]
author:
    - Yassine Azzouz (@yassineazzouz)
    - Alex Willmer (@moreati)
options:
  path:
    description:
      - 'path to the file being managed.  Aliases: I(dest), I(name)'
    required: true
    aliases: ['dest', 'name']
  state:
    required: false
    default: file
    description:
      - If C(directory), all immediate subdirectories will be created if they
        do not exist, they will be created with the supplied permissions.
        If C(file), the file will NOT be created if it does not exist.
        If C(absent), directories and files will be recursively deleted.
        If C(touch), an empty file will be created if the C(path) does not
        exist, while an existing file or directory will receive updated file access and
        modification times (similar to the way `touch` works from the command line).
    choices: [ file, directory, touch, absent ]
  owner:
    required: false
    default: null
    description:
      - name of the user that should own the file/directory, as would be fed to I(chown)
  group:
    required: false
    default: null
    description:
      - name of the group that should own the file/directory, as would be fed to I(chown)
  mode:
    required: false
    default: null
    description:
      - mode the file or directory should be. For those used to I(/usr/bin/chmod)
        remember that modes are actually octal numbers (like 0644).
        Leaving off the leading zero will likely have unexpected results.
        The mode may be specified as a symbolic mode (for example, C(u+rwx) or C(u=rw,g=r,o=r)).
  replication:
    required: false
    default: null
    description:
      - The replication factor to be applied to the file. This option applies only to files.
  namequota:
    required: false
    default: null
    description:
      - The name quota to be applied to the directory. This option applies only to directories.
  spacequota:
    required: false
    default: null
    description:
      - The space quota to be applied to the directory. This option applies only to directories.
  recursive:
    required: false
    default: false
    type: bool
    description:
      - recursively set the specified file attributes (applies only to state=directory)
'''

EXAMPLES = '''
- name: "Create test Folder"
  hdfsfile:
    authentication: "kerberos"
    principal: "hdfs@HADOOP.LOCALDOMAIN"
    password: "{{hdfs_kerberos_password}}"
    verify: True
    truststore: "/opt/cloudera/security/cacerts/platform-ca.crt"
    state: "directory"
    path: "/user/yassine"
    urls: "{{namenodes_urls}}"
    mode: "u=rw,g=r,o=rwX"

- name: "Create subdirectory"
  hdfsfile:
    authentication: "kerberos"
    principal: "hdfs@HADOOP.LOCALDOMAIN"
    password: "{{hdfs_kerberos_password}}"
    verify: True
    truststore: "/opt/cloudera/security/cacerts/platform-ca.crt"
    state: "directory"
    path: "/user/yassine/subdir"
    owner: "hadoop"
    group: "supergroup"
    mode: 0766
    urls: "{{namenodes_urls}}"

- name: "Remove directory"
  hdfsfile:
    authentication: "kerberos"
    principal: "hdfs@HADOOP.LOCALDOMAIN"
    password: "{{hdfs_kerberos_password}}"
    verify: True
    truststore: "/opt/cloudera/security/cacerts/platform-ca.crt"
    state: "absent"
    path: "/user/yassine/subdir"
    urls: "{{namenodes_urls}}"
'''

RETURN = '''
path:
    description: HDFS Path of the target file.
    returned: always
    type: str
'''

import time

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.hdfsbase import HDFSAnsibleModule, hdfs_argument_spec, hdfs_required_together, hdfs_mutually_exclusive, hdfs_required_if


# recursive,spacequota and namequota  options requires state to be 'directory'
def invalid_if():
    return [
        ('state', 'file', ['recursive', 'spacequota', 'namequota']),
        ('state', 'touch', ['recursive', 'spacequota', 'namequota']),
        ('state', 'absent', ['recursive', 'spacequota', 'namequota']),
    ]


def main():
    argument_spec = hdfs_argument_spec()
    argument_spec.update(
        state=dict(choices=['file', 'directory', 'touch', 'absent'], default='file'),
        path=dict(aliases=['dest', 'name'], required=True),
        owner=dict(required=False, default=None),
        group=dict(required=False, default=None),
        mode=dict(required=False, default=None, type='raw'),
        replication=dict(required=False, default=None),
        namequota=dict(required=False, default=None),
        spacequota=dict(required=False, default=None),
        recursive=dict(default=False, type='bool'),
    )

    required_together = hdfs_required_together()
    mutually_exclusive = hdfs_mutually_exclusive()
    required_if = hdfs_required_if()

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        mutually_exclusive=mutually_exclusive
    )

    hdfs = HDFSAnsibleModule(module, invalid_if=invalid_if())

    # The ansible file module uses a dict called file_args then populate it with file parameters
    # Tehn pass that dict as an argument to other functions.
    # I personally find that oweful since it make undrestanding what is beeing passed to the function each time
    # very difficult,so the developer have to follow the code from the begining to see what is beeing changed.
    ''' Get all hdfs arguments '''
    params = module.params
    state = params['state']
    path = params['path']
    recursive = params['recursive']
    owner = params['owner']
    group = params['group']
    replication = params['replication']
    mode = params['mode']
    spacequota = params['spacequota']
    namequota = params['namequota']

    prev_state = hdfs.get_state(path)

    # state should default to file, but since that creates many conflicts,
    # default to 'current' when it exists.
    if state is None:
        if prev_state != 'absent':
            state = prev_state
        else:
            state = 'file'

    changed = False

    if state == 'absent':
        if state != prev_state:
            if prev_state == 'directory' or prev_state == 'file':
                hdfs.hdfs_delete(path, recursive=True)
            module.exit_json(path=path, changed=True)
        else:
            module.exit_json(path=path, changed=False)

    elif state == 'file':
        if prev_state != 'file':
            # file is not absent and any other state is a conflict
            hdfs.hdfs_fail_json(path=path, msg='file (%s) is %s, cannot continue' % (path, prev_state))

        if spacequota is not None or namequota is not None:
            # Duplicated check
            # file is not absent and any other state is a conflict
            hdfs.hdfs_fail_json(path=path, msg="spacequota and namequota options requires state to be 'directory'" % (path))

        changed |= hdfs.hdfs_set_attributes(path=path, owner=owner, group=group,
                                            replication=replication, permission=mode)

        module.exit_json(path=path, changed=changed)

    elif state == 'directory':
        if prev_state == 'absent':
            changed = True
            curpath = ''
            # Split the path so we can apply filesystem attributes recursively from the root (/) directory for absolute paths or the base path
            # of a relative path.  We can then walk the appropriate directory path to apply attributes.
            for dirname in path.strip('/').split('/'):
                curpath = '/'.join([curpath, dirname])
                if not hdfs.hdfs_exist(curpath):
                    hdfs.hdfs_makedirs(curpath)
                    changed |= hdfs.hdfs_set_attributes(path=curpath, owner=owner, group=group,
                                                        replication=replication,
                                                        permission=mode)
        # We already know prev_state is not 'absent', therefore it exists in some form.
        elif prev_state != 'directory':
            hdfs.hdfs_fail_json(path=path, msg='%s already exists as a %s' % (path, prev_state))

        # Set the attribute for the actual destination path
        # Quotas are never set recursively; just to the destination directory
        changed |= hdfs.hdfs_set_attributes(path=path, owner=owner, group=group, replication=replication,
                                            quota=namequota, spaceQuota=spacequota, permission=mode)

        if recursive:
            changed |= hdfs.hdfs_set_attributes_recursive(path=path, owner=owner, group=group, replication=replication, permission=mode)

        module.exit_json(path=path, changed=changed)

    elif state == 'touch':
        if prev_state == 'absent':
            hdfs.hdfs_touch(path)
        elif prev_state in ['file', 'directory']:
            ts = int(time.time() * 1000)
            hdfs.hdfs_set_times(path, access_time=ts, modification_time=ts)
        else:
            hdfs.hdfs_fail_json(msg='Cannot touch other than files, directories (%s is %s)' % (path, prev_state))

        # If the set attribute fails we need make sure to delete the created file
        # No way to catch errors at this stage : maybe a function at the hdfsbase level could help
        #  client.delete(path)
        hdfs.hdfs_set_attributes(path=path, owner=owner, group=group, replication=replication, permission=mode)

        module.exit_json(path=path, changed=True)

    hdfs.hdfs_fail_json(path=path, msg='unexpected position reached')


if __name__ == '__main__':
    main()
