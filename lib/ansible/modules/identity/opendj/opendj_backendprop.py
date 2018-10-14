#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2016, Werner Dijkerman (ikben@werner-dijkerman.nl)
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: opendj_backendprop
short_description: Will update the backend configuration of OpenDJ via the dsconfig set-backend-prop command.
description:
   - This module will update settings for OpenDJ with the command set-backend-prop.
   - It will check first via de get-backend-prop if configuration needs to be applied.
version_added: "2.2"
author:
    - Werner Dijkerman (@dj-wasabi)
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
            - The Admin port on which the OpenDJ instance is available.
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
    backend:
        description:
            - The name of the backend on which the property needs to be updated.
        required: true
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
        default: "present"
'''

EXAMPLES = '''
  - name: "Add or update OpenDJ backend properties"
    action: opendj_backendprop
            hostname=localhost
            port=4444
            username="cn=Directory Manager"
            password=password
            backend=userRoot
            name=index-entry-limit
            value=5000
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule


class BackendProp(object):

    def __init__(self, module):
        self._module = module

    def get_property(self, opendj_bindir, hostname, port, username, password_method, backend_name):
        my_command = [
            opendj_bindir + '/dsconfig',
            'get-backend-prop',
            '-h', hostname,
            '--port', str(port),
            '--bindDN', username,
            '--backend-name', backend_name,
            '-n', '-X', '-s'
        ] + password_method
        rc, stdout, stderr = self._module.run_command(my_command)
        if rc == 0:
            return stdout
        else:
            self._module.fail_json(msg="Error message: " + str(stderr))

    def set_property(self, opendj_bindir, hostname, port, username, password_method, backend_name, name, value):
        my_command = [
            opendj_bindir + '/dsconfig',
            'set-backend-prop',
            '-h', hostname,
            '--port', str(port),
            '--bindDN', username,
            '--backend-name', backend_name,
            '--set', name + ":" + value,
            '-n', '-X'
        ] + password_method
        rc, stdout, stderr = self._module.run_command(my_command)
        if rc == 0:
            return True
        else:
            self._module.fail_json(msg="Error message: " + stderr)

    def validate_data(self, data=None, name=None, value=None):
        for config_line in data.split('\n'):
            if config_line:
                split_line = config_line.split()
                if split_line[0] == name:
                    if split_line[1] == value:
                        return True
        return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            opendj_bindir=dict(default="/opt/opendj/bin", type="path"),
            hostname=dict(required=True),
            port=dict(required=True),
            username=dict(default="cn=Directory Manager", required=False),
            password=dict(required=False, no_log=True),
            passwordfile=dict(required=False, type="path"),
            backend=dict(required=True),
            name=dict(required=True),
            value=dict(required=True),
            state=dict(default="present"),
        ),
        supports_check_mode=True,
        mutually_exclusive=[['password', 'passwordfile']],
        required_one_of=[['password', 'passwordfile']]
    )

    opendj_bindir = module.params['opendj_bindir']
    hostname = module.params['hostname']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    passwordfile = module.params['passwordfile']
    backend_name = module.params['backend']
    name = module.params['name']
    value = module.params['value']
    state = module.params['state']

    if module.params["password"] is not None:
        password_method = ['-w', password]
    elif module.params["passwordfile"] is not None:
        password_method = ['-j', passwordfile]

    opendj = BackendProp(module)
    validate = opendj.get_property(opendj_bindir=opendj_bindir,
                                   hostname=hostname,
                                   port=port,
                                   username=username,
                                   password_method=password_method,
                                   backend_name=backend_name)

    if validate:
        if not opendj.validate_data(data=validate, name=name, value=value):
            if module.check_mode:
                module.exit_json(changed=True)
            if opendj.set_property(opendj_bindir=opendj_bindir,
                                   hostname=hostname,
                                   port=port,
                                   username=username,
                                   password_method=password_method,
                                   backend_name=backend_name,
                                   name=name,
                                   value=value):
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)
        else:
            module.exit_json(changed=False)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
