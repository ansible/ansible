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

module: na_cdot_volume

short_description: Manage NetApp cDOT volumes
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy volumes on NetApp cDOT
    - auth_basic

options:

  state:
    required: true
    description:
    - Whether the specified volume should exist or not.
    choices: ['present', 'absent']

  name:
    required: true
    description:
    - The name of the lun to manage

  new_name:
    required: false
    description:
    - Rename the specified volume to the new name.
    - If the volume is referenced in the /etc/exports file, remember to make
    - the name change in /etc/exports also so that the affected file system can
    - be exported by the filer after the filer reboots.

    Note: Set "is-infinite" to True to rename and re-size Infinite Volumes.

  is_infinite:
    required: false
    description:
    - Set True if the volume is an Infinite Volume
    choices: ['True', 'False']
    default: 'False'

  is_online:
    required: false
    description:
    - Whether the specified volume is online, or not.
    choices: ['True', 'False']
    default: 'True'

  aggregate_name:
    required: false
    note: required when state == 'present'
    description:
    - The name of the aggregate the flexvol should exist on

  size:
    required: false
    note: required when state == 'present'
    description:
    - The size of the volume in (size_unit)

  size_unit:
    required: false
    description:
    - The unit used to interpret the size parameter
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: 'gb'

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

    - name: Create FlexVol
      na_cdot_volume:
        state: present
        name: ansibleVolume
        is_infinite: False
        aggregate_name: aggr1
        size: 20
        size_unit: mb
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Make FlexVol offline
      na_cdot_volume:
        state: present
        name: ansibleVolume
        is_infinite: False
        is_online: False
        vserver: ansibleVServer
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

"""

RETURN = """
msg:
    description: Successfully created FlexVol
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successfully changed FlexVol status to offline
    returned: success
    type: string
    sample: '{"changed": true}'

"""

"""
TODO:
    Add more configurable parameters
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


