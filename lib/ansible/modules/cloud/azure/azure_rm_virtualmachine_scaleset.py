#!/usr/bin/python
#
# Copyright (c) 2016 Sertac Ozercan, <seozerca@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualmachine_scaleset

version_added: "2.4"

short_description: Manage Azure virtual machine scale sets.

description:
    - Create and update a virtual machine scale set.

options:
    resource_group:
        description:
            - Name of the resource group containing the virtual machine scale set.
        required: true
    name:
        description:
            - Name of the virtual machine.
        required: true
    state:
        description:
            - Assert the state of the virtual machine scale set.
            - State 'present' will check that the machine exists with the requested configuration. If the configuration
              of the existing machine does not match, the machine will be updated.
              state.
            - State 'absent' will remove the virtual machine scale set.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
    short_hostname:
        description:
            - Short host name
    vm_size:
        description:
            - A valid Azure VM size value. For example, 'Standard_D4'. The list of choices varies depending on the
              subscription and location. Check your subscription for available choices.
        required: true
    capacity:
        description:
            - Capacity of VMSS.
        required: true
        default: 1
    tier:
        description:
            - SKU Tier.
        choices:
            - Basic
            - Standard
    upgrade_policy:
        description:
            - Upgrade policy.
        choices:
            - Manual
            - Automatic
    admin_username:
        description:
            - Admin username used to access the host after it is created. Required when creating a VM.
    admin_password:
        description:
            - Password for the admin username. Not required if the os_type is Linux and SSH password authentication
              is disabled by setting ssh_password_enabled to false.
    ssh_password_enabled:
        description:
            - When the os_type is Linux, setting ssh_password_enabled to false will disable SSH password authentication
              and require use of SSH keys.
        type: bool
        default: true
    ssh_public_keys:
        description:
            - "For os_type Linux provide a list of SSH keys. Each item in the list should be a dictionary where the
              dictionary contains two keys: path and key_data. Set the path to the default location of the
              authorized_keys files. On an Enterprise Linux host, for example, the path will be
              /home/<admin username>/.ssh/authorized_keys. Set key_data to the actual value of the public key."
    image:
        description:
            - Specifies the image used to build the VM.
            - If a string, the image is sourced from a custom image based on the
              name.
            - 'If a dict with the keys C(publisher), C(offer), C(sku), and
              C(version), the image is sourced from a Marketplace image. NOTE:
              set image.version to C(latest) to get the most recent version of a
              given image.'
            - 'If a dict with the keys C(name) and C(resource_group), the image
              is sourced from a custom image based on the C(name) and
              C(resource_group) set. NOTE: the key C(resource_group) is optional
              and if omitted, all images in the subscription will be searched for
              by C(name).'
            - Custom image support was added in Ansible 2.5
        required: true
    os_disk_caching:
        description:
            - Type of OS disk caching.
        choices:
            - ReadOnly
            - ReadWrite
        default: ReadOnly
        aliases:
            - disk_caching
    os_type:
        description:
            - Base type of operating system.
        choices:
            - Windows
            - Linux
        default: Linux
    managed_disk_type:
        description:
            - Managed disk type.
        choices:
            - Standard_LRS
            - Premium_LRS
    data_disks:
        description:
            - Describes list of data disks.
        version_added: "2.4"
        suboptions:
            lun:
                description:
                    - The logical unit number for data disk.
                default: 0
                version_added: "2.4"
            disk_size_gb:
                description:
                    - The initial disk size in GB for blank data disks.
                version_added: "2.4"
            managed_disk_type:
                description:
                    - Managed data disk type.
                choices:
                    - Standard_LRS
                    - Premium_LRS
                version_added: "2.4"
            caching:
                description:
                    - Type of data disk caching.
                choices:
                    - ReadOnly
                    - ReadWrite
                default: ReadOnly
                version_added: "2.4"
    virtual_network_resource_group:
        description:
            - When creating a virtual machine, if a specific virtual network from another resource group should be
              used, use this parameter to specify the resource group to use.
        version_added: "2.5"
    virtual_network_name:
        description:
            - Virtual Network name.
        aliases:
            - virtual_network
    subnet_name:
        description:
            - Subnet name.
        aliases:
            - subnet
    load_balancer:
        description:
            - Load balancer name.
        version_added: "2.5"
    remove_on_absent:
        description:
            - When removing a VM using state 'absent', also remove associated resources.
            - "It can be 'all' or a list with any of the following: ['network_interfaces', 'virtual_storage', 'public_ips']."
            - Any other input will be ignored.
        default: ['all']

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Sertac Ozercan (@sozercan)"

