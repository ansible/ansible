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
module: ovirt_disk
short_description: "Module to manage Virtual Machine and floating disks in oVirt/RHV"
version_added: "2.2"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage Virtual Machine and floating disks in oVirt/RHV."
options:
    id:
        description:
            - "ID of the disk to manage. Either C(id) or C(name) is required."
    name:
        description:
            - "Name of the disk to manage. Either C(id) or C(name)/C(alias) is required."
        aliases: ['alias']
    description:
        description:
            - "Description of the disk image to manage."
        version_added: "2.5"
    vm_name:
        description:
            - "Name of the Virtual Machine to manage. Either C(vm_id) or C(vm_name) is required if C(state) is I(attached) or I(detached)."
    vm_id:
        description:
            - "ID of the Virtual Machine to manage. Either C(vm_id) or C(vm_name) is required if C(state) is I(attached) or I(detached)."
    state:
        description:
            - "Should the Virtual Machine disk be present/absent/attached/detached/exported."
        choices: ['present', 'absent', 'attached', 'detached', 'exported']
        default: 'present'
    download_image_path:
        description:
            - "Path on a file system where disk should be downloaded."
            - "Note that you must have an valid oVirt/RHV engine CA in your system trust store
               or you must provide it in C(ca_file) parameter."
            - "Note that the disk is not downloaded when the file already exists,
               but you can forcibly download the disk when using C(force) I (true)."
        version_added: "2.3"
    upload_image_path:
        description:
            - "Path to disk image, which should be uploaded."
            - "Note if C(size) is not specified the size of the disk will be determined by the size of the specified image."
            - "Note that currently we support only compatibility version 0.10 of the qcow disk."
            - "Note that you must have an valid oVirt/RHV engine CA in your system trust store
               or you must provide it in C(ca_file) parameter."
            - "Note that there is no reliable way to achieve idempotency, so
               if you want to upload the disk even if the disk with C(id) or C(name) exists,
               then please use C(force) I(true). If you will use C(force) I(false), which
               is default, then the disk image won't be uploaded."
            - "Note that to upload iso the C(format) should be 'raw'"
        version_added: "2.3"
    size:
        description:
            - "Size of the disk. Size should be specified using IEC standard units.
               For example 10GiB, 1024MiB, etc."
            - "Size can be only increased, not decreased."
    interface:
        description:
            - "Driver of the storage interface."
            - "It's required parameter when creating the new disk."
        choices: ['virtio', 'ide', 'virtio_scsi']
    format:
        description:
            - Specify format of the disk.
            - Note that this option isn't idempotent as it's not currently possible to change format of the disk via API.
        default: 'cow'
        choices: ['raw', 'cow']
    content_type:
        description:
            - Specify if the disk is a data disk or ISO image or a one of a the Hosted Engine disk types
            - The Hosted Engine disk content types are available with Engine 4.3+ and Ansible 2.8
        choices: ['data', 'iso', 'hosted_engine', 'hosted_engine_sanlock', 'hosted_engine_metadata', 'hosted_engine_configuration']
        default: 'data'
        version_added: "2.8"
    sparse:
        required: False
        type: bool
        version_added: "2.5"
        description:
            - "I(True) if the disk should be sparse (also known as I(thin provision)).
              If the parameter is omitted, cow disks will be created as sparse and raw disks as I(preallocated)"
            - Note that this option isn't idempotent as it's not currently possible to change sparseness of the disk via API.
    storage_domain:
        description:
            - "Storage domain name where disk should be created."
    storage_domains:
        description:
            - "Storage domain names where disk should be copied."
            - "C(**IMPORTANT**)"
            - "There is no reliable way to achieve idempotency, so every time
               you specify this parameter the disks are copied, so please handle
               your playbook accordingly to not copy the disks all the time. This
               is valid only for VM and floating disks, template disks works
               as expected."
        version_added: "2.3"
    force:
        description:
            - "Please take a look at C(image_path) documentation to see the correct
               usage of this parameter."
        version_added: "2.3"
        type: bool
    profile:
        description:
            - "Disk profile name to be attached to disk. By default profile is chosen by oVirt/RHV engine."
    quota_id:
        description:
            - "Disk quota ID to be used for disk. By default quota is chosen by oVirt/RHV engine."
        version_added: "2.5"
    bootable:
        description:
            - "I(True) if the disk should be bootable. By default when disk is created it isn't bootable."
        type: bool
        default: 'no'
    shareable:
        description:
            - "I(True) if the disk should be shareable. By default when disk is created it isn't shareable."
        type: bool
    logical_unit:
        description:
            - "Dictionary which describes LUN to be directly attached to VM:"
        suboptions:
            address:
                description:
                    - Address of the storage server. Used by iSCSI.
            port:
                description:
                    - Port of the storage server. Used by iSCSI.
            target:
                description:
                    - iSCSI target.
            lun_id:
                description:
                    - LUN id.
            username:
                description:
                    - CHAP Username to be used to access storage server. Used by iSCSI.
            password:
                description:
                    - CHAP Password of the user to be used to access storage server. Used by iSCSI.
            storage_type:
                description:
                    - Storage type either I(fcp) or I(iscsi).
    sparsify:
        description:
            - "I(True) if the disk should be sparsified."
            - "Sparsification frees space in the disk image that is not used by
               its filesystem. As a result, the image will occupy less space on
               the storage."
            - "Note that this parameter isn't idempotent, as it's not possible
               to check if the disk should be or should not be sparsified."
        version_added: "2.4"
        type: bool
    openstack_volume_type:
        description:
            - "Name of the openstack volume type. This is valid when working
               with cinder."
        version_added: "2.4"
    image_provider:
        description:
            - "When C(state) is I(exported) disk is exported to given Glance image provider."
            - "C(**IMPORTANT**)"
            - "There is no reliable way to achieve idempotency, so every time
               you specify this parameter the disk is exported, so please handle
               your playbook accordingly to not export the disk all the time.
               This option is valid only for template disks."
        version_added: "2.4"
    host:
        description:
            - "When the hypervisor name is specified the newly created disk or
               an existing disk will refresh its information about the
               underlying storage( Disk size, Serial, Product ID, Vendor ID ...)
               The specified host will be used for gathering the storage
               related information. This option is only valid for passthrough
               disks. This option requires at least the logical_unit.id to be
               specified"
        version_added: "2.8"
    wipe_after_delete:
        description:
            - "If the disk's Wipe After Delete is enabled, then the disk is first wiped."
        type: bool
    activate:
        description:
            - I(True) if the disk should be activated.
            - When creating disk of virtual machine it is set to I(True).
        version_added: "2.8"
        type: bool
