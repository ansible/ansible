#!/usr/bin/python

# (c) 2016, NetApp, Inc
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
#

DOCUMENTATION = '''

module: na_cdot_users

short_description: useradmin configuration and management
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy users
    - auth_basic

options:

  state:
    required: true
    description:
    - Whether the specified user should exist or not.
    choices: ['present', 'absent']

  name:
    required: true
    description:
    - The name of the user to manage

  application:
    required: true
    description:
    - application
    choices: ['console', 'http','ontapi','rsh','snmp','sp','ssh','telnet']

  authentication_method:
    required: true
    description:
    - Authentication method for the application.
    - Not all authentication methods are valid for an application. Valid authentication methods for each application are
    - password for console application
    - password, domain, nsswitch, cert for http application.
    - password, domain, nsswitch, cert for ontapi application.
    - community for snmp application (when creating SNMPv1 and SNMPv2 users).
    - usm and community for snmp application (when creating SNMPv3 users).
    - password for sp application.
    - password for rsh application.
    - password for telnet application.
    - password, publickey, domain, nsswitch for ssh application.
    choices: ['community', 'password', 'publickey', 'domain', 'nsswitch', 'usm']

  set_password:
    required: false
    description:
    - Password for the user account. 
    -   This is ignored for creating snmp users. 
    -   This is required for creating non-snmp users.
    -   For an existing user, this value will be used as the new password.

  role_name:
    required: false
    note: required when state == 'present'
    description:
    - role name

  vserver:
    required: true
    description:
    - vserver

  hostname:
    required: true
    description:
    - hostname

  username:
    required: true
    description:
    - username

  password:
    required: true
    description:
    - password

'''

EXAMPLES = """

    - name: Create User 
      na_cdot_user:
        state: present
        name: SampleUser
        application: ssh
        authentication_method: password
        set_password: apn1242183u1298u41
        role_name: vsadmin
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

"""

RETURN = """
msg:
    description: Successfully created User
    returned: success
    type: string
    sample: '{"changed": true}'

"""

"""
TODO:
    Go through the role list to ensure role exists before applying, and then
    log the appropriate error. Presently, a generic 'entry doesn't exist'
    error is logged.

    Add 'comment' and 'snmpv3-login-info' as configurable parameters.

    Add ability to update properties. Use a flag to ensure that it's the
    user's desired behavior.

    Add lock/unlock capability.

"""

import sys
import json
import logging
from itertools import ifilter
from traceback import format_exc

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

import socket
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from netapp_lib.api.zapi import zapi
from netapp_lib.api.zapi import errors as zapi_errors

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NetAppCDOTUser(object):
    """
    Common operations to manage users and roles.
    """

    def __init__(self):
        logger.debug('Init %s', self.__class__.__name__)

        self.module = AnsibleModule(
            argument_spec=dict(
                state=dict(required=True, choices=['present', 'absent']),
                name=dict(required=True, type='str'),

                application=dict(required=True, type='str', choices=[
                    'console', 'http', 'ontapi', 'rsh',
                    'snmp', 'sp', 'ssh', 'telnet']),
                authentication_method=dict(required=True, type='str',
                                           choices=['community', 'password',
                                                    'publickey', 'domain',
                                                    'nsswitch', 'usm']),
                set_password=dict(required=False, type='str', default=None),
                role_name=dict(required=False, type='str'),

                vserver=dict(required=True, type='str'),
                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('state', 'present', ['role_name'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']

        self.application = p['application']
        self.authentication_method = p['authentication_method']
        self.set_password = p['set_password']
        self.role_name = p['role_name']

        self.vserver = p['vserver']
        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']

        # set up zapi
        self.server = zapi.NaServer(self.hostname)
        self.server.set_username(self.username)
        self.server.set_password(self.password)
        # Todo : Remove hardcoded values.
        self.server.set_api_version(major=1,
                                    minor=21)
        self.server.set_port(80)
        self.server.set_server_type('FILER')
        self.server.set_transport_type('HTTP')

    def get_user(self):
        """
        Checks if the user exists.

        :return:
            True if user found
            False if user is not found
        :rtype: bool
        """

        security_login_get_iter = zapi.NaElement('security-login-get-iter')
        query_details = zapi.NaElement.create_node_with_children(
            'security-login-account-info', **{'vserver': self.vserver,
                                              'user-name':self.name,
                                              'application': self.application,
                                              'authentication-method':
                                                  self.authentication_method})

        query = zapi.NaElement('query')
        query.add_child_elem(query_details)
        security_login_get_iter.add_child_elem(query)

        try:
            result = self.server.invoke_successfully(security_login_get_iter,
                                                     enable_tunneling=False)
        except zapi.NaApiError, e:
            # Error 16034 denotes a user not being found.
            if str(e.code) == "16034":
                return False
            else:
                raise

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return True
        else:
            return False

    def create_user(self):
        logger.debug('Creating user %s', self.name)

        user_create = zapi.NaElement.create_node_with_children(
            'security-login-create', **{'vserver': self.vserver,
                                        'user-name': self.name,
                                        'application': self.application,
                                        'authentication-method':
                                            self.authentication_method,
                                        'role-name': self.role_name})
        if self.password is not None:
            user_create.add_new_child('password', self.password)

        try:
            self.server.invoke_successfully(user_create,
                                            enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error creating user %s. Error code: '
                             '%s', self.name, str(e.code))
            raise

    def delete_user(self):
        logger.debug('Removing user %s', self.name)

        user_delete = zapi.NaElement.create_node_with_children(
            'security-login-delete', **{'vserver': self.vserver,
                                        'user-name': self.name,
                                        'application': self.application,
                                        'authentication-method':
                                            self.authentication_method})

        try:
            self.server.invoke_successfully(user_delete,
                                            enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error removing user %s. Error code: %s ',
                             self.name, str(e.code))
            raise

    def change_password(self):
        """
        Changes the password

        :return:
            True if password updated
            False if password is not updated
        :rtype: bool
        """
        self.server.set_vserver(self.vserver)
        modify_password = zapi.NaElement.create_node_with_children(
            'security-login-modify-password', **{
                'new-password': str(self.set_password),
                'user-name': self.name})
        try:
            self.server.invoke_successfully(modify_password,
                                            enable_tunneling=True)
        except zapi.NaApiError, e:
            if str(e.code) == '13114':
                return False
            else:
                logger.exception('Error setting password %s. Error code: %s ',
                                 self.name, str(e.code))
                raise
        self.server.set_vserver(None)
        return True

    def apply(self):
        property_changed = False
        password_changed = False
        user_exists = self.get_user()

        if user_exists:
            if self.state == 'absent':
                logger.debug(
                    "CHANGED: user exists, but requested state is "
                    "'absent'")
                property_changed = True

            elif self.state == 'present':
                if not self.set_password is None:
                    password_changed = self.change_password()
        else:
            if self.state == 'present':
                logger.debug(
                    "CHANGED: user does not exist, but requested state is"
                    "'present'")

                property_changed = True

        if property_changed:
            if self.module.check_mode:
                logger.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not user_exists:
                        self.create_user()

                    """ TODO: Add ability to update parameters.
                    else:
                    """
                elif self.state == 'absent':
                    self.delete_user()
        else:
            logger.debug("exiting with no changes")
        changed = property_changed or password_changed
        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTUser()

    try:
        v.apply()
    except Exception, e:
        logger.debug("Exception in apply(): \n%s" % format_exc(e))
        raise

main()
