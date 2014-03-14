#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013, Peter Sprygada <sprygada@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
DOCUMENTATION = '''
---
module: ejabberd_user
version_added: "1.5"
author: Peter Sprygada
short_description: Manages users for ejabberd servers
requirements:
    - ejabberd with mod_admin_extra
description:
    - This module provides user management for ejabberd servers
options:
    username:
        description:
            - the name of the user to manage
        required: true
    host:
        description:
            - the ejabberd host associated with this username
        required: true
    password:
        description:
            - the password to assign to the username
        required: false
    logging:
        description:
            - enables or disables the local syslog facility for this module
        required: false
        default: false
        choices: [ 'true', 'false', 'yes', 'no' ]
    state:
        description:
            - describe the desired state of the user to be managed
        required: false
        default: 'present'
        choices: [ 'present', 'absent' ]
notes:
    - Password parameter is required for state == present only
    - Passwords must be stored in clear text for this release
    - The ejabberd configuration file must include mod_admin_extra as a module.
'''
EXAMPLES = '''
Example playbook entries using the ejabberd_user module to manage users state.

    tasks:

    - name: create a user if it does not exists
      action: ejabberd_user username=test host=server password=password

    - name: delete a user if it exists
      action: ejabberd_user username=test host=server state=absent
'''
import syslog

class EjabberdUserException(Exception):
    """ Base exeption for EjabberdUser class object """
    pass

class EjabberdUser(object):
    """ This object represents a user resource for an ejabberd server.   The
    object manages user creation and deletion using ejabberdctl.  The following
    commands are currently supported:
        * ejabberdctl register
        * ejabberdctl deregister
    """

    def __init__(self, module):
        self.module = module
        self.logging = module.params.get('logging')
        self.state = module.params.get('state')
        self.host = module.params.get('host')
        self.user = module.params.get('username')
        self.pwd = module.params.get('password')

    @property
    def changed(self):
        """ This method will check the current user and see if the password has
        changed.   It will return True if the user does not match the supplied
        credentials and False if it does not
        """
        try:
            options = [self.user, self.host, self.pwd]
            (rc, out, err) = self.run_command('check_password', options)
        except EjabberdUserException, e:
            (rc, out, err) = (1, None, "required attribute(s) missing")
        return rc

    @property
    def exists(self):
        """ This method will check to see if the supplied username exists for
        host specified.  If the user exists True is returned, otherwise False
        is returned
        """
        try:
            options = [self.user, self.host]
            (rc, out, err) = self.run_command('check_account', options)
        except EjabberdUserException, e:
            (rc, out, err) = (1, None, "required attribute(s) missing")
        return True if rc == 0 else False

    def log(self, entry):
        """ This method will log information to the local syslog facility """
        if self.logging:
            syslog.openlog('ansible-%s' % os.path.basename(__file__))
            syslog.syslog(syslog.LOG_NOTICE, entry)

    def run_command(self, cmd, options):
        """ This method will run the any command specified and return the
        returns using the Ansible common module
        """
        if not all(options):
            raise EjabberdUserException

        cmd = 'ejabberdctl %s ' % cmd
        cmd += " ".join(options)
        self.log('command: %s' % cmd)
        return self.module.run_command(cmd.split())

    def update(self):
        """ The update method will update the credentials for the user provided
        """
        try:
            options = [self.user, self.host, self.pwd]
            (rc, out, err) = self.run_command('change_password', options)
        except EjabberdUserException, e:
            (rc, out, err) = (1, None, "required attribute(s) missing")
        return (rc, out, err)

    def create(self):
        """ The create method will create a new user on the host with the
        password provided
        """
        try:
            options = [self.user, self.host, self.pwd]
            (rc, out, err) = self.run_command('register', options)
        except EjabberdUserException, e:
            (rc, out, err) = (1, None, "required attribute(s) missing")
        return (rc, out, err)

    def delete(self):
        """ The delete method will delete the user from the host
        """
        try:
            options = [self.user, self.host]
            (rc, out, err) = self.run_command('unregister', options)
        except EjabberdUserException, e:
            (rc, out, err) = (1, None, "required attribute(s) missing")
        return (rc, out, err)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            host=dict(default=None, type='str'),
            username=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
            logging=dict(default=False, type='bool')
        ),
        supports_check_mode = True
    )

    obj = EjabberdUser(module)

    rc = None
    result = dict()

    if obj.state == 'absent':
        if obj.exists:
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = obj.delete()
            if rc != 0:
                module.fail_json(msg=err, rc=rc)

    elif obj.state == 'present':
        if not obj.exists:
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = obj.create()
        elif obj.changed:
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = obj.update()
        if rc is not None and rc != 0:
            module.fail_json(msg=err, rc=rc)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True

    module.exit_json(**result)


# import module snippets
from ansible.module_utils.basic import *
main()
