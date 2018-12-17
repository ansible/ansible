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
module: ovirt_snapshot
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
    disk_id:
        description:
            - "Disk id which you want to upload or download"
            - "To get disk, you need to define disk_id or disk_name"
        version_added: "2.8"
    disk_name:
        description:
            - "Disk name which you want to upload or download"
        version_added: "2.8"
    download_image_path:
        description:
            - "Path on a file system where snapshot should be downloaded."
            - "Note that you must have an valid oVirt/RHV engine CA in your system trust store
               or you must provide it in C(ca_file) parameter."
            - "Note that the snapshot is not downloaded when the file already exists,
               but you can forcibly download the snapshot when using C(force) I (true)."
        version_added: "2.8"
    upload_image_path:
        description:
            - "Path to disk image, which should be uploaded."
        version_added: "2.8"
    use_memory:
        description:
            - "If I(true) and C(state) is I(present) save memory of the Virtual
               Machine if it's running."
            - "If I(true) and C(state) is I(restore) restore memory of the
               Virtual Machine."
            - "Note that Virtual Machine will be paused while saving the memory."
        aliases:
            - "restore_memory"
            - "save_memory"
        type: bool
    keep_days_old:
        description:
            - "Number of days after which should snapshot be deleted."
            - "It will check all snapshots of virtual machine and delete them, if they are older."
        version_added: "2.8"
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
- ovirt_snapshot:
    vm_name: rhel7
    description: MySnapshot
  register: snapshot

# Create snapshot and save memory:
- ovirt_snapshot:
    vm_name: rhel7
    description: SnapWithMem
    use_memory: true
  register: snapshot

# Restore snapshot:
- ovirt_snapshot:
    state: restore
    vm_name: rhel7
    snapshot_id: "{{ snapshot.id }}"

# Remove snapshot:
- ovirt_snapshot:
    state: absent
    vm_name: rhel7
    snapshot_id: "{{ snapshot.id }}"

# Upload local image to disk and attach it to vm:
# Since Ansible 2.8
- ovirt_snapshot:
    name: mydisk
    vm_name: myvm
    upload_image_path: /path/to/mydisk.qcow2

# Download snapshot to local file system:
# Since Ansible 2.8
- ovirt_snapshot:
    snapshot_id: 7de90f31-222c-436c-a1ca-7e655bd5b60c
    disk_name: DiskName
    vm_name: myvm
    download_image_path: /home/user/mysnaphost.qcow2

# Delete all snapshots older than 2 days
- ovirt_snapshot:
    vm_name: test
    keep_days_old: 2
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
snapshots:
    description: List of deleted snapshots when keep_days_old is defined and snapshot is older than the input days
    returned: On success returns deleted snapshots
    type: list
