#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_datacenter
short_description: Module to manage data centers in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage data centers in oVirt/RHV"
options:
    id:
        description:
            - "ID of the datacenter to manage."
        version_added: "2.8"
    name:
        description:
            - "Name of the data center to manage."
        required: true
    state:
        description:
            - "Should the data center be present or absent."
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
        type: bool
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
            - "IMPORTANT: This option is deprecated in oVirt/RHV 4.1. You should
               use C(mac_pool) in C(ovirt_clusters) module, as MAC pools are
               set per cluster since 4.1."
    force:
        description:
            - "This parameter can be used only when removing a data center.
              If I(True) data center will be forcibly removed, even though it
              contains some clusters. Default value is I(False), which means
              that only empty data center can be removed."
        version_added: "2.5"
        default: False
        type: bool

extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create datacenter
- ovirt_datacenter:
    name: mydatacenter
    local: True
    compatibility_version: 4.0
    quota_mode: enabled

# Remove datacenter
- ovirt_datacenter:
    state: absent
    name: mydatacenter

# Change Datacenter Name
- ovirt_datacenter:
    id: 00000000-0000-0000-0000-000000000000
    name: "new_datacenter_name"
'''

RETURN = '''
id:
    description: "ID of the managed datacenter"
    returned: "On success if datacenter is found."
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
data_center:
    description: "Dictionary of all the datacenter attributes. Datacenter attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/datacenter."
    returned: "On success if datacenter is found."
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
            id=self._module.params['id'],
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
            equal(self._module.params.get('name'), entity.name) and
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
        id=dict(default=None),
        compatibility_version=dict(default=None),
        quota_mode=dict(choices=['disabled', 'audit', 'enabled']),
        comment=dict(default=None),
        mac_pool=dict(default=None),
        force=dict(default=None, type='bool'),
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
        data_centers_module = DatacentersModule(
            connection=connection,
            module=module,
            service=data_centers_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = data_centers_module.create()
        elif state == 'absent':
            ret = data_centers_module.remove(force=module.params['force'])

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
