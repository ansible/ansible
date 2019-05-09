#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Matt Martz <matt@sivel.net>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
author: 'Matt Martz (@sivel)'
short_description: 'Deploys a VMware virtual machine from an OVF or OVA file'
description:
- 'This module can be used to deploy a VMware VM from an OVF or OVA file'
module: vmware_deploy_ovf
notes: []
options:
    allow_duplicates:
        default: "yes"
        description:
          - Whether or not to allow duplicate VM names. ESXi allows duplicates, vCenter may not.
        type: bool
    datacenter:
        default: ha-datacenter
        description:
        - Datacenter to deploy to.
    cluster:
        description:
        - Cluster to deploy to.
    datastore:
        default: datastore1
        description:
        - Datastore to deploy to.
    deployment_option:
        description:
        - The key of the chosen deployment option.
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
        - Disk provisioning type.
    fail_on_spec_warnings:
        description:
        - Cause the module to treat OVF Import Spec warnings as errors.
        default: "no"
        type: bool
    folder:
        description:
        - Absolute path of folder to place the virtual machine.
        - If not specified, defaults to the value of C(datacenter.vmFolder).
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
    inject_ovf_env:
        description:
        - Force the given properties to be inserted into an OVF Environment and injected through VMware Tools.
        version_added: "2.8"
        type: bool
    name:
        description:
        - Name of the VM to work with.
        - Virtual machine names in vCenter are not necessarily unique, which may be problematic.
    networks:
        default:
            VM Network: VM Network
        description:
        - 'C(key: value) mapping of OVF network name, to the vCenter network name.'
    ovf:
        description:
        - 'Path to OVF or OVA file to deploy.'
        aliases:
            - ova
    power_on:
        default: true
        description:
        - 'Whether or not to power on the virtual machine after creation.'
        type: bool
    properties:
        description:
        - The assignment of values to the properties found in the OVF as key value pairs.
    resource_pool:
        default: Resources
        description:
        - 'Resource Pool to deploy to.'
    wait:
        default: true
        description:
        - 'Wait for the host to power on.'
        type: bool
    wait_for_ip_address:
        default: false
        description:
        - Wait until vCenter detects an IP address for the VM.
        - This requires vmware-tools (vmtoolsd) to properly work after creation.
        type: bool
requirements:
    - pyvmomi
version_added: "2.7"
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- vmware_deploy_ovf:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    ovf: /path/to/ubuntu-16.04-amd64.ovf
    wait_for_ip_address: true
  delegate_to: localhost

# Deploys a new VM named 'NewVM' in specific datacenter/cluster, with network mapping taken from variable and using ova template from an absolute path
- vmware_deploy_ovf:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: Datacenter1
    cluster: Cluster1
    datastore: vsandatastore
    name: NewVM
    networks: "{u'VM Network':u'{{ ProvisioningNetworkLabel }}'}"
    validate_certs: no
    power_on: no
    ovf: /absolute/path/to/template/mytemplate.ova
  delegate_to: localhost
'''


RETURN = r'''
instance:
    description: metadata about the new virtual machine
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

import xml.etree.ElementTree as ET

from threading import Thread

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types
from ansible.module_utils.urls import generic_urlparse, open_url, urlparse, urlunparse
from ansible.module_utils.vmware import (HAS_PYVMOMI, connect_to_api, find_datacenter_by_name, find_datastore_by_name,
                                         find_network_by_name, find_resource_pool_by_name, find_vm_by_name, find_cluster_by_name,
                                         gather_vm_facts, vmware_argument_spec, wait_for_task, wait_for_vm_ip)
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
        except Exception:
            pass

    def read(self, size=10240):
        chunk = tarfile.ExFileObject.read(self, size)
        self.bytes_read += len(chunk)
        return chunk


