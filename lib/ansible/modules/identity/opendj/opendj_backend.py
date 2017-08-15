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
module: opendj_backend
short_description: Will will create or delete an backend in OpenDJ
description:
   - This module will create/delete a backend in OpenDJ.
   - This module will create a 'root' entry, this is done via temporary creating a file in /tmp and when import is done, it is deleted.
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
            - Location to the password file which holds the password for user configured in bind_dn.
            - Either password or passwordfile is needed.
        required: false
    name:
        description:
            - The name of the backend to create.
        required: true
    bind_dn:
        description:
            - The username to connect to OpenDJ.
        required: false
        default: cn=Directory Manager
    base_dn:
        description:
            - The base DN. Example dc=example,dc=com.
        required: True
    type:
        description:
            - The type of backend you want to use for OpenDJ.
        required: false
        choices: ["je", "pdb"]
        default: "je"
    enabled:
        description:
            - If the backend needs to be enabled when the backend is created.
        required: false
        choices: ['True', 'False']
        default: "True"
    state:
        description:
            - If configuration needs to be added/deleted
        required: false
        choices: ['present', 'absent']
        default: "present"
'''

EXAMPLES = '''
    - name: "Create Pizza Backend"
      action: opendj_backend
              hostname=localhost
              port=4444
              password=password
              name=myPizzaBackend
              bind_dn="cn=Directory Manager"
              base_dn=dc=ansible,dc=example,dc=com
              enabled=true

    - name: "Delete Pizza Backend"
      action: opendj_backend
              hostname=localhost
              port=4444
              password=password
              name=myPizzaBackend
              bind_dn="cn=Directory Manager"
              base_dn=dc=ansible,dc=example,dc=com
              type=pdb
              enabled=true
              state=absent

'''

RETURN = '''