extends_documentation_fragment: ovirt
'''


EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create and attach new disk to VM
- ovirt_disk:
    name: myvm_disk
    vm_name: rhel7
    size: 10GiB
    format: cow
    interface: virtio
    storage_domain: data

# Attach logical unit to VM rhel7
- ovirt_disk:
    vm_name: rhel7
    logical_unit:
      target: iqn.2016-08-09.brq.str-01:omachace
      id: 1IET_000d0001
      address: 10.34.63.204
    interface: virtio

# Detach disk from VM
- ovirt_disk:
    state: detached
    name: myvm_disk
    vm_name: rhel7
    size: 10GiB
    format: cow
    interface: virtio

# Change Disk Name
- ovirt_disk:
    id: 00000000-0000-0000-0000-000000000000
    storage_domain: data
    name: "new_disk_name"
    vm_name: rhel7

# Upload local image to disk and attach it to vm:
# Since Ansible 2.3
- ovirt_disk:
    name: mydisk
    vm_name: myvm
    interface: virtio
    size: 10GiB
    format: cow
    image_path: /path/to/mydisk.qcow2
    storage_domain: data

# Download disk to local file system:
# Since Ansible 2.3
- ovirt_disk:
    id: 7de90f31-222c-436c-a1ca-7e655bd5b60c
    download_image_path: /home/user/mydisk.qcow2

# Export disk as image to Glance domain
# Since Ansible 2.4
- ovirt_disk:
    id: 7de90f31-222c-436c-a1ca-7e655bd5b60c
    image_provider: myglance
    state: exported

# Defining a specific quota while creating a disk image:
# Since Ansible 2.5
- ovirt_quotas_info:
    data_center: Default
    name: myquota
  register: quota
- ovirt_disk:
    name: mydisk
    size: 10GiB
    storage_domain: data
    description: somedescriptionhere
    quota_id: "{{ quota.ovirt_quotas[0]['id'] }}"

# Upload an ISO image
# Since Ansible 2.8
-  ovirt_disk:
     name: myiso
     upload_image_path: /path/to/iso/image
     storage_domain: data
     size: 4 GiB
     wait: true
     bootable: true
     format: raw
     content_type: iso

# Add fiber chanel disk
- name: Create disk
  ovirt_disk:
    name: fcp_disk
    host: my_host
    logical_unit:
        id: 3600a09803830447a4f244c4657597777
        storage_type: fcp
'''


