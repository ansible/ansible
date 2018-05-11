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
module: ovirt_snapshots
short_description: "Module to manage Virtual Machine Snapshots in oVirt/RHV"
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage Virtual Machine Snapshots in oVirt/RHV"
options:
    snapshot_id:
        description:
            - "ID of the snapshot to manage."
    vm_name:
        description:
            - "Name of the Virtual Machine to manage."
        required: true
    state:
        description:
            - "Should the Virtual Machine snapshot be restore/present/absent."
        choices: ['restore', 'present', 'absent']
        default: present
    description:
        description:
            - "Description of the snapshot."
    use_memory:
        description:
            - "If I(true) and C(state) is I(present) save memory of the Virtual
               Machine if it's running."
            - "If I(true) and C(state) is I(restore) restore memory of the
               Virtual Machine."
            - "Note that Virtual Machine will be paused while saving the memory."
notes:
    - "Note that without a guest agent the data on the created snapshot may be
       inconsistent."
    - "Deleting a snapshot does not remove any information from the virtual
       machine - it simply removes a return-point. However, restoring a virtual
       machine from a snapshot deletes any content that was written to the
       virtual machine after the time the snapshot was taken."
extends_documentation_fragment: ovirt
'''


EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create snapshot:
- ovirt_snapshots:
    vm_name: rhel7
    description: MySnapshot
  register: snapshot

# Create snapshot and save memory:
- ovirt_snapshots:
    vm_name: rhel7
    description: SnapWithMem
    use_memory: true
  register: snapshot

# Restore snapshot:
- ovirt_snapshots:
    state: restore
    vm_name: rhel7
    snapshot_id: "{{ snapshot.id }}"

# Remove snapshot:
- ovirt_snapshots:
    state: absent
    vm_name: rhel7
    snapshot_id: "{{ snapshot.id }}"
'''


RETURN = '''
id:
    description: ID of the snapshot which is managed
    returned: On success if snapshot is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
snapshot:
    description: "Dictionary of all the snapshot attributes. Snapshot attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/snapshot."
    returned: On success if snapshot is found.
    type: dict
'''


import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    get_entity,
    ovirt_full_argument_spec,
    search_by_name,
    wait,
)


def create_snapshot(module, vm_service, snapshots_service):
    changed = False
    snapshot = get_entity(
        snapshots_service.snapshot_service(module.params['snapshot_id'])
    )
    if snapshot is None:
        if not module.check_mode:
            snapshot = snapshots_service.add(
                otypes.Snapshot(
                    description=module.params.get('description'),
                    persist_memorystate=module.params.get('use_memory'),
                )
            )
        changed = True
        wait(
            service=snapshots_service.snapshot_service(snapshot.id),
            condition=lambda snap: snap.snapshot_status == otypes.SnapshotStatus.OK,
            wait=module.params['wait'],
            timeout=module.params['timeout'],
        )
    return {
        'changed': changed,
        'id': snapshot.id,
        'snapshot': get_dict_of_struct(snapshot),
    }


def remove_snapshot(module, vm_service, snapshots_service):
    changed = False
    snapshot = get_entity(
        snapshots_service.snapshot_service(module.params['snapshot_id'])
    )

    if snapshot:
        snapshot_service = snapshots_service.snapshot_service(snapshot.id)
        if not module.check_mode:
            snapshot_service.remove()
        changed = True
        wait(
            service=snapshot_service,
            condition=lambda snapshot: snapshot is None,
            wait=module.params['wait'],
            timeout=module.params['timeout'],
        )

    return {
        'changed': changed,
        'id': snapshot.id if snapshot else None,
        'snapshot': get_dict_of_struct(snapshot),
    }


def restore_snapshot(module, vm_service, snapshots_service):
    changed = False
    snapshot_service = snapshots_service.snapshot_service(
        module.params['snapshot_id']
    )
    snapshot = get_entity(snapshot_service)
    if snapshot is None:
        raise Exception(
            "Snapshot with id '%s' doesn't exist" % module.params['snapshot_id']
        )

    if snapshot.snapshot_status != otypes.SnapshotStatus.IN_PREVIEW:
        if not module.check_mode:
            snapshot_service.restore(
                restore_memory=module.params.get('use_memory'),
            )
        changed = True
    else:
        if not module.check_mode:
            vm_service.commit_snapshot()
        changed = True

    if changed:
        wait(
            service=snapshot_service,
            condition=lambda snap: snap.snapshot_status == otypes.SnapshotStatus.OK,
            wait=module.params['wait'],
            timeout=module.params['timeout'],
        )
    return {
        'changed': changed,
        'id': snapshot.id if snapshot else None,
        'snapshot': get_dict_of_struct(snapshot),
    }


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['restore', 'present', 'absent'],
            default='present',
        ),
        vm_name=dict(required=True),
        snapshot_id=dict(default=None),
        description=dict(default=None),
        use_memory=dict(
            default=None,
            type='bool',
            aliases=['restore_memory', 'save_memory'],
        ),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'absent', ['snapshot_id']),
            ('state', 'restore', ['snapshot_id']),
        ]
    )
    check_sdk(module)

    vm_name = module.params.get('vm_name')
    auth = module.params.pop('auth')
    connection = create_connection(auth)
    vms_service = connection.system_service().vms_service()
    vm = search_by_name(vms_service, vm_name)
    if not vm:
        module.fail_json(
            msg="Vm '{name}' doesn't exist.".format(name=vm_name),
        )

    vm_service = vms_service.vm_service(vm.id)
    snapshots_service = vms_service.vm_service(vm.id).snapshots_service()
    try:
        state = module.params['state']
        if state == 'present':
            ret = create_snapshot(module, vm_service, snapshots_service)
        elif state == 'restore':
            ret = restore_snapshot(module, vm_service, snapshots_service)
        elif state == 'absent':
            ret = remove_snapshot(module, vm_service, snapshots_service)
        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
