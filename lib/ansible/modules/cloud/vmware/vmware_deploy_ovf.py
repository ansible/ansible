#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
author: 'Matt Martz (@sivel)'
short_description: 'Deploys a VMWare VM from an OVF file'
description:
- 'Deploys a VMWare VM from an OVF file'
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
        - 'Path to OVF file to deploy'
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
- vmware_ovf:
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
import time
import traceback

from threading import Thread

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from ansible.module_utils.vmware import (HAS_PYVMOMI, connect_to_api, find_datacenter_by_name, find_datastore_by_name,
                                         gather_vm_facts, get_all_objs, vmware_argument_spec, wait_for_task)
try:
    from ansible.module_utils.vmware import vim
    from pyVmomi import vmodl
except ImportError:
    pass


def find_resource_pool_by_name(content, resource_pool_name):

    resource_pools = get_all_objs(content, [vim.ResourcePool])
    for resource_pool in resource_pools:
        if resource_pool.name == resource_pool_name:
            return resource_pool

    return None


def find_network_by_name(content, network_name):

    networks = get_all_objs(content, [vim.Network])
    for network in networks:
        if network.name == network_name:
            return network

    return None


def wait_for_vm_ip(content, vm, poll=100, sleep=5):
    ips = None
    facts = {}
    thispoll = 0
    while not ips and thispoll <= poll:
        facts = gather_vm_facts(content, vm)
        if facts['ipv4'] or facts['ipv6']:
            ips = True
        else:
            time.sleep(sleep)
            thispoll += 1

    return facts


class ProgressReader(io.FileIO):
    def __init__(self, name, mode='r', closefd=True):
        self.bytes_read = 0
        io.FileIO.__init__(self, name, mode=mode, closefd=closefd)

    def read(self, size=1024):
        chunk = io.FileIO.read(self, size)
        self.bytes_read += len(chunk)
        return chunk


class VMDKUploader(Thread):
    def __init__(self, module, vmdk, size, url, validate_certs):
        Thread.__init__(self)
        self.module = module
        self.vmdk = vmdk
        self.size = size
        self.url = url
        self.validate_certs = validate_certs
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

        try:
            with ProgressReader(self.vmdk, 'rb') as self.f:
                open_url(self.url, data=self.f, headers=headers, method='POST', validate_certs=self.validate_certs)
        except Exception:
            self.e = sys.exc_info()


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
            'type': 'path',
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

    ovf_dir = os.path.dirname(module.params['ovf'])

    si = connect_to_api(module)

    datastore = find_datastore_by_name(si, module.params['datastore'])
    if not datastore:
        module.fail_json(msg='%(datastore) could not be located' % module.params)

    datacenter = find_datacenter_by_name(si, module.params['datacenter'])
    if not datacenter:
        module.fail_json(msg='%(datacenter)s could not be located' % module.params)

    resource_pool = find_resource_pool_by_name(si, module.params['resource_pool'])
    if not resource_pool:
        module.fail_json(msg='%(resource_pool)s could not be located' % module.params)

    network_mappings = []
    for key, value in module.params['networks'].items():
        network = find_network_by_name(si, value)
        if not network:
            module.fail_json(msg='%(network)s could not be located' % module.params)
        network_mapping = vim.OvfManager.NetworkMapping()
        network_mapping.name = key
        network_mapping.network = network
        network_mappings.append(network_mapping)

    params = {
        'diskProvisioning': module.params['disk_provisioning'],
    }
    if module.params['name']:
        params['entityName'] = module.params['name']
    if network_mappings:
        params['networkMapping'] = network_mappings
    spec_params = vim.OvfManager.CreateImportSpecParams(**params)

    with open(module.params['ovf']) as f:
        ovf_descriptor = f.read()

    import_spec = si.ovfManager.CreateImportSpec(
        ovf_descriptor,
        resource_pool,
        datastore,
        spec_params
    )

    lease = resource_pool.ImportVApp(
        import_spec.importSpec,
        datacenter.vmFolder
    )

    while lease.state != vim.HttpNfcLease.State.ready:
        time.sleep(0.1)

    entity = lease.info.entity

    for file_item in import_spec.fileItem:
        vmdk_post_url = None
        for device_url in lease.info.deviceUrl:
            if file_item.deviceId == device_url.importKey:
                vmdk_post_url = device_url.url.replace('*', module.params['hostname'])
                break

        if not vmdk_post_url:
            module.fail_json(msg='Failed to find deviceUrl for file %s' % file_item.path)

        vmdk = os.path.join(ovf_dir, file_item.path)

        vmdk_size = os.stat(vmdk).st_size

        uploader = VMDKUploader(module, vmdk, vmdk_size, vmdk_post_url, module.params['validate_certs'])
        uploader.start()
        while uploader.is_alive():
            time.sleep(0.1)
            lease.HttpNfcLeaseProgress(int(100.0 * uploader.bytes_read / vmdk_size))

        if uploader.e:
            lease.HttpNfcLeaseAbort(vmodl.fault.SystemError(reason='%s' % to_native(uploader.e[1])))
            module.fail_json(
                msg='%s' % to_native(uploader.e[1]),
                exception=''.join(traceback.format_tb(uploader.e[2]))
            )

    lease.HttpNfcLeaseComplete()

    facts = {}

    if module.params['power_on']:
        task = entity.PowerOn()
        if module.params['wait']:
            wait_for_task(task)
            if module.params['wait_for_ip_address']:
                facts.update(wait_for_vm_ip(si, entity))

    if not facts:
        facts.update(gather_vm_facts(si, entity))

    module.exit_json(instance=facts, changed=True)


if __name__ == '__main__':
    main()
