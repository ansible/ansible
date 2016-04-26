#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
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

DOCUMENTATION = '''
---
module: azure_rm_virtualmachine

version_added: "2.1"

short_description: Manage Azure virtual machines.

description:
    - Create, update, stop and start a virtual machine. Provide an existing storage account and network interface or
      allow the module to create these for you. If you choose not to provide a network interface, the resource group
      must contain a virtual network with at least one subnet.
    - Currently requires an image found in the Azure Marketplace. Use azure_rm_virtualmachineimage_facts module
      to discover the publisher, offer, sku and version of a particular image.

options:
    resource_group:
        description:
            - Name of the resource group containing the virtual machine.
        required: true
    name:
        description:
            - Name of the virtual machine.
        required: true
    state:
        description:
            - Assert the state of the virtual machine.
            - State 'present' will check that the machine exists with the requested configuration. If the configuration
              of the existing machine does not match, the machine will be updated. Use options started, allocated and restarted to change the machine's power state.
            - State 'absent' will remove the virtual machine.
        default: present
        required: false
        choices:
            - absent
            - present
    started:
        description:
            - Use with state 'present' to start the machine. Set to false to have the machine be 'stopped'.
        default: true
        required: false
    allocated:
        description:
            - Toggle that controls if the machine is allocated/deallocated, only useful with state='present'.
        default: True
        required: false
    restarted:
        description:
            - Use with state 'present' to restart a running VM.
        default: false
        required: false
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
        default: null
        required: false
    short_hostname:
        description:
            - Name assigned internally to the host. On a linux VM this is the name returned by the `hostname` command.
              When creating a virtual machine, short_hostname defaults to name.
        default: null
        required: false
    vm_size:
        description:
            - A valid Azure VM size value. For example, 'Standard_D4'. The list of choices varies depending on the
              subscription and location. Check your subscription for available choices.
        default: Standard_D1
        required: false
    admin_username:
        description:
            - Admin username used to access the host after it is created. Required when creating a VM.
        default: null
        required: false
    admin_password:
        description:
            - Password for the admin username. Not required if the os_type is Linux and SSH password authentication
              is disabled by setting ssh_password_enabled to false.
        default: null
        required: false
    ssh_password_enabled:
        description:
            - When the os_type is Linux, setting ssh_password_enabled to false will disable SSH password authentication
              and require use of SSH keys.
        default: true
        required: false
    ssh_public_keys:
        description:
            - "For os_type Linux provide a list of SSH keys. Each item in the list should be a dictionary where the
              dictionary contains two keys: path and key_data. Set the path to the default location of the
              authorized_keys files. On an Enterprise Linux host, for example, the path will be
              /home/<admin username>/.ssh/authorized_keys. Set key_data to the actual value of the public key."
        default: null
        required: false
    image:
        description:
            - "A dictionary describing the Marketplace image used to build the VM. Will contain keys: publisher,
              offer, sku and version. NOTE: set image.version to 'latest' to get the most recent version of a given
              image."
        required: true
    storage_account_name:
        description:
            - Name of an existing storage account that supports creation of VHD blobs. If not specified for a new VM,
              a new storage account named <vm name>01 will be created using storage type 'Standard_LRS'.
        default: null
        required: false
    storage_container_name:
        description:
            - Name of the container to use within the storage account to store VHD blobs. If no name is specified a
              default container will created.
        default: vhds
        required: false
    storage_blob_name:
        description:
            - Name fo the storage blob used to hold the VM's OS disk image. If no name is provided, defaults to
              the VM name + '.vhd'. If you provide a name, it must end with '.vhd'
        aliases:
            - storage_blob
        default: null
        required: false
    os_disk_caching:
        description:
            - Type of OS disk caching.
        choices:
            - ReadOnly
            - ReadWrite
        default: ReadOnly
        aliases:
            - disk_caching
        required: false
    os_type:
        description:
            - Base type of operating system.
        choices:
            - Windows
            - Linux
        default:
            - Linux
        required: false
    public_ip_allocation_method:
        description:
            - If a public IP address is created when creating the VM (beacuse a Network Interface was not provided),
              determines if the public IP address remains permanently associated with the Network Interface. If set
              to 'Dynamic' the public IP address may change any time the VM is rebooted or power cycled.
        choices:
            - Dynamic
            - Static
        default:
            - Static
        aliases:
            - public_ip_allocation
        required: false
    open_ports:
        description:
            - If a network interface is created when creating the VM, a security group will be created as well. For
              Linux hosts a rule will be added to the security group allowing inbound TCP connections to the default
              SSH port 22, and for Windows hosts ports 3389 and 5986 will be opened. Override the default open ports by
              providing a list of ports.
        default: null
        required: false
    network_interface_names:
        description:
            - List of existing network interface names to add to the VM. If a network interface name is not provided
              when the VM is created, a default network interface will be created. In order for the module to create
              a network interface, at least one Virtual Network with one Subnet must exist.
        default: null
        required: false
    virtual_network_name:
        description:
            - When creating a virtual machine, if a network interface name is not provided, one will be created.
              The new network interface will be assigned to the first virtual network found in the resource group.
              Use this parameter to provide a specific virtual network instead.
        aliases:
            - virtual_network
        default: null
        required: false
    subnet_name:
        description:
            - When creating a virtual machine, if a network interface name is not provided, one will be created.
              The new network interface will be assigned to the first subnet found in the virtual network.
              Use this parameter to provide a specific subnet instead.
        aliases:
            - virtual_network
        default: null
        required: false
    remove_on_absent:
        description:
            - When removing a VM using state 'absent', also remove associated resources
            - "It can be 'all' or a list with any of the following: ['network_interfaces', 'virtual_storage', 'public_ips']"
            - Any other input will be ignored
        default: ['all']
        required: false

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''
EXAMPLES = '''

