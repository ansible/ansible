#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Werner Dijkerman (ikben@werner-dijkerman.nl)
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---
module: opendj_index
short_description: Index management for OpenDJ
description:
   - This module will create/update/rebuild/delete indexes in OpenDJ.
   - It will also rebuild Indexes if needed.
version_added: "2.2"
author:
    - Werner Dijkerman
options:
    opendj_bindir:
        description:
            - The path to the bin directory of OpenDJ.
        required: false
        default: /opt/opendj/bin
    hostname:
        description:
            - The hostname of the OpenDJ server.
        required: true
    port:
        description:
            - The Admin port on which OpenDJ is listening.
        required: true
    password:
        description:
            - The password for the cn=Directory Manager user.
            - Either password or passwordfile is needed.
        required: false
    passwordfile:
        description:
            - Location to the password file which holds the password for the cn=Directory Manager user.
            - Either password or passwordfile is needed.
        required: false
    backend:
        description:
            - The name of the backend which holds the data.
        required: true
    name:
        description:
            - The name of the Index.
        required: true
    type:
        description:
            - The index type.
        required: true
        choices: ['substring', 'equality', 'ordering']
    base_dn:
        description:
            - The base DN. Example dc=example,dc=com
            - This is needed only for rebuilding Indexes.
        required: false
    rebuild:
        description:
            - When an index is changed, set to True if an rebuild needs to be done.
            - Rebuilding is done in the background. Verify if rebuild is done successfully can only be done by examining the OpenDJ logfiles.
        required: False
        choices: ['True', 'False']
        default: "False"
    state:
        description:
            - present if an index needs to be added or updated.
            - absent if an index needs to be removed.
            - rebuild if an index needs to be rebuild.
            - Rebuilding is done in the background. Verify if rebuild is done successfully can only be done by examining the OpenDJ logfiles.
            - Rebuilding tasks are always added and thus task is always changed.
        required: false
        choices: ['present', 'absent', 'rebuild']
        default: "present"
'''

EXAMPLES = '''
  - name: "Add OpenDJ Indexes"
    action: opendj_index
            opendj_bindir=/opt/opendj2/bin
            hostname=localhost
            port=4444
            password=password
            backend=userRoot
            name=description
            type=substring
            rebuild=False

  - name: "Rebuild OpenDJ Indexes"
    action: opendj_index
            hostname=localhost
            port=4444
            password=password
            backend=userRoot
            name=description
            type=substring
            base_dn="dc=example,dc=com"
            rebuild=True
            state=rebuild

  - name: "Delete OpenDJ Indexes"
    action: opendj_index
            hostname=localhost
            port=4444
            password=password
            backend=userRoot
            name=description
            type=substring
            base_dn="dc=example,dc=com"
            state=absent
'''

RETURN = '''