'''

import subprocess
import time
from tempfile import mkstemp
import os
import re


class Backend(object):
    def __init__(self, module):
        self._module = module

    def get_backend(self, opendj_bindir, hostname, port, password_method, bind_dn):
        my_command = [
            opendj_bindir + '/dsconfig',
            'list-backends',
            '-h', hostname,
            '-p', str(port),
            '--bindDN', bind_dn,
            '-X'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return stdout
        else:
            return self._module.fail_json(msg="Error message while getting list backends: " + str(stderr))

    def create_backend(self, opendj_bindir, hostname, port, password_method, name, base_dn, bind_dn, type, enabled):
        my_command = [
            opendj_bindir + '/dsconfig',
            'create-backend',
            '--backend-name', name,
            '--set', 'base-dn:' + base_dn,
            '--set', 'enabled:' + str(enabled).lower(),
            '--bindDN', bind_dn,
            '-h', hostname,
            '-p', str(port),
            '-t', type,
            '-X', '-n'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return True
        else:
            return self._module.fail_json(msg="Error message while creating backend: " + str(stderr))

    def create_root(self, opendj_bindir, hostname, port, password_method, base_dn, bind_dn, name):
        dc = base_dn.split(',dc=')[0]
        dc = dc.split('dc=')[1]

        fd, file_path = tempfile.mkstemp()
        try:
            tmp_file = os.fdopen(fd, "w")
            tmp_file.write('dn: ' + base_dn + '\n')
            tmp_file.write('objectclass: top\n')
            tmp_file.write('objectclass: domain\n')
            tmp_file.write('dc: ' + dc + '\n')
            tmp_file.close()

            my_command = [
                opendj_bindir + '/import-ldif',
                '-n', name,
                '-b', base_dn,
                '-l', file_path,
                '-t', str(0),
                '-h', hostname,
                '-p', str(port),
                '-X'
            ] + password_method

            process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            task_id = stdout.split()[2]

            self.validate_task(opendj_bindir=opendj_bindir,
                               hostname=hostname,
                               port=port,
                               password_method=password_method,
                               bind_dn=bind_dn,
                               task_id=task_id)
        finally:
            os.remove(file_path)

        if process.returncode == 0:
            return True
        else:
            return self._module.fail_json(msg="Error message while creating root: " + str(stderr))

    def validate_task(self, opendj_bindir, hostname, port, password_method, bind_dn, task_id):
        for num in range(0, 5):
            my_command = [
                opendj_bindir + '/manage-tasks',
                '--bindDN', bind_dn,
                '-i', task_id,
                '-h', hostname,
                '-p', str(port),
                '-X', '-n'
            ] + password_method
            process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            for line in stdout.split('\n'):
                stripped_data = line.lstrip()
                if re.match('^Status', stripped_data):
                    my_stripped_data = stripped_data.lstrip().rstrip()
                    status = my_stripped_data.strip("Status").strip()

                    if status == 'Completed successfully':
                        return True
            time.sleep(2)
        return self._module.fail_json(msg="Error message while validating task: " + str(stderr))

    def delete_backend(self, opendj_bindir, hostname, port, password_method, bind_dn, name):
        my_command = [
            opendj_bindir + '/dsconfig',
            'delete-backend',
            '--backend-name', name,
            '-h', hostname,
            '-p', str(port),
            '--bindDN', bind_dn,
            '-X', '-n'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return True
        else:
            return self._module.fail_json(msg="Error message while deleting: " + str(stderr))

    def validate_name(self, data, name):
        for line in data.split('\n'):
            if line != '':
                current_backend = line.split(':')
                if current_backend[0].strip() == name:
                    return line
        return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            opendj_bindir=dict(default="/opt/opendj/bin"),
            hostname=dict(required=True),
            port=dict(required=True),
            password=dict(required=False, no_log=True),
            passwordfile=dict(required=False),
            name=dict(required=True),
            bind_dn=dict(required=True),
            base_dn=dict(required=True),
            type=dict(default="je", choices=["je", "pdb"]),
            enabled=dict(default=True, type='bool'),
            state=dict(default="present", choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    opendj_bindir = module.params['opendj_bindir']
    hostname = module.params['hostname']
    port = module.params['port']
    password = module.params['password']
    passwordfile = module.params['passwordfile']
    name = module.params['name']
    bind_dn = module.params['bind_dn']
    base_dn = module.params['base_dn']
    type = module.params['type']
    enabled = module.params['enabled']
    state = module.params['state']

    if module.params["password"] is not None:
        password_method = ['-w', password]
    elif module.params["passwordfile"] is not None:
        password_method = ['-j', passwordfile]
    else:
        module.fail_json(msg="No credentials are given. Use either 'password' or 'passwordfile'")

    if module.params["passwordfile"] and module.params["password"]:
        module.fail_json(msg="only one of 'password' or 'passwordfile' can be set")

    opendj = Backend(module)
    backend_data = opendj.get_backend(opendj_bindir=opendj_bindir,
                                      hostname=hostname,
                                      port=port,
                                      password_method=password_method,
                                      bind_dn=bind_dn)

    backend_validate = opendj.validate_name(data=backend_data, name=name)
    if backend_validate:
        if state == "present":
            module.exit_json(changed=False)
        if state == "absent":
            if module.check_mode:
                module.exit_json(changed=True)
            if opendj.delete_backend(opendj_bindir=opendj_bindir,
                                     hostname=hostname,
                                     port=port,
                                     password_method=password_method,
                                     bind_dn=bind_dn,
                                     name=name):
                module.exit_json(changed=True)

    else:
        if state == "present":
            if module.check_mode:
                module.exit_json(changed=True)
            if opendj.create_backend(opendj_bindir=opendj_bindir,
                                     hostname=hostname,
                                     port=port,
                                     name=name,
                                     base_dn=base_dn,
                                     bind_dn=bind_dn,
                                     password_method=password_method,
                                     type=type,
                                     enabled=enabled):
                opendj.create_root(opendj_bindir=opendj_bindir,
                                   hostname=hostname,
                                   port=port,
                                   password_method=password_method,
                                   base_dn=base_dn,
                                   bind_dn=bind_dn,
                                   name=name)
                module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
