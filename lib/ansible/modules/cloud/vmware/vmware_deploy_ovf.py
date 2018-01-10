#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
author: 'Matt Martz (@sivel)'
short_description: 'Deploys a VMware VM from an OVF or OVA file'
description:
- 'Deploys a VMware VM from an OVF or OVA file'
module: vmware_deploy_ovf
notes: []
options:
    datacenter:
        default: ha-datacenter
        description:
        - 'Datacenter to deploy to'
    datastore:
        default: datastore1
        description:
        - 'Datastore to deploy to'
    disk_provisioning:
        choices:
        - flat
        - eagerZeroedThick
        - monolithicSparse
        - twoGbMaxExtentSparse
        - twoGbMaxExtentFlat
        - thin
        - sparse
        - thick
        - seSparse
        - monolithicFlat
        default: thin
        description:
        - 'Disk provisioning type'
    name:
        description:
        - Name of the VM to work with.
        - VM names in vCenter are not necessarily unique, which may be problematic
    networks:
        default:
            VM Network: VM Network
        description:
        - 'C(key: value) mapping of OVF network name, to the vCenter network name'
    ovf:
        description:
        - 'Path to OVF or OVA file to deploy'
    power_on:
        default: true
        description:
        - 'Whether or not to power on the VM after creation'
        type: bool
    resource_pool:
        default: Resources
        description:
        - 'Resource Pool to deploy to'
    wait:
        default: true
        description:
        - 'Wait for the host to power on'
        type: bool
    wait_for_ip_address:
        default: false
        description:
        - Wait until vCenter detects an IP address for the VM.
        - This requires vmware-tools (vmtoolsd) to properly work after creation.
        type: bool
requirements:
    - pyvmomi
version_added: 2.5.0
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- vmware_deploy_ovf:
    hostname: esx.example.org
    username: root
    password: passw0rd
    ovf: /path/to/ubuntu-16.04-amd64.ovf
    wait_for_ip_address: true
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

RETURN = '''
instance:
    description: metadata about the new virtualmachine
    returned: always
    type: dict
    sample: None
'''

import io
import os
import sys
import tarfile
import time
import traceback

from threading import Thread

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types
from ansible.module_utils.urls import open_url
from ansible.module_utils.vmware import (HAS_PYVMOMI, connect_to_api, find_datacenter_by_name, find_datastore_by_name,
                                         find_network_by_name, find_resource_pool_by_name, gather_vm_facts,
                                         vmware_argument_spec, wait_for_task, wait_for_vm_ip)
try:
    from ansible.module_utils.vmware import vim
    from pyVmomi import vmodl
except ImportError:
    pass


def path_exists(value):
    if not isinstance(value, string_types):
        value = str(value)
    value = os.path.expanduser(os.path.expandvars(value))
    if not os.path.exists(value):
        raise ValueError('%s is not a valid path' % value)
    return value


class ProgressReader(io.FileIO):
    def __init__(self, name, mode='r', closefd=True):
        self.bytes_read = 0
        io.FileIO.__init__(self, name, mode=mode, closefd=closefd)

    def read(self, size=10240):
        chunk = io.FileIO.read(self, size)
        self.bytes_read += len(chunk)
        return chunk


class TarFileProgressReader(tarfile.ExFileObject):
    def __init__(self, *args):
        self.bytes_read = 0
        tarfile.ExFileObject.__init__(self, *args)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.close()
        except:
            pass

    def read(self, size=10240):
        chunk = tarfile.ExFileObject.read(self, size)
        self.bytes_read += len(chunk)
        return chunk


class VMDKUploader(Thread):
    def __init__(self, vmdk, url, validate_certs=True, tarinfo=None):
        Thread.__init__(self)

        self.vmdk = vmdk

        if tarinfo:
            self.size = tarinfo.size
        else:
            self.size = os.stat(vmdk).st_size

        self.url = url
        self.validate_certs = validate_certs
        self.tarinfo = tarinfo

        self.f = None
        self.e = None

    @property
    def bytes_read(self):
        try:
            return self.f.bytes_read
        except AttributeError:
            return 0

    def run(self):
        headers = {
            'Content-Type': 'application/x-vnd.vmware-streamVmdk',
            'Content-Length': self.size
        }

        if self.tarinfo:
            try:
                with TarFileProgressReader(self.vmdk, self.tarinfo) as self.f:
                    open_url(self.url, data=self.f, headers=headers, method='POST', validate_certs=self.validate_certs)
            except Exception:
                self.e = sys.exc_info()
        else:
            try:
                with ProgressReader(self.vmdk, 'rb') as self.f:
                    open_url(self.url, data=self.f, headers=headers, method='POST', validate_certs=self.validate_certs)
            except Exception:
                self.e = sys.exc_info()


