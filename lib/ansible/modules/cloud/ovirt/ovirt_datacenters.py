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
module: ovirt_datacenters
short_description: Module to manage data centers in oVirt
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage data centers in oVirt"
options:
    name:
        description:
            - "Name of the the data center to manage."
        required: true
    state:
        description:
            - "Should the data center be present or absent"
        choices: ['present', 'absent']
        default: present
    description:
        description:
            - "Description of the data center."
    comment:
        description:
            - "Comment of the data center."
    local:
        description:
            - "I(True) if the data center should be local, I(False) if should be shared."
            - "Default value is set by engine."
    compatibility_version:
        description:
            - "Compatibility version of the data center."
    quota_mode:
        description:
            - "Quota mode of the data center. One of I(disabled), I(audit) or I(enabled)"
        choices: ['disabled', 'audit', 'enabled']
    mac_pool:
        description:
            - "MAC pool to be used by this datacenter."
            - "IMPORTANT: This option is deprecated in oVirt 4.1. You should
               use C(mac_pool) in C(ovirt_clusters) module, as MAC pools are
               set per cluster since 4.1."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create datacenter
- ovirt_datacenters:
    name: mydatacenter
    local: True
    compatibility_version: 4.0
    quota_mode: enabled

# Remove datacenter
- ovirt_datacenters:
    state: absent
    name: mydatacenter
'''

RETURN = '''
id:
    description: "ID of the managed datacenter"
    returned: "On success if datacenter is found."
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
data_center:
    description: "Dictionary of all the datacenter attributes. Datacenter attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/datacenter."
    returned: "On success if datacenter is found."
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
    search_by_name,
)


class DatacentersModule(BaseModule):

    def __get_major(self, full_version):
        if full_version is None:
            return None
        if isinstance(full_version, otypes.Version):
            return full_version.major
        return int(full_version.split('.')[0])

    def __get_minor(self, full_version):
        if full_version is None:
            return None
        if isinstance(full_version, otypes.Version):
            return full_version.minor
        return int(full_version.split('.')[1])

    def _get_mac_pool(self):
        mac_pool = None
        if self._module.params.get('mac_pool'):
            mac_pool = search_by_name(
                self._connection.system_service().mac_pools_service(),
                self._module.params.get('mac_pool'),
            )

        return mac_pool

    def build_entity(self):
        return otypes.DataCenter(
            name=self._module.params['name'],
            comment=self._module.params['comment'],
            description=self._module.params['description'],
            mac_pool=otypes.MacPool(
                id=getattr(self._get_mac_pool(), 'id', None),
            ) if self._module.params.get('mac_pool') else None,
            quota_mode=otypes.QuotaModeType(
                self._module.params['quota_mode']
            ) if self._module.params['quota_mode'] else None,
            local=self._module.params['local'],
            version=otypes.Version(
                major=self.__get_major(self._module.params['compatibility_version']),
                minor=self.__get_minor(self._module.params['compatibility_version']),
            ) if self._module.params['compatibility_version'] else None,
        )

    def update_check(self, entity):
        minor = self.__get_minor(self._module.params.get('compatibility_version'))
        major = self.__get_major(self._module.params.get('compatibility_version'))
        return (
            equal(getattr(self._get_mac_pool(), 'id', None), getattr(entity.mac_pool, 'id', None)) and
            equal(self._module.params.get('comment'), entity.comment) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self._module.params.get('quota_mode'), str(entity.quota_mode)) and
            equal(self._module.params.get('local'), entity.local) and
            equal(minor, self.__get_minor(entity.version)) and
            equal(major, self.__get_major(entity.version))
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(default=None, required=True),
        description=dict(default=None),
        local=dict(type='bool'),
        compatibility_version=dict(default=None),
        quota_mode=dict(choices=['disabled', 'audit', 'enabled']),
        comment=dict(default=None),
        mac_pool=dict(default=None),
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
        data_centers_service = connection.system_service().data_centers_service()
        clusters_module = DatacentersModule(
            connection=connection,
            module=module,
            service=data_centers_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = clusters_module.create()
        elif state == 'absent':
            ret = clusters_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
