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
module: ovirt_snapshots_facts
short_description: Retrieve facts about one or more oVirt/RHV virtual machine snapshots
author: "Ondra Machacek (@machacekondra)"
version_added: "2.3"
description:
    - "Retrieve facts about one or more oVirt/RHV virtual machine snapshots."
notes:
    - "This module creates a new top-level C(ovirt_snapshots) fact, which
       contains a list of snapshots."
options:
    vm:
        description:
            - "Name of the VM with snapshot."
        required: true
    description:
        description:
            - "Description of the snapshot, can be used as glob expression."
    snapshot_id:
        description:
            - "Id of the snaphost we want to retrieve facts about."
extends_documentation_fragment: ovirt_facts
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about all snapshots which description start with C(update) for VM named C(centos7):
- ovirt_snapshots_facts:
    vm: centos7
    description: update*
- debug:
    var: ovirt_snapshots
'''

RETURN = '''
ovirt_snapshots:
    description: "List of dictionaries describing the snapshot. Snapshot attribtues are mapped to dictionary keys,
                  all snapshot attributes can be found at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/snapshot."
    returned: On success.
    type: list
'''


import fnmatch
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_facts_full_argument_spec,
    search_by_name,
)


def main():
    argument_spec = ovirt_facts_full_argument_spec(
        vm=dict(required=True),
        description=dict(default=None),
        snapshot_id=dict(default=None),
    )
    module = AnsibleModule(argument_spec)
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        vms_service = connection.system_service().vms_service()
        vm_name = module.params['vm']
        vm = search_by_name(vms_service, vm_name)
        if vm is None:
            raise Exception("VM '%s' was not found." % vm_name)

        snapshots_service = vms_service.service(vm.id).snapshots_service()
        if module.params['description']:
            snapshots = [
                e for e in snapshots_service.list()
                if fnmatch.fnmatch(e.description, module.params['description'])
            ]
        elif module.params['snapshot_id']:
            snapshots = [
                snapshots_service.snapshot_service(module.params['snapshot_id']).get()
            ]
        else:
            snapshots = snapshots_service.list()

        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_snapshots=[
                    get_dict_of_struct(
                        struct=c,
                        connection=connection,
                        fetch_nested=module.params.get('fetch_nested'),
                        attributes=module.params.get('nested_attributes'),
                    ) for c in snapshots
                ],
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
