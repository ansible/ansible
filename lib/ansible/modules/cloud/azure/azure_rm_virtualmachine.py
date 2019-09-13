#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualmachine

version_added: "2.1"

short_description: Manage Azure virtual machines.

description:
    - Create, update, stop and start a virtual machine. Provide an existing storage account and network interface or
      allow the module to create these for you. If you choose not to provide a network interface, the resource group
      must contain a virtual network with at least one subnet.
    - Before Ansible 2.5, this required an image found in the Azure Marketplace which can be discovered with
      M(azure_rm_virtualmachineimage_facts). In Ansible 2.5 and newer, custom images can be used as well, see the
      examples for more details.
    - If you need to use the I(custom_data) option, many images in the marketplace are not cloud-init ready. Thus, data
      sent to I(custom_data) would be ignored. If the image you are attempting to use is not listed in
      U(https://docs.microsoft.com/en-us/azure/virtual-machines/linux/using-cloud-init#cloud-init-overview),
      follow these steps U(https://docs.microsoft.com/en-us/azure/virtual-machines/linux/cloudinit-prepare-custom-image).

options:
    resource_group:
        description:
            - Name of the resource group containing the virtual machine.
        required: true
    name:
        description:
            - Name of the virtual machine.
        required: true
    custom_data:
        description:
            - Data which is made available to the virtual machine and used by e.g., cloud-init.
        version_added: "2.5"
    state:
        description:
            - Assert the state of the virtual machine.
            - State C(present) will check that the machine exists with the requested configuration. If the configuration
              of the existing machine does not match, the machine will be updated. Use options started, allocated and restarted to change the machine's power
              state.
            - State C(absent) will remove the virtual machine.
        default: present
        choices:
            - absent
            - present
    started:
        description:
            - Use with state C(present) to start the machine. Set to false to have the machine be 'stopped'.
        default: true
        type: bool
    allocated:
        description:
            - Toggle that controls if the machine is allocated/deallocated, only useful with state='present'.
        default: True
        type: bool
    generalized:
        description:
            - Use with state C(present) to generalize the machine. Set to true to generalize the machine.
            - Please note that this operation is irreversible.
        type: bool
        version_added: "2.8"
    restarted:
        description:
            - Use with state C(present) to restart a running VM.
        type: bool
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
    short_hostname:
        description:
            - Name assigned internally to the host. On a linux VM this is the name returned by the `hostname` command.
              When creating a virtual machine, short_hostname defaults to name.
    vm_size:
        description:
            - A valid Azure VM size value. For example, 'Standard_D4'. The list of choices varies depending on the
              subscription and location. Check your subscription for available choices. Required when creating a VM.
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
        default: true
        type: bool
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
              and if omitted, all images in the subscription will be searched
              for by C(name).'
            - Custom image support was added in Ansible 2.5
        required: true
    availability_set:
        description:
            - Name or ID of an existing availability set to add the VM to. The availability_set should be in the same resource group as VM.
        version_added: "2.5"
    storage_account_name:
        description:
            - Name of an existing storage account that supports creation of VHD blobs. If not specified for a new VM,
              a new storage account named <vm name>01 will be created using storage type 'Standard_LRS'.
        aliases:
            - storage_account
    storage_container_name:
        description:
            - Name of the container to use within the storage account to store VHD blobs. If no name is specified a
              default container will created.
        default: vhds
        aliases:
            - storage_container
    storage_blob_name:
        description:
            - Name of the storage blob used to hold the VM's OS disk image. If no name is provided, defaults to
              the VM name + '.vhd'. If you provide a name, it must end with '.vhd'
        aliases:
            - storage_blob
    managed_disk_type:
        description:
            - Managed OS disk type
        choices:
            - Standard_LRS
            - StandardSSD_LRS
            - Premium_LRS
        version_added: "2.4"
    os_disk_name:
        description:
            - OS disk name
        version_added: "2.8"
    os_disk_caching:
        description:
            - Type of OS disk caching.
        choices:
            - ReadOnly
            - ReadWrite
        default: ReadOnly
        aliases:
            - disk_caching
    os_disk_size_gb:
        description:
            - Type of OS disk size in GB.
        version_added: "2.7"
    os_type:
        description:
            - Base type of operating system.
        choices:
            - Windows
            - Linux
        default: Linux
    data_disks:
        description:
            - Describes list of data disks.
        version_added: "2.4"
        suboptions:
            lun:
                description:
                    - The logical unit number for data disk
                default: 0
                version_added: "2.4"
            disk_size_gb:
                description:
                    - The initial disk size in GB for blank data disks
                version_added: "2.4"
            managed_disk_type:
                description:
                    - Managed data disk type
                choices:
                    - Standard_LRS
                    - StandardSSD_LRS
                    - Premium_LRS
                version_added: "2.4"
            storage_account_name:
                description:
                    - Name of an existing storage account that supports creation of VHD blobs. If not specified for a new VM,
                      a new storage account named <vm name>01 will be created using storage type 'Standard_LRS'.
                version_added: "2.4"
            storage_container_name:
                description:
                    - Name of the container to use within the storage account to store VHD blobs. If no name is specified a
                      default container will created.
                default: vhds
                version_added: "2.4"
            storage_blob_name:
                description:
                    - Name fo the storage blob used to hold the VM's OS disk image. If no name is provided, defaults to
                      the VM name + '.vhd'. If you provide a name, it must end with '.vhd'
                version_added: "2.4"
            caching:
                description:
                    - Type of data disk caching.
                choices:
                    - ReadOnly
                    - ReadWrite
                default: ReadOnly
                version_added: "2.4"
    public_ip_allocation_method:
        description:
            - If a public IP address is created when creating the VM (because a Network Interface was not provided),
              determines if the public IP address remains permanently associated with the Network Interface. If set
              to 'Dynamic' the public IP address may change any time the VM is rebooted or power cycled.
            - The C(Disabled) choice was added in Ansible 2.6.
        choices:
            - Dynamic
            - Static
            - Disabled
        default: Static
        aliases:
            - public_ip_allocation
    open_ports:
        description:
            - If a network interface is created when creating the VM, a security group will be created as well. For
              Linux hosts a rule will be added to the security group allowing inbound TCP connections to the default
              SSH port 22, and for Windows hosts ports 3389 and 5986 will be opened. Override the default open ports by
              providing a list of ports.
    network_interface_names:
        description:
            - List of existing network interface names to add to the VM.
            - Item can be a str of name or resource id of the network interface.
            - Item can also be a dict contains C(resource_group) and C(name) of the network interface.
            - If a network interface name is not provided when the VM is created, a default network interface will be created.
            - In order for the module to create a new network interface, at least one Virtual Network with one Subnet must exist.
        aliases:
            - network_interfaces
    virtual_network_resource_group:
        description:
            - When creating a virtual machine, if a specific virtual network from another resource group should be
              used, use this parameter to specify the resource group to use.
        version_added: "2.4"
    virtual_network_name:
        description:
            - When creating a virtual machine, if a network interface name is not provided, one will be created.
            - The network interface will be assigned to the first virtual network found in the resource group.
            - Use this parameter to provide a specific virtual network instead.
            - If the virtual network in in another resource group, specific resource group by C(virtual_network_resource_group).
        aliases:
            - virtual_network
    subnet_name:
        description:
            - When creating a virtual machine, if a network interface name is not provided, one will be created.
            - The new network interface will be assigned to the first subnet found in the virtual network.
            - Use this parameter to provide a specific subnet instead.
            - If the subnet is in another resource group, specific resource group by C(virtual_network_resource_group).
        aliases:
            - subnet
    remove_on_absent:
        description:
            - "When removing a VM using state 'absent', also remove associated resources."
            - "It can be 'all' or 'all_autocreated' or  a list with any of the following: ['network_interfaces', 'virtual_storage', 'public_ips']."
            - "To remove all resources referred by VM use 'all'."
            - "To remove all resources that were automatically created while provisioning VM use 'all_autocreated'."
            - Any other input will be ignored.
        default: ['all']
    plan:
        description:
            - A dictionary describing a third-party billing plan for an instance
        version_added: 2.5
        suboptions:
            name:
                description:
                    - billing plan name
                required: true
            product:
                description:
                    - product name
                required: true
            publisher:
                description:
                    - publisher offering the plan
                required: true
            promotion_code:
                description:
                    - optional promotion code
    accept_terms:
        description:
            - Accept terms for marketplace images that require it
            - Only Azure service admin/account admin users can purchase images from the marketplace
        type: bool
        default: false
        version_added: "2.7"
    zones:
        description:
            - A list of Availability Zones for your virtual machine
        type: list
        version_added: "2.8"
    license_type:
        description:
            - Specifies that the image or disk that is being used was licensed on-premises. This element is only
              used for images that contain the Windows Server operating system.
            - "Note: To unset this value, it has to be set to the string 'None'."
        version_added: 2.8
        choices:
            - Windows_Server
            - Windows_Client
    vm_identity:
        description:
            - Identity for the virtual machine.
        version_added: 2.8
        choices:
            - SystemAssigned
    winrm:
        description:
            - List of Windows Remote Management configurations of the VM.
        version_added: 2.8
        suboptions:
            protocol:
                description:
                    - Specifies the protocol of listener
                required: true
                choices:
                    - http
                    - https
            source_vault:
                description:
                    - The relative URL of the Key Vault containing the certificate
            certificate_url:
                description:
                    - This is the URL of a certificate that has been uploaded to Key Vault as a secret.
            certificate_store:
                description:
                    - Specifies the certificate store on the Virtual Machine to which the certificate
                      should be added. The specified certificate store is implicitly in the LocalMachine account.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"
    - "Christopher Perrin (@cperrin88)"

'''
EXAMPLES = '''

- name: Create VM with defaults
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm10
    admin_username: chouseknecht
    admin_password: <your password here>
    image:
      offer: CentOS
      publisher: OpenLogic
      sku: '7.1'
      version: latest

- name: Create an availability set for managed disk vm
  azure_rm_availabilityset:
    name: avs-managed-disk
    resource_group: myResourceGroup
    platform_update_domain_count: 5
    platform_fault_domain_count: 2
    sku: Aligned

- name: Create a VM with managed disk
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: vm-managed-disk
    admin_username: adminUser
    availability_set: avs-managed-disk
    managed_disk_type: Standard_LRS
    image:
      offer: CoreOS
      publisher: CoreOS
      sku: Stable
      version: latest
    vm_size: Standard_D4

- name: Create a VM with existing storage account and NIC
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm002
    vm_size: Standard_D4
    storage_account: testaccount001
    admin_username: adminUser
    ssh_public_keys:
      - path: /home/adminUser/.ssh/authorized_keys
        key_data: < insert yor ssh public key here... >
    network_interfaces: testvm001
    image:
      offer: CentOS
      publisher: OpenLogic
      sku: '7.1'
      version: latest

- name: Create a VM with OS and multiple data managed disks
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm001
    vm_size: Standard_D4
    managed_disk_type: Standard_LRS
    admin_username: adminUser
    ssh_public_keys:
      - path: /home/adminUser/.ssh/authorized_keys
        key_data: < insert yor ssh public key here... >
    image:
      offer: CoreOS
      publisher: CoreOS
      sku: Stable
      version: latest
    data_disks:
        - lun: 0
          disk_size_gb: 64
          managed_disk_type: Standard_LRS
        - lun: 1
          disk_size_gb: 128
          managed_disk_type: Premium_LRS

- name: Create a VM with OS and multiple data storage accounts
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm001
    vm_size: Standard_DS1_v2
    admin_username: adminUser
    ssh_password_enabled: false
    ssh_public_keys:
    - path: /home/adminUser/.ssh/authorized_keys
      key_data: < insert yor ssh public key here... >
    network_interfaces: testvm001
    storage_container: osdisk
    storage_blob: osdisk.vhd
    image:
      offer: CoreOS
      publisher: CoreOS
      sku: Stable
      version: latest
    data_disks:
    - lun: 0
      disk_size_gb: 64
      storage_container_name: datadisk1
      storage_blob_name: datadisk1.vhd
    - lun: 1
      disk_size_gb: 128
      storage_container_name: datadisk2
      storage_blob_name: datadisk2.vhd

- name: Create a VM with a custom image
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm001
    vm_size: Standard_DS1_v2
    admin_username: adminUser
    admin_password: password01
    image: customimage001

- name: Create a VM with a custom image from a particular resource group
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm001
    vm_size: Standard_DS1_v2
    admin_username: adminUser
    admin_password: password01
    image:
      name: customimage001
      resource_group: myResourceGroup

- name: Create VM with spcified OS disk size
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: big-os-disk
    admin_username: chouseknecht
    admin_password: <your password here>
    os_disk_size_gb: 512
    image:
      offer: CentOS
      publisher: OpenLogic
      sku: '7.1'
      version: latest

- name: Create VM with OS and Plan, accepting the terms
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: f5-nva
    admin_username: chouseknecht
    admin_password: <your password here>
    image:
      publisher: f5-networks
      offer: f5-big-ip-best
      sku: f5-bigip-virtual-edition-200m-best-hourly
      version: latest
    plan:
      name: f5-bigip-virtual-edition-200m-best-hourly
      product: f5-big-ip-best
      publisher: f5-networks

- name: Power Off
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm002
    started: no

- name: Deallocate
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm002
    allocated: no

- name: Power On
  azure_rm_virtualmachine:
    resource_group:
    name: testvm002

- name: Restart
  azure_rm_virtualmachine:
    resource_group:
    name: testvm002
    restarted: yes

- name: Create a VM with an Availability Zone
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm001
    vm_size: Standard_DS1_v2
    admin_username: adminUser
    admin_password: password01
    image: customimage001
    zones: [1]

- name: Remove a VM and all resources that were autocreated
  azure_rm_virtualmachine:
    resource_group: myResourceGroup
    name: testvm002
    remove_on_absent: all_autocreated
    state: absent
'''

RETURN = '''
powerstate:
    description: Indicates if the state is running, stopped, deallocated, generalized
    returned: always
    type: str
    example: running
deleted_vhd_uris:
    description: List of deleted Virtual Hard Disk URIs.
    returned: 'on delete'
    type: list
    example: ["https://testvm104519.blob.core.windows.net/vhds/testvm10.vhd"]
deleted_network_interfaces:
    description: List of deleted NICs.
    returned: 'on delete'
    type: list
    example: ["testvm1001"]
deleted_public_ips:
    description: List of deleted public IP address names.
    returned: 'on delete'
    type: list
    example: ["testvm1001"]
azure_vm:
    description: Facts about the current state of the object. Note that facts are not part of the registered output but available directly.
    returned: always
    type: complex
    contains: {
        "properties": {
            "availabilitySet": {
                    "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Compute/availabilitySets/MYAVAILABILITYSET"
            },
            "hardwareProfile": {
                "vmSize": "Standard_D1"
            },
            "instanceView": {
                "disks": [
                    {
                        "name": "testvm10.vhd",
                        "statuses": [
                            {
                                "code": "ProvisioningState/succeeded",
                                "displayStatus": "Provisioning succeeded",
                                "level": "Info",
                                "time": "2016-03-30T07:11:16.187272Z"
                            }
                        ]
                    }
                ],
                "statuses": [
                    {
                        "code": "ProvisioningState/succeeded",
                        "displayStatus": "Provisioning succeeded",
                        "level": "Info",
                        "time": "2016-03-30T20:33:38.946916Z"
                    },
                    {
                        "code": "PowerState/running",
                        "displayStatus": "VM running",
                        "level": "Info"
                    }
                ],
                "vmAgent": {
                    "extensionHandlers": [],
                    "statuses": [
                        {
                            "code": "ProvisioningState/succeeded",
                            "displayStatus": "Ready",
                            "level": "Info",
                            "message": "GuestAgent is running and accepting new configurations.",
                            "time": "2016-03-30T20:31:16.000Z"
                        }
                    ],
                    "vmAgentVersion": "WALinuxAgent-2.0.16"
                }
            },
            "networkProfile": {
                "networkInterfaces": [
                    {
                        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkInterfaces/testvm10_NIC01",
                        "name": "testvm10_NIC01",
                        "properties": {
                            "dnsSettings": {
                                "appliedDnsServers": [],
                                "dnsServers": []
                            },
                            "enableIPForwarding": false,
                            "ipConfigurations": [
                                {
                                    "etag": 'W/"041c8c2a-d5dd-4cd7-8465-9125cfbe2cf8"',
                                    "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkInterfaces/testvm10_NIC01/ipConfigurations/default",
                                    "name": "default",
                                    "properties": {
                                        "privateIPAddress": "10.10.0.5",
                                        "privateIPAllocationMethod": "Dynamic",
                                        "provisioningState": "Succeeded",
                                        "publicIPAddress": {
                                            "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/publicIPAddresses/testvm10_PIP01",
                                            "name": "testvm10_PIP01",
                                            "properties": {
                                                "idleTimeoutInMinutes": 4,
                                                "ipAddress": "13.92.246.197",
                                                "ipConfiguration": {
                                                    "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkInterfaces/testvm10_NIC01/ipConfigurations/default"
                                                },
                                                "provisioningState": "Succeeded",
                                                "publicIPAllocationMethod": "Static",
                                                "resourceGuid": "3447d987-ca0d-4eca-818b-5dddc0625b42"
                                            }
                                        }
                                    }
                                }
                            ],
                            "macAddress": "00-0D-3A-12-AA-14",
                            "primary": true,
                            "provisioningState": "Succeeded",
                            "resourceGuid": "10979e12-ccf9-42ee-9f6d-ff2cc63b3844",
                            "virtualMachine": {
                                "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Compute/virtualMachines/testvm10"
                            }
                        }
                    }
                ]
            },
            "osProfile": {
                "adminUsername": "chouseknecht",
                "computerName": "test10",
                "linuxConfiguration": {
                    "disablePasswordAuthentication": false
                },
                "secrets": []
            },
            "provisioningState": "Succeeded",
            "storageProfile": {
                "dataDisks": [
                    {
                        "caching": "ReadWrite",
                        "createOption": "empty",
                        "diskSizeGB": 64,
                        "lun": 0,
                        "name": "datadisk1.vhd",
                        "vhd": {
                            "uri": "https://testvm10sa1.blob.core.windows.net/datadisk/datadisk1.vhd"
                        }
                    }
                ],
                "imageReference": {
                    "offer": "CentOS",
                    "publisher": "OpenLogic",
                    "sku": "7.1",
                    "version": "7.1.20160308"
                },
                "osDisk": {
                    "caching": "ReadOnly",
                    "createOption": "fromImage",
                    "name": "testvm10.vhd",
                    "osType": "Linux",
                    "vhd": {
                        "uri": "https://testvm10sa1.blob.core.windows.net/vhds/testvm10.vhd"
                    }
                }
            }
        },
        "type": "Microsoft.Compute/virtualMachines"
    }
'''  # NOQA

import base64
import random
import re

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import parse_resource_id
    from msrest.polling import LROPoller
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.basic import to_native, to_bytes
from ansible.module_utils.azure_rm_common import AzureRMModuleBase, azure_id_to_dict, normalize_location_name, format_resource_id


AZURE_OBJECT_CLASS = 'VirtualMachine'

AZURE_ENUM_MODULES = ['azure.mgmt.compute.models']


def extract_names_from_blob_uri(blob_uri, storage_suffix):
    # HACK: ditch this once python SDK supports get by URI
    m = re.match(r'^https://(?P<accountname>[^.]+)\.blob\.{0}/'
                 r'(?P<containername>[^/]+)/(?P<blobname>.+)$'.format(storage_suffix), blob_uri)
    if not m:
        raise Exception("unable to parse blob uri '%s'" % blob_uri)
    extracted_names = m.groupdict()
    return extracted_names


class AzureRMVirtualMachine(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            custom_data=dict(type='str'),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
            location=dict(type='str'),
            short_hostname=dict(type='str'),
            vm_size=dict(type='str'),
            admin_username=dict(type='str'),
            admin_password=dict(type='str', no_log=True),
            ssh_password_enabled=dict(type='bool', default=True),
            ssh_public_keys=dict(type='list'),
            image=dict(type='raw'),
            availability_set=dict(type='str'),
            storage_account_name=dict(type='str', aliases=['storage_account']),
            storage_container_name=dict(type='str', aliases=['storage_container'], default='vhds'),
            storage_blob_name=dict(type='str', aliases=['storage_blob']),
            os_disk_caching=dict(type='str', aliases=['disk_caching'], choices=['ReadOnly', 'ReadWrite'],
                                 default='ReadOnly'),
            os_disk_size_gb=dict(type='int'),
            managed_disk_type=dict(type='str', choices=['Standard_LRS', 'StandardSSD_LRS', 'Premium_LRS']),
            os_disk_name=dict(type='str'),
            os_type=dict(type='str', choices=['Linux', 'Windows'], default='Linux'),
            public_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static', 'Disabled'], default='Static',
                                             aliases=['public_ip_allocation']),
            open_ports=dict(type='list'),
            network_interface_names=dict(type='list', aliases=['network_interfaces'], elements='raw'),
            remove_on_absent=dict(type='list', default=['all']),
            virtual_network_resource_group=dict(type='str'),
            virtual_network_name=dict(type='str', aliases=['virtual_network']),
            subnet_name=dict(type='str', aliases=['subnet']),
            allocated=dict(type='bool', default=True),
            restarted=dict(type='bool', default=False),
            started=dict(type='bool', default=True),
            generalized=dict(type='bool', default=False),
            data_disks=dict(type='list'),
            plan=dict(type='dict'),
            zones=dict(type='list'),
            accept_terms=dict(type='bool', default=False),
            license_type=dict(type='str', choices=['Windows_Server', 'Windows_Client']),
            vm_identity=dict(type='str', choices=['SystemAssigned']),
            winrm=dict(type='list')
        )

        self.resource_group = None
        self.name = None
        self.custom_data = None
        self.state = None
        self.location = None
        self.short_hostname = None
        self.vm_size = None
        self.admin_username = None
        self.admin_password = None
        self.ssh_password_enabled = None
        self.ssh_public_keys = None
        self.image = None
        self.availability_set = None
        self.storage_account_name = None
        self.storage_container_name = None
        self.storage_blob_name = None
        self.os_type = None
        self.os_disk_caching = None
        self.os_disk_size_gb = None
        self.managed_disk_type = None
        self.os_disk_name = None
        self.network_interface_names = None
        self.remove_on_absent = set()
        self.tags = None
        self.force = None
        self.public_ip_allocation_method = None
        self.open_ports = None
        self.virtual_network_resource_group = None
        self.virtual_network_name = None
        self.subnet_name = None
        self.allocated = None
        self.restarted = None
        self.started = None
        self.generalized = None
        self.differences = None
        self.data_disks = None
        self.plan = None
        self.accept_terms = None
        self.zones = None
        self.license_type = None
        self.vm_identity = None

        self.results = dict(
            changed=False,
            actions=[],
            powerstate_change=None,
            ansible_facts=dict(azure_vm=None)
        )

        super(AzureRMVirtualMachine, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        # make sure options are lower case
        self.remove_on_absent = set([resource.lower() for resource in self.remove_on_absent])

        # convert elements to ints
        self.zones = [int(i) for i in self.zones] if self.zones else None

        changed = False
        powerstate_change = None
        results = dict()
        vm = None
        network_interfaces = []
        requested_vhd_uri = None
        data_disk_requested_vhd_uri = None
        disable_ssh_password = None
        vm_dict = None
        image_reference = None
        custom_image = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        self.location = normalize_location_name(self.location)

        if self.state == 'present':
            # Verify parameters and resolve any defaults

            if self.vm_size and not self.vm_size_is_valid():
                self.fail("Parameter error: vm_size {0} is not valid for your subscription and location.".format(
                    self.vm_size
                ))

            if self.network_interface_names:
                for nic_name in self.network_interface_names:
                    nic = self.parse_network_interface(nic_name)
                    network_interfaces.append(nic)

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

            if self.plan:
                if not self.plan.get('name') or not self.plan.get('product') or not self.plan.get('publisher'):
                    self.fail("parameter error: plan must include name, product, and publisher")

            if not self.storage_blob_name and not self.managed_disk_type:
                self.storage_blob_name = self.name + '.vhd'
            elif self.managed_disk_type:
                self.storage_blob_name = self.name

            if self.storage_account_name and not self.managed_disk_type:
                properties = self.get_storage_account(self.storage_account_name)

                requested_vhd_uri = '{0}{1}/{2}'.format(properties.primary_endpoints.blob,
                                                        self.storage_container_name,
                                                        self.storage_blob_name)

            disable_ssh_password = not self.ssh_password_enabled

        try:
            self.log("Fetching virtual machine {0}".format(self.name))
            vm = self.compute_client.virtual_machines.get(self.resource_group, self.name, expand='instanceview')
            self.check_provisioning_state(vm, self.state)
            vm_dict = self.serialize_vm(vm)

            if self.state == 'present':
                differences = []
                current_nics = []
                results = vm_dict

                # Try to determine if the VM needs to be updated
                if self.network_interface_names:
                    for nic in vm_dict['properties']['networkProfile']['networkInterfaces']:
                        current_nics.append(nic['id'])

                    if set(current_nics) != set(network_interfaces):
                        self.log('CHANGED: virtual machine {0} - network interfaces are different.'.format(self.name))
                        differences.append('Network Interfaces')
                        updated_nics = [dict(id=id, primary=(i == 0))
                                        for i, id in enumerate(network_interfaces)]
                        vm_dict['properties']['networkProfile']['networkInterfaces'] = updated_nics
                        changed = True

                if self.os_disk_caching and \
                   self.os_disk_caching != vm_dict['properties']['storageProfile']['osDisk']['caching']:
                    self.log('CHANGED: virtual machine {0} - OS disk caching'.format(self.name))
                    differences.append('OS Disk caching')
                    changed = True
                    vm_dict['properties']['storageProfile']['osDisk']['caching'] = self.os_disk_caching

                if self.os_disk_name and \
                   self.os_disk_name != vm_dict['properties']['storageProfile']['osDisk']['name']:
                    self.log('CHANGED: virtual machine {0} - OS disk name'.format(self.name))
                    differences.append('OS Disk name')
                    changed = True
                    vm_dict['properties']['storageProfile']['osDisk']['name'] = self.os_disk_name

                if self.os_disk_size_gb and \
                   self.os_disk_size_gb != vm_dict['properties']['storageProfile']['osDisk'].get('diskSizeGB'):
                    self.log('CHANGED: virtual machine {0} - OS disk size '.format(self.name))
                    differences.append('OS Disk size')
                    changed = True
                    vm_dict['properties']['storageProfile']['osDisk']['diskSizeGB'] = self.os_disk_size_gb

                if self.vm_size and \
                   self.vm_size != vm_dict['properties']['hardwareProfile']['vmSize']:
                    self.log('CHANGED: virtual machine {0} - size '.format(self.name))
                    differences.append('VM size')
                    changed = True
                    vm_dict['properties']['hardwareProfile']['vmSize'] = self.vm_size

                update_tags, vm_dict['tags'] = self.update_tags(vm_dict.get('tags', dict()))
                if update_tags:
                    differences.append('Tags')
                    changed = True

                if self.short_hostname and self.short_hostname != vm_dict['properties']['osProfile']['computerName']:
                    self.log('CHANGED: virtual machine {0} - short hostname'.format(self.name))
                    differences.append('Short Hostname')
                    changed = True
                    vm_dict['properties']['osProfile']['computerName'] = self.short_hostname

                if self.started and vm_dict['powerstate'] not in ['starting', 'running'] and self.allocated:
                    self.log("CHANGED: virtual machine {0} not running and requested state 'running'".format(self.name))
                    changed = True
                    powerstate_change = 'poweron'
                elif self.state == 'present' and vm_dict['powerstate'] == 'running' and self.restarted:
                    self.log("CHANGED: virtual machine {0} {1} and requested state 'restarted'"
                             .format(self.name, vm_dict['powerstate']))
                    changed = True
                    powerstate_change = 'restarted'
                elif self.state == 'present' and not self.allocated and vm_dict['powerstate'] not in ['deallocated', 'deallocating']:
                    self.log("CHANGED: virtual machine {0} {1} and requested state 'deallocated'"
                             .format(self.name, vm_dict['powerstate']))
                    changed = True
                    powerstate_change = 'deallocated'
                elif not self.started and vm_dict['powerstate'] == 'running':
                    self.log("CHANGED: virtual machine {0} running and requested state 'stopped'".format(self.name))
                    changed = True
                    powerstate_change = 'poweroff'
                elif self.generalized and vm_dict['powerstate'] != 'generalized':
                    self.log("CHANGED: virtual machine {0} requested to be 'generalized'".format(self.name))
                    changed = True
                    powerstate_change = 'generalized'

                vm_dict['zones'] = [int(i) for i in vm_dict['zones']] if 'zones' in vm_dict and vm_dict['zones'] else None
                if self.zones != vm_dict['zones']:
                    self.log("CHANGED: virtual machine {0} zones".format(self.name))
                    differences.append('Zones')
                    changed = True

                if self.license_type is not None and vm_dict['properties'].get('licenseType') != self.license_type:
                    differences.append('License Type')
                    changed = True
                self.differences = differences

            elif self.state == 'absent':
                self.log("CHANGED: virtual machine {0} exists and requested state is 'absent'".format(self.name))
                results = dict()
                changed = True

        except CloudError:
            self.log('Virtual machine {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: virtual machine {0} does not exist but state is 'present'.".format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['ansible_facts']['azure_vm'] = results
        self.results['powerstate_change'] = powerstate_change

        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
                default_storage_account = None
                if not vm:
                    # Create the VM
                    self.log("Create virtual machine {0}".format(self.name))
                    self.results['actions'].append('Created VM {0}'.format(self.name))

                    # Validate parameters
                    if not self.admin_username:
                        self.fail("Parameter error: admin_username required when creating a virtual machine.")

                    if self.os_type == 'Linux':
                        if disable_ssh_password and not self.ssh_public_keys:
                            self.fail("Parameter error: ssh_public_keys required when disabling SSH password.")

                    if not image_reference:
                        self.fail("Parameter error: an image is required when creating a virtual machine.")

                    availability_set_resource = None
                    if self.availability_set:
                        parsed_availability_set = parse_resource_id(self.availability_set)
                        availability_set = self.get_availability_set(parsed_availability_set.get('resource_group', self.resource_group),
                                                                     parsed_availability_set.get('name'))
                        availability_set_resource = self.compute_models.SubResource(id=availability_set.id)

                        if self.zones:
                            self.fail("Parameter error: you can't use Availability Set and Availability Zones at the same time")

                    # Get defaults
                    if not self.network_interface_names:
                        default_nic = self.create_default_nic()
                        self.log("network interface:")
                        self.log(self.serialize_obj(default_nic, 'NetworkInterface'), pretty_print=True)
                        network_interfaces = [default_nic.id]

                    # os disk
                    if not self.storage_account_name and not self.managed_disk_type:
                        storage_account = self.create_default_storage_account()
                        self.log("storage account:")
                        self.log(self.serialize_obj(storage_account, 'StorageAccount'), pretty_print=True)
                        requested_vhd_uri = 'https://{0}.blob.{1}/{2}/{3}'.format(
                            storage_account.name,
                            self._cloud_environment.suffixes.storage_endpoint,
                            self.storage_container_name,
                            self.storage_blob_name)
                        default_storage_account = storage_account  # store for use by data disks if necessary

                    if not self.short_hostname:
                        self.short_hostname = self.name

                    nics = [self.compute_models.NetworkInterfaceReference(id=id, primary=(i == 0))
                            for i, id in enumerate(network_interfaces)]

                    # os disk
                    if self.managed_disk_type:
                        vhd = None
                        managed_disk = self.compute_models.ManagedDiskParameters(storage_account_type=self.managed_disk_type)
                    elif custom_image:
                        vhd = None
                        managed_disk = None
                    else:
                        vhd = self.compute_models.VirtualHardDisk(uri=requested_vhd_uri)
                        managed_disk = None

                    plan = None
                    if self.plan:
                        plan = self.compute_models.Plan(name=self.plan.get('name'), product=self.plan.get('product'),
                                                        publisher=self.plan.get('publisher'),
                                                        promotion_code=self.plan.get('promotion_code'))

                    license_type = self.license_type

                    vm_resource = self.compute_models.VirtualMachine(
                        location=self.location,
                        tags=self.tags,
                        os_profile=self.compute_models.OSProfile(
                            admin_username=self.admin_username,
                            computer_name=self.short_hostname,
                        ),
                        hardware_profile=self.compute_models.HardwareProfile(
                            vm_size=self.vm_size
                        ),
                        storage_profile=self.compute_models.StorageProfile(
                            os_disk=self.compute_models.OSDisk(
                                name=self.os_disk_name if self.os_disk_name else self.storage_blob_name,
                                vhd=vhd,
                                managed_disk=managed_disk,
                                create_option=self.compute_models.DiskCreateOptionTypes.from_image,
                                caching=self.os_disk_caching,
                                disk_size_gb=self.os_disk_size_gb
                            ),
                            image_reference=image_reference,
                        ),
                        network_profile=self.compute_models.NetworkProfile(
                            network_interfaces=nics
                        ),
                        availability_set=availability_set_resource,
                        plan=plan,
                        zones=self.zones,
                    )

                    if self.license_type is not None:
                        vm_resource.license_type = self.license_type

                    if self.vm_identity:
                        vm_resource.identity = self.compute_models.VirtualMachineIdentity(type=self.vm_identity)

                    if self.winrm:
                        winrm_listeners = list()
                        for winrm_listener in self.winrm:
                            winrm_listeners.append(self.compute_models.WinRMListener(
                                protocol=winrm_listener.get('protocol'),
                                certificate_url=winrm_listener.get('certificate_url')
                            ))
                            if winrm_listener.get('source_vault'):
                                if not vm_resource.os_profile.secrets:
                                    vm_resource.os_profile.secrets = list()

                                vm_resource.os_profile.secrets.append(self.compute_models.VaultSecretGroup(
                                    source_vault=self.compute_models.SubResource(
                                        id=winrm_listener.get('source_vault')
                                    ),
                                    vault_certificates=[
                                        self.compute_models.VaultCertificate(
                                            certificate_url=winrm_listener.get('certificate_url'),
                                            certificate_store=winrm_listener.get('certificate_store')
                                        ),
                                    ]
                                ))

                        winrm = self.compute_models.WinRMConfiguration(
                            listeners=winrm_listeners
                        )

                        if not vm_resource.os_profile.windows_configuration:
                            vm_resource.os_profile.windows_configuration = self.compute_models.WindowsConfiguration(
                                win_rm=winrm
                            )
                        elif not vm_resource.os_profile.windows_configuration.win_rm:
                            vm_resource.os_profile.windows_configuration.win_rm = winrm

                    if self.admin_password:
                        vm_resource.os_profile.admin_password = self.admin_password

                    if self.custom_data:
                        # Azure SDK (erroneously?) wants native string type for this
                        vm_resource.os_profile.custom_data = to_native(base64.b64encode(to_bytes(self.custom_data)))

                    if self.os_type == 'Linux':
                        vm_resource.os_profile.linux_configuration = self.compute_models.LinuxConfiguration(
                            disable_password_authentication=disable_ssh_password
                        )
                    if self.ssh_public_keys:
                        ssh_config = self.compute_models.SshConfiguration()
                        ssh_config.public_keys = \
                            [self.compute_models.SshPublicKey(path=key['path'], key_data=key['key_data']) for key in self.ssh_public_keys]
                        vm_resource.os_profile.linux_configuration.ssh = ssh_config

                    # data disk
                    if self.data_disks:
                        data_disks = []
                        count = 0

                        for data_disk in self.data_disks:
                            if not data_disk.get('managed_disk_type'):
                                if not data_disk.get('storage_blob_name'):
                                    data_disk['storage_blob_name'] = self.name + '-data-' + str(count) + '.vhd'
                                    count += 1

                                if data_disk.get('storage_account_name'):
                                    data_disk_storage_account = self.get_storage_account(data_disk['storage_account_name'])
                                else:
                                    if(not default_storage_account):
                                        data_disk_storage_account = self.create_default_storage_account()
                                        self.log("data disk storage account:")
                                        self.log(self.serialize_obj(data_disk_storage_account, 'StorageAccount'), pretty_print=True)
                                        default_storage_account = data_disk_storage_account  # store for use by future data disks if necessary
                                    else:
                                        data_disk_storage_account = default_storage_account

                                if not data_disk.get('storage_container_name'):
                                    data_disk['storage_container_name'] = 'vhds'

                                data_disk_requested_vhd_uri = 'https://{0}.blob.{1}/{2}/{3}'.format(
                                    data_disk_storage_account.name,
                                    self._cloud_environment.suffixes.storage_endpoint,
                                    data_disk['storage_container_name'],
                                    data_disk['storage_blob_name']
                                )

                            if not data_disk.get('managed_disk_type'):
                                data_disk_managed_disk = None
                                disk_name = data_disk['storage_blob_name']
                                data_disk_vhd = self.compute_models.VirtualHardDisk(uri=data_disk_requested_vhd_uri)
                            else:
                                data_disk_vhd = None
                                data_disk_managed_disk = self.compute_models.ManagedDiskParameters(storage_account_type=data_disk['managed_disk_type'])
                                disk_name = self.name + "-datadisk-" + str(count)
                                count += 1

                            data_disk['caching'] = data_disk.get(
                                'caching', 'ReadOnly'
                            )

                            data_disks.append(self.compute_models.DataDisk(
                                lun=data_disk['lun'],
                                name=disk_name,
                                vhd=data_disk_vhd,
                                caching=data_disk['caching'],
                                create_option=self.compute_models.DiskCreateOptionTypes.empty,
                                disk_size_gb=data_disk['disk_size_gb'],
                                managed_disk=data_disk_managed_disk,
                            ))

                        vm_resource.storage_profile.data_disks = data_disks

                    # Before creating VM accept terms of plan if `accept_terms` is True
                    if self.accept_terms is True:
                        if not all([self.plan.get('name'), self.plan.get('product'), self.plan.get('publisher')]):
                            self.fail("parameter error: plan must be specified and include name, product, and publisher")
                        try:
                            plan_name = self.plan.get('name')
                            plan_product = self.plan.get('product')
                            plan_publisher = self.plan.get('publisher')
                            term = self.marketplace_client.marketplace_agreements.get(
                                publisher_id=plan_publisher, offer_id=plan_product, plan_id=plan_name)
                            term.accepted = True
                            agreement = self.marketplace_client.marketplace_agreements.create(
                                publisher_id=plan_publisher, offer_id=plan_product, plan_id=plan_name, parameters=term)
                        except Exception as exc:
                            self.fail(("Error accepting terms for virtual machine {0} with plan {1}. " +
                                       "Only service admin/account admin users can purchase images " +
                                       "from the marketplace. - {2}").format(self.name, self.plan, str(exc)))

                    self.log("Create virtual machine with parameters:")
                    self.create_or_update_vm(vm_resource, 'all_autocreated' in self.remove_on_absent)

                elif self.differences and len(self.differences) > 0:
                    # Update the VM based on detected config differences

                    self.log("Update virtual machine {0}".format(self.name))
                    self.results['actions'].append('Updated VM {0}'.format(self.name))
                    nics = [self.compute_models.NetworkInterfaceReference(id=interface['id'], primary=(i == 0))
                            for i, interface in enumerate(vm_dict['properties']['networkProfile']['networkInterfaces'])]

                    # os disk
                    if not vm_dict['properties']['storageProfile']['osDisk'].get('managedDisk'):
                        managed_disk = None
                        vhd = self.compute_models.VirtualHardDisk(uri=vm_dict['properties']['storageProfile']['osDisk'].get('vhd', {}).get('uri'))
                    else:
                        vhd = None
                        managed_disk = self.compute_models.ManagedDiskParameters(
                            storage_account_type=vm_dict['properties']['storageProfile']['osDisk']['managedDisk'].get('storageAccountType')
                        )

                    availability_set_resource = None
                    try:
                        availability_set_resource = self.compute_models.SubResource(id=vm_dict['properties']['availabilitySet'].get('id'))
                    except Exception:
                        # pass if the availability set is not set
                        pass

                    if 'imageReference' in vm_dict['properties']['storageProfile'].keys():
                        if 'id' in vm_dict['properties']['storageProfile']['imageReference'].keys():
                            image_reference = self.compute_models.ImageReference(
                                id=vm_dict['properties']['storageProfile']['imageReference']['id']
                            )
                        else:
                            image_reference = self.compute_models.ImageReference(
                                publisher=vm_dict['properties']['storageProfile']['imageReference'].get('publisher'),
                                offer=vm_dict['properties']['storageProfile']['imageReference'].get('offer'),
                                sku=vm_dict['properties']['storageProfile']['imageReference'].get('sku'),
                                version=vm_dict['properties']['storageProfile']['imageReference'].get('version')
                            )
                    else:
                        image_reference = None

                    # You can't change a vm zone
                    if vm_dict['zones'] != self.zones:
                        self.fail("You can't change the Availability Zone of a virtual machine (have: {0}, want: {1})".format(vm_dict['zones'], self.zones))

                    if 'osProfile' in vm_dict['properties']:
                        os_profile = self.compute_models.OSProfile(
                            admin_username=vm_dict['properties'].get('osProfile', {}).get('adminUsername'),
                            computer_name=vm_dict['properties'].get('osProfile', {}).get('computerName')
                        )
                    else:
                        os_profile = None
                    license_type = None
                    if self.license_type is None:
                        license_type = "None"

                    vm_resource = self.compute_models.VirtualMachine(
                        location=vm_dict['location'],
                        os_profile=os_profile,
                        hardware_profile=self.compute_models.HardwareProfile(
                            vm_size=vm_dict['properties']['hardwareProfile'].get('vmSize')
                        ),
                        storage_profile=self.compute_models.StorageProfile(
                            os_disk=self.compute_models.OSDisk(
                                name=vm_dict['properties']['storageProfile']['osDisk'].get('name'),
                                vhd=vhd,
                                managed_disk=managed_disk,
                                create_option=vm_dict['properties']['storageProfile']['osDisk'].get('createOption'),
                                os_type=vm_dict['properties']['storageProfile']['osDisk'].get('osType'),
                                caching=vm_dict['properties']['storageProfile']['osDisk'].get('caching'),
                                disk_size_gb=vm_dict['properties']['storageProfile']['osDisk'].get('diskSizeGB')
                            ),
                            image_reference=image_reference
                        ),
                        availability_set=availability_set_resource,
                        network_profile=self.compute_models.NetworkProfile(
                            network_interfaces=nics
                        )
                    )

                    if self.license_type is not None:
                        vm_resource.license_type = self.license_type

                    if vm_dict.get('tags'):
                        vm_resource.tags = vm_dict['tags']

                    # Add custom_data, if provided
                    if vm_dict['properties'].get('osProfile', {}).get('customData'):
                        custom_data = vm_dict['properties']['osProfile']['customData']
                        # Azure SDK (erroneously?) wants native string type for this
                        vm_resource.os_profile.custom_data = to_native(base64.b64encode(to_bytes(custom_data)))

                    # Add admin password, if one provided
                    if vm_dict['properties'].get('osProfile', {}).get('adminPassword'):
                        vm_resource.os_profile.admin_password = vm_dict['properties']['osProfile']['adminPassword']

                    # Add linux configuration, if applicable
                    linux_config = vm_dict['properties'].get('osProfile', {}).get('linuxConfiguration')
                    if linux_config:
                        ssh_config = linux_config.get('ssh', None)
                        vm_resource.os_profile.linux_configuration = self.compute_models.LinuxConfiguration(
                            disable_password_authentication=linux_config.get('disablePasswordAuthentication', False)
                        )
                        if ssh_config:
                            public_keys = ssh_config.get('publicKeys')
                            if public_keys:
                                vm_resource.os_profile.linux_configuration.ssh = self.compute_models.SshConfiguration(public_keys=[])
                                for key in public_keys:
                                    vm_resource.os_profile.linux_configuration.ssh.public_keys.append(
                                        self.compute_models.SshPublicKey(path=key['path'], key_data=key['keyData'])
                                    )

                    # data disk
                    if vm_dict['properties']['storageProfile'].get('dataDisks'):
                        data_disks = []

                        for data_disk in vm_dict['properties']['storageProfile']['dataDisks']:
                            if data_disk.get('managedDisk'):
                                managed_disk_type = data_disk['managedDisk'].get('storageAccountType')
                                data_disk_managed_disk = self.compute_models.ManagedDiskParameters(storage_account_type=managed_disk_type)
                                data_disk_vhd = None
                            else:
                                data_disk_vhd = data_disk['vhd']['uri']
                                data_disk_managed_disk = None

                            data_disks.append(self.compute_models.DataDisk(
                                lun=int(data_disk['lun']),
                                name=data_disk.get('name'),
                                vhd=data_disk_vhd,
                                caching=data_disk.get('caching'),
                                create_option=data_disk.get('createOption'),
                                disk_size_gb=int(data_disk['diskSizeGB']),
                                managed_disk=data_disk_managed_disk,
                            ))
                        vm_resource.storage_profile.data_disks = data_disks

                    self.log("Update virtual machine with parameters:")
                    self.create_or_update_vm(vm_resource, False)

                # Make sure we leave the machine in requested power state
                if (powerstate_change == 'poweron' and
                        self.results['ansible_facts']['azure_vm']['powerstate'] != 'running'):
                    # Attempt to power on the machine
                    self.power_on_vm()

                elif (powerstate_change == 'poweroff' and
                        self.results['ansible_facts']['azure_vm']['powerstate'] == 'running'):
                    # Attempt to power off the machine
                    self.power_off_vm()

                elif powerstate_change == 'restarted':
                    self.restart_vm()

                elif powerstate_change == 'deallocated':
                    self.deallocate_vm()
                elif powerstate_change == 'generalized':
                    self.power_off_vm()
                    self.generalize_vm()

                self.results['ansible_facts']['azure_vm'] = self.serialize_vm(self.get_vm())

            elif self.state == 'absent':
                # delete the VM
                self.log("Delete virtual machine {0}".format(self.name))
                self.results['ansible_facts']['azure_vm'] = None
                self.delete_vm(vm)

        # until we sort out how we want to do this globally
        del self.results['actions']

        return self.results

    def get_vm(self):
        '''
        Get the VM with expanded instanceView

        :return: VirtualMachine object
        '''
        try:
            vm = self.compute_client.virtual_machines.get(self.resource_group, self.name, expand='instanceview')
            return vm
        except Exception as exc:
            self.fail("Error getting virtual machine {0} - {1}".format(self.name, str(exc)))

    def serialize_vm(self, vm):
        '''
        Convert a VirtualMachine object to dict.

        :param vm: VirtualMachine object
        :return: dict
        '''

        result = self.serialize_obj(vm, AZURE_OBJECT_CLASS, enum_modules=AZURE_ENUM_MODULES)
        result['id'] = vm.id
        result['name'] = vm.name
        result['type'] = vm.type
        result['location'] = vm.location
        result['tags'] = vm.tags

        result['powerstate'] = dict()
        if vm.instance_view:
            result['powerstate'] = next((s.code.replace('PowerState/', '')
                                         for s in vm.instance_view.statuses if s.code.startswith('PowerState')), None)
            for s in vm.instance_view.statuses:
                if s.code.lower() == "osstate/generalized":
                    result['powerstate'] = 'generalized'

        # Expand network interfaces to include config properties
        for interface in vm.network_profile.network_interfaces:
            int_dict = azure_id_to_dict(interface.id)
            nic = self.get_network_interface(int_dict['resourceGroups'], int_dict['networkInterfaces'])
            for interface_dict in result['properties']['networkProfile']['networkInterfaces']:
                if interface_dict['id'] == interface.id:
                    nic_dict = self.serialize_obj(nic, 'NetworkInterface')
                    interface_dict['name'] = int_dict['networkInterfaces']
                    interface_dict['properties'] = nic_dict['properties']
        # Expand public IPs to include config properties
        for interface in result['properties']['networkProfile']['networkInterfaces']:
            for config in interface['properties']['ipConfigurations']:
                if config['properties'].get('publicIPAddress'):
                    pipid_dict = azure_id_to_dict(config['properties']['publicIPAddress']['id'])
                    try:
                        pip = self.network_client.public_ip_addresses.get(pipid_dict['resourceGroups'],
                                                                          pipid_dict['publicIPAddresses'])
                    except Exception as exc:
                        self.fail("Error fetching public ip {0} - {1}".format(pipid_dict['publicIPAddresses'],
                                                                              str(exc)))
                    pip_dict = self.serialize_obj(pip, 'PublicIPAddress')
                    config['properties']['publicIPAddress']['name'] = pipid_dict['publicIPAddresses']
                    config['properties']['publicIPAddress']['properties'] = pip_dict['properties']

        self.log(result, pretty_print=True)
        if self.state != 'absent' and not result['powerstate']:
            self.fail("Failed to determine PowerState of virtual machine {0}".format(self.name))
        return result

    def power_off_vm(self):
        self.log("Powered off virtual machine {0}".format(self.name))
        self.results['actions'].append("Powered off virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machines.power_off(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error powering off virtual machine {0} - {1}".format(self.name, str(exc)))
        return True

    def power_on_vm(self):
        self.results['actions'].append("Powered on virtual machine {0}".format(self.name))
        self.log("Power on virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machines.start(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error powering on virtual machine {0} - {1}".format(self.name, str(exc)))
        return True

    def restart_vm(self):
        self.results['actions'].append("Restarted virtual machine {0}".format(self.name))
        self.log("Restart virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machines.restart(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error restarting virtual machine {0} - {1}".format(self.name, str(exc)))
        return True

    def deallocate_vm(self):
        self.results['actions'].append("Deallocated virtual machine {0}".format(self.name))
        self.log("Deallocate virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machines.deallocate(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deallocating virtual machine {0} - {1}".format(self.name, str(exc)))
        return True

    def generalize_vm(self):
        self.results['actions'].append("Generalize virtual machine {0}".format(self.name))
        self.log("Generalize virtual machine {0}".format(self.name))
        try:
            response = self.compute_client.virtual_machines.generalize(self.resource_group, self.name)
            if isinstance(response, LROPoller):
                self.get_poller_result(response)
        except Exception as exc:
            self.fail("Error generalizing virtual machine {0} - {1}".format(self.name, str(exc)))
        return True

    def remove_autocreated_resources(self, tags):
        if tags:
            sa_name = tags.get('_own_sa_')
            nic_name = tags.get('_own_nic_')
            pip_name = tags.get('_own_pip_')
            nsg_name = tags.get('_own_nsg_')
            if sa_name:
                self.delete_storage_account(self.resource_group, sa_name)
            if nic_name:
                self.delete_nic(self.resource_group, nic_name)
            if pip_name:
                self.delete_pip(self.resource_group, pip_name)
            if nsg_name:
                self.delete_nsg(self.resource_group, nsg_name)

    def delete_vm(self, vm):
        vhd_uris = []
        managed_disk_ids = []
        nic_names = []
        pip_names = []

        if 'all_autocreated' not in self.remove_on_absent:
            if self.remove_on_absent.intersection(set(['all', 'virtual_storage'])):
                # store the attached vhd info so we can nuke it after the VM is gone
                if(vm.storage_profile.os_disk.managed_disk):
                    self.log('Storing managed disk ID for deletion')
                    managed_disk_ids.append(vm.storage_profile.os_disk.managed_disk.id)
                elif(vm.storage_profile.os_disk.vhd):
                    self.log('Storing VHD URI for deletion')
                    vhd_uris.append(vm.storage_profile.os_disk.vhd.uri)

                data_disks = vm.storage_profile.data_disks
                for data_disk in data_disks:
                    if data_disk is not None:
                        if(data_disk.vhd):
                            vhd_uris.append(data_disk.vhd.uri)
                        elif(data_disk.managed_disk):
                            managed_disk_ids.append(data_disk.managed_disk.id)

                # FUTURE enable diff mode, move these there...
                self.log("VHD URIs to delete: {0}".format(', '.join(vhd_uris)))
                self.results['deleted_vhd_uris'] = vhd_uris
                self.log("Managed disk IDs to delete: {0}".format(', '.join(managed_disk_ids)))
                self.results['deleted_managed_disk_ids'] = managed_disk_ids

            if self.remove_on_absent.intersection(set(['all', 'network_interfaces'])):
                # store the attached nic info so we can nuke them after the VM is gone
                self.log('Storing NIC names for deletion.')
                for interface in vm.network_profile.network_interfaces:
                    id_dict = azure_id_to_dict(interface.id)
                    nic_names.append(dict(name=id_dict['networkInterfaces'], resource_group=id_dict['resourceGroups']))
                self.log('NIC names to delete {0}'.format(str(nic_names)))
                self.results['deleted_network_interfaces'] = nic_names
                if self.remove_on_absent.intersection(set(['all', 'public_ips'])):
                    # also store each nic's attached public IPs and delete after the NIC is gone
                    for nic_dict in nic_names:
                        nic = self.get_network_interface(nic_dict['resource_group'], nic_dict['name'])
                        for ipc in nic.ip_configurations:
                            if ipc.public_ip_address:
                                pip_dict = azure_id_to_dict(ipc.public_ip_address.id)
                                pip_names.append(dict(name=pip_dict['publicIPAddresses'], resource_group=pip_dict['resourceGroups']))
                    self.log('Public IPs to  delete are {0}'.format(str(pip_names)))
                    self.results['deleted_public_ips'] = pip_names

        self.log("Deleting virtual machine {0}".format(self.name))
        self.results['actions'].append("Deleted virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machines.delete(self.resource_group, self.name)
            # wait for the poller to finish
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting virtual machine {0} - {1}".format(self.name, str(exc)))

        if 'all_autocreated' in self.remove_on_absent:
            self.remove_autocreated_resources(vm.tags)
        else:
            # TODO: parallelize nic, vhd, and public ip deletions with begin_deleting
            # TODO: best-effort to keep deleting other linked resources if we encounter an error
            if self.remove_on_absent.intersection(set(['all', 'virtual_storage'])):
                self.log('Deleting VHDs')
                self.delete_vm_storage(vhd_uris)
                self.log('Deleting managed disks')
                self.delete_managed_disks(managed_disk_ids)

            if self.remove_on_absent.intersection(set(['all', 'network_interfaces'])):
                self.log('Deleting network interfaces')
                for nic_dict in nic_names:
                    self.delete_nic(nic_dict['resource_group'], nic_dict['name'])

            if self.remove_on_absent.intersection(set(['all', 'public_ips'])):
                self.log('Deleting public IPs')
                for pip_dict in pip_names:
                    self.delete_pip(pip_dict['resource_group'], pip_dict['name'])

        return True

    def get_network_interface(self, resource_group, name):
        try:
            nic = self.network_client.network_interfaces.get(resource_group, name)
            return nic
        except Exception as exc:
            self.fail("Error fetching network interface {0} - {1}".format(name, str(exc)))
        return True

    def delete_nic(self, resource_group, name):
        self.log("Deleting network interface {0}".format(name))
        self.results['actions'].append("Deleted network interface {0}".format(name))
        try:
            poller = self.network_client.network_interfaces.delete(resource_group, name)
        except Exception as exc:
            self.fail("Error deleting network interface {0} - {1}".format(name, str(exc)))
        self.get_poller_result(poller)
        # Delete doesn't return anything. If we get this far, assume success
        return True

    def delete_pip(self, resource_group, name):
        self.results['actions'].append("Deleted public IP {0}".format(name))
        try:
            poller = self.network_client.public_ip_addresses.delete(resource_group, name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting {0} - {1}".format(name, str(exc)))
        # Delete returns nada. If we get here, assume that all is well.
        return True

    def delete_nsg(self, resource_group, name):
        self.results['actions'].append("Deleted NSG {0}".format(name))
        try:
            poller = self.network_client.network_security_groups.delete(resource_group, name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting {0} - {1}".format(name, str(exc)))
        return True

    def delete_managed_disks(self, managed_disk_ids):
        for mdi in managed_disk_ids:
            try:
                poller = self.rm_client.resources.delete_by_id(mdi, '2017-03-30')
                self.get_poller_result(poller)
            except Exception as exc:
                self.fail("Error deleting managed disk {0} - {1}".format(mdi, str(exc)))
        return True

    def delete_storage_account(self, resource_group, name):
        self.log("Delete storage account {0}".format(name))
        self.results['actions'].append("Deleted storage account {0}".format(name))
        try:
            self.storage_client.storage_accounts.delete(self.resource_group, name)
        except Exception as exc:
            self.fail("Error deleting storage account {0} - {1}".format(name, str(exc)))
        return True

    def delete_vm_storage(self, vhd_uris):
        # FUTURE: figure out a cloud_env independent way to delete these
        for uri in vhd_uris:
            self.log("Extracting info from blob uri '{0}'".format(uri))
            try:
                blob_parts = extract_names_from_blob_uri(uri, self._cloud_environment.suffixes.storage_endpoint)
            except Exception as exc:
                self.fail("Error parsing blob URI {0}".format(str(exc)))
            storage_account_name = blob_parts['accountname']
            container_name = blob_parts['containername']
            blob_name = blob_parts['blobname']

            blob_client = self.get_blob_client(self.resource_group, storage_account_name)

            self.log("Delete blob {0}:{1}".format(container_name, blob_name))
            self.results['actions'].append("Deleted blob {0}:{1}".format(container_name, blob_name))
            try:
                blob_client.delete_blob(container_name, blob_name)
            except Exception as exc:
                self.fail("Error deleting blob {0}:{1} - {2}".format(container_name, blob_name, str(exc)))
        return True

    def get_marketplace_image_version(self):
        try:
            versions = self.compute_client.virtual_machine_images.list(self.location,
                                                                       self.image['publisher'],
                                                                       self.image['offer'],
                                                                       self.image['sku'])
        except Exception as exc:
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
        return None

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
        return None

    def get_availability_set(self, resource_group, name):
        try:
            return self.compute_client.availability_sets.get(resource_group, name)
        except Exception as exc:
            self.fail("Error fetching availability set {0} - {1}".format(name, str(exc)))

    def get_storage_account(self, name):
        try:
            account = self.storage_client.storage_accounts.get_properties(self.resource_group,
                                                                          name)
            return account
        except Exception as exc:
            self.fail("Error fetching storage account {0} - {1}".format(name, str(exc)))

    def create_or_update_vm(self, params, remove_autocreated_on_failure):
        try:
            poller = self.compute_client.virtual_machines.create_or_update(self.resource_group, self.name, params)
            self.get_poller_result(poller)
        except Exception as exc:
            if remove_autocreated_on_failure:
                self.remove_autocreated_resources(params.tags)
            self.fail("Error creating or updating virtual machine {0} - {1}".format(self.name, str(exc)))

    def vm_size_is_valid(self):
        '''
        Validate self.vm_size against the list of virtual machine sizes available for the account and location.

        :return: boolean
        '''
        try:
            sizes = self.compute_client.virtual_machine_sizes.list(self.location)
        except Exception as exc:
            self.fail("Error retrieving available machine sizes - {0}".format(str(exc)))
        for size in sizes:
            if size.name == self.vm_size:
                return True
        return False

    def create_default_storage_account(self):
        '''
        Create a default storage account <vm name>XXXX, where XXXX is a random number. If <vm name>XXXX exists, use it.
        Otherwise, create one.

        :return: storage account object
        '''
        account = None
        valid_name = False
        if self.tags is None:
            self.tags = {}

        # Attempt to find a valid storage account name
        storage_account_name_base = re.sub('[^a-zA-Z0-9]', '', self.name[:20].lower())
        for i in range(0, 5):
            rand = random.randrange(1000, 9999)
            storage_account_name = storage_account_name_base + str(rand)
            if self.check_storage_account_name(storage_account_name):
                valid_name = True
                break

        if not valid_name:
            self.fail("Failed to create a unique storage account name for {0}. Try using a different VM name."
                      .format(self.name))

        try:
            account = self.storage_client.storage_accounts.get_properties(self.resource_group, storage_account_name)
        except CloudError:
            pass

        if account:
            self.log("Storage account {0} found.".format(storage_account_name))
            self.check_provisioning_state(account)
            return account
        sku = self.storage_models.Sku(name=self.storage_models.SkuName.standard_lrs)
        sku.tier = self.storage_models.SkuTier.standard
        kind = self.storage_models.Kind.storage
        parameters = self.storage_models.StorageAccountCreateParameters(sku=sku, kind=kind, location=self.location)
        self.log("Creating storage account {0} in location {1}".format(storage_account_name, self.location))
        self.results['actions'].append("Created storage account {0}".format(storage_account_name))
        try:
            poller = self.storage_client.storage_accounts.create(self.resource_group, storage_account_name, parameters)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Failed to create storage account: {0} - {1}".format(storage_account_name, str(exc)))
        self.tags['_own_sa_'] = storage_account_name
        return self.get_storage_account(storage_account_name)

    def check_storage_account_name(self, name):
        self.log("Checking storage account name availability for {0}".format(name))
        try:
            response = self.storage_client.storage_accounts.check_name_availability(name)
            if response.reason == 'AccountNameInvalid':
                raise Exception("Invalid default storage account name: {0}".format(name))
        except Exception as exc:
            self.fail("Error checking storage account name availability for {0} - {1}".format(name, str(exc)))

        return response.name_available

    def create_default_nic(self):
        '''
        Create a default Network Interface <vm name>01. Requires an existing virtual network
        with one subnet. If NIC <vm name>01 exists, use it. Otherwise, create one.

        :return: NIC object
        '''

        network_interface_name = self.name + '01'
        nic = None
        if self.tags is None:
            self.tags = {}

        self.log("Create default NIC {0}".format(network_interface_name))
        self.log("Check to see if NIC {0} exists".format(network_interface_name))
        try:
            nic = self.network_client.network_interfaces.get(self.resource_group, network_interface_name)
        except CloudError:
            pass

        if nic:
            self.log("NIC {0} found.".format(network_interface_name))
            self.check_provisioning_state(nic)
            return nic

        self.log("NIC {0} does not exist.".format(network_interface_name))

        virtual_network_resource_group = None
        if self.virtual_network_resource_group:
            virtual_network_resource_group = self.virtual_network_resource_group
        else:
            virtual_network_resource_group = self.resource_group

        if self.virtual_network_name:
            try:
                self.network_client.virtual_networks.list(virtual_network_resource_group, self.virtual_network_name)
                virtual_network_name = self.virtual_network_name
            except CloudError as exc:
                self.fail("Error: fetching virtual network {0} - {1}".format(self.virtual_network_name, str(exc)))

        else:
            # Find a virtual network
            no_vnets_msg = "Error: unable to find virtual network in resource group {0}. A virtual network " \
                           "with at least one subnet must exist in order to create a NIC for the virtual " \
                           "machine.".format(virtual_network_resource_group)

            virtual_network_name = None
            try:
                vnets = self.network_client.virtual_networks.list(virtual_network_resource_group)
            except CloudError:
                self.log('cloud error!')
                self.fail(no_vnets_msg)

            for vnet in vnets:
                virtual_network_name = vnet.name
                self.log('vnet name: {0}'.format(vnet.name))
                break

            if not virtual_network_name:
                self.fail(no_vnets_msg)

        if self.subnet_name:
            try:
                subnet = self.network_client.subnets.get(virtual_network_resource_group, virtual_network_name, self.subnet_name)
                subnet_id = subnet.id
            except Exception as exc:
                self.fail("Error: fetching subnet {0} - {1}".format(self.subnet_name, str(exc)))
        else:
            no_subnets_msg = "Error: unable to find a subnet in virtual network {0}. A virtual network " \
                             "with at least one subnet must exist in order to create a NIC for the virtual " \
                             "machine.".format(virtual_network_name)

            subnet_id = None
            try:
                subnets = self.network_client.subnets.list(virtual_network_resource_group, virtual_network_name)
            except CloudError:
                self.fail(no_subnets_msg)

            for subnet in subnets:
                subnet_id = subnet.id
                self.log('subnet id: {0}'.format(subnet_id))
                break

            if not subnet_id:
                self.fail(no_subnets_msg)

        pip = None
        if self.public_ip_allocation_method != 'Disabled':
            self.results['actions'].append('Created default public IP {0}'.format(self.name + '01'))
            sku = self.network_models.PublicIPAddressSku(name="Standard") if self.zones else None
            pip_facts = self.create_default_pip(self.resource_group, self.location, self.name + '01', self.public_ip_allocation_method, sku=sku)
            pip = self.network_models.PublicIPAddress(id=pip_facts.id, location=pip_facts.location, resource_guid=pip_facts.resource_guid, sku=sku)
            self.tags['_own_pip_'] = self.name + '01'

        self.results['actions'].append('Created default security group {0}'.format(self.name + '01'))
        group = self.create_default_securitygroup(self.resource_group, self.location, self.name + '01', self.os_type,
                                                  self.open_ports)
        self.tags['_own_nsg_'] = self.name + '01'

        parameters = self.network_models.NetworkInterface(
            location=self.location,
            ip_configurations=[
                self.network_models.NetworkInterfaceIPConfiguration(
                    private_ip_allocation_method='Dynamic',
                )
            ]
        )
        parameters.ip_configurations[0].subnet = self.network_models.Subnet(id=subnet_id)
        parameters.ip_configurations[0].name = 'default'
        parameters.network_security_group = self.network_models.NetworkSecurityGroup(id=group.id,
                                                                                     location=group.location,
                                                                                     resource_guid=group.resource_guid)
        parameters.ip_configurations[0].public_ip_address = pip

        self.log("Creating NIC {0}".format(network_interface_name))
        self.log(self.serialize_obj(parameters, 'NetworkInterface'), pretty_print=True)
        self.results['actions'].append("Created NIC {0}".format(network_interface_name))
        try:
            poller = self.network_client.network_interfaces.create_or_update(self.resource_group,
                                                                             network_interface_name,
                                                                             parameters)
            new_nic = self.get_poller_result(poller)
            self.tags['_own_nic_'] = network_interface_name
        except Exception as exc:
            self.fail("Error creating network interface {0} - {1}".format(network_interface_name, str(exc)))
        return new_nic

    def parse_network_interface(self, nic):
        nic = self.parse_resource_to_dict(nic)
        if 'name' not in nic:
            self.fail("Invalid network interface {0}".format(str(nic)))
        return format_resource_id(val=nic['name'],
                                  subscription_id=nic['subscription_id'],
                                  resource_group=nic['resource_group'],
                                  namespace='Microsoft.Network',
                                  types='networkInterfaces')


def main():
    AzureRMVirtualMachine()


if __name__ == '__main__':
    main()