class NetAppCDOTVolume(object):

    def __init__(self):

        self._size_unit_map = dict(
            bytes=1,
            b=1,
            kb=1024,
            mb=1024 ** 2,
            gb=1024 ** 3,
            tb=1024 ** 4,
            pb=1024 ** 5,
            eb=1024 ** 6,
            zb=1024 ** 7,
            yb=1024 ** 8
        )

        self.module = AnsibleModule(
            argument_spec=dict(
                state=dict(required=True, choices=['present', 'absent']),
                name=dict(required=True, type='str'),
                new_name=dict(required=False, type='str', default=None),
                is_infinite=dict(required=False, type='bool', default=False),
                is_online=dict(required=False, type='bool', default=True),
                size=dict(type='int'),
                size_unit=dict(default='gb',
                               choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                        'pb', 'eb', 'zb', 'yb'], type='str'),
                aggregate_name=dict(type='str'),

                vserver=dict(required=True, type='str'),
                hostname=dict(required=True, type='str'),
                username=dict(required=True, type='str'),
                password=dict(required=True, type='str'),
            ),
            required_if=[
                ('state', 'present', ['aggregate_name', 'size'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.new_name = p['new_name']
        self.is_infinite = p['is_infinite']
        self.is_online = p['is_online']
        self.size_unit = p['size_unit']
        if p['size'] is not None:
            self.size = p['size'] * self._size_unit_map[self.size_unit]
        else:
            self.size = None
        self.aggregate_name = p['aggregate_name']
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

    def get_volume(self):
        """
        Return details about the volume
        :param:
            name : Name of the volume

        :return: Details about the volume. None if not found.
        :rtype: dict
        """
        volume_info = zapi.NaElement('volume-get-iter')
        volume_attributes = zapi.NaElement('volume-attributes')
        volume_id_attributes = zapi.NaElement('volume-id-attributes')
        volume_id_attributes.add_new_child('name', self.name)
        volume_attributes.add_child_elem(volume_id_attributes)

        query = zapi.NaElement('query')
        query.add_child_elem(volume_attributes)

        volume_info.add_child_elem(query)

        result = self.server.invoke_successfully(volume_info, True)

        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            volume_attributes = result.get_child_by_name(
                'attributes-list').get_child_by_name(
                'volume-attributes')
            # Get volume's current size
            volume_space_attributes = volume_attributes.get_child_by_name(
                'volume-space-attributes')
            current_size = volume_space_attributes.get_child_content('size')

            # Get volume's state (online/offline)
            volume_state_attributes = volume_attributes.get_child_by_name(
                'volume-state-attributes')
            current_state = volume_state_attributes.get_child_content('state')
            is_online = None
            if current_state == "online":
                is_online = True
            elif current_state == "offline":
                is_online = False
            else:
                logger.debug('Unable to determine whether volume is '
                             'online/offline')
            return_value = {
                'name': self.name,
                'size': current_size,
                'is_online': is_online,
            }

        return return_value

    def create_volume(self):
        logger.debug('Creating volume %s of size %s', self.name, self.size)

        volume_create = zapi.NaElement.create_node_with_children(
            'volume-create', **{'volume': self.name,
                                'containing-aggr-name': self.aggregate_name,
                                'size': str(self.size)})

        try:
            self.server.invoke_successfully(volume_create,
                                            enable_tunneling=True)
        except zapi.NaApiError:
            logger.exception('Error provisioning volume %s of size %s',
                             self.name, self.size)
            raise

    def delete_volume(self):
        logger.debug('Deleting volume %s', self.name)

        if self.is_infinite:
            volume_delete = zapi.NaElement.create_node_with_children(
                'volume-destroy-async', **{'volume-name': self.name})
        else:
            volume_delete = zapi.NaElement.create_node_with_children(
                'volume-destroy', **{'name': self.name, 'unmount-and-offline':
                    'true'})

        try:
            self.server.invoke_successfully(volume_delete,
                                            enable_tunneling=True)
        except zapi.NaApiError:
            logger.exception('Error deleting volume %s', self.name)
            raise

    def rename_volume(self):
        """
        Rename the volume.

        Note: 'is_infinite' needs to be set to True in order to rename an
        Infinite Volume.
        """
        logger.debug('Renaming volume %s', self.name)

        if self.is_infinite:
            volume_rename = zapi.NaElement.create_node_with_children(
                'volume-rename-async',
                **{'volume-name': self.name, 'new-volume-name': str(
                    self.new_name)})
        else:
            volume_rename = zapi.NaElement.create_node_with_children(
                'volume-rename', **{'volume': self.name, 'new-volume-name': str(
                    self.new_name)})
        try:
            self.server.invoke_successfully(volume_rename,
                                            enable_tunneling=True)
        except zapi.NaApiError:
            logger.exception('Error renaming volume %s', self.name)
            raise

    def resize_volume(self):
        """
        Re-size the volume.

        Note: 'is_infinite' needs to be set to True in order to rename an
        Infinite Volume.
        """
        logger.debug('Re-sizing volume %s', self.name)

        if self.is_infinite:
            volume_resize = zapi.NaElement.create_node_with_children(
                'volume-size-async',
                **{'volume-name': self.name, 'new-size': str(
                    self.size)})
        else:
            volume_resize = zapi.NaElement.create_node_with_children(
                'volume-size', **{'volume': self.name, 'new-size': str(
                    self.size)})
        try:
            self.server.invoke_successfully(volume_resize,
                                            enable_tunneling=True)
        except zapi.NaApiError:
            logger.exception('Error re-sizing volume %s', self.name)
            raise

    def change_volume_state(self):
        """
        Change volume's state (offline/online).

        Note: 'is_infinite' needs to be set to True in order to change the
        state of an Infinite Volume.
        """
        logger.debug('Changing state of volume %s', self.name)
        state_requested = None
        if self.is_online:
            # Requested state is 'online'.
            state_requested = "online"
            if self.is_infinite:
                volume_change_state = zapi.NaElement.create_node_with_children(
                    'volume-online-async',
                    **{'volume-name': self.name})
            else:
                volume_change_state = zapi.NaElement.create_node_with_children(
                    'volume-online',
                    **{'name': self.name})
        else:
            # Requested state is 'offline'.
            state_requested = "offline"
            if self.is_infinite:
                volume_change_state = zapi.NaElement.create_node_with_children(
                    'volume-offline-async',
                    **{'volume-name': self.name})
            else:
                volume_change_state = zapi.NaElement.create_node_with_children(
                    'volume-offline',
                    **{'name': self.name})
        try:
            self.server.invoke_successfully(volume_change_state,
                                            enable_tunneling=True)
        except zapi.NaApiError:
            logger.exception('Error changing the state of volume %s to %s',
                             self.name, state_requested)
            raise

    def apply(self):
        changed = False
        volume_exists = False
        rename_volume = False
        resize_volume = False
        volume_detail = self.get_volume()

        if volume_detail:
            volume_exists = True

            if self.state == 'absent':
                logger.debug(
                    "CHANGED: volume exists, but requested state is 'absent'")
                changed = True

            elif self.state == 'present':
                if self.new_name is not None and not self.new_name == \
                        self.name:
                    logger.debug(
                        "CHANGED: volume needs to be renamed")
                    rename_volume = True
                    changed = True
                if str(volume_detail['size']) != str(self.size):
                    logger.debug(
                        "CHANGED: volume needs to be re-sized")
                    resize_volume = True
                    changed = True
                if volume_detail['is_online'] is not \
                        None and volume_detail['is_online'] != \
                        self.is_online:
                    if self.is_online is False:
                        logger.debug(
                            "CHANGED: volume is online but requested state "
                            "is offline")
                    else:
                        logger.debug(
                            "CHANGED: volume is offline but requested state "
                            "is online")
                    changed = True

        else:
            if self.state == 'present':
                logger.debug(
                    "CHANGED: volume does not exist, but requested state is "
                    "'present'")

                changed = True

        if changed:
            if self.module.check_mode:
                logger.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not volume_exists:
                        self.create_volume()

                    else:
                        if resize_volume:
                            self.resize_volume()
                        if volume_detail['is_online'] is not \
                                None and volume_detail['is_online'] != \
                                self.is_online:
                            self.change_volume_state()
                        # Ensure re-naming is the last change made.
                        if rename_volume:
                            self.rename_volume()

                elif self.state == 'absent':
                    self.delete_volume()
        else:
            logger.debug("exiting with no changes")

        # TODO: include other details about the volume (size, cache config,
        # etc)
        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTVolume()

    try:
        v.apply()
    except Exception, e:
        logger.debug("Exception in apply(): \n%s" % format_exc(e))
        raise

main()