- name: Create VM with defaults
  azure_rm_virtualmachine:
    resource_group: Testing
    name: testvm10
    admin_username: chouseknecht
    admin_password: <your password here>
    image:
      offer: CentOS
      publisher: OpenLogic
      sku: '7.1'
      version: latest

- name: Create a VM with exiting storage account and NIC
  azure_rm_virtualmachine:
    resource_group: Testing
    name: testvm002
    vm_size: Standard_D4
    storage_account: testaccount001
    admin_username: adminUser
    ssh_public_keys:
      path: /home/adminUser/.ssh/authorized_keys
      key_data: < insert yor ssh public key here... >
    network_interfaces: testvm001
    image:
      offer: CentOS
      publisher: OpenLogic
      sku: '7.1'
      version: latest

- name: Power Off
  azure_rm_virtualmachine:
    resource_group: Testing
    name: testvm002
    started: no

- name: Deallocate
  azure_rm_virtualmachine:
    resource_group: Testing
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

- name: remove vm and all resources except public ips
  azure_rm_virtualmachine:
    resource_group: Testing
    name: testvm002
    state: absent
    remove_on_absent:
        - network_interfaces
        - virtual_storage
'''

RETURN = '''
powerstate:
    description: Indicates if the state is running, stopped, deallocated
    returned: always
    type: string
    sample: running
