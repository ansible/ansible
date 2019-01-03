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
module: ovirt_vmpool
short_description: Module to manage VM pools in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage VM pools in oVirt/RHV."
options:
    id:
        description:
            - "ID of the vmpool to manage."
        version_added: "2.8"
    name:
        description:
            - "Name of the VM pool to manage."
        required: true
    comment:
        description:
            - Comment of the Virtual Machine pool.
    state:
        description:
            - "Should the VM pool be present/absent."
            - "Note that when C(state) is I(absent) all VMs in VM pool are stopped and removed."
        choices: ['present', 'absent']
        default: present
    template:
        description:
            - "Name of the template, which will be used to create VM pool."
    description:
        description:
            - "Description of the VM pool."
    cluster:
        description:
            - "Name of the cluster, where VM pool should be created."
    type:
        description:
            - "Type of the VM pool. Either manual or automatic."
            - "C(manual) - The administrator is responsible for explicitly returning the virtual machine to the pool.
               The virtual machine reverts to the original base image after the administrator returns it to the pool."
            - "C(Automatic) - When the virtual machine is shut down, it automatically reverts to its base image and
               is returned to the virtual machine pool."
            - "Default value is set by engine."
        choices: ['manual', 'automatic']
    vm_per_user:
        description:
            - "Maximum number of VMs a single user can attach to from this pool."
            - "Default value is set by engine."
    prestarted:
        description:
            - "Number of pre-started VMs defines the number of VMs in run state, that are waiting
               to be attached to Users."
            - "Default value is set by engine."
    vm_count:
        description:
            - "Number of VMs in the pool."
            - "Default value is set by engine."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create VM pool from template
- ovirt_vmpool:
    cluster: mycluster
    name: myvmpool
    template: rhel7
    vm_count: 2
    prestarted: 2
    vm_per_user: 1

# Remove vmpool, note that all VMs in pool will be stopped and removed:
- ovirt_vmpool:
    state: absent
    name: myvmpool

# Change Pool Name
- ovirt_vmpool:
    id: 00000000-0000-0000-0000-000000000000
    name: "new_pool_name"
'''

RETURN = '''
id:
    description: ID of the VM pool which is managed
    returned: On success if VM pool is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
vm_pool:
    description: "Dictionary of all the VM pool attributes. VM pool attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/vm_pool."
    returned: On success if VM pool is found.
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
    check_params,
    check_sdk,
    create_connection,
    equal,
    get_link_name,
    ovirt_full_argument_spec,
    wait,
)


class VmPoolsModule(BaseModule):

    def build_entity(self):
        return otypes.VmPool(
            id=self._module.params['id'],
            name=self._module.params['name'],
            description=self._module.params['description'],
            comment=self._module.params['comment'],
            cluster=otypes.Cluster(
                name=self._module.params['cluster']
            ) if self._module.params['cluster'] else None,
            template=otypes.Template(
                name=self._module.params['template']
            ) if self._module.params['template'] else None,
            max_user_vms=self._module.params['vm_per_user'],
            prestarted_vms=self._module.params['prestarted'],
            size=self._module.params['vm_count'],
            type=otypes.VmPoolType(
                self._module.params['type']
            ) if self._module.params['type'] else None,
        )

    def update_check(self, entity):
        return (
            equal(self._module.params.get('name'), entity.name) and
            equal(self._module.params.get('cluster'), get_link_name(self._connection, entity.cluster)) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self._module.params.get('comment'), entity.comment) and
            equal(self._module.params.get('vm_per_user'), entity.max_user_vms) and
            equal(self._module.params.get('prestarted'), entity.prestarted_vms) and
            equal(self._module.params.get('vm_count'), entity.size)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        id=dict(default=None),
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(required=True),
        template=dict(default=None),
        cluster=dict(default=None),
        description=dict(default=None),
        comment=dict(default=None),
        vm_per_user=dict(default=None, type='int'),
        prestarted=dict(default=None, type='int'),
        vm_count=dict(default=None, type='int'),
        type=dict(default=None, choices=['automatic', 'manual']),
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
        vm_pools_service = connection.system_service().vm_pools_service()
        vm_pools_module = VmPoolsModule(
            connection=connection,
            module=module,
            service=vm_pools_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = vm_pools_module.create()

            # Wait for all VM pool VMs to be created:
            if module.params['wait']:
                vms_service = connection.system_service().vms_service()
                for vm in vms_service.list(search='pool=%s' % module.params['name']):
                    wait(
                        service=vms_service.service(vm.id),
                        condition=lambda vm: vm.status in [otypes.VmStatus.DOWN, otypes.VmStatus.UP],
                        timeout=module.params['timeout'],
                    )

        elif state == 'absent':
            ret = vm_pools_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