'''
EXAMPLES = '''

- name: Create VMSS
  azure_rm_virtualmachine_scaleset:
    resource_group: Testing
    name: testvmss
    vm_size: Standard_DS1_v2
    capacity: 2
    virtual_network_name: testvnet
    subnet_name: testsubnet
    admin_username: adminUser
    ssh_password_enabled: false
    ssh_public_keys:
      - path: /home/adminUser/.ssh/authorized_keys
        key_data: < insert yor ssh public key here... >
    managed_disk_type: Standard_LRS
    image:
      offer: CoreOS
      publisher: CoreOS
      sku: Stable
      version: latest
    data_disks:
      - lun: 0
        disk_size_gb: 64
        caching: ReadWrite
        managed_disk_type: Standard_LRS

- name: Create a VMSS with a custom image
  azure_rm_virtualmachine_scaleset:
    resource_group: Testing
    name: testvmss
    vm_size: Standard_DS1_v2
    capacity: 2
    virtual_network_name: testvnet
    subnet_name: testsubnet
    admin_username: adminUser
    admin_password: password01
    managed_disk_type: Standard_LRS
    image: customimage001

- name: Create a VMSS with a custom image from a particular resource group
  azure_rm_virtualmachine_scaleset:
    resource_group: Testing
    name: testvmss
    vm_size: Standard_DS1_v2
    capacity: 2
    virtual_network_name: testvnet
    subnet_name: testsubnet
    admin_username: adminUser
    admin_password: password01
    managed_disk_type: Standard_LRS
    image:
      name: customimage001
      resource_group: Testing
'''

RETURN = '''
azure_vmss:
    description: Facts about the current state of the object. Note that facts are not part of the registered output but available directly.
    returned: always
    type: complex
    contains: {
        "properties": {
            "overprovision": true,
            "singlePlacementGroup": true,
            "upgradePolicy": {
                "mode": "Manual"
            },
            "virtualMachineProfile": {
                "networkProfile": {
                    "networkInterfaceConfigurations": [
                        {
                            "name": "testvmss",
                            "properties": {
                                "dnsSettings": {
                                    "dnsServers": []
                                },
                                "enableAcceleratedNetworking": false,
                                "ipConfigurations": [
                                    {
                                        "name": "default",
                                        "properties": {
                                            "privateIPAddressVersion": "IPv4",
                                            "subnet": {
                                                "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/testvnet/subnets/testsubnet"
                                            }
                                        }
                                    }
                                ],
                                "primary": true
                            }
                        }
                    ]
                },
                "osProfile": {
                    "adminUsername": "testuser",
                    "computerNamePrefix": "testvmss",
                    "linuxConfiguration": {
                        "disablePasswordAuthentication": true,
                        "ssh": {
                            "publicKeys": [
                                {
                                    "keyData": "",
                                    "path": "/home/testuser/.ssh/authorized_keys"
                                }
                            ]
                        }
                    },
                    "secrets": []
                },
                "storageProfile": {
                    "dataDisks": [
                        {
                            "caching": "ReadWrite",
                            "createOption": "empty",
                            "diskSizeGB": 64,
                            "lun": 0,
                            "managedDisk": {
                                "storageAccountType": "Standard_LRS"
                            }
                        }
                    ],
                    "imageReference": {
                        "offer": "CoreOS",
                        "publisher": "CoreOS",
                        "sku": "Stable",
                        "version": "899.17.0"
                    },
                    "osDisk": {
                        "caching": "ReadWrite",
                        "createOption": "fromImage",
                        "managedDisk": {
                            "storageAccountType": "Standard_LRS"
                        }
                    }
                }
            }
        },
        "sku": {
            "capacity": 2,
            "name": "Standard_DS1_v2",
            "tier": "Standard"
        },
        "tags": null,
        "type": "Microsoft.Compute/virtualMachineScaleSets"
    }
