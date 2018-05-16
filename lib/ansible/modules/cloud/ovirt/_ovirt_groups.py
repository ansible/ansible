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
module: ovirt_group
short_description: Module to manage groups in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage groups in oVirt/RHV"
options:
    name:
        description:
            - "Name of the group to manage."
        required: true
    state:
        description:
            - "Should the group be present/absent."
        choices: ['present', 'absent']
        default: present
    authz_name:
        description:
            - "Authorization provider of the group. In previous versions of oVirt/RHV known as domain."
        required: true
        aliases: ['domain']
    namespace:
        description:
            - "Namespace of the authorization provider, where group resides."
        required: false
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add group group1 from authorization provider example.com-authz
- ovirt_group:
    name: group1
    domain: example.com-authz

# Add group group1 from authorization provider example.com-authz
# In case of multi-domain Active Directory setup, you should pass
# also namespace, so it adds correct group:
- ovirt_group:
    name: group1
    namespace: dc=ad2,dc=example,dc=com
    domain: example.com-authz

# Remove group group1 with authorization provider example.com-authz
- ovirt_group:
    state: absent
    name: group1
    domain: example.com-authz
'''

RETURN = '''
id:
    description: ID of the group which is managed
    returned: On success if group is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
group:
    description: "Dictionary of all the group attributes. Group attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/group."
    returned: On success if group is found.
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
    equal,
    ovirt_full_argument_spec,
)


def _group(connection, module):
    groups = connection.system_service().groups_service().list(
        search="name={name}".format(
            name=module.params['name'],
        )
    )

    # If found more groups, filter them by namespace and authz name:
    # (filtering here, as oVirt/RHV backend doesn't support it)
    if len(groups) > 1:
        groups = [
            g for g in groups if (
                equal(module.params['namespace'], g.namespace) and
                equal(module.params['authz_name'], g.domain.name)
            )
        ]
    return groups[0] if groups else None


class GroupsModule(BaseModule):

    def build_entity(self):
        return otypes.Group(
            domain=otypes.Domain(
                name=self._module.params['authz_name']
            ),
            name=self._module.params['name'],
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

    if module._name == 'ovirt_groups':
        module.deprecate("The 'ovirt_groups' module is being renamed 'ovirt_group'", version=2.8)

    check_sdk(module)
    check_params(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        groups_service = connection.system_service().groups_service()
        groups_module = GroupsModule(
            connection=connection,
            module=module,
            service=groups_service,
        )
        group = _group(connection, module)
        state = module.params['state']
        if state == 'present':
            ret = groups_module.create(entity=group)
        elif state == 'absent':
            ret = groups_module.remove(entity=group)

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
