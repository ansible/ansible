#!/usr/bin/python
#
# Copyright (c) 2017 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_image
version_added: "2.5"
short_description: Manage Azure image
description:
    - Create, delete an image from virtual machine, blob uri, managed disk or snapshot.
options:
    resource_group:
        description:
            - Name of resource group.
        required: true
    name:
        description:
            - Name of the image.
        required: true
    source:
        description:
            - OS disk source from the same region.
            - It can be a virtual machine, OS disk blob URI, managed OS disk, or OS snapshot.
            - Each type of source except for blob URI can be given as resource id, name or a dict contains C(resource_group), C(name) and C(type).
            - If source type is blob URI, the source should be the full URI of the blob in string type.
            - If you specify the I(type) in a dict, acceptable value contains C(disks), C(virtual_machines) and C(snapshots).
        type: raw
        required: true
    data_disk_sources:
        description:
            - List of data disk sources, including unmanaged blob URI, managed disk id or name, or snapshot id or name.
        type: list
    location:
        description:
            - Location of the image. Derived from I(resource_group) if not specified.
    os_type:
        description: The OS type of image.
        choices:
            - Windows
            - Linux
    state:
        description:
            - Assert the state of the image. Use C(present) to create or update a image and C(absent) to delete an image.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
- name: Create an image from a virtual machine
  azure_rm_image:
    resource_group: myResourceGroup
    name: myImage
    source: myVirtualMachine

- name: Create an image from os disk
  azure_rm_image:
    resource_group: myResourceGroup
    name: myImage
    source: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Compute/disks/disk001
    data_disk_sources:
        - datadisk001
        - datadisk002
    os_type: Linux

- name: Create an image from os disk via dict
  azure_rm_image:
    resource_group: myResourceGroup
    name: myImage
    source:
        type: disks
        resource_group: myResourceGroup
        name: disk001
    data_disk_sources:
        - datadisk001
        - datadisk002
    os_type: Linux

- name: Delete an image
  azure_rm_image:
    state: absent
    resource_group: myResourceGroup
    name: myImage
    source: testvm001