'''

import subprocess


class OpenDJIdexes(object):
    def __init__(self, module):
        self._module = module

    def get_index(self, opendj_bindir, hostname, port, password_method, backend_name):
        my_command = [
            opendj_bindir + '/dsconfig',
            '-n', 'list-local-db-indexes',
            '--backend-name', backend_name,
            '-h', hostname,
            '-p', port,
            '-X'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            return stdout
        else:
            return self._module.fail_json(msg="Error message: " + str(stderr))

    def create_index(self, opendj_bindir, hostname, port, password_method, backend_name, name, type):
        my_command = [
            opendj_bindir + '/dsconfig',
            'create-local-db-index',
            '--backend-name', backend_name,
            '--index-name', name,
            '--set', 'index-type:' + type,
            '-h', hostname,
            '-p', port,
            '-X', '-n'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            return True
        else:
            return self._module.fail_json(msg="Error message: " + str(stderr))

    def update_index(self, opendj_bindir, hostname, port, password_method, backend_name, name, type):
        my_command = [
            opendj_bindir + '/dsconfig',
            'set-local-db-index-prop',
            '--backend-name', backend_name,
            '--index-name', name,
            '--set', 'index-type:' + type,
            '-h', hostname,
            '-p', port,
            '-X', '-n'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            return True
        else:
            return self._module.fail_json(msg="Error message: " + str(stderr))

    def rebuild_index(self, opendj_bindir, hostname, port, password_method, base_dn, name):
        my_command = [
            opendj_bindir + '/rebuild-index',
            '-b', base_dn,
            '-i', name,
            '-h', hostname,
            '-p', port,
            '-t', '0', '-X'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            return True
        else:
            return self._module.fail_json(msg="Error message: " + str(stderr))

    def delete_index(self, opendj_bindir, hostname, port, password_method, backend_name, name):
        my_command = [
            opendj_bindir + '/dsconfig',
            'delete-local-db-index',
            '--backend-name', backend_name,
            '--index-name', name,
            '-h', hostname,
            '-p', port,
            '-X', '-n'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            return True
        else:
            return self._module.fail_json(msg="Error message: " + str(stderr))

    def validate_name(self, data, name):
        for line in data.split('\n'):
            if line != '':
                current_index = line.split(':')
                if current_index[0].strip() == name:
                    return line
        return False

    def validate_type(self, data, type):
        line_split = data.split(':')
        types = line_split[1]
        for type in types.split(','):
            if type.strip() == type:
                return True
        return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            opendj_bindir=dict(default="/opt/opendj/bin"),
            hostname=dict(required=True),
            port=dict(required=True),
            password=dict(required=False, nolog=True),
            passwordfile=dict(required=False),
            backend=dict(required=True),
            name=dict(required=True),
            type=dict(required=True, choices=['substring', 'equality', 'ordering']),
            base_dn=dict(required=False),
            rebuild=dict(default=False, type='bool'),
            state=dict(default="present", choices=['present', 'absent', 'rebuild']),
        ),
        supports_check_mode=True
    )

    opendj_bindir = module.params['opendj_bindir']
    hostname = module.params['hostname']
    port = module.params['port']
    password = module.params['password']
    passwordfile = module.params['passwordfile']
    backend_name = module.params['backend']
    name = module.params['name']
    type = module.params['type']
    base_dn = module.params['base_dn']
    rebuild = module.params['rebuild']
    state = module.params['state']

    if password is not None:
        password_method = ['-w', password]
    elif passwordfile is not None:
        password_method = ['-j', passwordfile]
    else:
        module.fail_json(msg="No credentials are given. Use either 'password' or 'passwordfile'")

    opendj = OpenDJIdexes(module)
    index_data = opendj.get_index(opendj_bindir=opendj_bindir,
                                  hostname=hostname,
                                  port=port,
                                  password_method=password_method,
                                  backend_name=backend_name)
    index_validate = opendj.validate_name(data=index_data, name=name)
    if index_validate:
        if state == "present":
            if not opendj.validate_type(data=index_validate, type=type):
                if module.check_mode:
                    module.exit_json(changed=True)
                if opendj.updated_index(opendj_bindir=opendj_bindir,
                                        hostname=hostname,
                                        port=port,
                                        password_method=password_method,
                                        backend_name=backend_name,
                                        name=name,
                                        type=type):
                    if rebuild:
                        opendj.rebuild_index(opendj_bindir=opendj_bindir,
                                             hostname=hostname,
                                             port=port,
                                             password_method=password_method,
                                             base_dn=base_dn,
                                             name=name)
                    module.exit_json(changed=True)
            module.exit_json(changed=False)
        if state == "rebuild":
            opendj.rebuild_index(opendj_bindir=opendj_bindir,
                                 hostname=hostname,
                                 port=port,
                                 password_method=password_method,
                                 base_dn=base_dn,
                                 name=name)
        module.exit_json(changed=True)
        if state == "absent":
            if module.check_mode:
                module.exit_json(changed=True)
            if opendj.delete_index(opendj_bindir=opendj_bindir,
                                   hostname=hostname,
                                   port=port,
                                   password_method=password_method,
                                   backend_name=backend_name,
                                   name=name):
                module.exit_json(changed=True)
    else:
        if state == "present":
            if module.check_mode:
                module.exit_json(changed=True)
            if opendj.create_index(opendj_bindir=opendj_bindir,
                                   hostname=hostname,
                                   port=port,
                                   password_method=password_method,
                                   backend_name=backend_name,
                                   name=name,
                                   type=type):
                module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)


from ansible.module_utils.basic import *
main()