RETURN = '''
id:
    description: "ID of the managed disk"
    returned: "On success if disk is found."
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
disk:
    description: "Dictionary of all the disk attributes. Disk attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/disk."
    returned: "On success if disk is found and C(vm_id) or C(vm_name) wasn't passed."
    type: dict

disk_attachment:
    description: "Dictionary of all the disk attachment attributes. Disk attachment attributes can be found
                  on your oVirt/RHV instance at following url:
                  http://ovirt.github.io/ovirt-engine-api-model/master/#types/disk_attachment."
    returned: "On success if disk is found and C(vm_id) or C(vm_name) was passed and VM was found."
    type: dict
'''

import os
import time
import traceback
import ssl

from ansible.module_utils.six.moves.http_client import HTTPSConnection, IncompleteRead
from ansible.module_utils.six.moves.urllib.parse import urlparse
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
    convert_to_bytes,
    equal,
    follow_link,
    get_id_by_name,
    ovirt_full_argument_spec,
    search_by_name,
    wait,
)


def create_transfer_connection(module, transfer, context, connect_timeout=10, read_timeout=60):
    url = urlparse(transfer.transfer_url)
    connection = HTTPSConnection(
        url.netloc, context=context, timeout=connect_timeout)
    try:
        connection.connect()
    except Exception as e:
        # Typically ConnectionRefusedError or socket.gaierror.
        module.warn("Cannot connect to %s, trying %s: %s" % (transfer.transfer_url, transfer.proxy_url, e))

        url = urlparse(transfer.proxy_url)
        connection = HTTPSConnection(
            url.netloc, context=context, timeout=connect_timeout)
        connection.connect()

    connection.sock.settimeout(read_timeout)
    return connection, url


def _search_by_lun(disks_service, lun_id):
    """
    Find disk by LUN ID.
    """
    res = [
        disk for disk in disks_service.list(search='disk_type=lun') if (
            disk.lun_storage.id == lun_id
        )
    ]
    return res[0] if res else None


