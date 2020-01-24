#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Diane Wang <dianew@vmware.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vmware_export_ovf
short_description: Exports a VMware virtual machine to an OVF file, device files and a manifest file
description: >
   This module can be used to export a VMware virtual machine to OVF template from vCenter server or ESXi host.
version_added: '2.8'
author:
- Diane Wang (@Tomorrow9) <dianew@vmware.com>
requirements:
- python >= 2.6
- PyVmomi
notes: []
options:
  name:
    description:
    - Name of the virtual machine to export.
    - This is a required parameter, if parameter C(uuid) or C(moid) is not supplied.
    type: str
  uuid:
    description:
    - Uuid of the virtual machine to export.
    - This is a required parameter, if parameter C(name) or C(moid) is not supplied.
    type: str
  moid:
    description:
    - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
    - This is required if C(name) or C(uuid) is not supplied.
    version_added: '2.9'
    type: str
  datacenter:
    default: ha-datacenter
    description:
    - Datacenter name of the virtual machine to export.
    - This parameter is case sensitive.
    type: str
  folder:
    description:
    - Destination folder, absolute path to find the specified guest.
    - The folder should include the datacenter. ESX's datacenter is ha-datacenter.
    - This parameter is case sensitive.
    - 'If multiple machines are found with same name, this parameter is used to identify
       uniqueness of the virtual machine. version_added 2.5'
    - 'Examples:'
    - '   folder: /ha-datacenter/vm'
    - '   folder: ha-datacenter/vm'
    - '   folder: /datacenter1/vm'
    - '   folder: datacenter1/vm'
    - '   folder: /datacenter1/vm/folder1'
    - '   folder: datacenter1/vm/folder1'
    - '   folder: /folder1/datacenter1/vm'
    - '   folder: folder1/datacenter1/vm'
    - '   folder: /folder1/datacenter1/vm/folder2'
    type: str
  export_dir:
    description:
    - Absolute path to place the exported files on the server running this task, must have write permission.
    - If folder not exist will create it, also create a folder under this path named with VM name.
    required: yes
    type: path
  export_with_images:
    default: false
    description:
    - Export an ISO image of the media mounted on the CD/DVD Drive within the virtual machine.
    type: bool
  download_timeout:
    description:
    - The user defined timeout in minute of exporting file.
    - If the vmdk file is too large to export in 10 minutes, specify the value larger than 10, the maximum value is 60.
    default: 10
    type: int
    version_added: '2.9'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- vmware_export_ovf:
    validate_certs: false
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    name: '{{ vm_name }}'
    export_with_images: true
    export_dir: /path/to/ovf_template/
  delegate_to: localhost
'''

RETURN = r'''
instance:
    description: list of the exported files, if exported from vCenter server, device file is not named with vm name
    returned: always
    type: dict
    sample: None