'''  # NOQA

import random
import re

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import parse_resource_id

except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, azure_id_to_dict


AZURE_OBJECT_CLASS = 'VirtualMachineScaleSet'

AZURE_ENUM_MODULES = ['azure.mgmt.compute.models']


class AzureRMVirtualMachineScaleSet(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
            location=dict(type='str'),
            short_hostname=dict(type='str'),
            vm_size=dict(type='str', required=True),
            tier=dict(type='str', choices=['Basic', 'Standard']),
            capacity=dict(type='int', default=1),
            upgrade_policy=dict(type='str', choices=['Automatic', 'Manual']),
            admin_username=dict(type='str'),
            admin_password=dict(type='str', no_log=True),
            ssh_password_enabled=dict(type='bool', default=True),
            ssh_public_keys=dict(type='list'),
            image=dict(type='raw'),
            os_disk_caching=dict(type='str', aliases=['disk_caching'], choices=['ReadOnly', 'ReadWrite'],
                                 default='ReadOnly'),
            os_type=dict(type='str', choices=['Linux', 'Windows'], default='Linux'),
            managed_disk_type=dict(type='str', choices=['Standard_LRS', 'Premium_LRS']),
            data_disks=dict(type='list'),
            subnet_name=dict(type='str', aliases=['subnet']),
            load_balancer=dict(type='str'),
            virtual_network_resource_group=dict(type='str'),
            virtual_network_name=dict(type='str', aliases=['virtual_network']),
            remove_on_absent=dict(type='list', default=['all']),
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.short_hostname = None
        self.vm_size = None
        self.capacity = None
        self.tier = None
        self.upgrade_policy = None
        self.admin_username = None
        self.admin_password = None
        self.ssh_password_enabled = None
        self.ssh_public_keys = None
        self.image = None
        self.os_disk_caching = None
        self.managed_disk_type = None
        self.data_disks = None
        self.os_type = None
        self.subnet_name = None
        self.virtual_network_resource_group = None
        self.virtual_network_name = None
        self.tags = None
        self.differences = None
        self.load_balancer = None

        self.results = dict(
            changed=False,
            actions=[],
            ansible_facts=dict(azure_vmss=None)
        )

        super(AzureRMVirtualMachineScaleSet, self).__init__(
            derived_arg_spec=self.module_arg_spec,
            supports_check_mode=True
        )

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        # make sure options are lower case
        self.remove_on_absent = set([resource.lower() for resource in self.remove_on_absent])

        # default virtual_network_resource_group to resource_group
        if not self.virtual_network_resource_group:
            self.virtual_network_resource_group = self.resource_group

        changed = False
        results = dict()
        vmss = None
        disable_ssh_password = None
        vmss_dict = None
        virtual_network = None
        subnet = None
        image_reference = None
        custom_image = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        if self.state == 'present':
            # Verify parameters and resolve any defaults

            if self.vm_size and not self.vm_size_is_valid():
                self.fail("Parameter error: vm_size {0} is not valid for your subscription and location.".format(
                    self.vm_size
                ))

            # if self.virtual_network_name:
            #     virtual_network = self.get_virtual_network(self.virtual_network_name)

            if self.ssh_public_keys:
                msg = "Parameter error: expecting ssh_public_keys to be a list of type dict where " \
                    "each dict contains keys: path, key_data."
                for key in self.ssh_public_keys:
                    if not isinstance(key, dict):
                        self.fail(msg)
                    if not key.get('path') or not key.get('key_data'):
                        self.fail(msg)

            if self.image and isinstance(self.image, dict):
                if all(key in self.image for key in ('publisher', 'offer', 'sku', 'version')):
                    marketplace_image = self.get_marketplace_image_version()
                    if self.image['version'] == 'latest':
                        self.image['version'] = marketplace_image.name
                        self.log("Using image version {0}".format(self.image['version']))

                    image_reference = self.compute_models.ImageReference(
                        publisher=self.image['publisher'],
                        offer=self.image['offer'],
                        sku=self.image['sku'],
                        version=self.image['version']
                    )
                elif self.image.get('name'):
                    custom_image = True
                    image_reference = self.get_custom_image_reference(
                        self.image.get('name'),
                        self.image.get('resource_group'))
                else:
                    self.fail("parameter error: expecting image to contain [publisher, offer, sku, version] or [name, resource_group]")
            elif self.image and isinstance(self.image, str):
                custom_image = True
                image_reference = self.get_custom_image_reference(self.image)
            elif self.image:
                self.fail("parameter error: expecting image to be a string or dict not {0}".format(type(self.image).__name__))

            disable_ssh_password = not self.ssh_password_enabled

        try:
            self.log("Fetching virtual machine scale set {0}".format(self.name))
            vmss = self.compute_client.virtual_machine_scale_sets.get(self.resource_group, self.name)
            self.check_provisioning_state(vmss, self.state)
            vmss_dict = self.serialize_vmss(vmss)

            if self.state == 'present':
                differences = []
                results = vmss_dict

                if self.os_disk_caching and \
                   self.os_disk_caching != vmss_dict['properties']['virtualMachineProfile']['storageProfile']['osDisk']['caching']:
                    self.log('CHANGED: virtual machine scale set {0} - OS disk caching'.format(self.name))
                    differences.append('OS Disk caching')
                    changed = True
                    vmss_dict['properties']['virtualMachineProfile']['storageProfile']['osDisk']['caching'] = self.os_disk_caching

                if self.capacity and \
                   self.capacity != vmss_dict['sku']['capacity']:
                    self.log('CHANGED: virtual machine scale set {0} - Capacity'.format(self.name))
                    differences.append('Capacity')
                    changed = True
                    vmss_dict['sku']['capacity'] = self.capacity

                if self.data_disks and \
                   len(self.data_disks) != len(vmss_dict['properties']['virtualMachineProfile']['storageProfile'].get('dataDisks', [])):
                    self.log('CHANGED: virtual machine scale set {0} - Data Disks'.format(self.name))
                    differences.append('Data Disks')
                    changed = True

                update_tags, vmss_dict['tags'] = self.update_tags(vmss_dict.get('tags', dict()))
                if update_tags:
                    differences.append('Tags')
                    changed = True

                self.differences = differences

            elif self.state == 'absent':
                self.log("CHANGED: virtual machine scale set {0} exists and requested state is 'absent'".format(self.name))
                results = dict()
                changed = True

        except CloudError:
            self.log('Virtual machine scale set {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: virtual machine scale set {0} does not exist but state is 'present'.".format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['ansible_facts']['azure_vmss'] = results

        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                if not vmss:
                    # Create the VMSS
                    self.log("Create virtual machine scale set {0}".format(self.name))
                    self.results['actions'].append('Created VMSS {0}'.format(self.name))

                    # Validate parameters
                    if not self.admin_username:
                        self.fail("Parameter error: admin_username required when creating a virtual machine scale set.")

                    if self.os_type == 'Linux':
                        if disable_ssh_password and not self.ssh_public_keys:
                            self.fail("Parameter error: ssh_public_keys required when disabling SSH password.")

                    if not self.virtual_network_name:
                        default_vnet = self.create_default_vnet()
                        virtual_network = default_vnet.id
                        self.virtual_network_name = default_vnet.name

                    if self.subnet_name:
                        subnet = self.get_subnet(self.virtual_network_name, self.subnet_name)

                    load_balancer_backend_address_pools = None
                    load_balancer_inbound_nat_pools = None
                    if self.load_balancer:
                        load_balancer = self.get_load_balancer(self.load_balancer)
                        load_balancer_backend_address_pools = ([self.compute_models.SubResource(resource.id)
                                                                for resource in load_balancer.backend_address_pools]
                                                               if load_balancer.backend_address_pools else None)
                        load_balancer_inbound_nat_pools = ([self.compute_models.SubResource(resource.id)
                                                            for resource in load_balancer.inbound_nat_pools]
                                                           if load_balancer.inbound_nat_pools else None)

                    if not self.short_hostname:
                        self.short_hostname = self.name

                    if not image_reference:
                        self.fail("Parameter error: an image is required when creating a virtual machine.")

                    managed_disk = self.compute_models.VirtualMachineScaleSetManagedDiskParameters(storage_account_type=self.managed_disk_type)

                    vmss_resource = self.compute_models.VirtualMachineScaleSet(
                        self.location,
                        tags=self.tags,
                        upgrade_policy=self.compute_models.UpgradePolicy(
                            mode=self.upgrade_policy
                        ),
                        sku=self.compute_models.Sku(
                            name=self.vm_size,
                            capacity=self.capacity,
                            tier=self.tier,
                        ),
                        virtual_machine_profile=self.compute_models.VirtualMachineScaleSetVMProfile(
                            os_profile=self.compute_models.VirtualMachineScaleSetOSProfile(
                                admin_username=self.admin_username,
                                computer_name_prefix=self.short_hostname,
                            ),
                            storage_profile=self.compute_models.VirtualMachineScaleSetStorageProfile(
                                os_disk=self.compute_models.VirtualMachineScaleSetOSDisk(
                                    managed_disk=managed_disk,
                                    create_option=self.compute_models.DiskCreateOptionTypes.from_image,
                                    caching=self.os_disk_caching,
                                ),
                                image_reference=image_reference,
                            ),
                            network_profile=self.compute_models.VirtualMachineScaleSetNetworkProfile(
                                network_interface_configurations=[
                                    self.compute_models.VirtualMachineScaleSetNetworkConfiguration(
                                        name=self.name,
                                        primary=True,
                                        ip_configurations=[
                                            self.compute_models.VirtualMachineScaleSetIPConfiguration(
                                                name='default',
                                                subnet=self.compute_models.ApiEntityReference(
                                                    id=subnet.id
                                                ),
                                                primary=True,
                                                load_balancer_backend_address_pools=load_balancer_backend_address_pools,
                                                load_balancer_inbound_nat_pools=load_balancer_inbound_nat_pools
                                            )
                                        ]
                                    )
                                ]
                            )
                        )
                    )

                    if self.admin_password:
                        vmss_resource.virtual_machine_profile.os_profile.admin_password = self.admin_password

                    if self.os_type == 'Linux':
                        vmss_resource.virtual_machine_profile.os_profile.linux_configuration = self.compute_models.LinuxConfiguration(
                            disable_password_authentication=disable_ssh_password
                        )

                    if self.ssh_public_keys:
                        ssh_config = self.compute_models.SshConfiguration()
                        ssh_config.public_keys = \
                            [self.compute_models.SshPublicKey(path=key['path'], key_data=key['key_data']) for key in self.ssh_public_keys]
                        vmss_resource.virtual_machine_profile.os_profile.linux_configuration.ssh = ssh_config

                    if self.data_disks:
                        data_disks = []

                        for data_disk in self.data_disks:
                            data_disk_managed_disk = self.compute_models.VirtualMachineScaleSetManagedDiskParameters(
                                storage_account_type=data_disk['managed_disk_type']
                            )

                            data_disk['caching'] = data_disk.get(
                                'caching',
                                self.compute_models.CachingTypes.read_only
                            )

                            data_disks.append(self.compute_models.VirtualMachineScaleSetDataDisk(
                                lun=data_disk['lun'],
                                caching=data_disk['caching'],
                                create_option=self.compute_models.DiskCreateOptionTypes.empty,
                                disk_size_gb=data_disk['disk_size_gb'],
                                managed_disk=data_disk_managed_disk,
                            ))

                        vmss_resource.virtual_machine_profile.storage_profile.data_disks = data_disks

                    self.log("Create virtual machine with parameters:")
                    self.create_or_update_vmss(vmss_resource)

                elif self.differences and len(self.differences) > 0:
                    self.log("Update virtual machine scale set {0}".format(self.name))
                    self.results['actions'].append('Updated VMSS {0}'.format(self.name))

                    vmss_resource = self.get_vmss()
                    vmss_resource.virtual_machine_profile.storage_profile.os_disk.caching = self.os_disk_caching
                    vmss_resource.sku.capacity = self.capacity

                    data_disks = []
                    for data_disk in self.data_disks:
                        data_disks.append(self.compute_models.VirtualMachineScaleSetDataDisk(
                            lun=data_disk['lun'],
                            caching=data_disk['caching'],
                            create_option=self.compute_models.DiskCreateOptionTypes.empty,
                            disk_size_gb=data_disk['disk_size_gb'],
                            managed_disk=self.compute_models.VirtualMachineScaleSetManagedDiskParameters(
                                storage_account_type=data_disk['managed_disk_type']
                            ),
                        ))
                    vmss_resource.virtual_machine_profile.storage_profile.data_disks = data_disks

                    self.log("Update virtual machine with parameters:")
                    self.create_or_update_vmss(vmss_resource)

                self.results['ansible_facts']['azure_vmss'] = self.serialize_vmss(self.get_vmss())

            elif self.state == 'absent':
                # delete the VM
                self.log("Delete virtual machine scale set {0}".format(self.name))
                self.results['ansible_facts']['azure_vmss'] = None
                self.delete_vmss(vmss)

        # until we sort out how we want to do this globally
        del self.results['actions']

        return self.results

    def get_vmss(self):
        '''
        Get the VMSS

        :return: VirtualMachineScaleSet object
        '''
        try:
            vmss = self.compute_client.virtual_machine_scale_sets.get(self.resource_group, self.name)
            return vmss
        except CloudError as exc:
            self.fail("Error getting virtual machine scale set {0} - {1}".format(self.name, str(exc)))

    def get_virtual_network(self, name):
        try:
            vnet = self.network_client.virtual_networks.get(self.virtual_network_resource_group, name)
            return vnet
        except CloudError as exc:
            self.fail("Error fetching virtual network {0} - {1}".format(name, str(exc)))

    def get_subnet(self, vnet_name, subnet_name):
        self.log("Fetching subnet {0} in virtual network {1}".format(subnet_name, vnet_name))
        try:
            subnet = self.network_client.subnets.get(self.virtual_network_resource_group, vnet_name, subnet_name)
        except CloudError as exc:
            self.fail("Error: fetching subnet {0} in virtual network {1} - {2}".format(
                subnet_name,
                vnet_name,
                str(exc)))
        return subnet

    def get_load_balancer(self, id):
        id_dict = parse_resource_id(id)
        try:
            return self.network_client.load_balancers.get(id_dict.get('resource_group', self.resource_group), id_dict.get('name'))
        except CloudError as exc:
            self.fail("Error fetching load balancer {0} - {1}".format(id, str(exc)))

    def serialize_vmss(self, vmss):
        '''
        Convert a VirtualMachineScaleSet object to dict.

        :param vm: VirtualMachineScaleSet object
        :return: dict
        '''

        result = self.serialize_obj(vmss, AZURE_OBJECT_CLASS, enum_modules=AZURE_ENUM_MODULES)
        result['id'] = vmss.id
        result['name'] = vmss.name
        result['type'] = vmss.type
        result['location'] = vmss.location
        result['tags'] = vmss.tags

        return result

    def delete_vmss(self, vmss):
        self.log("Deleting virtual machine scale set {0}".format(self.name))
        self.results['actions'].append("Deleted virtual machine scale set {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machine_scale_sets.delete(self.resource_group, self.name)
            # wait for the poller to finish
            self.get_poller_result(poller)
        except CloudError as exc:
            self.fail("Error deleting virtual machine scale set {0} - {1}".format(self.name, str(exc)))

        return True

    def get_marketplace_image_version(self):
        try:
            versions = self.compute_client.virtual_machine_images.list(self.location,
                                                                       self.image['publisher'],
                                                                       self.image['offer'],
                                                                       self.image['sku'])
        except CloudError as exc:
            self.fail("Error fetching image {0} {1} {2} - {3}".format(self.image['publisher'],
                                                                      self.image['offer'],
                                                                      self.image['sku'],
                                                                      str(exc)))
        if versions and len(versions) > 0:
            if self.image['version'] == 'latest':
                return versions[len(versions) - 1]
            for version in versions:
                if version.name == self.image['version']:
                    return version

        self.fail("Error could not find image {0} {1} {2} {3}".format(self.image['publisher'],
                                                                      self.image['offer'],
                                                                      self.image['sku'],
                                                                      self.image['version']))

    def get_custom_image_reference(self, name, resource_group=None):
        try:
            if resource_group:
                vm_images = self.compute_client.images.list_by_resource_group(resource_group)
            else:
                vm_images = self.compute_client.images.list()
        except Exception as exc:
            self.fail("Error fetching custom images from subscription - {0}".format(str(exc)))

        for vm_image in vm_images:
            if vm_image.name == name:
                self.log("Using custom image id {0}".format(vm_image.id))
                return self.compute_models.ImageReference(id=vm_image.id)

        self.fail("Error could not find image with name {0}".format(name))

    def create_or_update_vmss(self, params):
        try:
            poller = self.compute_client.virtual_machine_scale_sets.create_or_update(self.resource_group, self.name, params)
            self.get_poller_result(poller)
        except CloudError as exc:
            self.fail("Error creating or updating virtual machine {0} - {1}".format(self.name, str(exc)))

    def vm_size_is_valid(self):
        '''
        Validate self.vm_size against the list of virtual machine sizes available for the account and location.

        :return: boolean
        '''
        try:
            sizes = self.compute_client.virtual_machine_sizes.list(self.location)
        except CloudError as exc:
            self.fail("Error retrieving available machine sizes - {0}".format(str(exc)))
        for size in sizes:
            if size.name == self.vm_size:
                return True
        return False


def main():
    AzureRMVirtualMachineScaleSet()

if __name__ == '__main__':
    main()