'''


import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass


import os
import ssl
import time

from ansible.module_utils.six.moves.http_client import HTTPSConnection, IncompleteRead
from ansible.module_utils.six.moves.urllib.parse import urlparse

from datetime import datetime
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    get_entity,
    ovirt_full_argument_spec,
    search_by_name,
    wait,
    get_id_by_name
)


def transfer(connection, module, direction, transfer_func):
    transfers_service = connection.system_service().image_transfers_service()
    transfer = transfers_service.add(
        otypes.ImageTransfer(
            image=otypes.Image(
                id=module.params['disk_id'],
            ),
            direction=direction,
        )
    )
    transfer_service = transfers_service.image_transfer_service(transfer.id)

    try:
        # After adding a new transfer for the disk, the transfer's status will be INITIALIZING.
        # Wait until the init phase is over. The actual transfer can start when its status is "Transferring".
        while transfer.phase == otypes.ImageTransferPhase.INITIALIZING:
            time.sleep(module.params['poll_interval'])
            transfer = transfer_service.get()

        proxy_url = urlparse(transfer.proxy_url)
        context = ssl.create_default_context()
        auth = module.params['auth']
        if auth.get('insecure'):
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        elif auth.get('ca_file'):
            context.load_verify_locations(cafile=auth.get('ca_file'))

        proxy_connection = HTTPSConnection(
            proxy_url.hostname,
            proxy_url.port,
            context=context,
        )

        transfer_func(
            transfer_service,
            proxy_connection,
            proxy_url,
            transfer.signed_ticket
        )
        return True
    finally:
        transfer_service.finalize()
        while transfer.phase in [
            otypes.ImageTransferPhase.TRANSFERRING,
            otypes.ImageTransferPhase.FINALIZING_SUCCESS,
        ]:
            time.sleep(module.params['poll_interval'])
            transfer = transfer_service.get()
        if transfer.phase in [
            otypes.ImageTransferPhase.UNKNOWN,
            otypes.ImageTransferPhase.FINISHED_FAILURE,
            otypes.ImageTransferPhase.FINALIZING_FAILURE,
            otypes.ImageTransferPhase.CANCELLED,
        ]:
            raise Exception(
                "Error occurred while uploading image. The transfer is in %s" % transfer.phase
            )
        if module.params.get('logical_unit'):
            disks_service = connection.system_service().disks_service()
            wait(
                service=disks_service.service(module.params['id']),
                condition=lambda d: d.status == otypes.DiskStatus.OK,
                wait=module.params['wait'],
                timeout=module.params['timeout'],
            )


def upload_disk_image(connection, module):
    def _transfer(transfer_service, proxy_connection, proxy_url, transfer_ticket):
        BUF_SIZE = 128 * 1024
        path = module.params['upload_image_path']

        image_size = os.path.getsize(path)
        proxy_connection.putrequest("PUT", proxy_url.path)
        proxy_connection.putheader('Content-Length', "%d" % (image_size,))
        proxy_connection.endheaders()
        with open(path, "rb") as disk:
            pos = 0
            while pos < image_size:
                to_read = min(image_size - pos, BUF_SIZE)
                chunk = disk.read(to_read)
                if not chunk:
                    transfer_service.pause()
                    raise RuntimeError("Unexpected end of file at pos=%d" % pos)
                proxy_connection.send(chunk)
                pos += len(chunk)

    return transfer(
        connection,
        module,
        otypes.ImageTransferDirection.UPLOAD,
        transfer_func=_transfer,
    )


def download_disk_image(connection, module):
    def _transfer(transfer_service, proxy_connection, proxy_url, transfer_ticket):
        BUF_SIZE = 128 * 1024
        transfer_headers = {
            'Authorization': transfer_ticket,
        }
        proxy_connection.request(
            'GET',
            proxy_url.path,
            headers=transfer_headers,
        )
        r = proxy_connection.getresponse()
        path = module.params["download_image_path"]
        image_size = int(r.getheader('Content-Length'))
        with open(path, "wb") as mydisk:
            pos = 0
            while pos < image_size:
                to_read = min(image_size - pos, BUF_SIZE)
                chunk = r.read(to_read)
                if not chunk:
                    raise RuntimeError("Socket disconnected")
                mydisk.write(chunk)
                pos += len(chunk)

    return transfer(
        connection,
        module,
        otypes.ImageTransferDirection.DOWNLOAD,
        transfer_func=_transfer,
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


def remove_snapshot(module, vm_service, snapshots_service, snapshot_id=None):
    changed = False
    if not snapshot_id:
        snapshot_id = module.params['snapshot_id']
    snapshot = get_entity(
        snapshots_service.snapshot_service(snapshot_id)
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


def get_snapshot_disk_id(module, snapshots_service):
    snapshot_service = snapshots_service.snapshot_service(module.params.get('snapshot_id'))
    snapshot_disks_service = snapshot_service.disks_service()

    disk_id = ''
    if module.params.get('disk_id'):
        disk_id = module.params.get('disk_id')
    elif module.params.get('disk_name'):
        disk_id = get_id_by_name(snapshot_disks_service, module.params.get('disk_name'))

    return disk_id


def remove_old_snapshosts(module, vm_service, snapshots_service):
    deleted_snapshots = []
    changed = False
    date_now = datetime.now()
    for snapshot in snapshots_service.list():
        if snapshot.vm is not None and snapshot.vm.name == module.params.get('vm_name'):
            diff = date_now - snapshot.date.replace(tzinfo=None)
            if diff.days >= module.params.get('keep_days_old'):
                snapshot = remove_snapshot(module, vm_service, snapshots_service, snapshot.id).get('snapshot')
                deleted_snapshots.append(snapshot)
                changed = True
    return dict(snapshots=deleted_snapshots, changed=changed)


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['restore', 'present', 'absent'],
            default='present',
        ),
        vm_name=dict(required=True),
        snapshot_id=dict(default=None),
        disk_id=dict(default=None),
        disk_name=dict(default=None),
        description=dict(default=None),
        download_image_path=dict(default=None),
        upload_image_path=dict(default=None),
        keep_days_old=dict(default=None, type='int'),
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
    ret = {}
    vm_name = module.params.get('vm_name')
    auth = module.params['auth']
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
            if module.params.get('disk_id') or module.params.get('disk_name'):
                module.params['disk_id'] = get_snapshot_disk_id(module, snapshots_service)
                if module.params['upload_image_path']:
                    ret['changed'] = upload_disk_image(connection, module)
                if module.params['download_image_path']:
                    ret['changed'] = download_disk_image(connection, module)
            if module.params.get('keep_days_old') is not None:
                ret = remove_old_snapshosts(module, vm_service, snapshots_service)
            else:
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