'''

import os
import hashlib
from time import sleep
from threading import Thread
from ansible.module_utils.urls import open_url
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
try:
    from pyVmomi import vim
    from pyVim import connect
except ImportError:
    pass


class LeaseProgressUpdater(Thread):
    def __init__(self, http_nfc_lease, update_interval):
        Thread.__init__(self)
        self._running = True
        self.httpNfcLease = http_nfc_lease
        self.updateInterval = update_interval
        self.progressPercent = 0

    def set_progress_percent(self, progress_percent):
        self.progressPercent = progress_percent

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            try:
                if self.httpNfcLease.state == vim.HttpNfcLease.State.done:
                    return
                self.httpNfcLease.HttpNfcLeaseProgress(self.progressPercent)
                sleep_sec = 0
                while True:
                    if self.httpNfcLease.state == vim.HttpNfcLease.State.done or self.httpNfcLease.state == vim.HttpNfcLease.State.error:
                        return
                    sleep_sec += 1
                    sleep(1)
                    if sleep_sec == self.updateInterval:
                        break
            except Exception:
                return


class VMwareExportVmOvf(PyVmomi):
    def __init__(self, module):
        super(VMwareExportVmOvf, self).__init__(module)
        self.mf_file = ''
        self.ovf_dir = ''
        # set read device content chunk size to 2 MB
        self.chunk_size = 2 * 2 ** 20
        # set lease progress update interval to 15 seconds
        self.lease_interval = 15
        self.facts = {'device_files': []}
        self.download_timeout = 10

    def create_export_dir(self, vm_obj):
        self.ovf_dir = os.path.join(self.params['export_dir'], vm_obj.name)
        if not os.path.exists(self.ovf_dir):
            try:
                os.makedirs(self.ovf_dir)
            except OSError as err:
                self.module.fail_json(msg='Exception caught when create folder %s, with error %s'
                                          % (self.ovf_dir, to_text(err)))
        self.mf_file = os.path.join(self.ovf_dir, vm_obj.name + '.mf')

    def download_device_files(self, headers, temp_target_disk, device_url, lease_updater, total_bytes_written,
                              total_bytes_to_write):
        mf_content = 'SHA256(' + os.path.basename(temp_target_disk) + ')= '
        sha256_hash = hashlib.sha256()
        response = None

        with open(self.mf_file, 'a') as mf_handle:
            with open(temp_target_disk, 'wb') as handle:
                try:
                    response = open_url(device_url, headers=headers, validate_certs=False, timeout=self.download_timeout)
                except Exception as err:
                    lease_updater.httpNfcLease.HttpNfcLeaseAbort()
                    lease_updater.stop()
                    self.module.fail_json(msg='Exception caught when getting %s, %s' % (device_url, to_text(err)))
                if not response:
                    lease_updater.httpNfcLease.HttpNfcLeaseAbort()
                    lease_updater.stop()
                    self.module.fail_json(msg='Getting %s failed' % device_url)
                if response.getcode() >= 400:
                    lease_updater.httpNfcLease.HttpNfcLeaseAbort()
                    lease_updater.stop()
                    self.module.fail_json(msg='Getting %s return code %d' % (device_url, response.getcode()))
                current_bytes_written = 0
                block = response.read(self.chunk_size)
                while block:
                    handle.write(block)
                    sha256_hash.update(block)
                    handle.flush()
                    os.fsync(handle.fileno())
                    current_bytes_written += len(block)
                    block = response.read(self.chunk_size)
                written_percent = ((current_bytes_written + total_bytes_written) * 100) / total_bytes_to_write
                lease_updater.progressPercent = int(written_percent)
            mf_handle.write(mf_content + sha256_hash.hexdigest() + '\n')
        self.facts['device_files'].append(temp_target_disk)
        return current_bytes_written

    def export_to_ovf_files(self, vm_obj):
        self.create_export_dir(vm_obj=vm_obj)
        export_with_iso = False
        if 'export_with_images' in self.params and self.params['export_with_images']:
            export_with_iso = True
        if 60 > self.params['download_timeout'] > 10:
            self.download_timeout = self.params['download_timeout']

        ovf_files = []
        # get http nfc lease firstly
        http_nfc_lease = vm_obj.ExportVm()
        # create a thread to track file download progress
        lease_updater = LeaseProgressUpdater(http_nfc_lease, self.lease_interval)
        total_bytes_written = 0
        # total storage space occupied by the virtual machine across all datastores
        total_bytes_to_write = vm_obj.summary.storage.unshared
        # new deployed VM with no OS installed
        if total_bytes_to_write == 0:
            total_bytes_to_write = vm_obj.summary.storage.committed
            if total_bytes_to_write == 0:
                http_nfc_lease.HttpNfcLeaseAbort()
                self.module.fail_json(msg='Total storage space occupied by the VM is 0.')
        headers = {'Accept': 'application/x-vnd.vmware-streamVmdk'}
        cookies = connect.GetStub().cookie
        if cookies:
            headers['Cookie'] = cookies
        lease_updater.start()
        try:
            while True:
                if http_nfc_lease.state == vim.HttpNfcLease.State.ready:
                    for deviceUrl in http_nfc_lease.info.deviceUrl:
                        file_download = False
                        if deviceUrl.targetId and deviceUrl.disk:
                            file_download = True
                        elif deviceUrl.url.split('/')[-1].split('.')[-1] == 'iso':
                            if export_with_iso:
                                file_download = True
                        elif deviceUrl.url.split('/')[-1].split('.')[-1] == 'nvram':
                            if self.host_version_at_least(version=(6, 7, 0), vm_obj=vm_obj):
                                file_download = True
                        else:
                            continue
                        device_file_name = deviceUrl.url.split('/')[-1]
                        # device file named disk-0.iso, disk-1.vmdk, disk-2.vmdk, replace 'disk' with vm name
                        if device_file_name.split('.')[0][0:5] == "disk-":
                            device_file_name = device_file_name.replace('disk', vm_obj.name)
                        temp_target_disk = os.path.join(self.ovf_dir, device_file_name)
                        device_url = deviceUrl.url
                        # if export from ESXi host, replace * with hostname in url
                        # e.g., https://*/ha-nfc/5289bf27-da99-7c0e-3978-8853555deb8c/disk-1.vmdk
                        if '*' in device_url:
                            device_url = device_url.replace('*', self.params['hostname'])
                        if file_download:
                            current_bytes_written = self.download_device_files(headers=headers,
                                                                               temp_target_disk=temp_target_disk,
                                                                               device_url=device_url,
                                                                               lease_updater=lease_updater,
                                                                               total_bytes_written=total_bytes_written,
                                                                               total_bytes_to_write=total_bytes_to_write)
                            total_bytes_written += current_bytes_written
                            ovf_file = vim.OvfManager.OvfFile()
                            ovf_file.deviceId = deviceUrl.key
                            ovf_file.path = device_file_name
                            ovf_file.size = current_bytes_written
                            ovf_files.append(ovf_file)
                    break
                elif http_nfc_lease.state == vim.HttpNfcLease.State.initializing:
                    sleep(2)
                    continue
                elif http_nfc_lease.state == vim.HttpNfcLease.State.error:
                    lease_updater.stop()
                    self.module.fail_json(msg='Get HTTP NFC lease error %s.' % http_nfc_lease.state.error[0].fault)

            # generate ovf file
            ovf_manager = self.content.ovfManager
            ovf_descriptor_name = vm_obj.name
            ovf_parameters = vim.OvfManager.CreateDescriptorParams()
            ovf_parameters.name = ovf_descriptor_name
            ovf_parameters.ovfFiles = ovf_files
            vm_descriptor_result = ovf_manager.CreateDescriptor(obj=vm_obj, cdp=ovf_parameters)
            if vm_descriptor_result.error:
                http_nfc_lease.HttpNfcLeaseAbort()
                lease_updater.stop()
                self.module.fail_json(msg='Create VM descriptor file error %s.' % vm_descriptor_result.error)
            else:
                vm_descriptor = vm_descriptor_result.ovfDescriptor
                ovf_descriptor_path = os.path.join(self.ovf_dir, ovf_descriptor_name + '.ovf')
                sha256_hash = hashlib.sha256()
                with open(self.mf_file, 'a') as mf_handle:
                    with open(ovf_descriptor_path, 'w') as handle:
                        handle.write(vm_descriptor)
                        sha256_hash.update(to_bytes(vm_descriptor))
                    mf_handle.write('SHA256(' + os.path.basename(ovf_descriptor_path) + ')= ' + sha256_hash.hexdigest() + '\n')
                http_nfc_lease.HttpNfcLeaseProgress(100)
                # self.facts = http_nfc_lease.HttpNfcLeaseGetManifest()
                http_nfc_lease.HttpNfcLeaseComplete()
                lease_updater.stop()
                self.facts.update({'manifest': self.mf_file, 'ovf_file': ovf_descriptor_path})
        except Exception as err:
            kwargs = {
                'changed': False,
                'failed': True,
                'msg': "get exception: %s" % to_text(err),
            }
            http_nfc_lease.HttpNfcLeaseAbort()
            lease_updater.stop()
            return kwargs
        return {'changed': True, 'failed': False, 'instance': self.facts}


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str', default='ha-datacenter'),
        export_dir=dict(type='path', required=True),
        export_with_images=dict(type='bool', default=False),
        download_timeout=dict(type='int', default=10),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=[
                               ['name', 'uuid', 'moid'],
                           ],
                           )
    pyv = VMwareExportVmOvf(module)
    vm = pyv.get_vm()
    if vm:
        vm_facts = pyv.gather_facts(vm)
        vm_power_state = vm_facts['hw_power_status'].lower()
        if vm_power_state != 'poweredoff':
            module.fail_json(msg='VM state should be poweredoff to export')
        results = pyv.export_to_ovf_files(vm_obj=vm)
        module.exit_json(**results)
    else:
        module.fail_json(msg='The specified virtual machine not found')


if __name__ == '__main__':
    main()
