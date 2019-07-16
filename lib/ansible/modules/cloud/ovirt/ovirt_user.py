#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
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
module: ovirt_user
short_description: Module to manage users in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage users in oVirt/RHV."
options:
    name:
        description:
            - "Name of the user to manage. In most LDAPs it's I(uid) of the user, but in Active Directory you must specify I(UPN) of the user."
        required: true
    state:
        description:
            - "Should the user be present/absent."
        choices: ['present', 'absent']
        default: present
    authz_name:
        description:
            - "Authorization provider of the user. In previous versions of oVirt/RHV known as domain."
        required: true
        aliases: ['domain']
    namespace:
        description:
            - "Namespace where the user resides. When using the authorization provider that stores users in the LDAP server,
               this attribute equals the naming context of the LDAP server."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add user user1 from authorization provider example.com-authz
- ovirt_user:
    name: user1
    domain: example.com-authz

# Add user user1 from authorization provider example.com-authz
# In case of Active Directory specify UPN:
- ovirt_user:
    name: user1@ad2.example.com
    domain: example.com-authz

# Remove user user1 with authorization provider example.com-authz
- ovirt_user:
    state: absent
    name: user1
    authz_name: example.com-authz
'''

RETURN = '''
id:
    description: ID of the user which is managed
    returned: On success if user is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
user:
    description: "Dictionary of all the user attributes. User attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/user."
    returned: On success if user is found.
    type: dict
'''

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    check_params,
    create_connection,
    ovirt_full_argument_spec,
)


def username(module):
    return '{0}@{1}'.format(module.params['name'], module.params['authz_name'])


class UsersModule(BaseModule):

    def build_entity(self):
        return otypes.User(
            domain=otypes.Domain(
                name=self._module.params['authz_name']
            ),
            user_name=username(self._module),
            principal=self._module.params['name'],
            namespace=self._module.params['namespace'],
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(required=True),
        authz_name=dict(required=True, aliases=['domain']),
        namespace=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    check_sdk(module)
    check_params(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        users_service = connection.system_service().users_service()
        users_module = UsersModule(
            connection=connection,
            module=module,
            service=users_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = users_module.create(
                search_params={
                    'usrname': username(module),
                }
            )
        elif state == 'absent':
            ret = users_module.remove(
                search_params={
                    'usrname': username(module),
                }
            )

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
