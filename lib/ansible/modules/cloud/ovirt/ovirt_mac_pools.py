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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_mac_pools
short_description: Module to manage MAC pools in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "This module manage MAC pools in oVirt/RHV."
options:
    name:
        description:
            - "Name of the MAC pool to manage."
        required: true
    description:
        description:
            - "Description of the MAC pool."
    state:
        description:
            - "Should the mac pool be present or absent."
        choices: ['present', 'absent']
        default: present
    allow_duplicates:
        description:
            - "If (true) allow a MAC address to be used multiple times in a pool."
            - "Default value is set by oVirt/RHV engine to I(false)."
    ranges:
        description:
            - "List of MAC ranges. The from and to should be split by comma."
            - "For example: 00:1a:4a:16:01:51,00:1a:4a:16:01:61"
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create MAC pool:
- ovirt_mac_pools:
    name: mymacpool
    allow_duplicates: false
    ranges:
      - 00:1a:4a:16:01:51,00:1a:4a:16:01:61
      - 00:1a:4a:16:02:51,00:1a:4a:16:02:61

# Remove MAC pool:
- ovirt_mac_pools:
    state: absent
    name: mymacpool
'''

RETURN = '''
id:
    description: ID of the MAC pool which is managed
    returned: On success if MAC pool is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
template:
    description: "Dictionary of all the MAC pool attributes. MAC pool attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/mac_pool."
    returned: On success if MAC pool is found.
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
    equal,
    create_connection,
    ovirt_full_argument_spec,
)


class MACPoolModule(BaseModule):

    def build_entity(self):
        return otypes.MacPool(
            name=self._module.params['name'],
            allow_duplicates=self._module.params['allow_duplicates'],
            description=self._module.params['description'],
            ranges=[
                otypes.Range(
                    from_=mac_range.split(',')[0],
                    to=mac_range.split(',')[1],
                )
                for mac_range in self._module.params['ranges']
            ],
        )

    def _compare_ranges(self, entity):
        if self._module.params['ranges'] is not None:
            ranges = sorted([
                '%s,%s' % (mac_range.from_, mac_range.to)
                for mac_range in entity.ranges
            ])
            return equal(sorted(self._module.params['ranges']), ranges)

        return True

    def update_check(self, entity):
        return (
            self._compare_ranges(entity) and
            equal(self._module.params['allow_duplicates'], entity.allow_duplicates) and
            equal(self._module.params['description'], entity.description)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(default=None, required=True),
        allow_duplicates=dict(default=None, type='bool'),
        description=dict(default=None),
        ranges=dict(default=None, type='list'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        mac_pools_service = connection.system_service().mac_pools_service()
        mac_pools_module = MACPoolModule(
            connection=connection,
            module=module,
            service=mac_pools_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = mac_pools_module.create()
        elif state == 'absent':
            ret = mac_pools_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