'''

RETURN = '''
id:
    description:
        - Image resource path.
    type: str
    returned: success
    example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Compute/images/myImage"
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMImage(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            source=dict(type='raw'),
            data_disk_sources=dict(type='list', default=[]),
            os_type=dict(type='str', choices=['Windows', 'Linux'])
        )

        self.results = dict(
            changed=False,
            id=None
        )

        required_if = [
            ('state', 'present', ['source'])
        ]

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.source = None
        self.data_disk_sources = None
        self.os_type = None

        super(AzureRMImage, self).__init__(self.module_arg_spec, supports_check_mode=True, required_if=required_if)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        results = None
        changed = False
        image = None

        if not self.location:
            # Set default location
            resource_group = self.get_resource_group(self.resource_group)
            self.location = resource_group.location

        self.log('Fetching image {0}'.format(self.name))
        image = self.get_image()
        if image:
            self.check_provisioning_state(image, self.state)
            results = image.id
            # update is not supported except for tags
            update_tags, tags = self.update_tags(image.tags)
            if update_tags:
                changed = True
                self.tags = tags
            if self.state == 'absent':
                changed = True
        # the image does not exist and create a new one
        elif self.state == 'present':
            changed = True

        self.results['changed'] = changed
        self.results['id'] = results

        if changed:
            if self.state == 'present':
                image_instance = None
                # create from virtual machine
                vm = self.get_source_vm()
                if vm:
                    if self.data_disk_sources:
                        self.fail('data_disk_sources is not allowed when capturing image from vm')
                    image_instance = self.compute_models.Image(location=self.location,
                                                               source_virtual_machine=self.compute_models.SubResource(id=vm.id),
                                                               tags=self.tags)
                else:
                    if not self.os_type:
                        self.fail('os_type is required to create the image')
                    os_disk = self.create_os_disk()
                    data_disks = self.create_data_disks()
                    storage_profile = self.compute_models.ImageStorageProfile(os_disk=os_disk, data_disks=data_disks)
                    image_instance = self.compute_models.Image(location=self.location, storage_profile=storage_profile, tags=self.tags)

                # finally make the change if not check mode
                if not self.check_mode and image_instance:
                    new_image = self.create_image(image_instance)
                    self.results['id'] = new_image.id

            elif self.state == 'absent':
                if not self.check_mode:
                    # delete image
                    self.delete_image()
                    # the delete does not actually return anything. if no exception, then we'll assume it worked.
                    self.results['id'] = None

        return self.results

    def resolve_storage_source(self, source):
        blob_uri = None
        disk = None
        snapshot = None
        # blob URI can only be given by str
        if isinstance(source, str) and source.lower().endswith('.vhd'):
            blob_uri = source
            return (blob_uri, disk, snapshot)

        tokenize = dict()
        if isinstance(source, dict):
            tokenize = source
        elif isinstance(source, str):
            tokenize = parse_resource_id(source)
        else:
            self.fail("source parameter should be in type string or dictionary")
        if tokenize.get('type') == 'disks':
            disk = format_resource_id(tokenize['name'],
                                      tokenize.get('subscription_id') or self.subscription_id,
                                      'Microsoft.Compute',
                                      'disks',
                                      tokenize.get('resource_group') or self.resource_group)
            return (blob_uri, disk, snapshot)

        if tokenize.get('type') == 'snapshots':
            snapshot = format_resource_id(tokenize['name'],
                                          tokenize.get('subscription_id') or self.subscription_id,
                                          'Microsoft.Compute',
                                          'snapshots',
                                          tokenize.get('resource_group') or self.resource_group)
            return (blob_uri, disk, snapshot)

        # not a disk or snapshots
        if 'type' in tokenize:
            return (blob_uri, disk, snapshot)

        # source can be name of snapshot or disk
        snapshot_instance = self.get_snapshot(tokenize.get('resource_group') or self.resource_group,
                                              tokenize['name'])
        if snapshot_instance:
            snapshot = snapshot_instance.id
            return (blob_uri, disk, snapshot)

        disk_instance = self.get_disk(tokenize.get('resource_group') or self.resource_group,
                                      tokenize['name'])
        if disk_instance:
            disk = disk_instance.id
        return (blob_uri, disk, snapshot)

    def create_os_disk(self):
        blob_uri, disk, snapshot = self.resolve_storage_source(self.source)
        snapshot_resource = self.compute_models.SubResource(id=snapshot) if snapshot else None
        managed_disk = self.compute_models.SubResource(id=disk) if disk else None
        return self.compute_models.ImageOSDisk(os_type=self.os_type,
                                               os_state=self.compute_models.OperatingSystemStateTypes.generalized,
                                               snapshot=snapshot_resource,
                                               managed_disk=managed_disk,
                                               blob_uri=blob_uri)

    def create_data_disk(self, lun, source):
        blob_uri, disk, snapshot = self.resolve_storage_source(source)
        if blob_uri or disk or snapshot:
            snapshot_resource = self.compute_models.SubResource(id=snapshot) if snapshot else None
            managed_disk = self.compute_models.SubResource(id=disk) if disk else None
            return self.compute_models.ImageDataDisk(lun=lun,
                                                     blob_uri=blob_uri,
                                                     snapshot=snapshot_resource,
                                                     managed_disk=managed_disk)

    def create_data_disks(self):
        return list(filter(None, [self.create_data_disk(lun, source) for lun, source in enumerate(self.data_disk_sources)]))

    def get_source_vm(self):
        # self.resource can be a vm (id/name/dict), or not a vm. return the vm iff it is an existing vm.
        resource = dict()
        if isinstance(self.source, dict):
            if self.source.get('type') != 'virtual_machines':
                return None
            resource = dict(type='virtualMachines',
                            name=self.source['name'],
                            resource_group=self.source.get('resource_group') or self.resource_group)
        elif isinstance(self.source, str):
            vm_resource_id = format_resource_id(self.source,
                                                self.subscription_id,
                                                'Microsoft.Compute',
                                                'virtualMachines',
                                                self.resource_group)
            resource = parse_resource_id(vm_resource_id)
        else:
            self.fail("Unsupported type of source parameter, please give string or dictionary")
        return self.get_vm(resource['resource_group'], resource['name']) if resource['type'] == 'virtualMachines' else None

    def get_snapshot(self, resource_group, snapshot_name):
        return self._get_resource(self.compute_client.snapshots.get, resource_group, snapshot_name)

    def get_disk(self, resource_group, disk_name):
        return self._get_resource(self.compute_client.disks.get, resource_group, disk_name)

    def get_vm(self, resource_group, vm_name):
        return self._get_resource(self.compute_client.virtual_machines.get, resource_group, vm_name, 'instanceview')

    def get_image(self):
        return self._get_resource(self.compute_client.images.get, self.resource_group, self.name)

    def _get_resource(self, get_method, resource_group, name, expand=None):
        try:
            if expand:
                return get_method(resource_group, name, expand=expand)
            else:
                return get_method(resource_group, name)
        except CloudError as cloud_err:
            # Return None iff the resource is not found
            if cloud_err.status_code == 404:
                self.log('{0}'.format(str(cloud_err)))
                return None
            self.fail('Error: failed to get resource {0} - {1}'.format(name, str(cloud_err)))
        except Exception as exc:
            self.fail('Error: failed to get resource {0} - {1}'.format(name, str(exc)))

    def create_image(self, image):
        try:
            poller = self.compute_client.images.create_or_update(self.resource_group, self.name, image)
            new_image = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating image {0} - {1}".format(self.name, str(exc)))
        self.check_provisioning_state(new_image)
        return new_image

    def delete_image(self):
        self.log('Deleting image {0}'.format(self.name))
        try:
            poller = self.compute_client.images.delete(self.resource_group, self.name)
            result = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting image {0} - {1}".format(self.name, str(exc)))

        return result


def main():
    AzureRMImage()


if __name__ == '__main__':
    main()
