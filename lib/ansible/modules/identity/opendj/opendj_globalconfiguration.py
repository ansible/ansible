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
module: opendj_globalconfiguration
short_description: Will update the Global Configuration for OpenDJ via the set-global-configuration-prop command.
description:
   - This module will update settings for OpenDJ with the command set-global-configuration-prop.
   - Before updating the value it will check the current value with get-global-configuration-prop.
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
    username:
         description:
             - The username to connect to.
         required: false
         default: cn=Directory Manager
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
    name:
        description:
            - The configuration setting to update.
        required: true
    value:
        description:
            - The value for the configuration item.
        required: true
    state:
        description:
            - If configuration needs to be added/updated
        required: false
        choices: ['present']
        default: "present"
'''

EXAMPLES = '''
- name: "Set lookthrough-limit"
  action: opendj_globalconfiguration
          hostname=localhost
          port=4444
          password=password
          name=lookthrough-limit
          value=0

- name: "Configure bind-with-dn-requires-password"
  action: opendj_globalconfiguration
          hostname=localhost
          port=4444
          password=password
          name=bind-with-dn-requires-password
          value=false
'''

RETURN = '''

'''

import subprocess


class GlobalConfiguration(object):
    def __init__(self, module):
        self._module = module

    def get_value(self, opendj_bindir, hostname, port, username, password_method, name):
        my_command = [
            opendj_bindir + '/dsconfig',
            'get-global-configuration-prop',
            '--property', name,
            '-D', username,
            '-h', hostname,
            '-p', str(port),
            '-X', '-n', '-s'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return stdout.split()[1]
        else:
            self._module.fail_json(msg="Error message: " + str(stderr))

    def set_value(self, opendj_bindir, hostname, port, username, password_method, name, value):
        my_command = [
            opendj_bindir + '/dsconfig',
            'set-global-configuration-prop',
            '--set', name + ':' + str(value),
            '-D', username,
            '-h', hostname,
            '-p', str(port),
            '-X', '-n', '-s'
        ] + password_method
        process = subprocess.Popen(my_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return True
        else:
            return self._module.fail_json(msg="Error message: " + str(stderr))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            opendj_bindir=dict(default="/opt/opendj/bin"),
            hostname=dict(required=True),
            port=dict(required=True),
            username=dict(default="cn=Directory Manager", required=False),
            password=dict(required=False, no_log=True),
            passwordfile=dict(required=False),
            name=dict(required=True),
            value=dict(required=True),
            state=dict(default="present", choices=['present']),
        ),
        supports_check_mode=True
    )

    opendj_bindir = module.params['opendj_bindir']
    hostname = module.params['hostname']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    passwordfile = module.params['passwordfile']
    name = module.params['name']
    value = module.params['value']
    state = module.params['state']

    if password is not None:
        password_method = ['-w', password]
    elif passwordfile is not None:
        password_method = ['-j', passwordfile]
    else:
        module.fail_json(msg="No credentials are given. Use either 'password' or 'passwordfile'")

    opendj = GlobalConfiguration(module)
    get_value = opendj.get_value(opendj_bindir=opendj_bindir,
                                 hostname=hostname,
                                 port=port,
                                 username=username,
                                 password_method=password_method,
                                 name=name)

    if get_value:
        if value != get_value:
            if module.check_mode:
                module.exit_json(changed=True)
            if opendj.set_value(opendj_bindir=opendj_bindir,
                                hostname=hostname,
                                port=port,
                                username=username,
                                password_method=password_method,
                                name=name,
                                value=value):
                module.exit_json(changed=True, msg="Configuration updated")
        else:
            module.exit_json(changed=False, msg="No need for updating configuration")
    else:
        module.fail_json(msg="No connection to OpenDJ can be made.")


from ansible.module_utils.basic import *
main()