state:
    description: Facts about the current state of the object.
    returned: always
    type: dict
    sample: {
        "properties": {
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
                        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/testvm10_NIC01",
                        "name": "testvm10_NIC01",
                        "properties": {
                            "dnsSettings": {
                                "appliedDnsServers": [],
                                "dnsServers": []
                            },
                            "enableIPForwarding": false,
                            "ipConfigurations": [
                                {
                                    "etag": "W/\"041c8c2a-d5dd-4cd7-8465-9125cfbe2cf8\"",
                                    "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/testvm10_NIC01/ipConfigurations/default",
                                    "name": "default",
                                    "properties": {
                                        "privateIPAddress": "10.10.0.5",
                                        "privateIPAllocationMethod": "Dynamic",
                                        "provisioningState": "Succeeded",
                                        "publicIPAddress": {
                                            "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/publicIPAddresses/testvm10_PIP01",
                                            "name": "testvm10_PIP01",
                                            "properties": {
                                                "idleTimeoutInMinutes": 4,
                                                "ipAddress": "13.92.246.197",
                                                "ipConfiguration": {
                                                    "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/networkInterfaces/testvm10_NIC01/ipConfigurations/default"
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
                                "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Compute/virtualMachines/testvm10"
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
                "dataDisks": [],
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
'''

import random

from ansible.module_utils.basic import *
from ansible.module_utils.azure_rm_common import *

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.compute.models import NetworkInterfaceReference, VirtualMachine, HardwareProfile, \
        StorageProfile, OSProfile, OSDisk, VirtualHardDisk, ImageReference, NetworkProfile, LinuxConfiguration, \
        SshConfiguration, SshPublicKey
    from azure.mgmt.network.models import PublicIPAddress, NetworkSecurityGroup, NetworkInterface, \
        NetworkInterfaceIPConfiguration, Subnet
    from azure.mgmt.storage.models import StorageAccountCreateParameters
    from azure.mgmt.compute.models.compute_management_client_enums import DiskCreateOptionTypes, VirtualMachineSizeTypes
except ImportError:
    # This is handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'VirtualMachine'


def extract_names_from_blob_uri(blob_uri):
    # HACK: ditch this once python SDK supports get by URI
    m = re.match('^https://(?P<accountname>[^\.]+)\.blob\.core\.windows\.net/'
                 '(?P<containername>[^/]+)/(?P<blobname>.+)$', blob_uri)
    if not m:
        raise Exception("unable to parse blob uri '%s'" % blob_uri)
    extracted_names = m.groupdict()
    return extracted_names


class AzureRMVirtualMachine(AzureRMModuleBase):   

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
            location=dict(type='str'),
            short_hostname=dict(type='str'),
            vm_size=dict(type='str', choices=[], default='Standard_D1'),
            admin_username=dict(type='str'),
            admin_password=dict(type='str', ),
            ssh_password_enabled=dict(type='bool', default=True),
            ssh_public_keys=dict(type='list'),
            image=dict(type='dict'),
            storage_account_name=dict(type='str', aliases=['storage_account']),
            storage_container_name=dict(type='str', aliases=['storage_container'], default='vhds'),
            storage_blob_name=dict(type='str', aliases=['storage_blob']),
            os_disk_caching=dict(type='str', aliases=['disk_caching'], choices=['ReadOnly', 'ReadWrite'],
                                 default='ReadOnly'),
            os_type=dict(type='str', choices=['Linux', 'Windows'], default='Linux'),
            public_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Static',
                                             aliases=['public_ip_allocation']),
            open_ports=dict(type='list'),
            network_interface_names=dict(type='list', aliases=['network_interfaces']),
            remove_on_absent=dict(type='list', default=['all']),
            virtual_network_name=dict(type='str', aliases=['virtual_network']),
            subnet_name=dict(type='str', aliases=['subnet']),
            allocated=dict(type='bool', default=True),
            restarted=dict(type='bool', default=False),
            started=dict(type='bool', default=True),
        )

        for key in VirtualMachineSizeTypes:
            self.module_arg_spec['vm_size']['choices'].append(getattr(key, 'value'))

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.short_hostname = None
        self.vm_size = None
        self.admin_username = None
        self.admin_password = None
        self.ssh_password_enabled = None
        self.ssh_public_keys = None
        self.image = None
        self.storage_account_name = None
        self.storage_container_name = None
        self.storage_blob_name = None
        self.os_type = None
        self.os_disk_caching = None
        self.network_interface_names = None
        self.remove_on_absent = set()
        self.tags = None
        self.force = None
        self.public_ip_allocation_method = None
        self.open_ports = None
        self.virtual_network_name = None
        self.subnet_name = None
        self.allocated = None
        self.restarted = None
        self.started = None
        self.differences = None

        self.results = dict(
            changed=False,
            actions=[],
            powerstate_change=None,
            state=dict()
        )

        super(AzureRMVirtualMachine, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                    supports_check_mode=True)

        # make sure options are lower case
        self.remove_on_absent = set([resource.lower() for resource in  self.remove_on_absent])

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec.keys() + ['tags']:
            setattr(self, key, kwargs[key])

        changed = False
        powerstate_change = None
        results = dict()
        vm = None
        network_interfaces = []
        requested_vhd_uri = None
        disable_ssh_password = None
        vm_dict = None

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        if self.state == 'present':
            # Verify parameters and resolve any defaults

            if self.vm_size and not self.vm_size_is_valid():
                self.fail("Parameter error: vm_size {0} is not valid for your subscription and location.".foramt(
                    self.vm_size
                ))

            if self.network_interface_names:
                for name in self.network_interface_names:
                    nic = self.get_network_interface(name)
                    network_interfaces.append(nic.id)

            if self.ssh_public_keys:
                msg = "Parameter error: expecting ssh_public_keys to be a list of type dict where " \
                    "each dict contains keys: path, key_data."
                for key in self.ssh_public_keys:
                    if not isinstance(key, dict):
                        self.fail(msg)
                    if not key.get('path') or not key.get('key_data'):
                        self.fail(msg)

            if self.image:
                if not self.image.get('publisher') or not self.image.get('offer') or not self.image.get('sku') \
                   or not self.image.get('version'):
                    self.error("parameter error: expecting image to contain publisher, offer, sku and version keys.")
                image_version = self.get_image_version()
                if self.image['version'] == 'latest':
                    self.image['version'] = image_version.name
                    self.log("Using image version {0}".format(self.image['version']))

            if not self.storage_blob_name:
                    self.storage_blob_name = self.name + '.vhd'

            if self.storage_account_name:
                self.get_storage_account(self.storage_account_name)

                requested_vhd_uri = 'https://{0}.blob.core.windows.net/{1}/{2}'.format(self.storage_account_name,
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
                        updated_nics = [dict(id=id) for id in network_interfaces]
                        vm_dict['properties']['networkProfile']['networkInterfaces'] = updated_nics
                        changed = True

                if self.os_disk_caching and \
                   self.os_disk_caching != vm_dict['properties']['storageProfile']['osDisk']['caching']:
                    self.log('CHANGED: virtual machine {0} - OS disk caching'.format(self.name))
                    differences.append('OS Disk caching')
                    changed = True
                    vm_dict['properties']['storageProfile']['osDisk']['caching'] = self.os_disk_caching

                update_tags, vm_dict['tags'] = self.update_tags(vm_dict.get('tags', dict()))
                if update_tags:
                    differences.append('Tags')
                    changed = True

                if self.short_hostname and self.short_hostname != vm_dict['properties']['osProfile']['computerName']:
                    self.log('CHANGED: virtual machine {0} - short hostname'.format(self.name))
                    differences.append('Short Hostname')
                    changed = True
                    vm_dict['properties']['osProfile']['computerName'] = self.short_hostname

                if self.started and vm_dict['powerstate'] != 'running':
                    self.log("CHANGED: virtual machine {0} not running and requested state 'running'".format(self.name))
                    changed = True
                    powerstate_change = 'poweron'
                elif self.state == 'present' and vm_dict['powerstate'] == 'running' and self.restarted:
                    self.log("CHANGED: virtual machine {0} {1} and requested state 'restarted'"
                             .format(self.name, vm_dict['powerstate']))
                    changed = True
                    powerstate_change = 'restarted'
                elif self.state == 'present' and not self.allocated and vm_dict['powerstate'] != 'deallocated':
                    self.log("CHANGED: virtual machine {0} {1} and requested state 'deallocated'"
                             .format(self.name, vm_dict['powerstate']))
                    changed = True
                    powerstate_change = 'deallocated'
                elif not self.started and vm_dict['powerstate'] == 'running':
                    self.log("CHANGED: virtual machine {0} running and requested state 'stopped'".format(self.name))
                    changed = True
                    powerstate_change = 'poweroff'

                self.differences = differences

            elif self.state == 'absent':
                self.log("CHANGED: virtual machine {0} exists and requested state is 'absent'".format(self.name))
                results = dict()
                changed = True

        except CloudError:
            self.log('Virtual machine {0} does not exist'.format(self.name))
            if self.state == 'present':
                self.log("CHANGED: virtual machine does not exist but state is present." \
                    .format(self.name))
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results
        self.results['powerstate_change'] = powerstate_change

        if self.check_mode:
            return self.results

        if changed:
            if self.state == 'present':
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

                    if not self.image:
                        self.fail("Parameter error: an image is required when creating a virtual machine.")

                    # Get defaults
                    if not self.network_interface_names:
                        default_nic = self.create_default_nic()
                        self.log("network interface:")
                        self.log(self.serialize_obj(default_nic, 'NetworkInterface'), pretty_print=True)
                        network_interfaces = [default_nic.id]

                    if not self.storage_account_name:
                        storage_account = self.create_default_storage_account()
                        self.log("storage account:")
                        self.log(self.serialize_obj(storage_account, 'StorageAccount'), pretty_print=True)
                        requested_vhd_uri = 'https://{0}.blob.core.windows.net/{1}/{2}'.format(
                            storage_account.name,
                            self.storage_container_name,
                            self.storage_blob_name)

                    if not self.short_hostname:
                        self.short_hostname = self.name

                    nics = [NetworkInterfaceReference(id=id) for id in network_interfaces]
                    vhd = VirtualHardDisk(uri=requested_vhd_uri)
                    vm_resource = VirtualMachine(
                        location=self.location,
                        name=self.name,
                        tags=self.tags,
                        os_profile=OSProfile(
                            admin_username=self.admin_username,
                            computer_name=self.short_hostname,
                        ),
                        hardware_profile=HardwareProfile(
                            vm_size=self.vm_size
                        ),
                        storage_profile=StorageProfile(
                            os_disk=OSDisk(
                                self.storage_blob_name,
                                vhd,
                                DiskCreateOptionTypes.from_image,
                                caching=self.os_disk_caching,
                            ),
                            image_reference=ImageReference(
                                publisher=self.image['publisher'],
                                offer=self.image['offer'],
                                sku=self.image['sku'],
                                version=self.image['version'],
                            ),
                        ),
                        network_profile=NetworkProfile(
                            network_interfaces=nics
                        ),
                    )

                    if self.admin_password:
                        vm_resource.os_profile.admin_password = self.admin_password

                    if self.os_type == 'Linux':
                        vm_resource.os_profile.linux_configuration = LinuxConfiguration(
                            disable_password_authentication=disable_ssh_password
                        )
                    if self.ssh_public_keys:
                        ssh_config = SshConfiguration()
                        ssh_config.public_keys = \
                            [SshPublicKey(path=key['path'], key_data=key['key_data']) for key in self.ssh_public_keys]
                        vm_resource.os_profile.linux_configuration.ssh = ssh_config

                    self.log("Create virtual machine with parameters:")
                    self.log(self.serialize_obj(vm_resource, 'VirtualMachine'), pretty_print=True)
                    self.results['state'] = self.create_or_update_vm(vm_resource)

                elif self.differences and len(self.differences) > 0:
                    # Update the VM based on detected config differences

                    self.log("Update virtual machine {0}".format(self.name))
                    self.results['actions'].append('Updated VM {0}'.format(self.name))

                    nics = [NetworkInterfaceReference(id=interface['id'])
                            for interface in vm_dict['properties']['networkProfile']['networkInterfaces']]
                    vhd = VirtualHardDisk(uri=vm_dict['properties']['storageProfile']['osDisk']['vhd']['uri'])
                    vm_resource = VirtualMachine(
                        id=vm_dict['id'],
                        location=vm_dict['location'],
                        name=vm_dict['name'],
                        type=vm_dict['type'],
                        os_profile=OSProfile(
                            admin_username=vm_dict['properties']['osProfile']['adminUsername'],
                            computer_name=vm_dict['properties']['osProfile']['computerName']
                        ),
                        hardware_profile=HardwareProfile(
                            vm_size=vm_dict['properties']['hardwareProfile']['vmSize']
                        ),
                        storage_profile=StorageProfile(
                            os_disk=OSDisk(
                                vm_dict['properties']['storageProfile']['osDisk']['name'],
                                vhd,
                                vm_dict['properties']['storageProfile']['osDisk']['createOption'],
                                os_type=vm_dict['properties']['storageProfile']['osDisk']['osType'],
                                caching=vm_dict['properties']['storageProfile']['osDisk']['caching']
                            ),
                            image_reference=ImageReference(
                                publisher=vm_dict['properties']['storageProfile']['imageReference']['publisher'],
                                offer=vm_dict['properties']['storageProfile']['imageReference']['offer'],
                                sku=vm_dict['properties']['storageProfile']['imageReference']['sku'],
                                version=vm_dict['properties']['storageProfile']['imageReference']['version']
                            ),
                        ),
                        network_profile=NetworkProfile(
                            network_interfaces=nics
                        ),
                    )

                    if vm_dict.get('tags'):
                        vm_resource.tags = vm_dict['tags']

                    # Add admin password, if one provided
                    if vm_dict['properties']['osProfile'].get('adminPassword'):
                        vm_resource.os_profile.admin_password = vm_dict['properties']['osProfile']['adminPassword']

                    # Add linux configuration, if applicable
                    linux_config = vm_dict['properties']['osProfile'].get('linuxConfiguration')
                    if linux_config:
                        ssh_config = linux_config.get('ssh', None)
                        vm_resource.os_profile.linux_configuration = LinuxConfiguration(
                            disable_password_authentication=linux_config.get('disablePasswordAuthentication', False)
                        )
                        if ssh_config:
                            public_keys = ssh_config.get('publicKeys')
                            if public_keys:
                                vm_resource.os_profile.linux_configuration.ssh = SshConfiguration(public_keys=[])
                                for key in public_keys:
                                    vm_resource.os_profile.linux_configuration.ssh.public_keys.append(
                                        SshConfiguration(
                                            path=key['path'],
                                            key_data=key['keyData']
                                        )
                                    )
                    self.log("Update virtual machine with parameters:")
                    self.log(self.serialize_obj(vm_resource, 'VirtualMachine'), pretty_print=True)
                    self.results['state'] = self.create_or_update_vm(vm_resource)

                # Make sure we leave the machine in requested power state
                if powerstate_change == 'poweron' and self.results['state']['powerstate'] != 'running':
                    # Attempt to power on the machine
                    self.power_on_vm()
                    self.results['state'] = self.serialize_vm(self.get_vm())

                elif powerstate_change == 'poweroff' and self.results['state']['powerstate'] == 'running':
                    # Attempt to power off the machine
                    self.power_off_vm()
                    self.results['state'] = self.serialize_vm(self.get_vm())

                elif powerstate_change == 'restarted':
                    self.restart_vm()
                    self.results['state'] = self.serialize_vm(self.get_vm())

                elif powerstate_change == 'deallocated':
                    self.deallocate_vm()
                    self.results['state'] = self.serialize_vm(self.get_vm())

            elif self.state == 'absent':
                # delete the VM
                self.log("Delete virtual machine {0}".format(self.name))
                self.results['state']['status'] = 'Deleted'
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
            self.fail("Error getting virtual machine (0) - {1}".format(self.name, str(exc)))

    def serialize_vm(self, vm):
        '''
        Convert a VirtualMachine object to dict.

        :param vm: VirtualMachine object
        :return: dict
        '''
        result = self.serialize_obj(vm, AZURE_OBJECT_CLASS)
        result['powerstate'] = next((s.code.replace('PowerState/', '')
                                     for s in vm.instance_view.statuses if s.code.startswith('PowerState')), None)

        # Expand network interfaces to include config properties
        for interface in vm.network_profile.network_interfaces:
            int_dict = azure_id_to_dict(interface.id)
            nic = self.get_network_interface(int_dict['networkInterfaces'])
            for interface_dict in result['properties']['networkProfile']['networkInterfaces']:
                if interface_dict['id'] == interface.id:
                    nic_dict = self.serialize_obj(nic, 'NetworkInterface')
                    interface_dict['name'] = int_dict['networkInterfaces']
                    interface_dict['properties'] = nic_dict['properties']

        # Expand public IPs to include config porperties
        for interface in  result['properties']['networkProfile']['networkInterfaces']:
            for config in interface['properties']['ipConfigurations']:
                if config['properties'].get('publicIPAddress'):
                    pipid_dict = azure_id_to_dict(config['properties']['publicIPAddress']['id'])
                    try:
                        pip = self.network_client.public_ip_addresses.get(self.resource_group,
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

    def delete_vm(self, vm):
        vhd_uris = []
        nic_names = []
        pip_names = []

        if self.remove_on_absent.intersection(set(['all','virtual_storage'])):
            # store the attached vhd info so we can nuke it after the VM is gone
            self.log('Storing VHD URI for deletion')
            vhd_uris.append(vm.storage_profile.os_disk.vhd.uri)
            self.log("VHD URIs to delete: {0}".format(', '.join(vhd_uris)))
            self.results['deleted_vhd_uris'] = vhd_uris

        if self.remove_on_absent.intersection(set(['all','network_interfaces'])):
            # store the attached nic info so we can nuke them after the VM is gone
            self.log('Storing NIC names for deletion.')
            for interface in vm.network_profile.network_interfaces:
                id_dict = azure_id_to_dict(interface.id)
                nic_names.append(id_dict['networkInterfaces'])
            self.log('NIC names to delete {0}'.format(', '.join(nic_names)))
            self.results['deleted_network_interfaces'] = nic_names
            if self.remove_on_absent.intersection(set(['all','public_ips'])):
                # also store each nic's attached public IPs and delete after the NIC is gone
                for name in nic_names:
                    nic = self.get_network_interface(name)
                    for ipc in nic.ip_configurations:
                        if ipc.public_ip_address:
                            pip_dict = azure_id_to_dict(ipc.public_ip_address.id)
                            pip_names.append(pip_dict['publicIPAddresses'])
                self.log('Public IPs to  delete are {0}'.format(', '.join(pip_names)))
                self.results['deleted_public_ips'] = pip_names

        self.log("Deleting virtual machine {0}".format(self.name))
        self.results['actions'].append("Deleted virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machines.delete(self.resource_group, self.name)
            # wait for the poller to finish
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting virtual machine {0} - {1}".format(self.name, str(exc)))

        # TODO: parallelize nic, vhd, and public ip deletions with begin_deleting
        # TODO: best-effort to keep deleting other linked resources if we encounter an error
        if self.remove_on_absent.intersection(set(['all','virtual_storage'])):
            self.log('Deleting virtual storage')
            self.delete_vm_storage(vhd_uris)

        if self.remove_on_absent.intersection(set(['all','network_interfaces'])):
            self.log('Deleting network interfaces')
            for name in nic_names:
                self.delete_nic(name)

        if self.remove_on_absent.intersection(set(['all','public_ips'])):
            self.log('Deleting public IPs')
            for name in pip_names:
                self.delete_pip(name)
        return True

    def get_network_interface(self, name):
        try:
            nic = self.network_client.network_interfaces.get(self.resource_group, name)
            return nic
        except Exception as exc:
            self.fail("Error fetching network interface {0} - {1}".format(name, str(exc)))

    def delete_nic(self, name):
        self.log("Deleting network interface {0}".format(name))
        self.results['actions'].append("Deleted network interface {0}".format(name))
        try:
            poller = self.network_client.network_interfaces.delete(self.resource_group, name)
        except Exception as exc:
            self.fail("Error deleting network interface {0} - {1}".format(name, str(exc)))
        self.get_poller_result(poller)
        # Delete doesn't return anything. If we get this far, assume success
        return True

    def delete_pip(self, name):
        self.results['actions'].append("Deleted public IP {0}".format(name))
        try:
            poller = self.network_client.public_ip_addresses.delete(self.resource_group, name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting {0} - {1}".format(name, str(exc)))
        # Delete returns nada. If we get here, assume that all is well.
        return True

    def delete_vm_storage(self, vhd_uris):
        for uri in vhd_uris:
            self.log("Extracting info from blob uri '{0}'".format(uri))
            try:
                blob_parts = extract_names_from_blob_uri(uri)
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

    def get_image_version(self):
        try:
            versions = self.compute_client.virtual_machine_images.list(self.location,
                                                                       self.image['publisher'],
                                                                       self.image['offer'],
                                                                       self.image['sku'])
        except Exception as exc:
            self.fail("Error fetching image {0} {1} {2} - {4}".format(self.image['publisher'],
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

    def get_storage_account(self, name):
        try:
            account = self.storage_client.storage_accounts.get_properties(self.resource_group,
                                                                          name)
            return account
        except Exception as exc:
            self.fail("Error fetching storage account {0} - {1}".format(self.storage_account_name, str(exc)))

    def create_or_update_vm(self, params):
        try:
            poller = self.compute_client.virtual_machines.create_or_update(self.resource_group, self.name, params)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating or updating virtual machine {0} - {1}".format(self.name, str(exc)))
        return self.serialize_vm(self.get_vm())

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

        # Attempt to find a valid storage account name
        for i in range(0, 5):
            rand = random.randrange(1000, 9999)
            storage_account_name = self.name[:20] + str(rand)
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

        parameters = StorageAccountCreateParameters(account_type='Standard_LRS', location=self.location)
        self.log("Creating storage account {0} in location {1}".format(storage_account_name, self.location))
        self.results['actions'].append("Created storage account {0}".format(storage_account_name))
        try:
            poller = self.storage_client.storage_accounts.create(self.resource_group, storage_account_name, parameters)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Failed to create storage account: {0} - {1}".format(storage_account_name, str(exc)))
        return self.get_storage_account(storage_account_name)

    def check_storage_account_name(self, name):
        self.log("Checking storage account name availability for {0}".format(name))
        try:
            response = self.storage_client.storage_accounts.check_name_availability(name)
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

        if self.virtual_network_name:
            try:
                self.network_client.virtual_networks.list(self.resource_group, self.virtual_network_name)
                virtual_network_name = self.virtual_network_name
            except Exception as exc:
                self.fail("Error: fetching virtual network {0} - {1}".format(self.virtual_network_name, str(exc)))
        else:
            # Find a virtual network
            no_vnets_msg = "Error: unable to find virtual network in resource group {0}. A virtual network " \
                           "with at least one subnet must exist in order to create a NIC for the virtual " \
                           "machine.".format(self.resource_group)

            virtual_network_name = None
            try:
                vnets = self.network_client.virtual_networks.list(self.resource_group)
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
                subnet = self.network_client.subnets.get(self.resource_group, virtual_network_name)
                subnet_id = subnet.id
            except Exception as exc:
                self.fail("Error: fetching subnet {0} - {1}".format(self.subnet_name, str(exc)))
        else:
            no_subnets_msg = "Error: unable to find a subnet in virtual network {0}. A virtual network " \
                             "with at least one subnet must exist in order to create a NIC for the virtual " \
                             "machine.".format(virtual_network_name)

            subnet_id = None
            try:
                subnets = self.network_client.subnets.list(self.resource_group, virtual_network_name)
            except CloudError:
                self.fail(no_subnets_msg)

            for subnet in subnets:
                subnet_id = subnet.id
                self.log('subnet id: {0}'.format(subnet_id))
                break

            if not subnet_id:
                self.fail(no_subnets_msg)

        self.results['actions'].append('Created default public IP {0}'.format(self.name + '01'))
        pip = self.create_default_pip(self.resource_group, self.location, self.name, self.public_ip_allocation_method)

        self.results['actions'].append('Created default security group {0}'.format(self.name + '01'))
        group = self.create_default_securitygroup(self.resource_group, self.location, self.name, self.os_type,
                                                  self.open_ports)

        parameters = NetworkInterface(
            location=self.location,
            name=network_interface_name,
            ip_configurations=[
                NetworkInterfaceIPConfiguration(
                    name='default',
                    private_ip_allocation_method='Dynamic',
                )
            ]
        )
        parameters.ip_configurations[0].subnet = Subnet(id=subnet_id)
        parameters.network_security_group = NetworkSecurityGroup(id=group.id,
                                                                 name=group.name,
                                                                 location=group.location,
                                                                 resource_guid=group.resource_guid)
        parameters.ip_configurations[0].public_ip_address = PublicIPAddress(id=pip.id,
                                                                            name=pip.name,
                                                                            location=pip.location,
                                                                            resource_guid=pip.resource_guid)

        self.log("Creating NIC {0}".format(network_interface_name))
        self.log(self.serialize_obj(parameters, 'NetworkInterface'), pretty_print=True)
        self.results['actions'].append("Created NIC {0}".format(network_interface_name))
        try:
            poller = self.network_client.network_interfaces.create_or_update(self.resource_group,
                                                                             network_interface_name,
                                                                             parameters)
            new_nic = self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error creating network interface {0} - {1}".format(network_interface_name, str(exc)))
        return new_nic


def main():
    AzureRMVirtualMachine()

if __name__ == '__main__':
    main()

