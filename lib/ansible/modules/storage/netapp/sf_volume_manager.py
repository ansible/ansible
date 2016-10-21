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

module: sf_volume_manager

short_description: Manage SolidFire volumes

description:
- Create, destroy, or update volumes on SolidFire
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
        - Create, Delete, or Update a volume with the passed parameters
        choices: ['create', 'delete', 'update']

    name:
        required: true when action == 'create'
        description:
        - The name of the volume to manage

    account_id:
        required: true when action == 'create'
        type: int
        description:
        - account_id for the owner of this volume

    enable512e:
        required: true when action == 'create'
        type: bool
        description:
        - Should the volume provides 512-byte sector emulation?

    qos:
        required: false
        description: Initial quality of service settings for this volume.

    attributes:
        required: false
        type: dict
        description: List of Name/Value pairs in JSON object format.

    volume_id:
        required: true when action == 'delete' or action == 'update'
        description:
        - The ID of the volume to manage or update

    size:
        required: true when action == 'create'
        description:
        - The size of the volume in (size_unit)

    size_unit:
        required: false
        description:
        - The unit used to interpret the size parameter
        choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
        default: 'gb'

    access:
        required: false
        description:
        - Access allowed for the volume
        choices: ['readOnly', 'readWrite', 'locked', 'replicationTarget']

                readOnly: Only read operations are allowed.

                readWrite: Reads and writes are allowed.

                locked: No reads or writes are allowed.

                replicationTarget: Identify a volume as the target volume for a paired set of volumes.
                                   If the volume is not paired, the access status is locked.

                If unspecified, the access settings of the clone will be the same as the source.

    set_create_time:
        required: false
        type: String
        description:
        - Identify the time at which the volume was created.

'''

'''
    Todo:
        Enable volume delete by Name and account ID. Currently only possible through volume_id.

        Before updating a volume, check the previous (current) attributes to currently report
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


class SolidFireVolume(object):

    def __init__(self):

        self._size_unit_map = dict(

            # SolidFire displays 1024 ** 3 as 1.1 GB, thus use 1000.
            bytes=1,
            b=1,
            kb=1000,
            mb=1000 ** 2,
            gb=1000 ** 3,
            tb=1000 ** 4,
            pb=1000 ** 5,
            eb=1000 ** 6,
            zb=1000 ** 7,
            yb=1000 ** 8
        )

        self.module = AnsibleModule(
            argument_spec=dict(
                action=dict(required=True, choices=['create', 'delete', 'update']),
                name=dict(type='str'),
                account_id=dict(type='str'),
                enable512e=dict(type='bool'),
                qos=dict(required=False, type='str'),
                attributes=dict(required=False, type='dict'),

                volume_id=dict(type='int'),
                size=dict(type='int'),
                size_unit=dict(default='gb',
                               choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                        'pb', 'eb', 'zb', 'yb'], type='str'),

                access=dict(required=False, type='str', choices=['readOnly', 'readWrite',
                                                                 'locked', 'replicationTarget']),
                set_create_time=dict(required=False, type='str'),

                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('action', 'create', ['name', 'account_id', 'size', 'enable512e']),
                ('action', 'delete', ['volume_id']),
                ('action', 'update', ['volume_id'])
            ],
            supports_check_mode=False
        )

        p = self.module.params

        # set up state variables
        self.action = p['action']
        self.name = p['name']
        self.account_id = p['account_id']
        self.enable512e = p['enable512e']
        self.qos = p['qos']
        self.attributes = p['attributes']

        self.volume_id = p['volume_id']
        self.size_unit = p['size_unit']
        if p['size'] is not None:
            self.size = p['size'] * self._size_unit_map[self.size_unit]
        else:
            self.size = None
        self.access = p['access']
        self.set_create_time = p['set_create_time']

        self.hostname = p['hostname']
        self.username = p['username']
        self.password = p['password']

        # create connection to solidfire cluster
        self.sfe = ElementFactory.create(self.hostname, self.username, self.password)

    def create_volume(self):
        logger.debug('Creating volume %s of size %s', self.name, self.size)

        try:
            create_volume_result = self.sfe.create_volume(name=self.name,
                                                          account_id=self.account_id,
                                                          total_size=self.size,
                                                          enable512e=self.enable512e,
                                                          qos=self.qos,
                                                          attributes=self.attributes)

        except:
            err = get_exception()
            logger.exception('Error provisioning volume %s of size %s : %s',
                             self.name, self.size, str(err))
            raise

    def delete_volume(self):
        logger.debug('Deleting volume %s', self.name)

        try:
            self.sfe.delete_volume(volume_id=self.volume_id)

        except:
            err = get_exception()
            logger.exception('Error deleting volume %s : %s', self.volume_id, str(err))
            raise

    def update_volume(self):
        logger.debug('Updating volume %s', self.name)

        try:
            self.sfe.modify_volume(self.volume_id, account_id=self.account_id,
                                   access=self.access, set_create_time=self.set_create_time,
                                   qos=self.qos, total_size=self.size,
                                   attributes=self.attributes)

        except:
            err = get_exception()
            logger.exception('Error updating volume %s : %s', self.volume_id, str(err))
            raise

    def apply(self):
        changed = False

        if self.action == 'create':
            self.create_volume()
            changed = True

        elif self.action == 'delete':
            self.delete_volume()
            changed = True

        elif self.action == 'update':
            self.update_volume()
            changed = True

        self.module.exit_json(changed=changed)


def main():
    v = SolidFireVolume()

    try:
        v.apply()
    except:
        err = get_exception()
        logger.debug("Exception in apply(): \n%s" % format_exc(err))
        raise

main()
