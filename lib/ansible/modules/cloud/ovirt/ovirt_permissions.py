#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_permissions
short_description: Module to manage permissions of users/groups in oVirt/RHV
version_added: "2.3"
author:
- Ondra Machacek (@machacekondra)
description:
    - Module to manage permissions of users/groups in oVirt/RHV.
options:
    role:
        description:
            - Name of the role to be assigned to user/group on specific object.
        default: UserRole
    state:
        description:
            - Should the permission be present/absent.
        choices: [ absent, present ]
        default: present
    object_id:
        description:
            - ID of the object where the permissions should be managed.
    object_name:
        description:
            - Name of the object where the permissions should be managed.
    object_type:
        description:
            - The object where the permissions should be managed.
        choices:
        - cluster
        - cpu_profile
        - data_center
        - disk
        - disk_profile
        - host
        - network
        - storage_domain
        - system
        - template
        - vm
        - vm_pool
        - vnic_profile
        default: vm
    user_name:
        description:
            - Username of the user to manage. In most LDAPs it's I(uid) of the user,
              but in Active Directory you must specify I(UPN) of the user.
            - Note that if user does not exist in the system this module will fail,
              you should ensure the user exists by using M(ovirt_users) module.
    group_name:
        description:
            - Name of the group to manage.
            - Note that if group does not exist in the system this module will fail,
               you should ensure the group exists by using M(ovirt_groups) module.
    authz_name:
        description:
            - Authorization provider of the user/group.
        required: true
        aliases: [ domain ]
    namespace:
        description:
            - Namespace of the authorization provider, where user/group resides.
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

- name: Add user user1 from authorization provider example.com-authz
  ovirt_permissions:
    user_name: user1
    authz_name: example.com-authz
    object_type: vm
    object_name: myvm
    role: UserVmManager

- name: Remove permission from user
  ovirt_permissions:
    state: absent
    user_name: user1
    authz_name: example.com-authz
    object_type: cluster
    object_name: mycluster
    role: ClusterAdmin
'''

RETURN = '''
id:
    description: ID of the permission which is managed
    returned: On success if permission is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
permission:
    description: "Dictionary of all the permission attributes. Permission attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/permission."
    returned: On success if permission is found.
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
    follow_link,
    get_link_name,
    ovirt_full_argument_spec,
    search_by_attributes,
    search_by_name,
)


def _objects_service(connection, object_type):
    if object_type == 'system':
        return connection.system_service()

    return getattr(
        connection.system_service(),
        '%ss_service' % object_type,
        None,
    )()


def _object_service(connection, module):
    object_type = module.params['object_type']
    objects_service = _objects_service(connection, object_type)
    if object_type == 'system':
        return objects_service

    object_id = module.params['object_id']
    if object_id is None:
        sdk_object = search_by_name(objects_service, module.params['object_name'])
        if sdk_object is None:
            raise Exception(
                "'%s' object '%s' was not found." % (
                    module.params['object_type'],
                    module.params['object_name']
                )
            )
        object_id = sdk_object.id

    return objects_service.service(object_id)


def _permission(module, permissions_service, connection):
    for permission in permissions_service.list():
        user = follow_link(connection, permission.user)
        if (
            equal(module.params['user_name'], user.principal if user else None) and
            equal(module.params['group_name'], get_link_name(connection, permission.group)) and
            equal(module.params['role'], get_link_name(connection, permission.role))
        ):
            return permission


class PermissionsModule(BaseModule):

    def _user(self):
        user = search_by_attributes(
            self._connection.system_service().users_service(),
            usrname="{name}@{authz_name}".format(
                name=self._module.params['user_name'],
                authz_name=self._module.params['authz_name'],
            ),
        )
        if user is None:
            raise Exception("User '%s' was not found." % self._module.params['user_name'])
        return user

    def _group(self):
        groups = self._connection.system_service().groups_service().list(
            search="name={name}".format(
                name=self._module.params['group_name'],
            )
        )

        # If found more groups, filter them by namespace and authz name:
        # (filtering here, as oVirt/RHV backend doesn't support it)
        if len(groups) > 1:
            groups = [
                g for g in groups if (
                    equal(self._module.params['namespace'], g.namespace) and
                    equal(self._module.params['authz_name'], g.domain.name)
                )
            ]
        if not groups:
            raise Exception("Group '%s' was not found." % self._module.params['group_name'])
        return groups[0]

    def build_entity(self):
        entity = self._group() if self._module.params['group_name'] else self._user()

        return otypes.Permission(
            user=otypes.User(
                id=entity.id
            ) if self._module.params['user_name'] else None,
            group=otypes.Group(
                id=entity.id
            ) if self._module.params['group_name'] else None,
            role=otypes.Role(
                name=self._module.params['role']
            ),
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        role=dict(type='str', default='UserRole'),
        object_type=dict(type='str', default='vm',
                         choices=[
                             'cluster',
                             'cpu_profile',
                             'data_center',
                             'disk',
                             'disk_profile',
                             'host',
                             'network',
                             'storage_domain',
                             'system',
                             'template',
                             'vm',
                             'vm_pool',
                             'vnic_profile',
                         ]),
        authz_name=dict(type='str', required=True, aliases=['domain']),
        object_id=dict(type='str'),
        object_name=dict(type='str'),
        user_name=dict(type='str'),
        group_name=dict(type='str'),
        namespace=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)

    if (module.params['object_name'] is None and module.params['object_id'] is None) and module.params['object_type'] != 'system':
        module.fail_json(msg='"object_name" or "object_id" is required')

    if module.params['user_name'] is None and module.params['group_name'] is None:
        module.fail_json(msg='"user_name" or "group_name" is required')

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        permissions_service = _object_service(connection, module).permissions_service()
        permissions_module = PermissionsModule(
            connection=connection,
            module=module,
            service=permissions_service,
        )

        permission = _permission(module, permissions_service, connection)
        state = module.params['state']
        if state == 'present':
            ret = permissions_module.create(entity=permission)
        elif state == 'absent':
            ret = permissions_module.remove(entity=permission)

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
