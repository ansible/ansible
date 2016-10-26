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

module: na_cdot_qtree

short_description: Manage qtrees

description:
- Create or destroy qtrees
    - auth_basic

options:

  state:
    required: true
    description:
    - Whether the specified qtree should exist or not.
    choices: ['present', 'absent']

  name:
    required: true
    description:
    - The name of the qtree to manage

  new_name:
    required: false
    description:
    - Rename the qtree

  flexvol_name:
    required: when state == 'present'
    description:
    - The name of the flexvol the qtree should exist on

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

    - name: Create QTree
          na_cdot_qtree:
            state: present
            name: ansibleQTree
            flexvol_name: ansibleVolume
            vserver: ansibleVServer
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

    - name: Rename QTree
          na_cdot_qtree:
            state: present
            name: ansibleQTree
            new_name: ansibleQTreeRenamed
            flexvol_name: ansibleVolume
            vserver: ansibleVServer
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

"""

RETURN = """
msg:
    description: Successfully created QTree
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successfully renamed QTree
    returned: success
    type: string
    sample: '{"changed": true}'

"""

"""
TODO:
    Add more configurable parameters:
        mode, security-style, oplocks, export-policy

    Add async delete
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


class NetAppCDOTQTree(object):

    def __init__(self):
        logger.debug('Init %s', self.__class__.__name__)

        self.module = AnsibleModule(
            argument_spec=dict(
                state=dict(required=True, choices=['present', 'absent']),
                name=dict(required=True, type='str'),
                new_name=dict(required=False, type='str', default=None),
                flexvol_name=dict(type='str'),
                vserver=dict(required=True, type='str'),
                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('state', 'present', ['flexvol_name'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.new_name = p['new_name']
        self.flexvol_name = p['flexvol_name']
        self.vserver = p['vserver']
        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']

        # set up zapi
        self.server = zapi.NaServer(self.hostname)
        self.server.set_username(self.username)
        self.server.set_password(self.password)
        self.server.set_vserver(self.vserver)
        # Todo : Remove hardcoded values.
        self.server.set_api_version(major=1,
                                    minor=21)
        self.server.set_port(80)
        self.server.set_server_type('FILER')
        self.server.set_transport_type('HTTP')

    def get_qtree(self):
        """
        Checks if the qtree exists.

        :return:
            True if qtree found
            False if qtree is not found
        :rtype: bool
        """

        qtree_list_iter = zapi.NaElement('qtree-list-iter')
        query_details = zapi.NaElement.create_node_with_children(
            'qtree-info', **{'vserver': self.vserver,
                             'volume':self.flexvol_name,
                             'qtree': self.name})

        query = zapi.NaElement('query')
        query.add_child_elem(query_details)
        qtree_list_iter.add_child_elem(query)

        result = self.server.invoke_successfully(qtree_list_iter,
                                                 enable_tunneling=True)

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return True
        else:
            return False

    def create_qtree(self):
        logger.debug('Creating qtree %s', self.name)

        qtree_create = zapi.NaElement.create_node_with_children(
            'qtree-create', **{'volume': self.flexvol_name,
                               'qtree': self.name})

        try:
            self.server.invoke_successfully(qtree_create,
                                            enable_tunneling=True)
        except zapi.NaApiError, e:
            logger.exception('Error provisioning qtree %s. Error code: %s',
                             self.name, str(e.code))
            raise

    def delete_qtree(self):
        logger.debug('Deleting qtree %s', self.name)
        path = '/vol/%s/%s' % (self.flexvol_name, self.name)
        qtree_delete = zapi.NaElement.create_node_with_children(
            'qtree-delete', **{'qtree': path})

        try:
            self.server.invoke_successfully(qtree_delete,
                                            enable_tunneling=True)
        except zapi.NaApiError:
            logger.exception('Error deleting qtree %s', path)
            raise

    def rename_qtree(self):
        logger.debug('Renaming qtree %s', self.name)
        path = '/vol/%s/%s' % (self.flexvol_name, self.name)
        new_path = '/vol/%s/%s' % (self.flexvol_name, self.new_name)
        qtree_rename = zapi.NaElement.create_node_with_children(
            'qtree-rename', **{'qtree': path,
                               'new-qtree-name': new_path})

        try:
            self.server.invoke_successfully(qtree_rename,
                                            enable_tunneling=True)
        except zapi.NaApiError, e:
            logger.exception('Error renaming qtree %s. Error code: %s',
                             self.name, str(e.code))
            raise

    def apply(self):
        changed = False
        qtree_exists = False
        rename_qtree = False
        qtree_detail = self.get_qtree()

        if qtree_detail:
            qtree_exists = True

            if self.state == 'absent':
                logger.debug(
                    "CHANGED: qtree exists, but requested state is 'absent'")
                changed = True

            elif self.state == 'present':
                if self.new_name is not None and not self.new_name == \
                        self.name:
                    changed = True
                    rename_qtree = True

        else:
            if self.state == 'present':
                logger.debug(
                    "CHANGED: qtree does not exist, but requested state is "
                    "'present'")

                changed = True

        if changed:
            if self.module.check_mode:
                logger.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not qtree_exists:
                        self.create_qtree()

                    else:
                        if rename_qtree:
                            self.rename_qtree()

                elif self.state == 'absent':
                    self.delete_qtree()
        else:
            logger.debug("exiting with no changes")

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTQTree()

    try:
        v.apply()
    except Exception, e:
        logger.debug("Exception in apply(): \n%s" % format_exc(e))
        raise

main()
