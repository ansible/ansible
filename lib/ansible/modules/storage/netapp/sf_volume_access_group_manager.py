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

#!/usr/bin/python

DOCUMENTATION = '''

module: sf_volume_access_group_manager

short_description: Manage SolidFire Volume Access Groups

description:
- Create, destroy, or update volume access groups on SolidFire
    - auth_basic

options:

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

    action:
        required: true
        description:
        - Create, Delete, or Update a volume access group with the passed parameters
        choices: ['create', 'delete', 'update']

    name:
        required: true when action == 'create'
        description:
        - Name of the volume access group. It is not required to be unique, but recommended.

    initiators:
        required: false
        type: str[]
        description:
        - List of initiators to include in the volume access group. If unspecified, the access
          group will start out without configured initiators.

    volumes:
        required: false
        type: int[]
        description:
        -  List of volumes to initially include in the volume access group. If unspecified,
           the access group will start without any volumes.

    virtual_network_id:
        required: false
        type: int[]
        description:
        -  The ID of the SolidFire Virtual Network ID to associate the volume access group with.

    virtual_network_tags:
        required: false
        type: int[]
        description:
        -  The ID of the VLAN Virtual Network Tag to associate the volume access group with.

    attributes:
        required: false
        type: dict
        description: List of Name/Value pairs in JSON object format.

    volume_access_group_id:
        required: true when action == 'delete' or action == 'update'
        description:
        - The ID of the volume access group to modify or delete.

'''

'''
        Before updating a volume access group, check the previous (current) attributes to currently report
        the 'changed' property

'''
import sys
import json
import logging
from traceback import format_exc

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.pycompat24 import get_exception

import socket
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from solidfire.factory import ElementFactory


class SolidFireVolumeAccessGroup(object):

    def __init__(self):

        self.module = AnsibleModule(
            argument_spec=dict(
                action=dict(required=True, choices=['create', 'delete', 'update']),

                name=dict(type='str'),
                initiators=dict(required=False, type='list'),
                volumes=dict(required=False, type='list'),
                virtual_network_id=dict(required=False, type='list'),
                virtual_network_tags=dict(required=False, type='list'),
                attributes=dict(required=False, type='dict'),

                volume_access_group_id=dict(type='int'),

                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('action', 'create', ['name']),
                ('action', 'delete', ['volume_access_group_id']),
                ('action', 'update', ['volume_access_group_id'])
            ],
            supports_check_mode=False
        )

        p = self.module.params

        # set up state variables
        self.action = p['action']
        self.name = p['name']
        self.initiators = p['initiators']
        self.volumes = p['volumes']
        self.virtual_network_id = p['virtual_network_id']
        self.virtual_network_tags = p['virtual_network_tags']
        self.attributes = p['attributes']
        self.volume_access_group_id = p['volume_access_group_id']

        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']

        # create connection to solidfire cluster
        self.sfe = ElementFactory.create(self.hostname, self.username, self.password)

    def create_volume_access_group(self):
        logger.debug('Creating volume access group %s', self.name)

        try:
            self.sfe.create_volume_access_group(name=self.name, initiators=self.initiators,
                                                volumes=self.volumes,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                attributes=self.attributes)
        except:
            err = get_exception()
            logger.exception('Error creating volume access group %s : %s',
                             self.name, str(err))
            raise

    def delete_volume_access_group(self):
        logger.debug('Deleting volume access group %s', self.volume_access_group_id)

        try:
            self.sfe.delete_volume_access_group(volume_access_group_id=self.volume_access_group_id)

        except:
            err = get_exception()
            logger.exception('Error deleting volume access group %s : %s', self.volume_access_group_id, str(err))
            raise

    def update_volume_access_group(self):
        logger.debug('Updating volume access group %s', self.volume_access_group_id)

        try:
            self.sfe.modify_volume_access_group(volume_access_group_id=self.volume_access_group_id,
                                                virtual_network_id=self.virtual_network_id,
                                                virtual_network_tags=self.virtual_network_tags,
                                                name=self.name, initiators=self.initiators,
                                                volumes=self.volumes, attributes=self.attributes)
        except:
            err = get_exception()
            logger.exception('Error updating volume access group %s : %s', self.volume_access_group_id, str(err))
            raise

    def apply(self):
        changed = False

        if self.action == 'create':
            self.create_volume_access_group()
            changed = True

        elif self.action == 'delete':
            self.delete_volume_access_group()
            changed = True

        elif self.action == 'update':
            self.update_volume_access_group()
            changed = True

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireVolumeAccessGroup()

    try:
        v.apply()
    except:
        err = get_exception()
        logger.debug("Exception in apply(): \n%s" % format_exc(err))
        raise

main()
