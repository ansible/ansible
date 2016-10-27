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

module: na_cdot_user_role

short_description: useradmin configuration and management
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
-
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
    - The name of the role to manage

  command_directory_name:
    required: true
    description:
    - The command or command directory to which the role has an access.

  access_level:
    required: false
    description:
    - The name of the role to manage
    choices: ['none', 'readonly', 'all']
    default: 'all'

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

    - name: Create User Role
      na_cdot_user_role:
        state: present
        name: ansibleRole
        command_directory_name: DEFAULT
        access_level: none
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

"""

RETURN = """
msg:
    description: Successfully created User Role
    returned: success
    type: string
    sample: '{"changed": true}'

"""


"""
TODO:
    Add ability to update properties.
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


class NetAppCDOTUserRole(object):

    def __init__(self):
        logger.debug('Init %s', self.__class__.__name__)

        self.module = AnsibleModule(
            argument_spec=dict(
                state=dict(required=True, choices=['present', 'absent']),
                name=dict(required=True, type='str'),

                command_directory_name=dict(required=True, type='str'),
                access_level=dict(required=False, type='str', default='all',
                                  choices=['none', 'readonly', 'all']),

                vserver=dict(required=True, type='str'),
                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),

            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']

        self.command_directory_name = p['command_directory_name']
        self.access_level = p['access_level']

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

    def get_role(self):
        """
        Checks if the role exists for specific command-directory-name.

        :return:
            True if role found
            False if role is not found
        :rtype: bool
        """

        security_login_role_get_iter = zapi.NaElement(
            'security-login-role-get-iter')
        query_details = zapi.NaElement.create_node_with_children(
            'security-login-role-info', **{'vserver': self.vserver,
                                           'role-name': self.name,
                                           'command-directory-name':
                                               self.command_directory_name})

        query = zapi.NaElement('query')
        query.add_child_elem(query_details)
        security_login_role_get_iter.add_child_elem(query)

        try:
            result = self.server.invoke_successfully(
                security_login_role_get_iter, enable_tunneling=False)
        except zapi.NaApiError, e:
            # Error 16031 denotes a role not being found.
            if str(e.code) == "16031":
                return False
            else:
                raise

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return True
        else:
            return False

    def create_role(self):
        logger.debug('Creating role %s', self.name)

        role_create = zapi.NaElement.create_node_with_children(
            'security-login-role-create', **{'vserver': self.vserver,
                                             'role-name': self.name,
                                             'command-directory-name':
                                                 self.command_directory_name,
                                             'access-level':
                                                 self.access_level})

        try:
            self.server.invoke_successfully(role_create,
                                            enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error creating role %s. Error code: '
                             '%s', self.name, str(e.code))
            raise

    def delete_role(self):
        logger.debug('Removing role %s', self.name)

        role_delete = zapi.NaElement.create_node_with_children(
            'security-login-role-delete', **{'vserver': self.vserver,
                                             'role-name': self.name,
                                             'command-directory-name':
                                                 self.command_directory_name})

        try:
            self.server.invoke_successfully(role_delete,
                                            enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error removing role %s. Error code: %s ',
                             self.name, str(e.code))
            raise

    def apply(self):
        changed = False
        role_exists = self.get_role()

        if role_exists:
            if self.state == 'absent':
                logger.debug(
                    "CHANGED: role exists, but requested state is "
                    "'absent'")
                changed = True

            """ TODO: Add ability to update parameters
            elif self.state == 'present':
            """
        else:
            if self.state == 'present':
                logger.debug(
                    "CHANGED: role does not exist, but requested state is"
                    "'present'")
                changed = True

        if changed:
            if self.module.check_mode:
                logger.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not role_exists:
                        self.create_role()

                    """ TODO: Add ability to update parameters
                    else:
                    """
                elif self.state == 'absent':
                    self.delete_role()
        else:
            logger.debug("exiting with no changes")

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTUserRole()

    try:
        v.apply()
    except Exception, e:
        logger.debug("Exception in apply(): \n%s" % format_exc(e))
        raise

main()
