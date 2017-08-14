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
'''
EXAMPLES = '''
'''  # NOQA

import random
import re

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.compute.models import NetworkInterfaceReference, \
                                          VirtualMachineScaleSet, HardwareProfile, \
                                          VirtualMachineScaleSetStorageProfile, VirtualMachineScaleSetOSProfile, \
                                          VirtualMachineScaleSetOSDisk, VirtualMachineScaleSetDataDisk, \
                                          VirtualHardDisk, VirtualMachineScaleSetManagedDiskParameters, \
                                          ImageReference, VirtualMachineScaleSetNetworkProfile, LinuxConfiguration, \
                                          SshConfiguration, SshPublicKey, VirtualMachineSizeTypes, \
                                          DiskCreateOptionTypes, CachingTypes, VirtualMachineScaleSetVMProfile, \
                                          VirtualMachineScaleSetIdentity, VirtualMachineScaleSetIPConfiguration, \
                                          VirtualMachineScaleSetPublicIPAddressConfigurationDnsSettings, \
                                          VirtualMachineScaleSetPublicIPAddressConfiguration, Sku, UpgradePolicy, \
                                          VirtualMachineScaleSetNetworkConfiguration, ApiEntityReference

    from azure.mgmt.network.models import PublicIPAddress, NetworkSecurityGroup, NetworkInterface, \
                                          NetworkInterfaceIPConfiguration, Subnet, VirtualNetwork

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
            capacity=dict(type='int', default=1),
            admin_username=dict(type='str'),
            admin_password=dict(type='str', no_log=True),
            ssh_password_enabled=dict(type='bool', default=True),
            ssh_public_keys=dict(type='list'),
            image=dict(type='dict'),
            os_disk_caching=dict(type='str', aliases=['disk_caching'], choices=['ReadOnly', 'ReadWrite'],
                                 default='ReadOnly'),
            os_type=dict(type='str', choices=['Linux', 'Windows'], default='Linux'),
            managed_disk_type=dict(type='str', choices=['Standard_LRS', 'Premium_LRS']),
            subnet_name=dict(type='str', aliases=['subnet']),
            virtual_network_resource_group=dict(type = 'str'),
            virtual_network_name=dict(type='str', aliases=['virtual_network']),
            remove_on_absent=dict(type='list', default=['all']),
            allocated=dict(type='bool', default=True),
            restarted=dict(type='bool', default=False),
            started=dict(type='bool', default=True),
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.short_hostname = None
        self.vm_size = None
        self.capacity = None
        self.admin_username = None
        self.admin_password = None
        self.ssh_password_enabled = None
        self.ssh_public_keys = None
        self.image = None
        self.os_disk_caching = None
        self.managed_disk_type = None
        self.os_type = None
        self.subnet_name = None
        self.virtual_network_resource_group = None
        self.virtual_network_name = None
        self.tags = None
        self.force = None
        self.allocated = None
        self.restarted = None
        self.started = None
        self.differences = None

        self.results = dict(
            changed=False,
            actions=[],
            powerstate_change=None,
            ansible_facts=dict(azure_vm=None)
        )

        super(AzureRMVirtualMachineScaleSet, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        # make sure options are lower case
        self.remove_on_absent = set([resource.lower() for resource in self.remove_on_absent])

        changed = False
        powerstate_change = None
        results = dict()
        vmss = None
        disable_ssh_password = None
        vmss_dict = None
        virtual_network = None
        subnet = None

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

            if self.image:
                if not self.image.get('publisher') or not self.image.get('offer') or not self.image.get('sku') \
                   or not self.image.get('version'):
                    self.error("parameter error: expecting image to contain publisher, offer, sku and version keys.")
                image_version = self.get_image_version()
                if self.image['version'] == 'latest':
                    self.image['version'] = image_version.name
                    self.log("Using image version {0}".format(self.image['version']))

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
                   self.os_disk_caching != vmss_dict['properties']['storageProfile']['osDisk']['caching']:
                    self.log('CHANGED: virtual machine scale set {0} - OS disk caching'.format(self.name))
                    differences.append('OS Disk caching')
                    changed = True
                    vmss_dict['properties']['storageProfile']['osDisk']['caching'] = self.os_disk_caching

                update_tags, vmss_dict['tags'] = self.update_tags(vmss_dict.get('tags', dict()))
                if update_tags:
                    differences.append('Tags')
                    changed = True

                if self.short_hostname and self.short_hostname != vmss_dict['properties']['osProfile']['computerName']:
                    self.log('CHANGED: virtual machine scale set {0} - short hostname'.format(self.name))
                    differences.append('Short Hostname')
                    changed = True
                    vmss_dict['properties']['osProfile']['computerName'] = self.short_hostname

                if self.started and vmss_dict['powerstate'] != 'running':
                    self.log("CHANGED: virtual machine scale set {0} not running and requested state 'running'".format(self.name))
                    changed = True
                    powerstate_change = 'poweron'
                elif self.state == 'present' and vmss_dict['powerstate'] == 'running' and self.restarted:
                    self.log("CHANGED: virtual machine scale set {0} {1} and requested state 'restarted'"
                             .format(self.name, vmss_dict['powerstate']))
                    changed = True
                    powerstate_change = 'restarted'
                elif self.state == 'present' and not self.allocated and vmss_dict['powerstate'] != 'deallocated':
                    self.log("CHANGED: virtual machine scale set {0} {1} and requested state 'deallocated'"
                             .format(self.name, vmss_dict['powerstate']))
                    changed = True
                    powerstate_change = 'deallocated'
                elif not self.started and vmss_dict['powerstate'] == 'running':
                    self.log("CHANGED: virtual machine scale set {0} running and requested state 'stopped'".format(self.name))
                    changed = True
                    powerstate_change = 'poweroff'

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
        self.results['powerstate_change'] = powerstate_change

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

                    if self.subnet_name:
                        subnet = self.get_subnet(self.virtual_network_name, self.subnet_name)

                    if not self.virtual_network_name:
                        default_vnet = self.create_default_vnet()
                        virtual_network = default_vnet.id

                    if not self.short_hostname:
                        self.short_hostname = self.name

                    managed_disk = VirtualMachineScaleSetManagedDiskParameters(storage_account_type=self.managed_disk_type)

                    # virtual_network = VirtualNetwork(id=id)
                    # subnet = Subnet(id=id)
                    # nics = [NetworkInterfaceReference(id=id) for id in network_interfaces]

                    vmss_resource = VirtualMachineScaleSet(
                        self.location,
                        tags=self.tags,
                        upgrade_policy=UpgradePolicy(
                            mode='Manual'
                        ),
                        sku=Sku(
                            name=self.vm_size,
                            capacity=self.capacity,
                            tier="Standard"
                        ),
                        virtual_machine_profile=VirtualMachineScaleSetVMProfile(
                            os_profile=VirtualMachineScaleSetOSProfile(
                                admin_username=self.admin_username,
                                computer_name_prefix=self.short_hostname,
                            ),
                            storage_profile=VirtualMachineScaleSetStorageProfile(
                                os_disk=VirtualMachineScaleSetOSDisk(
                                    managed_disk=managed_disk,
                                    create_option=DiskCreateOptionTypes.from_image,
                                    caching=self.os_disk_caching,
                                ),
                                image_reference=ImageReference(
                                    publisher=self.image['publisher'],
                                    offer=self.image['offer'],
                                    sku=self.image['sku'],
                                    version=self.image['version'],
                                ),
                            ),
                            network_profile=VirtualMachineScaleSetNetworkProfile(
                                network_interface_configurations=[
                                    VirtualMachineScaleSetNetworkConfiguration(
                                        name=self.name,
                                        primary=True,
                                        ip_configurations=[
                                            VirtualMachineScaleSetIPConfiguration(
                                                name='default',
                                                subnet=ApiEntityReference(
                                                    id=subnet.id
                                                )
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
                        vmss_resource.virtual_machine_profile.os_profile.linux_configuration = LinuxConfiguration(
                            disable_password_authentication=disable_ssh_password
                        )

                    if self.ssh_public_keys:
                        ssh_config = SshConfiguration()
                        ssh_config.public_keys = \
                            [SshPublicKey(path=key['path'], key_data=key['key_data']) for key in self.ssh_public_keys]
                        vmss_resource.virtual_machine_profile.os_profile.linux_configuration.ssh = ssh_config

                    self.log("Create virtual machine with parameters:")
                    self.create_or_update_vmss(vmss_resource)

                # Make sure we leave the machine in requested power state
                if (powerstate_change == 'poweron' and
                        self.results['ansible_facts']['azure_vmss']['powerstate'] != 'running'):
                    # Attempt to power on the machine
                    self.power_on_vmss()

                elif (powerstate_change == 'poweroff' and
                        self.results['ansible_facts']['azure_vmss']['powerstate'] == 'running'):
                    # Attempt to power off the machine
                    self.power_off_vmss()

                elif powerstate_change == 'restarted':
                    self.restart_vmss()

                elif powerstate_change == 'deallocated':
                    self.deallocate_vmss()

                self.results['ansible_facts']['azure_vmss'] = self.serialize_vmss(self.get_vmss())

            elif self.state == 'absent':
                # delete the VM
                self.log("Delete virtual machine {0}".format(self.name))
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
            vm = self.compute_client.virtual_machine_scale_sets.get(self.resource_group, self.name)
            return vm
        except Exception as exc:
            self.fail("Error getting virtual machine scale set {0} - {1}".format(self.name, str(exc)))

    def get_virtual_network(self, name):
        try:
            vnet = self.network_client.virtual_networks.get(self.resource_group, name)
            return vnet
        except Exception as exc:
            self.fail("Error fetching virtual network {0} - {1}".format(name, str(exc)))

    def get_subnet(self, vnet_name, subnet_name):
        self.log("Fetching subnet {0} in virtual network {1}".format(subnet_name, vnet_name))
        try:
            subnet = self.network_client.subnets.get(self.resource_group, vnet_name, subnet_name)
        except Exception as exc:
            self.fail("Error: fetching subnet {0} in virtual network {1} - {2}".format(subnet_name,
                                                                                      vnet_name,
                                                                                      str(exc)))
        return subnet

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

        result['powerstate'] = dict()
        vmss = self.compute_client.virtual_machine_scale_sets.get_instance_view(self.resource_group, self.name)

        if vmss.instance_view:
            result['powerstate'] = next((s.code.replace('PowerState/', '')
                                         for s in vmss.instance_view.statuses if s.code.startswith('PowerState')), None)

        # Expand public IPs to include config properties
        # for interface in result['properties']['networkProfile']['networkInterfaceConfigurations']:
        #     for config in interface['properties']['ipConfigurations']:
        #         if config['properties'].get('publicIPAddress'):
        #             pipid_dict = azure_id_to_dict(config['properties']['publicIPAddress']['id'])
        #             try:
        #                 pip = self.network_client.public_ip_addresses.get(self.resource_group,
        #                                                                   pipid_dict['publicIPAddresses'])
        #             except Exception as exc:
        #                 self.fail("Error fetching public ip {0} - {1}".format(pipid_dict['publicIPAddresses'],
        #                                                                       str(exc)))
        #             pip_dict = self.serialize_obj(pip, 'PublicIPAddress')
        #             config['properties']['publicIPAddress']['name'] = pipid_dict['publicIPAddresses']
        #             config['properties']['publicIPAddress']['properties'] = pip_dict['properties']

        self.log(result, pretty_print=True)
        if self.state != 'absent' and not result['powerstate']:
            self.fail("Failed to determine PowerState of virtual machine scale set {0}".format(self.name))
        return result

    def power_off_vmss(self):
        self.log("Powered off virtual machine {0}".format(self.name))
        self.results['actions'].append("Powered off virtual machine scale set {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machine_scale_sets.power_off(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error powering off virtual machine scale set {0} - {1}".format(self.name, str(exc)))
        return True

    def power_on_vmss(self):
        self.results['actions'].append("Powered on virtual machine scale set {0}".format(self.name))
        self.log("Power on virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machine_scale_sets.start(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error powering on virtual machine scale set {0} - {1}".format(self.name, str(exc)))
        return True

    def restart_vmss(self):
        self.results['actions'].append("Restarted virtual machine scale set {0}".format(self.name))
        self.log("Restart virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machine_scale_sets.restart(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error restarting virtual machine scale set {0} - {1}".format(self.name, str(exc)))
        return True

    def deallocate_vmss(self):
        self.results['actions'].append("Deallocated virtual machine scale set {0}".format(self.name))
        self.log("Deallocate virtual machine {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machine_scale_sets.deallocate(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deallocating virtual machine scale set {0} - {1}".format(self.name, str(exc)))
        return True

    def delete_vmss(self, vmss):
        self.log("Deleting virtual machine scale set {0}".format(self.name))
        self.results['actions'].append("Deleted virtual machine scale set {0}".format(self.name))
        try:
            poller = self.compute_client.virtual_machine_scale_sets.delete(self.resource_group, self.name)
            # wait for the poller to finish
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting virtual machine scale set {0} - {1}".format(self.name, str(exc)))

        return True

    def get_image_version(self):
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

    def create_or_update_vmss(self, params):
        try:
            poller = self.compute_client.virtual_machine_scale_sets.create_or_update(self.resource_group, self.name, params)
            self.get_poller_result(poller)
        except Exception as exc:
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

    # def create_default_nic(self):
    #     '''
    #     Create a default Network Interface <vm name>01. Requires an existing virtual network
    #     with one subnet. If NIC <vm name>01 exists, use it. Otherwise, create one.

    #     :return: NIC object
    #     '''

    #     network_interface_name = self.name + '01'
    #     nic = None

    #     self.log("Create default NIC {0}".format(network_interface_name))
    #     self.log("Check to see if NIC {0} exists".format(network_interface_name))
    #     try:
    #         nic = self.network_client.network_interfaces.get(self.resource_group, network_interface_name)
    #     except CloudError:
    #         pass

    #     if nic:
    #         self.log("NIC {0} found.".format(network_interface_name))
    #         self.check_provisioning_state(nic)
    #         return nic

    #     self.log("NIC {0} does not exist.".format(network_interface_name))

    #     virtual_network_resource_group = None
    #     if self.virtual_network_resource_group:
    #         virtual_network_resource_group = self.virtual_network_resource_group
    #     else:
    #         virtual_network_resource_group = self.resource_group

    #     if self.virtual_network_name:
    #         try:
    #             self.network_client.virtual_networks.list(virtual_network_resource_group, self.virtual_network_name)
    #             virtual_network_name = self.virtual_network_name
    #         except CloudError:
    #             self.fail("Error: fetching virtual network {0} - {1}".format(self.virtual_network_name, str(exc)))

    #     else:
    #         # Find a virtual network
    #         no_vnets_msg = "Error: unable to find virtual network in resource group {0}. A virtual network " \
    #                        "with at least one subnet must exist in order to create a NIC for the virtual " \
    #                        "machine.".format(self.resource_group)

    #         virtual_network_name = None
    #         try:
    #             vnets = self.network_client.virtual_networks.list(self.resource_group)
    #         except CloudError:
    #             self.log('cloud error!')
    #             self.fail(no_vnets_msg)

    #         for vnet in vnets:
    #             virtual_network_name = vnet.name
    #             self.log('vnet name: {0}'.format(vnet.name))
    #             break

    #         if not virtual_network_name:
    #             self.fail(no_vnets_msg)

    #     if self.subnet_name:
    #         try:
    #             subnet = self.network_client.subnets.get(self.resource_group, virtual_network_name, self.subnet_name)
    #             subnet_id = subnet.id
    #         except Exception as exc:
    #             self.fail("Error: fetching subnet {0} - {1}".format(self.subnet_name, str(exc)))
    #     else:
    #         no_subnets_msg = "Error: unable to find a subnet in virtual network {0}. A virtual network " \
    #                          "with at least one subnet must exist in order to create a NIC for the virtual " \
    #                          "machine.".format(virtual_network_name)

    #         subnet_id = None
    #         try:
    #             subnets = self.network_client.subnets.list(virtual_network_resource_group, virtual_network_name)
    #         except CloudError:
    #             self.fail(no_subnets_msg)

    #         for subnet in subnets:
    #             subnet_id = subnet.id
    #             self.log('subnet id: {0}'.format(subnet_id))
    #             break

    #         if not subnet_id:
    #             self.fail(no_subnets_msg)

    #     self.results['actions'].append('Created default public IP {0}'.format(self.name + '01'))
    #     pip = self.create_default_pip(self.resource_group, self.location, self.name, self.public_ip_allocation_method)

    #     self.results['actions'].append('Created default security group {0}'.format(self.name + '01'))
    #     group = self.create_default_securitygroup(self.resource_group, self.location, self.name, self.os_type,
    #                                               self.open_ports)

    #     parameters = NetworkInterface(
    #         location=self.location,
    #         ip_configurations=[
    #             NetworkInterfaceIPConfiguration(
    #                 private_ip_allocation_method='Dynamic',
    #             )
    #         ]
    #     )
    #     parameters.ip_configurations[0].subnet = Subnet(id=subnet_id)
    #     parameters.ip_configurations[0].name = 'default'
    #     parameters.network_security_group = NetworkSecurityGroup(id=group.id,
    #                                                              location=group.location,
    #                                                              resource_guid=group.resource_guid)
    #     parameters.ip_configurations[0].public_ip_address = PublicIPAddress(id=pip.id,
    #                                                                         location=pip.location,
    #                                                                         resource_guid=pip.resource_guid)

    #     self.log("Creating NIC {0}".format(network_interface_name))
    #     self.log(self.serialize_obj(parameters, 'NetworkInterface'), pretty_print=True)
    #     self.results['actions'].append("Created NIC {0}".format(network_interface_name))
    #     try:
    #         poller = self.network_client.network_interfaces.create_or_update(self.resource_group,
    #                                                                          network_interface_name,
    #                                                                          parameters)
    #         new_nic = self.get_poller_result(poller)
    #     except Exception as exc:
    #         self.fail("Error creating network interface {0} - {1}".format(network_interface_name, str(exc)))
    #     return new_nic


def main():
    AzureRMVirtualMachineScaleSet()

if __name__ == '__main__':
    main()
