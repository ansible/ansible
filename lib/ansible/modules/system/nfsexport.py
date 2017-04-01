#!/usr/bin/python
#
# Copyright (c) 2017 Randy Nance. All rights reserved.
#
# This file is part of Ansible
#
# Ansible is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Ansible is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with Ansible; if not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = """
---
module: nfsexport
version_added: "2.4"
short_description: This module will configure a nfs exports file
description:
    - This module will configure an nfs share by writing an entry in the exports file.
notes:
    - This module only changes the exports file itself. If changes are made, the
      exportfs command should be run and the nfs daemon reloaded.
author: "Randy Nance"
options:
    path:
        description:
            - Directory to export.
        required: true
    dest:
        description:
           - Export file to write to.
        default: /etc/exports
    clients:
        description:
            - list of nfs clients and host specific options.
        default: "*"
    options:
        description:
            - Nfs export options for all clients in export entry.
    state:
        description:
            - Whether to add or remove export path from file.
        default: present
        choices:
            - present
            - absent
"""

EXAMPLES = """
- name: ensure "/home 10.0.0.1(rw)" exists in /etc/exports
  nfsexport:
    path: /home
    clients: 10.0.0.1(rw)
    state: present

- name: ensure "/nfs/share -sync,root_squash 10.0.0.1(rw) 10.1.0.0/24(ro)" exists in /etc/exports
  nfsexport:
    path: /nfs/share
    clients:
      - 10.0.0.1(rw)
      - 10.1.0.0/24(ro)
    options: sync,root_squash

- name: remove "/home/user *" from /etc/nfsexports if present
  nfsexport:
    path: /home/user
    dest: /etc/nfsexports
    state: absent

- name: ensure "/nfs/share *(ro,sync)" exists in /etc/exports
  nfsexport:
    path: /nfs/share
    options: ro,sync
"""

RETURN = """ # """

import os
from ansible.module_utils.basic import AnsibleModule


def write_to_file(mod, filepath, mode, content):
    try:
        fd = open(filepath, mode)
    except IOError as err:
        mod.fail_json(msg="failed to open %s for writing: %s" % (filepath, str(err)))
    fd.writelines(content)
    fd.close()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, type='path'),
            dest=dict(default='/etc/exports'),
            clients=dict(default='*'),
            options=dict(default=''),
            state=dict(default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True
    )

    params = module.params
    path = params['path'].strip()
    dest = params['dest'].strip()
    state = params['state']

    # build list of clients
    if isinstance(params['clients'], list):
        clients = params['clients']
    else:
        clients = []
        for host in params['clients'].strip('[]').split(','):
            clients.append(host.strip().strip("'"))

    # build list of options applied to all allowed clients
    if params['options'] != '':
        if isinstance(params['options'], list):
            options = params['options']
        else:
            options = []
            for opt in params['options'].strip('[]').strip(','):
                options.append(opt.strip().strip("'"))
        options = str.join(',', options)
    else:
        options = ''

    # determine options format to use based on number of clients and options
    if params['clients'] == '*':
        if params['options'] != '':
            options = "(%s)" % (options)
        exportline = "%s *%s\n" % (params['path'], options)
    else:
        if params['options'] != '':
            options = "-%s " % (options)
        clients = str.join(' ', clients)
        exportline = "%s %s%s\n" % (params['path'], options, clients)

    # Check if destination file exists already
    if os.path.exists(dest):
        try:
            current_exports = open(dest, 'r').readlines()
        except IOError as err:
            module.fail_json(msg="failed to open %s for reading: %s" % (dest, str(err)))
        # Check if the parameters match an export which is already
        # defined
        for i, line in enumerate(current_exports):
            # Do not check empty strings
            if line.strip():
                line_path = line.split()[0].strip()
                if line_path == path:
                    if state == 'absent':
                        # Found export path, and state is 'absent'. Removing line
                        if module.check_mode:
                            module.exit_json(changed=True)
                        del current_exports[i]
                    elif state == 'present':
                        if line == exportline:
                            # path and clients match, and should be present
                            module.exit_json(changed=False)
                        else:
                            # path matches, but clients have changed. Update the file!
                            if module.check_mode:
                                module.exit_json(changed=True)
                            current_exports[i] = exportline
                    # Write changes to file
                    write_to_file(module, dest, 'w', current_exports)
                    module.exit_json(changed=True)

    # Export path not present
    if state == 'absent':
        # path should not be present, do nothing and exit
        module.exit_json(changed=False)
    elif state == 'present':
        # path should be present, proceed and add one.
        if module.check_mode:
            module.exit_json(changed=True)
        write_to_file(module, dest, 'a', exportline)
        module.exit_json(changed=True)

if __name__ == '__main__':
    main()