def transfer(connection, module, direction, transfer_func):
    transfers_service = connection.system_service().image_transfers_service()
    transfer = transfers_service.add(
        otypes.ImageTransfer(
            image=otypes.Image(
                id=module.params['id'],
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

        context = ssl.create_default_context()
        auth = module.params['auth']
        if auth.get('insecure'):
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        elif auth.get('ca_file'):
            context.load_verify_locations(cafile=auth.get('ca_file'))

        transfer_connection, transfer_url = create_transfer_connection(module, transfer, context)
        transfer_func(
            transfer_service,
            transfer_connection,
            transfer_url,
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
        if not module.params.get('logical_unit'):
            disks_service = connection.system_service().disks_service()
            wait(
                service=disks_service.service(module.params['id']),
                condition=lambda d: d.status == otypes.DiskStatus.OK,
                wait=module.params['wait'],
                timeout=module.params['timeout'],
            )


def download_disk_image(connection, module):
    def _transfer(transfer_service, transfer_connection, transfer_url):
        BUF_SIZE = 128 * 1024
        transfer_connection.request('GET', transfer_url.path)
        r = transfer_connection.getresponse()
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


def upload_disk_image(connection, module):
    def _transfer(transfer_service, transfer_connection, transfer_url):
        BUF_SIZE = 128 * 1024
        path = module.params['upload_image_path']

        image_size = os.path.getsize(path)
        transfer_connection.putrequest("PUT", transfer_url.path)
        transfer_connection.putheader('Content-Length', "%d" % (image_size,))
        transfer_connection.endheaders()
        with open(path, "rb") as disk:
            pos = 0
            while pos < image_size:
                to_read = min(image_size - pos, BUF_SIZE)
                chunk = disk.read(to_read)
                if not chunk:
                    transfer_service.pause()
                    raise RuntimeError("Unexpected end of file at pos=%d" % pos)
                transfer_connection.send(chunk)
                pos += len(chunk)

    return transfer(
        connection,
        module,
        otypes.ImageTransferDirection.UPLOAD,
        transfer_func=_transfer,
    )


class DisksModule(BaseModule):

    def build_entity(self):
        hosts_service = self._connection.system_service().hosts_service()
        logical_unit = self._module.params.get('logical_unit')
        size = convert_to_bytes(self._module.params.get('size'))
        if not size and self._module.params.get('upload_image_path'):
            size = os.path.getsize(self._module.params.get('upload_image_path'))
        disk = otypes.Disk(
            id=self._module.params.get('id'),
            name=self._module.params.get('name'),
            description=self._module.params.get('description'),
            format=otypes.DiskFormat(
                self._module.params.get('format')
            ) if self._module.params.get('format') else None,
            content_type=otypes.DiskContentType(
                self._module.params.get('content_type')
            ) if self._module.params.get('content_type') else None,
            sparse=self._module.params.get(
                'sparse'
            ) if self._module.params.get(
                'sparse'
            ) is not None else self._module.params.get('format') != 'raw',
            openstack_volume_type=otypes.OpenStackVolumeType(
                name=self.param('openstack_volume_type')
            ) if self.param('openstack_volume_type') else None,
            provisioned_size=size,
            storage_domains=[
                otypes.StorageDomain(
                    name=self._module.params.get('storage_domain'),
                ),
            ],
            quota=otypes.Quota(id=self._module.params.get('quota_id')) if self.param('quota_id') else None,
            shareable=self._module.params.get('shareable'),
            wipe_after_delete=self.param('wipe_after_delete'),
            lun_storage=otypes.HostStorage(
                host=otypes.Host(
                    id=get_id_by_name(hosts_service, self._module.params.get('host'))
                ) if self.param('host') else None,
                type=otypes.StorageType(
                    logical_unit.get('storage_type', 'iscsi')
                ),
                logical_units=[
                    otypes.LogicalUnit(
                        address=logical_unit.get('address'),
                        port=logical_unit.get('port', 3260),
                        target=logical_unit.get('target'),
                        id=logical_unit.get('id'),
                        username=logical_unit.get('username'),
                        password=logical_unit.get('password'),
                    )
                ],
            ) if logical_unit else None,
        )
        if hasattr(disk, 'initial_size') and self._module.params['upload_image_path']:
            disk.initial_size = size

        return disk

    def update_storage_domains(self, disk_id):
        changed = False
        disk_service = self._service.service(disk_id)
        disk = disk_service.get()
        sds_service = self._connection.system_service().storage_domains_service()

        # We don't support move&copy for non file based storages:
        if disk.storage_type != otypes.DiskStorageType.IMAGE:
            return changed

        # Initiate move:
        if self._module.params['storage_domain']:
            new_disk_storage_id = get_id_by_name(sds_service, self._module.params['storage_domain'])
            if new_disk_storage_id in [sd.id for sd in disk.storage_domains]:
                return changed
            changed = self.action(
                action='move',
                entity=disk,
                action_condition=lambda d: new_disk_storage_id != d.storage_domains[0].id,
                wait_condition=lambda d: d.status == otypes.DiskStatus.OK,
                storage_domain=otypes.StorageDomain(
                    id=new_disk_storage_id,
                ),
                post_action=lambda _: time.sleep(self._module.params['poll_interval']),
            )['changed']

        if self._module.params['storage_domains']:
            for sd in self._module.params['storage_domains']:
                new_disk_storage = search_by_name(sds_service, sd)
                changed = changed or self.action(
                    action='copy',
                    entity=disk,
                    action_condition=(
                        lambda disk: new_disk_storage.id not in [sd.id for sd in disk.storage_domains]
                    ),
                    wait_condition=lambda disk: disk.status == otypes.DiskStatus.OK,
                    storage_domain=otypes.StorageDomain(
                        id=new_disk_storage.id,
                    ),
                )['changed']

        return changed

    def _update_check(self, entity):
        return (
            equal(self._module.params.get('name'), entity.name) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self.param('quota_id'), getattr(entity.quota, 'id', None)) and
            equal(convert_to_bytes(self._module.params.get('size')), entity.provisioned_size) and
            equal(self._module.params.get('shareable'), entity.shareable) and
            equal(self.param('wipe_after_delete'), entity.wipe_after_delete)
        )


class DiskAttachmentsModule(DisksModule):

    def build_entity(self):
        return otypes.DiskAttachment(
            disk=super(DiskAttachmentsModule, self).build_entity(),
            interface=otypes.DiskInterface(
                self._module.params.get('interface')
            ) if self._module.params.get('interface') else None,
            bootable=self._module.params.get('bootable'),
            active=self.param('activate'),
        )

    def update_check(self, entity):
        return (
            super(DiskAttachmentsModule, self)._update_check(follow_link(self._connection, entity.disk)) and
            equal(self._module.params.get('interface'), str(entity.interface)) and
            equal(self._module.params.get('bootable'), entity.bootable) and
            equal(self.param('activate'), entity.active)
        )


def searchable_attributes(module):
    """
    Return all searchable disk attributes passed to module.
    """
    attributes = {
        'name': module.params.get('name'),
        'Storage.name': module.params.get('storage_domain'),
        'vm_names': module.params.get('vm_name'),
    }
    return dict((k, v) for k, v in attributes.items() if v is not None)


def get_vm_service(connection, module):
    if module.params.get('vm_id') is not None or module.params.get('vm_name') is not None and module.params['state'] != 'absent':
        vms_service = connection.system_service().vms_service()

        # If `vm_id` isn't specified, find VM by name:
        vm_id = module.params['vm_id']
        if vm_id is None:
            vm_id = get_id_by_name(vms_service, module.params['vm_name'])

        if vm_id is None:
            module.fail_json(
                msg="VM don't exists, please create it first."
            )

        return vms_service.vm_service(vm_id)


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent', 'attached', 'detached', 'exported'],
            default='present'
        ),
        id=dict(default=None),
        name=dict(default=None, aliases=['alias']),
        description=dict(default=None),
        vm_name=dict(default=None),
        vm_id=dict(default=None),
        size=dict(default=None),
        interface=dict(default=None,),
        storage_domain=dict(default=None),
        storage_domains=dict(default=None, type='list'),
        profile=dict(default=None),
        quota_id=dict(default=None),
        format=dict(default='cow', choices=['raw', 'cow']),
        content_type=dict(
            default='data',
            choices=['data', 'iso', 'hosted_engine', 'hosted_engine_sanlock', 'hosted_engine_metadata', 'hosted_engine_configuration']
        ),
        sparse=dict(default=None, type='bool'),
        bootable=dict(default=None, type='bool'),
        shareable=dict(default=None, type='bool'),
        logical_unit=dict(default=None, type='dict'),
        download_image_path=dict(default=None),
        upload_image_path=dict(default=None, aliases=['image_path']),
        force=dict(default=False, type='bool'),
        sparsify=dict(default=None, type='bool'),
        openstack_volume_type=dict(default=None),
        image_provider=dict(default=None),
        host=dict(default=None),
        wipe_after_delete=dict(type='bool', default=None),
        activate=dict(default=None, type='bool'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    lun = module.params.get('logical_unit')
    host = module.params['host']
    # Fail when host is specified with the LUN id. Lun id is needed to identify
    # an existing disk if already available inthe environment.
    if (host and lun is None) or (host and lun.get("id") is None):
        module.fail_json(
            msg="Can not use parameter host ({0!s}) without "
            "specifying the logical_unit id".format(host)
        )

    check_sdk(module)
    check_params(module)

    try:
        disk = None
        state = module.params['state']
        auth = module.params.get('auth')
        connection = create_connection(auth)
        disks_service = connection.system_service().disks_service()
        disks_module = DisksModule(
            connection=connection,
            module=module,
            service=disks_service,
        )

        force_create = False
        vm_service = get_vm_service(connection, module)
        if lun:
            disk = _search_by_lun(disks_service, lun.get('id'))
        else:
            disk = disks_module.search_entity(search_params=searchable_attributes(module))
            if vm_service and disk:
                # If the VM don't exist in VMs disks, but still it's found it means it was found
                # for template with same name as VM, so we should force create the VM disk.
                force_create = disk.id not in [a.disk.id for a in vm_service.disk_attachments_service().list() if a.disk]

        ret = None
        # First take care of creating the VM, if needed:
        if state in ('present', 'detached', 'attached'):
            # Always activate disk when its being created
            if vm_service is not None and disk is None:
                module.params['activate'] = module.params['activate'] is None or module.params['activate']
            ret = disks_module.create(
                entity=disk if not force_create else None,
                result_state=otypes.DiskStatus.OK if lun is None else None,
                fail_condition=lambda d: d.status == otypes.DiskStatus.ILLEGAL if lun is None else False,
                force_create=force_create,
                _wait=True if module.params['upload_image_path'] else module.params['wait'],
            )
            is_new_disk = ret['changed']
            ret['changed'] = ret['changed'] or disks_module.update_storage_domains(ret['id'])
            # We need to pass ID to the module, so in case we want detach/attach disk
            # we have this ID specified to attach/detach method:
            module.params['id'] = ret['id']

            # Upload disk image in case it's new disk or force parameter is passed:
            if module.params['upload_image_path'] and (is_new_disk or module.params['force']):
                if module.params['format'] == 'cow' and module.params['content_type'] == 'iso':
                    module.warn("To upload an ISO image 'format' parameter needs to be set to 'raw'.")
                uploaded = upload_disk_image(connection, module)
                ret['changed'] = ret['changed'] or uploaded
            # Download disk image in case it's file don't exist or force parameter is passed:
            if (
                module.params['download_image_path'] and (not os.path.isfile(module.params['download_image_path']) or module.params['force'])
            ):
                downloaded = download_disk_image(connection, module)
                ret['changed'] = ret['changed'] or downloaded

            # Disk sparsify, only if disk is of image type:
            if not module.check_mode:
                disk = disks_service.disk_service(module.params['id']).get()
                if disk.storage_type == otypes.DiskStorageType.IMAGE:
                    ret = disks_module.action(
                        action='sparsify',
                        action_condition=lambda d: module.params['sparsify'],
                        wait_condition=lambda d: d.status == otypes.DiskStatus.OK,
                    )

        # Export disk as image to glance domain
        elif state == 'exported':
            disk = disks_module.search_entity()
            if disk is None:
                module.fail_json(
                    msg="Can not export given disk '%s', it doesn't exist" %
                        module.params.get('name') or module.params.get('id')
                )
            if disk.storage_type == otypes.DiskStorageType.IMAGE:
                ret = disks_module.action(
                    action='export',
                    action_condition=lambda d: module.params['image_provider'],
                    wait_condition=lambda d: d.status == otypes.DiskStatus.OK,
                    storage_domain=otypes.StorageDomain(name=module.params['image_provider']),
                )
        elif state == 'absent':
            ret = disks_module.remove()

        # If VM was passed attach/detach disks to/from the VM:
        if vm_service:
            disk_attachments_service = vm_service.disk_attachments_service()
            disk_attachments_module = DiskAttachmentsModule(
                connection=connection,
                module=module,
                service=disk_attachments_service,
                changed=ret['changed'] if ret else False,
            )

            if state == 'present' or state == 'attached':
                ret = disk_attachments_module.create()
                if lun is None:
                    wait(
                        service=disk_attachments_service.service(ret['id']),
                        condition=lambda d: follow_link(connection, d.disk).status == otypes.DiskStatus.OK,
                        wait=module.params['wait'],
                        timeout=module.params['timeout'],
                    )
            elif state == 'detached':
                ret = disk_attachments_module.remove()

        # When the host parameter is specified and the disk is not being
        # removed, refresh the information about the LUN.
        if state != 'absent' and host:
            hosts_service = connection.system_service().hosts_service()
            host_id = get_id_by_name(hosts_service, host)
            disks_service.disk_service(disk.id).refresh_lun(otypes.Host(id=host_id))

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
