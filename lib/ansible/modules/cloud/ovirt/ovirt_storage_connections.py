#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Red Hat, Inc.
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_storage_connections
short_description: Module to manage storage connections in oVirt
version_added: "2.4"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage storage connections in oVirt"
options:
    id:
        description:
            - "Id of the storage connection to manage."
    state:
        description:
            - "Should the storage connection be present or absent."
        choices: ['present', 'absent']
        default: present
    storage:
        description:
            - "Name of the storage domain to be used with storage connection."
    address:
        description:
            - "Address of the storage server. E.g.: myserver.mydomain.com"
    path:
        description:
            - "Path of the mount point of the storage. E.g.: /path/to/my/data"
    nfs_version:
        description:
            - "NFS version. One of: I(auto), I(v3), I(v4) or I(v4_1)."
    nfs_timeout:
        description:
            - "The time in tenths of a second to wait for a response before retrying NFS requests. Range 0 to 65535."
    nfs_retrans:
        description:
            - "The number of times to retry a request before attempting further recovery actions. Range 0 to 65535."
    mount_options:
        description:
            - "Option which will be passed when mounting storage."
    password:
        description:
            - "A CHAP password for logging into a target."
    username:
        description:
            - "A CHAP username for logging into a target."
    port:
        description:
            - "Port of the iSCSI storage server."
    target:
        description:
            - "The target IQN for the storage device."
    type:
        description:
            - "Storage type. For example: I(nfs), I(iscsi), etc."
    vfs_type:
        description:
            - "Virtual File System type."
    force:
        description:
            - "This parameter is releven only when updating a connection."
            - "If I(true) the storage domain don't have to be in I(MAINTENANCE)
               state, so the storage connection is updated."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add new storage connection:
- ovirt_storage_connections:
    storage: myiscsi
    address: 10.34.63.199
    target: iqn.2016-08-09.domain-01:nickname
    port: 3260
    type: iscsi

# Update the existing storage connection address:
- ovirt_storage_connections:
    id: 26915c96-92ff-47e5-9e77-b581db2f2d36
    address: 10.34.63.204
    force: true

# Remove storage connection:
- ovirt_storage_connections:
    id: 26915c96-92ff-47e5-9e77-b581db2f2d36
'''

RETURN = '''
id:
    description: ID of the storage connection which is managed
    returned: On success if storage connection is found.
    type: string
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
storage_connection:
    description: "Dictionary of all the storage connection attributes. Storage connection attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/storage_connection."
    returned: On success if storage connection is found.
    type: dict
'''

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    ovirt_full_argument_spec,
    search_by_name,
)


class StorageConnectionModule(BaseModule):

    def build_entity(self):
        return otypes.StorageConnection(
            address=self.param('address'),
            path=self.param('path'),
            nfs_version=self.param('nfs_version'),
            nfs_timeo=self.param('nfs_timeout'),
            nfs_retrans=self.param('nfs_retrans'),
            mount_options=self.param('mount_options'),
            password=self.param('password'),
            username=self.param('username'),
            port=self.param('port'),
            target=self.param('target'),
            type=otypes.StorageType(
                self.param('type')
            ) if self.param('type') is not None else None,
            vfs_type=self.param('vfs_type'),
        )

    def post_present(self, entity_id):
        if self.param('storage'):
            sds_service = self._connection.system_service().storage_domains_service()
            sd = search_by_name(sds_service, self.param('storage'))
            if sd is None:
                raise Exception(
                    "Storage '%s' was not found." % self.param('storage')
                )

            if entity_id not in [
                sd_conn.id for sd_conn in self._connection.follow_link(sd.storage_connections)
            ]:
                scs_service = sds_service.storage_domain_service(sd.id).storage_connections_service()
                if not self._module.check_mode:
                    scs_service.add(
                        connection=otypes.StorageConnection(
                            id=entity_id,
                        ),
                    )
                self.changed = True

    def update_check(self, entity):
        return (
            equal(self.param('address'), entity.address) and
            equal(self.param('path'), entity.path) and
            equal(self.param('nfs_version'), entity.nfs_version) and
            equal(self.param('nfs_timeout'), entity.nfs_timeo) and
            equal(self.param('nfs_retrans'), entity.nfs_retrans) and
            equal(self.param('mount_options'), entity.mount_options) and
            equal(self.param('password'), entity.password) and
            equal(self.param('username'), entity.username) and
            equal(self.param('port'), entity.port) and
            equal(self.param('target'), entity.target) and
            equal(self.param('type'), str(entity.type)) and
            equal(self.param('vfs_type'), entity.vfs_type)
        )


def find_sc_by_attributes(module, storage_connections_service):
    for sd_conn in [
        sc for sc in storage_connections_service.list()
        if str(sc.type) == module.params['type']
    ]:
        sd_conn_type = str(sd_conn.type)
        if sd_conn_type in ['nfs', 'posixfs', 'glusterfs', 'localfs']:
            if (
                module.params['address'] == sd_conn.address and
                module.params['path'] == sd_conn.path
            ):
                return sd_conn
        elif sd_conn_type in ['iscsi', 'fcp']:
            if (
                module.params['address'] == sd_conn.address and
                module.params['target'] == sd_conn.target
            ):
                return sd_conn


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        id=dict(default=None),
        address=dict(default=None),
        path=dict(default=None),
        nfs_version=dict(default=None),
        nfs_timeout=dict(default=None, type='int'),
        nfs_retrans=dict(default=None, type='int'),
        mount_options=dict(default=None),
        password=dict(default=None, no_log=True),
        username=dict(default=None),
        port=dict(default=None, type='int'),
        target=dict(default=None),
        type=dict(default=None),
        vfs_type=dict(default=None),
        force=dict(type='bool', default=False),
        storage=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        storage_connections_service = connection.system_service().storage_connections_service()
        storage_connection_module = StorageConnectionModule(
            connection=connection,
            module=module,
            service=storage_connections_service,
        )
        entity = None
        if module.params['id'] is None:
            entity = find_sc_by_attributes(module, storage_connections_service)

        state = module.params['state']
        if state == 'present':
            ret = storage_connection_module.create(
                entity=entity,
                update_params={'force': True},
            )
            storage_connection_module.post_present(ret['id'])
        elif state == 'absent':
            ret = storage_connection_module.remove(entity=entity)

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
