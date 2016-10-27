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

module: na_cdot_svm

short_description: Manage NetApp cDOT svm
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy svm on NetApp cDOT
    - auth_basic

options:

  state:
    required: true
    description:
    - Whether the specified lun should exist or not.
    choices: ['present', 'absent']

  name:
    required: true
    description:
    - The name of the svm to manage

  new_name:
    required: false
    description:
    - Rename the SVM

  root_volume:
    required: false
    note: required when state == 'present'
    description:
    - Root volume of the svm.

  root_volume_aggregate:
    required: when state == 'present'
    description:
    - The aggregate on which the root volume will be created.

  root_volume_security_style:
    required: when state == 'present'
    description:
    -   Security Style of the root volume. When specified as part of the 
    -   vserver-create, this field represents the security style for the
    -   Vserver root volume. When specified as part of vserver-get-iter
    -   call, this will return the list of matching Vservers. Possible
    -   values are 'unix', 'ntfs', 'mixed'. The 'unified' security style,
    -   which applies only to Infinite Volumes, cannot be applied to a
    -   Vserver's root volume.
    choices: ['unix', 'ntfs', 'mixed', 'unified']
        details:
        -   "unix"      - NFS,
        -   "ntfs"      - CIFS,
        -   "mixed"     - Mixed,
        -   "unified"   - Unified

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

    - name: Create SVM
      na_cdot_svm:
        state: present
        name: ansibleVServer
        root_volume: vol1
        root_volume_aggregate: aggr1
        root_volume_security_style: mixed
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"


    - name: Rename Manager
      na_cdot_svm:
        state: present
        name: ansibleVServer
        new_name: ansibleVServerRenamed
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

"""

RETURN = """
msg:
    description: Successfully created SVM
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successfully renamed SVM
    returned: success
    type: string
    sample: '{"changed": true}'

"""

"""
TODO:
    Add more configurable parameters:
        force_remove - remove all associated volumes
        name-server-switch
        name-mapping-switch
        language
        snapshot-policy
        quota-policy
        ...
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


class NetAppCDOTSVM(object):

    def __init__(self):
        logger.debug('Init %s', self.__class__.__name__)

        self.module = AnsibleModule(
            argument_spec=dict(
                state=dict(required=True, choices=['present', 'absent']),
                name=dict(required=True, type='str'),
                new_name=dict(required=False, type='str', default=None),
                root_volume=dict(type='str'),
                root_volume_aggregate=dict(type='str'),
                root_volume_security_style=dict(type='str', choices=['nfs',
                                                                     'cifs',
                                                                     'mixed',
                                                                     'unified'
                                                                     ]),

                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('state', 'present', ['root_volume',
                                      'root_volume_aggregate',
                                      'root_volume_security_style'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.new_name = p['new_name']
        self.root_volume = p['root_volume']
        self.root_volume_aggregate = p['root_volume_aggregate']
        self.root_volume_security_style = p['root_volume_security_style']
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

    def get_vserver(self):
        """
        Checks if vserver exists.

        :return:
            True if vserver found
            False if vserver is not found
        :rtype: bool
        """

        vserver_info = zapi.NaElement('vserver-get-iter')
        query_details = zapi.NaElement.create_node_with_children(
            'vserver-info', **{'vserver-name': self.name})

        query = zapi.NaElement('query')
        query.add_child_elem(query_details)
        vserver_info.add_child_elem(query)

        result = self.server.invoke_successfully(vserver_info,
                                                 enable_tunneling=False)

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):

            """
            TODO:
                Return more relevant parameters about vserver that can
                be updated by the playbook.
            """
            return True
        else:
            return False

    def create_vserver(self):
        logger.debug('Creating vserver %s with root volume %s on root '
                     'aggregate %s', self.name, self.root_volume,
                     self.root_volume_aggregate)

        vserver_create = zapi.NaElement.create_node_with_children(
            'vserver-create', **{'vserver-name': self.name,
                                 'root-volume': self.root_volume,
                                 'root-volume-aggregate':
                                     self.root_volume_aggregate,
                                 'root-volume-security-style':
                                     self.root_volume_security_style
                                 })

        try:
            self.server.invoke_successfully(vserver_create,
                                            enable_tunneling=False)
        except zapi.NaApiError:
            logger.exception('Error provisioning vserver %s with root volume '
                             '%s on root aggregate %s', self.name,
                             self.root_volume, self.root_volume_aggregate)
            raise

    def delete_vserver(self):
        logger.debug('Deleting vserver %s with root volume %s on root '
                     'aggregate %s', self.name, self.root_volume,
                     self.root_volume_aggregate)

        vserver_delete = zapi.NaElement.create_node_with_children(
            'vserver-destroy', **{'vserver-name': self.name})

        try:
            self.server.invoke_successfully(vserver_delete,
                                            enable_tunneling=False)
        except zapi.NaApiError:
            logger.exception('Error deleting vserver %s with root volume %s '
                             'on root aggregate %s', self.name,
                             self.root_volume, self.root_volume_aggregate)
            raise

    def rename_vserver(self):
        logger.debug('Renaming svm %s', self.name)

        vserver_rename = zapi.NaElement.create_node_with_children(
            'vserver-rename', **{'vserver-name': self.name,
                                 'new-name': self.new_name})

        try:
            self.server.invoke_successfully(vserver_rename,
                                            enable_tunneling=False)
        except zapi.NaApiError, e:
            logger.exception('Error renaming SVM %s. Error : %s',
                             self.name, str(e.code))
            raise

    def apply(self):
        changed = False
        vserver_exists = self.get_vserver()
        rename_vserver = False
        if vserver_exists:
            if self.state == 'absent':
                logger.debug(
                    "CHANGED: vserver exists, but requested state is 'absent'")
                changed = True

            elif self.state == 'present':
                if self.new_name is not None and not self.new_name == \
                        self.name:
                    changed = True
                    rename_vserver = True

        else:
            if self.state == 'present':
                logger.debug(
                    "CHANGED: vserver does not exist, but requested state is "
                    "'present'")

                changed = True

        if changed:
            if self.module.check_mode:
                logger.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not vserver_exists:
                        self.create_vserver()

                    else:
                        if rename_vserver:
                            self.rename_vserver()

                elif self.state == 'absent':
                    self.delete_vserver()
        else:
            logger.debug("exiting with no changes")

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTSVM()

    try:
        v.apply()
    except Exception, e:
        logger.debug("Exception in apply(): \n%s" % format_exc(e))
        raise

main()