class VMDKUploader(Thread):
    def __init__(self, vmdk, url, validate_certs=True, tarinfo=None, create=False):
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

        self._create = create

    @property
    def bytes_read(self):
        try:
            return self.f.bytes_read
        except AttributeError:
            return 0

    def _request_opts(self):
        '''
        Requests for vmdk files differ from other file types. Build the request options here to handle that
        '''
        headers = {
            'Content-Length': self.size,
            'Content-Type': 'application/octet-stream',
        }

        if self._create:
            # Non-VMDK
            method = 'PUT'
            headers['Overwrite'] = 't'
        else:
            # VMDK
            method = 'POST'
            headers['Content-Type'] = 'application/x-vnd.vmware-streamVmdk'

        return {
            'method': method,
            'headers': headers,
        }

    def _open_url(self):
        open_url(self.url, data=self.f, validate_certs=self.validate_certs, **self._request_opts())

    def run(self):
        if self.tarinfo:
            try:
                with TarFileProgressReader(self.vmdk, self.tarinfo) as self.f:
                    self._open_url()
            except Exception:
                self.e = sys.exc_info()
        else:
            try:
                with ProgressReader(self.vmdk, 'rb') as self.f:
                    self._open_url()
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

        if self.params['cluster']:
            cluster = find_cluster_by_name(self.si, self.params['cluster'])
            if cluster is None:
                self.module.fail_json(msg="Unable to find cluster '%(cluster)s'" % self.params)
            else:
                self.resource_pool = cluster.resourcePool
        else:
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
        if self.params['deployment_option']:
            params['deploymentOption'] = self.params['deployment_option']
        if self.params['properties']:
            params['propertyMapping'] = []
            for key, value in self.params['properties'].items():
                property_mapping = vim.KeyValue()
                property_mapping.key = key
                property_mapping.value = str(value) if isinstance(value, bool) else value
                params['propertyMapping'].append(property_mapping)

        if self.params['folder']:
            folder = self.si.searchIndex.FindByInventoryPath(self.params['folder'])
        else:
            folder = datacenter.vmFolder

        spec_params = vim.OvfManager.CreateImportSpecParams(**params)

        ovf_descriptor = self.get_ovf_descriptor()

        self.import_spec = self.si.ovfManager.CreateImportSpec(
            ovf_descriptor,
            resource_pool,
            datastore,
            spec_params
        )

        errors = [to_native(e.msg) for e in getattr(self.import_spec, 'error', [])]
        if self.params['fail_on_spec_warnings']:
            errors.extend(
                (to_native(w.msg) for w in getattr(self.import_spec, 'warning', []))
            )
        if errors:
            self.module.fail_json(
                msg='Failure validating OVF import spec: %s' % '. '.join(errors)
            )

        for warning in getattr(self.import_spec, 'warning', []):
            self.module.warn('Problem validating OVF import spec: %s' % to_native(warning.msg))

        if not self.params['allow_duplicates']:
            name = self.import_spec.importSpec.configSpec.name
            match = find_vm_by_name(self.si, name, folder=folder)
            if match:
                self.module.exit_json(instance=gather_vm_facts(self.si, match), changed=False)

        if self.module.check_mode:
            self.module.exit_json(changed=True, instance={'hw_name': name})

        try:
            self.lease = resource_pool.ImportVApp(
                self.import_spec.importSpec,
                folder
            )
        except vmodl.fault.SystemError as e:
            self.module.fail_json(
                msg='Failed to start import: %s' % to_native(e.msg)
            )

        while self.lease.state != vim.HttpNfcLease.State.ready:
            time.sleep(0.1)

        self.entity = self.lease.info.entity

        return self.lease, self.import_spec

    def _normalize_url(self, url):
        '''
        The hostname in URLs from vmware may be ``*`` update it accordingly
        '''
        url_parts = generic_urlparse(urlparse(url))
        if url_parts.hostname == '*':
            if url_parts.port:
                url_parts.netloc = '%s:%d' % (self.params['hostname'], url_parts.port)
            else:
                url_parts.netloc = self.params['hostname']

        return urlunparse(url_parts.as_list())

    def upload(self):
        if self.params['ovf'] is None:
            self.module.fail_json(msg="OVF path is required for upload operation.")

        ovf_dir = os.path.dirname(self.params['ovf'])

        lease, import_spec = self.get_lease()

        uploaders = []

        for file_item in import_spec.fileItem:
            device_upload_url = None
            for device_url in lease.info.deviceUrl:
                if file_item.deviceId == device_url.importKey:
                    device_upload_url = self._normalize_url(device_url.url)
                    break

            if not device_upload_url:
                lease.HttpNfcLeaseAbort(
                    vmodl.fault.SystemError(reason='Failed to find deviceUrl for file %s' % file_item.path)
                )
                self.module.fail_json(
                    msg='Failed to find deviceUrl for file %s' % file_item.path
                )

            vmdk_tarinfo = None
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

            uploaders.append(
                VMDKUploader(
                    vmdk,
                    device_upload_url,
                    self.params['validate_certs'],
                    tarinfo=vmdk_tarinfo,
                    create=file_item.create
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

    def inject_ovf_env(self):
        attrib = {
            'xmlns': 'http://schemas.dmtf.org/ovf/environment/1',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xmlns:oe': 'http://schemas.dmtf.org/ovf/environment/1',
            'xmlns:ve': 'http://www.vmware.com/schema/ovfenv',
            'oe:id': '',
            've:esxId': self.entity._moId
        }
        env = ET.Element('Environment', **attrib)

        platform = ET.SubElement(env, 'PlatformSection')
        ET.SubElement(platform, 'Kind').text = self.si.about.name
        ET.SubElement(platform, 'Version').text = self.si.about.version
        ET.SubElement(platform, 'Vendor').text = self.si.about.vendor
        ET.SubElement(platform, 'Locale').text = 'US'

        prop_section = ET.SubElement(env, 'PropertySection')
        for key, value in self.params['properties'].items():
            params = {
                'oe:key': key,
                'oe:value': str(value) if isinstance(value, bool) else value
            }
            ET.SubElement(prop_section, 'Property', **params)

        opt = vim.option.OptionValue()
        opt.key = 'guestinfo.ovfEnv'
        opt.value = '<?xml version="1.0" encoding="UTF-8"?>' + to_native(ET.tostring(env))

        config_spec = vim.vm.ConfigSpec()
        config_spec.extraConfig = [opt]

        task = self.entity.ReconfigVM_Task(config_spec)
        wait_for_task(task)

    def deploy(self):
        facts = {}

        if self.params['inject_ovf_env']:
            self.inject_ovf_env()

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
            facts.update(gather_vm_facts(self.si, self.entity))

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
        'cluster': {
            'default': None,
        },
        'deployment_option': {
            'default': None,
        },
        'folder': {
            'default': None,
        },
        'inject_ovf_env': {
            'default': False,
            'type': 'bool',
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
            'aliases': ['ova'],
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
        'properties': {
            'type': 'dict',
        },
        'wait': {
            'type': 'bool',
            'default': True,
        },
        'wait_for_ip_address': {
            'type': 'bool',
            'default': False,
        },
        'allow_duplicates': {
            'type': 'bool',
            'default': True,
        },
        'fail_on_spec_warnings': {
            'type': 'bool',
            'default': False,
        },
    })
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi python library not found')

    deploy_ovf = VMwareDeployOvf(module)
    deploy_ovf.upload()
    deploy_ovf.complete()
    facts = deploy_ovf.deploy()

    module.exit_json(instance=facts, changed=True)


if __name__ == '__main__':
    main()