class VMwareDeployOvf:
    def __init__(self, module):
        self.si = connect_to_api(module)
        self.module = module
        self.params = module.params

        self.datastore = None
        self.datacenter = None
        self.resource_pool = None
        self.network_mappings = []

        self.ovf_descriptor = None
        self.tar = None

        self.lease = None
        self.import_spec = None
        self.entity = None

    def get_objects(self):
        self.datastore = find_datastore_by_name(self.si, self.params['datastore'])
        if not self.datastore:
            self.module.fail_json(msg='%(datastore)s could not be located' % self.params)

        self.datacenter = find_datacenter_by_name(self.si, self.params['datacenter'])
        if not self.datacenter:
            self.module.fail_json(msg='%(datacenter)s could not be located' % self.params)

        self.resource_pool = find_resource_pool_by_name(self.si, self.params['resource_pool'])
        if not self.resource_pool:
            self.module.fail_json(msg='%(resource_pool)s could not be located' % self.params)

        for key, value in self.params['networks'].items():
            network = find_network_by_name(self.si, value)
            if not network:
                self.module.fail_json(msg='%(network)s could not be located' % self.params)
            network_mapping = vim.OvfManager.NetworkMapping()
            network_mapping.name = key
            network_mapping.network = network
            self.network_mappings.append(network_mapping)

        return self.datastore, self.datacenter, self.resource_pool, self.network_mappings

    def get_ovf_descriptor(self):
        if tarfile.is_tarfile(self.params['ovf']):
            self.tar = tarfile.open(self.params['ovf'])
            ovf = None
            for candidate in self.tar.getmembers():
                dummy, ext = os.path.splitext(candidate.name)
                if ext.lower() == '.ovf':
                    ovf = candidate
                    break
            if not ovf:
                self.module.fail_json(msg='Could not locate OVF file in %(ovf)s' % self.params)

            self.ovf_descriptor = to_native(self.tar.extractfile(ovf).read())
        else:
            with open(self.params['ovf']) as f:
                self.ovf_descriptor = f.read()

        return self.ovf_descriptor

    def get_lease(self):
        datastore, datacenter, resource_pool, network_mappings = self.get_objects()

        params = {
            'diskProvisioning': self.params['disk_provisioning'],
        }
        if self.params['name']:
            params['entityName'] = self.params['name']
        if network_mappings:
            params['networkMapping'] = network_mappings

        spec_params = vim.OvfManager.CreateImportSpecParams(**params)

        ovf_descriptor = self.get_ovf_descriptor()

        self.import_spec = self.si.ovfManager.CreateImportSpec(
            ovf_descriptor,
            resource_pool,
            datastore,
            spec_params
        )

        joined_errors = '. '.join(to_native(e.msg) for e in getattr(self.import_spec, 'error', []))
        if joined_errors:
            self.module.fail_json(
                msg='Failure validating OVF import spec: %s' % joined_errors
            )

        for warning in getattr(self.import_spec, 'warning', []):
            self.module.warn('Problem validating OVF import spec: %s' % to_native(warning.msg))

        try:
            self.lease = resource_pool.ImportVApp(
                self.import_spec.importSpec,
                datacenter.vmFolder
            )
        except vmodl.fault.SystemError as e:
            self.module.fail_json(
                msg='Failed to start import: %s' % to_native(e.msg)
            )

        while self.lease.state != vim.HttpNfcLease.State.ready:
            time.sleep(0.1)

        self.entity = self.lease.info.entity

        return self.lease, self.import_spec

    def upload(self):
        ovf_dir = os.path.dirname(self.params['ovf'])

        lease, import_spec = self.get_lease()

        uploaders = []

        for file_item in import_spec.fileItem:
            vmdk_post_url = None
            for device_url in lease.info.deviceUrl:
                if file_item.deviceId == device_url.importKey:
                    vmdk_post_url = device_url.url.replace('*', self.params['hostname'])
                    break

            if not vmdk_post_url:
                lease.HttpNfcLeaseAbort(
                    vmodl.fault.SystemError(reason='Failed to find deviceUrl for file %s' % file_item.path)
                )
                self.module.fail_json(
                    msg='Failed to find deviceUrl for file %s' % file_item.path
                )

            if self.tar:
                vmdk = self.tar
                try:
                    vmdk_tarinfo = self.tar.getmember(file_item.path)
                except KeyError:
                    lease.HttpNfcLeaseAbort(
                        vmodl.fault.SystemError(reason='Failed to find VMDK file %s in OVA' % file_item.path)
                    )
                    self.module.fail_json(
                        msg='Failed to find VMDK file %s in OVA' % file_item.path
                    )
            else:
                vmdk = os.path.join(ovf_dir, file_item.path)
                try:
                    path_exists(vmdk)
                except ValueError:
                    lease.HttpNfcLeaseAbort(
                        vmodl.fault.SystemError(reason='Failed to find VMDK file at %s' % vmdk)
                    )
                    self.module.fail_json(
                        msg='Failed to find VMDK file at %s' % vmdk
                    )
                vmdk_tarinfo = None

            uploaders.append(
                VMDKUploader(
                    vmdk,
                    vmdk_post_url,
                    self.params['validate_certs'],
                    tarinfo=vmdk_tarinfo
                )
            )

        total_size = sum(u.size for u in uploaders)
        total_bytes_read = [0] * len(uploaders)
        for i, uploader in enumerate(uploaders):
            uploader.start()
            while uploader.is_alive():
                time.sleep(0.1)
                total_bytes_read[i] = uploader.bytes_read
                lease.HttpNfcLeaseProgress(int(100.0 * sum(total_bytes_read) / total_size))

            if uploader.e:
                lease.HttpNfcLeaseAbort(
                    vmodl.fault.SystemError(reason='%s' % to_native(uploader.e[1]))
                )
                self.module.fail_json(
                    msg='%s' % to_native(uploader.e[1]),
                    exception=''.join(traceback.format_tb(uploader.e[2]))
                )

    def complete(self):
        self.lease.HttpNfcLeaseComplete()

    def power_on(self):
        facts = {}
        if self.params['power_on']:
            task = self.entity.PowerOn()
            if self.params['wait']:
                wait_for_task(task)
                if self.params['wait_for_ip_address']:
                    _facts = wait_for_vm_ip(self.si, self.entity)
                    if not _facts:
                        self.module.fail_json(msg='Waiting for IP address timed out')
                    facts.update(_facts)

        if not facts:
            gather_vm_facts(self.si, self.entity)

        return facts


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update({
        'name': {},
        'datastore': {
            'default': 'datastore1',
        },
        'datacenter': {
            'default': 'ha-datacenter',
        },
        'resource_pool': {
            'default': 'Resources',
        },
        'networks': {
            'default': {
                'VM Network': 'VM Network',
            },
            'type': 'dict',
        },
        'ovf': {
            'type': path_exists,
        },
        'disk_provisioning': {
            'choices': [
                'flat',
                'eagerZeroedThick',
                'monolithicSparse',
                'twoGbMaxExtentSparse',
                'twoGbMaxExtentFlat',
                'thin',
                'sparse',
                'thick',
                'seSparse',
                'monolithicFlat'
            ],
            'default': 'thin',
        },
        'power_on': {
            'type': 'bool',
            'default': True,
        },
        'wait': {
            'type': 'bool',
            'default': True,
        },
        'wait_for_ip_address': {
            'type': 'bool',
            'default': False,
        },
    })
    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not module.params['power_on'] and (module.params['wait_for_ip_address'] or module.params['wait']):
        module.fail_json(msg='Cannot wait for VM when power_on=False')

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi python library not found')

    deploy_ovf = VMwareDeployOvf(module)
    deploy_ovf.upload()
    deploy_ovf.complete()
    facts = deploy_ovf.power_on()

    module.exit_json(instance=facts, changed=True)


if __name__ == '__main__':
    main()
