#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communications Cloud Infrastructure Services
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_server
short_description: Create, Update and Delete Servers
description:
    - Create, Update and Delete Servers
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        default: na
        choices:
          - Valid values can be found in nttmcp.common.config.py under
            APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTT LTD Cloud Web UI
    network_domain:
        description:
            - The name of the Cloud Network Domain
        required: false
    vlan:
        description:
            - The name of the vlan in which the server is housed
            - Not used for create
        required: false
    name:
        description:
            - The name of the server
        required: true
    description:
        description:
            - The description of the VLAN
        required: false
    image:
        description:
            - The name of the Image to use whend creating a new server
            - Use ntt_mcp_infrastructure -> state=get_image to get a list
            - of that available images
        required: false
    cpu:
        description:
            - CPU object with the following attributes
        required: false
        suboptions:
            speed:
                description:
                    - STANDARD, HIGHPERFORMANCE
                required: false
            count:
                description:
                    - The number of CPU sockets as an Integer
                required: false
            coresPerSocket:
                description:
                    - The number of cores per CPU socket as an Integer
                required: false
    memory_gb:
        description:
            - Integer value for the server memory size
        required: false
    network_info:
        description:
            - Network object with the following attributes
            - (primary_nic) (object)
            - (vlan) the name of the server's vlan OR
            - (privateIpv4) the IPv4 address to give the server
            - (additional_nic) (list of objects)
            - (vlan) the name of the server's vlan OR
            - (privateIpv4) the IPv4 address to give the server
        required: false
    primary_dns:
        description:
            - Primary DNS serverto assign to the server
        required: false
    secondary_dns:
        description:
            - Secondary DNS serverto assign to the server
        required: false
    ipv4_gw:
        description:
            - IPv4 default gateway
        required: false
    ipv6_gw:
        description:
            - IPv6 default gateway
        required: false
    disks:
        description:
            - List of disk objects containing
        required: false
        suboptions:
            id:
                description:
                    - The UUID of the disk
                required: false
            speed:
                description:
                    - STANDARD,HIGHPERFORMANCE,ECONOMY,PROVISIONEDIOPS
                required: false
            iops:
                description:
                    - The number of required IOPS as an Integer
                    - IOPS are only applicable for PROVISIONEDIOPS disk speeds
                    - Ensure IOPS is within the range for a disk size. The lower the IOPS the longer the deployment time
                    - The higher the IOPS the greater the cost
                required: false
    disk_id:
        description:
            - the disk UUID when expanding or modifying disks
        required: false
    disk_size:
        description:
            - The disk size when expanding a disk in GB
        required: false
    disk_iops:
        description:
            - The new required IOPS as an Integer when re-sizing a disk
            - If no value is provided and the current IOPS is less than 3 x
            - the new disk size a new IOPS count of 3 x the new disk size will be
            - applied.
        required: false
    admin_password:
        description:
            - The administrator/root password to assign to the new server
            - If left blank the module will generate and return one
        required: false
    start:
        description:
            - Whether to start the server after creation
        choices: [true, false]
        required: false
    ngoc:
        description:
            - Non Guest OS Customization - Used to specify that the image should not be customized during deployment
            - All IP addressing and OS accounts are created by the administrator outside of the cloud orchestration
            - This is used primarily for customer imported images
        choices: [true, false]
        default: false
        required: false
    server_state:
        description:
            - Various server states to check
        default: NORMAL
        required: false
    state:
        description:
            - The action to be performed
        required: true
        default: create
        choices: [create,delete,update,get,start,stop,hard_stop,expand_disk,reboot]
    wait:
        description:
            - Should Ansible wait for the task to complete before continuing
        required: false
        default: true
        choices: [true, false]
    wait_time:
        description:
            - The maximum time the Ansible should wait for the task to complete in seconds
        required: false
        default: 1800
    wait_poll_interval:
        description:
            - The time in between checking the status of the task in seconds
        required: false
        default: 10
    wait_for_vmtools:
        description:
            - Should Ansible wait for VMWare Tools to be running before continuing
            - This should only be used for server images that are running VMWare Tools
            - This should not be used for NGOC (Non Guest OS Customization) servers/images
        required: false
        default: false
        choices: [true, false]
notes:
    - N/A
'''

EXAMPLES = '''
# Create a Server
- name: Create a server
  ntt_mcp_server:
    region: na
    datacenter: NA9
    name: "APITEST"
    image: "CentOS 7 64-bit 2 CPU"
    disks:
      - id: "xxxx"
        speed: "STD"
      - id: "zzzz"
        speed: PROVISIONEDIOPS
        iops: 50
    cpu:
      speed: "STANDARD"
      count: 1
      coresPerSocket: 2
    network_info:
      network_domain: "xyz"
      primary_nic:
        vlan: "zyx"
      additional_nic:
        - networkAdapter: "VMXNET3"
          vlan: "abc"
          privateIpv4: "10.0.0.20"
  start: True
  wait_for_vmtools: True
  state: present
# Update a Server
- name: Update a server
  ntt_mcp_server:
    region: na
    datacenter: NA9
    network_domain: "xxxx"
    name: "APITEST"
    memory_gb: 4
    cpu:
      count: 2
      coresPerSocket: 2
    wait: True
    wait_for_vmtools: True
    start: True
    state: present
# Delete a Server
- name: Delete a server
  ntt_mcp_server:
    region: na
    datacenter: NA9
    name: "APITEST"
    wait: True
    state: absent
# Send a server a Start/Stop/Reboot command and wait for VMWare Tools to be running
- name: Command a server
  ntt_mcp_server:
    region: na
    datacenter: NA9
    network_domain: "APITEST"
    name: "yyyy"
    state: stop
    wait_for_vmtools: True
'''

RETURN = '''
data:
    description: Server objects
    returned: success
    type: complex
    contains:
        started:
            description: Is the server running
            type: bool
            returned: when state == present and wait is True
        guest:
            description: Information about the guest OS
            type: complex
            returned: when state == present and wait is True
            contains:
                osCustomization:
                    description: Does the image support guest OS customization
                    type: bool
                vmTools:
                    description: VMWare Tools information
                    type: complex
                    contains:
                        type:
                            description: VMWare Tools or Open VM Tools
                            type: str
                            sample: VMWARE_TOOLS
                        runningStatus:
                            description: Is VMWare Tools running
                            type: str
                            sample: NOT_RUNNING
                        apiVersion:
                            description: The version of VMWare Tools
                            type: int
                            sample: 9256
                        versionStatus:
                            description: Additional information
                            type: str
                            sample: NEED_UPGRADE
                operatingSystem:
                    description: Operating system information
                    type: complex
                    contains:
                        displayName:
                            description: The OS display name
                            type: str
                            sample: CENTOS7/64
                        id:
                            description: The OS UUID
                            type: str
                            sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                        family:
                            description: The OS family
                            type: str
                            sample: UNIX
                        osUnitsGroupId:
                            description: The OS billing group
                            type: str
                            sample: CENTOS
        source:
            description: The source of the image
            type: complex
            returned: when state == present and wait is True
            contains:
                type:
                    description: The id type of the image
                    type: str
                    sample: IMAGE_ID
                value:
                    description: The UUID of the image
                    type: str
                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
        floppy:
            description: List of the attached floppy drives
            type: complex
            returned: when state == present and wait is True
            contains:
                driveNumber:
                    description: The drive number
                    type: int
                    sample: 0
                state:
                    description: The state of the drive
                    type: str
                    sample: NORMAL
                id:
                    description: The UUID of the drive
                    type: str
                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                key:
                    description: Internal usage
                    type: int
                    sample: 8000
        networkInfo:
            description: Server network information
            type: complex
            returned: when state == present and wait is True
            contains:
                networkDomainId:
                    description: The UUID of the Cloud Network Domain the server resides in
                    type: str
                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                primaryNic:
                    description: The primary NIC on the server
                    type: complex
                    contains:
                        macAddress:
                            description: the MAC address
                            type: str
                            sample: aa:aa:aa:aa:aa:aa
                        vlanName:
                            description: The name of the VLAN the server resides in
                            type: str
                            sample: my_vlan
                        vlanId:
                            description: the UUID of the VLAN the server resides in
                            type: str
                            sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                        state:
                            description: The state of the NIC
                            type: str
                            sample: NORMAL
                        privateIpv4:
                            description: The IPv4 address of the server
                            type: str
                            sample: 10.0.0.10
                        connected:
                            description: Is the NIC connected
                            type: bool
                        key:
                            description: Internal Usage
                            type: int
                            sample: 4000
                        ipv6:
                            description: The IPv6 address of the server
                            type: str
                            sample: "1111:1111:1111:1111:0:0:0:1"
                        networkAdapter:
                            description: The VMWare NIC type
                            type: str
                            sample: VMXNET3
                        id:
                            description: The UUID of the NIC
                            type: str
                            sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
        ideController:
            description: List of the server's IDE controllers
            type: complex
            returned: when state == present and wait is True
            contains:
                state:
                    description: The state of the controller
                    type: str
                    sample: NORMAL
                channel:
                    description: The IDE channel number
                    type: int
                    sample: 0
                key:
                    description: Internal Usage
                    type: int
                    sample: 200
                adapterType:
                    description: The type of the controller
                    type: str
                    sample: IDE
                id:
                    description: The UUID of the controller
                    type: str
                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                deviceOrDisk:
                    description: List of the attached devices/disks
                    type: complex
                    contains:
                        device:
                            description: Device/Disk object
                            type: complex
                            contains:
                                slot:
                                    description: The slot number on the controller used by this device
                                    type: int
                                    sample: 0
                                state:
                                    description: The state of the device/disk
                                    type: str
                                    sample: NORMAL
                                type:
                                    description: The type of the device/disk
                                    type: str
                                    sample: CDROM
                                id:
                                    description: The UUID of the device/disk
                                    type: str
                                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
        createTime:
            description: The creation date of the server
            type: str
            returned: when state == present and wait is True
            sample: "2019-01-14T11:12:31.000Z"
        datacenterId:
            description: Datacenter id/location
            type: str
            returned: when state == present and wait is True
            sample: NA9
        scsiController:
            description: List of the SCSI controllers and disk configuration for the image
            type: complex
            returned: when state == present and wait is True
            contains:
                adapterType:
                    description: The name of the adapter
                    type: str
                    sample: "LSI_LOGIC_SAS"
                busNumber:
                    description: The SCSI bus number
                    type: int
                    sample: 1
                disk:
                    description: List of disks associated with this image
                    type: complex
                    contains:
                        id:
                            description: The disk id
                            type: str
                            sample: "112b7faa-ffff-ffff-ffff-dc273085cbe4"
                        scsiId:
                            description: The id of the disk on the SCSI controller
                            type: int
                            sample: 0
                        sizeGb:
                            description: The initial size of the disk in GB
                            type: int
                            sample: 10
                        speed:
                            description: The disk speed
                            type: str
                            sample: "STANDARD"
                id:
                    description: The SCSI controller id
                    type: str
                    sample: "112b7faa-ffff-ffff-ffff-dc273085cbe4"
                key:
                    description: Internal use
                    type: int
                    sample: 1000
        state:
            description: The state of the server
            type: str
            returned: when state == present and wait is True
            sample: NORMAL
        tag:
            description: List of informational tags associated with the server
            type: complex
            returned: when state == present and wait is True
            contains:
                value:
                    description: The tag value
                    type: str
                    sample: my_tag_value
                tagKeyName:
                    description: The tag name
                    type: str
                    sample: my_tag
                tagKeyId:
                    description: the UUID of the tag
                    type: str
                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
        virtualHardware:
            description: Information on the virtual hardware of the server
            type: complex
            returned: when state == present and wait is True
            contains:
                upToDate:
                    description: Is the VM hardware up to date
                    type: bool
                version:
                    description: The VM hardware version
                    type: str
                    sample: VMX-10
        memoryGb:
            description: Server memory in GB
            type: int
            returned: when state == present and wait is True
            sample: 4
        id:
            description: The UUID of the server
            type: str
            returned: when state == present
            sample:  b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
        sataController:
            description: List of SATA controllers on the server
            type: list
            returned: when state == present and wait is True
            contains:
                adapterType:
                    description: The name of the adapter
                    type: str
                    sample: "LSI_LOGIC_SAS"
                busNumber:
                    description: The SCSI bus number
                    type: int
                    sample: 1
                disk:
                    description: List of disks associated with this image
                    type: complex
                    contains:
                        id:
                            description: The disk id
                            type: str
                            sample: "112b7faa-ffff-ffff-ffff-dc273085cbe4"
                        scsiId:
                            description: The id of the disk on the SCSI controller
                            type: int
                            sample: 0
                        sizeGb:
                            description: The initial size of the disk in GB
                            type: int
                            sample: 10
                        speed:
                            description: The disk speed
                            type: str
                            sample: "STANDARD"
                id:
                    description: The SCSI controller id
                    type: str
                    sample: "112b7faa-ffff-ffff-ffff-dc273085cbe4"
                key:
                    description: Internal use
                    type: int
                    sample: 1000
        cpu:
            description: The default CPU specifications for the image
            type: complex
            returned: when state == present and wait is True
            contains:
                coresPerSocket:
                    description: # of cores per CPU socket
                    type: int
                    sample: 1
                count:
                    description: The number of CPUs
                    type: int
                    sample: 2
                speed:
                    description: The CPU reservation to be applied
                    type: str
                    sample: "STANDARD"
        deployed:
            description: Is the server deployed
            type: bool
            returned: when state == present and wait is True
        name:
            description: The name of the server
            type: str
            returned: when state == present and wait is True
            sample: my_server
        admin_password:
            description: The root/admin password allocated to the system if one was not provided
            type: str
            returned: when state == present
            sample: 'mypassword'
'''

import traceback
from time import sleep
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object, generate_password, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_config import (SERVER_STATES, VARIABLE_IOPS, IOPS_MULTIPLIER, DISK_CONTROLLER_TYPES,
                                                         MAX_IOPS_PER_GB, MAX_DISK_SIZE, MAX_DISK_IOPS)
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


CORE = {
    'module': None,
    'client': None,
    'region': None,
    'datacenter': None,
    'network_domain_id': None,
    'name': None,
    'wait_for_vmtools': False
    }


def create_server(module, client):
    """
    Create a server

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :returns: The created server
    """
    return_data = return_object('server')
    return_data['server'] = {}
    params = {}
    disks = module.params.get('disks')
    network = module.params.get('network_info')
    datacenter = module.params.get('datacenter')
    ngoc = module.params.get('ngoc')
    wait = module.params.get('wait')
    image_name = module.params.get('image')
    datacenter = module.params.get('datacenter')

    try:
        image = client.list_image(datacenter_id=datacenter, image_name=image_name)
        image_id = image.get('osImage')[0].get('id')
    except (KeyError, IndexError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed to find the  Image {0} - {1}'.format(image_name, e))

    # Check disk configurations
    if disks:
        params['disk'] = []
        for disk in disks:
            if 'id' in disk:
                if 'speed' not in disk:
                    module.fail_json(msg='Disk speed is required.')
                elif ('iops' in disk and disk['speed'] not in VARIABLE_IOPS):
                    module.fail_json(msg='Disk IOPS are required when disk_speed is: {0}.'.format(disk['speed']))
                params['disk'].append(disk)
            else:
                module.fail_json(msg='Disks IDs are required.')

    # Check and load the network configuration for the server
    params['networkInfo'] = {}
    try:
        if 'primary_nic' in network:
            primary_nic = {}
            if 'network_domain' in network:
                params['networkInfo']['networkDomainId'] = (
                    client.get_network_domain_by_name(
                        name=network['network_domain'],
                        datacenter=module.params['datacenter']
                    )['id']
                )
            else:
                module.fail_json(msg='A Cloud Network Domain is required.')
            if 'privateIpv4' in network['primary_nic']:
                primary_nic['privateIpv4'] = network['primary_nic']['privateIpv4']
            elif 'vlan' in network['primary_nic']:
                primary_nic['vlanId'] = client.get_vlan_by_name(name=network['primary_nic']['vlan'],
                                                                datacenter=module.params['datacenter'],
                                                                network_domain_id=params['networkInfo']['networkDomainId']
                                                               )['id']
            else:
                module.fail_json(msg='An IPv4 address or VLAN is required.')
            params['networkInfo']['primaryNic'] = primary_nic
        else:
            module.fail_json(msg='Primary NIC required.')

        if 'additional_nic' in network:
            additional_nic = []
            for nic in network['additional_nic']:
                new_nic = {}
                if 'networkAdapter' not in nic:
                    module.fail_json(msg='NIC Adapter is required')
                if 'privateIpv4' in nic:
                    new_nic['privateIpv4'] = nic['privateIpv4']
                elif 'vlan' in nic:
                    new_nic['vlanId'] = client.get_vlan_by_name(name=network['nic']['vlan'],
                                                                datacenter=module.params['datacenter'],
                                                                network_domain_id=(params['networkInfo']['networkDomainId'])
                                                               )['id']
                else:
                    module.fail_json('An IPv4 address of VLAN is required for additional NICs')
                additional_nic.append(new_nic)
            params['networkInfo']['additionalNic'] = additional_nic
    except (KeyError, IndexError, NTTMCPAPIException) as e:
        module.fail_json(msg='{0}'.format(e))

    network_domain_id = params['networkInfo']['networkDomainId']

    params['imageId'] = image_id
    params['name'] = module.params['name']
    params['start'] = module.params['start']
    if module.params['cpu']:
        params['cpu'] = module.params['cpu']
    if module.params['memory_gb']:
        params['memoryGb'] = module.params['memory_gb']
    if module.params['primary_dns']:
        params['primaryDns'] = module.params['primary_dns']
    if module.params['secondary_dns']:
        params['secondaryDns'] = module.params['secondary_dns']
    if module.params['ipv4_gw']:
        params['ipv4Gateway'] = module.params['ipv4_gw']
    if module.params['ipv6_gw']:
        params['ipv6Gateway'] = module.params['ipv6_gw']
    if not ngoc:
        if module.params['admin_password']:
            params['administratorPassword'] = module.params['admin_password']
        else:
            params['administratorPassword'] = generate_password()

    try:
        result = client.create_server(ngoc, params)
        new_server_id = result['info'][0]['value']
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not create the server - {0}'.format(e.message), exception=traceback.format_exc())

    if wait:
        wait_result = wait_for_server(module, client, params.get('name'), datacenter, network_domain_id, 'NORMAL', module.params.get('start'), None)
        if not wait_result:
            module.fail_json(msg='Timeout. Could not verify the server creation. Password: {0}'.format(params.get('administratorPassword')))
        wait_result['password'] = params.get('administratorPassword')
        return_data['server'] = wait_result
    else:
        return_data['server'] = {'id': new_server_id}

    if ngoc:
        msg = 'Server {0} has been successfully created '.format(params['name'])
    else:
        msg = 'Server {0} has been successfully created with the password: {1}'.format(params['name'], params['administratorPassword'])

    module.exit_json(changed=True, msg=msg, data=return_data['server'])


def update_server(module, client, server):
    """
    Update an existing server

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server: The dict containing the existing server to be updated
    :returns: The updated server
    """
    return_data = return_object('server')
    return_data['server'] = {}
    params = {}
    cpu = {}
    network_domain_id = server['networkInfo']['networkDomainId']
    datacenter = server['datacenterId']
    name = server['name']
    params['id'] = server['id']
    start = module.params['start']
    wait_for_vmtools = CORE['wait_for_vmtools']

    if module.params['cpu'] is not None:
        cpu = module.params['cpu']
        if 'count' in cpu:
            params['cpuCount'] = cpu['count']
        if 'coresPerSocket' in cpu:
            params['coresPerSocket'] = cpu['coresPerSocket']
        if 'speed' in cpu:
            params['cpuSpeed'] = cpu['speed']
    if module.params['memory_gb'] is not None:
        params['memoryGb'] = module.params['memory_gb']

    try:
        client.reconfigure_server(params=params)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not update the server - {0}'.format(e))
    # Temporarily disable any waiting for VMWare Tools
    CORE['wait_for_vmtools'] = False
    if module.params['wait']:
        wait_result = wait_for_server(module, client, name, datacenter, network_domain_id, 'NORMAL', False, False, None)
        if not wait_result:
            module.fail_json(msg='Timeout. Could not verify the server update was successful. Check manually')
        return_data['server'] = wait_result
    else:
        return_data['server'] = {'id': server['id']}
    # Reset waiting for VMWare Tools back to the user defined value
    CORE['wait_for_vmtools'] = wait_for_vmtools
    if start:
        server_command(module, client, server, 'start', True)

    module.exit_json(changed=True, data=return_data['server'])


def compare_server(module, server):
    """
    Compare two servers

    :arg module: The Ansible module instance
    :arg server: The existing server dict
    :returns: Any differences between the two Cloud Network Domains
    """
    params = {}
    existing_server = {}
    existing_server['cpu'] = server.get('cpu')
    existing_server['memoryGb'] = server.get('memoryGb')
    params['cpu'] = deepcopy(server.get('cpu'))
    params['memoryGb'] = server.get('memoryGb')
    if module.params.get('cpu'):
        params['cpu']['speed'] = module.params.get('cpu').get('speed', server.get('cpu').get('speed'))
        params['cpu']['count'] = module.params.get('cpu').get('count', server.get('cpu').get('count'))
        params['cpu']['coresPerSocket'] = module.params.get('cpu').get('coresPerSocket', server.get('cpu').get('coresPerSocket'))
    if module.params['memory_gb'] is not None:
        params['memoryGb'] = module.params.get('memory_gb')

    compare_result = compare_json(params, existing_server, None)
    if module.check_mode:
        module.exit_json(data=compare_result)
    return compare_result.get('changes')


def expand_disk(module, client, server):
    """
    Expand a existing disk

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server: The dict containing the server to be updated
    :returns: The updated server
    """
    disk_id = module.params.get('disk_id')
    disk_size = module.params.get('disk_size')
    disk_iops = module.params.get('disk_iops')
    if disk_id is None:
        module.fail_json(changed=False, msg='No disk id provided.')
    if disk_size is None:
        module.fail_json(msg='No size provided. A value larger than 10 is required for disk_size.')
    name = server.get('name')
    server_id = server.get('id')
    network_domain_id = server.get('networkInfo').get('networkDomainId')
    datacenter = server.get('datacenterId')
    wait_poll_interval = module.params.get('wait_poll_interval')
    start = module.params.get('start')
    wait_for_vmtools = CORE['wait_for_vmtools']

    # Check the disk ID provided is valid
    disk = get_disk_by_id(server, module.params.get('disk_id'))
    if not disk:
        module.fail_json(msg='Could not locate the disk {0}'.format(disk_id))

    # Temporarily disbale any waiting for VMWare Tools
    CORE['wait_for_vmtools'] = False

    # Check IOPS count is within minimum spec
    if disk.get('speed') == 'PROVISIONEDIOPS':
        disk_iops = validate_disk_iops(disk, disk_size, disk_iops)
        try:
            expand_piops_disk(server_id, disk, disk_size, disk_iops)
        except NTTMCPAPIException as e:
            module.fail_json(msg='Could not update the disk IOPS as required: {0}'.format(e))
    else:
        try:
            client.expand_disk(server_id=server_id, disk_id=disk_id, disk_size=disk_size)
        except NTTMCPAPIException as e:
            module.fail_json(msg='Could not expand the disk - {0}'.format(e))
        if module.params.get('wait'):
            wait_result = wait_for_server(module, client, name, datacenter, network_domain_id, 'NORMAL', False, False, wait_poll_interval)
            if not wait_result:
                module.fail_json(msg='Timeout. Could not verify the server update was successful. Check manually')

    # Reset VMWare Tools back to the user defined value
    CORE['wait_for_vmtools'] = wait_for_vmtools

    msg = 'Server disk has been successfully been expanded to {0}GB'.format(str(disk_size))

    if start:
        server_command(module, client, server, 'start', True)

    try:
        servers = client.list_servers(datacenter=datacenter, network_domain_id=network_domain_id)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Failed to get a list of servers - {0}'.format(e.message), exception=traceback.format_exc())

    server_exists = [x for x in servers if x['name'] == name]
    if server_exists:
        server = server_exists[0]
    else:
        server = []
    module.exit_json(changed=True, msg=msg, data=server)


def expand_piops_disk(server_id, disk, new_disk_size, new_disk_iops):
    """
    Wrapper function for expanding the size and iops on a provisioned IOPS disk

    :arg server_id: The UUID of the server
    :arg disk: The disk dictionary
    :arg new_disk_size: The end state size in GB
    :arg new_disk_iops: The final state IOPS count
    :returns: Nothing
    """
    if new_disk_size > MAX_DISK_SIZE:
        CORE.get('module').fail_json(msg='The disk size {0} is greater than the maximum allowed disk size {1}'.format(new_disk_size, MAX_DISK_SIZE))
    if new_disk_iops > MAX_DISK_IOPS:
        CORE.get('module').fail_json(msg='The disk iops {0} is greater than the maximum allowed disk IOPS {1}'.format(new_disk_iops, MAX_DISK_IOPS))
    try:
        update_piops_disk(server_id, disk.get('id'), disk.get('sizeGb'), disk.get('iops'), new_disk_size, new_disk_iops)
    except NTTMCPAPIException as e:
        CORE.get('module').fail_json(msg='Error modifying the disk {0}: {1}'.format(disk.get('id'), e))


def update_piops_disk(server_id, disk_id, current_size, current_iops, final_size, final_iops):
    """
    Handle the task increasing both IOPS and size on a provisioned IOPS disk in the correct order

    :arg server_id: The UUID of the server
    :arg disk_id: The UUID of the disk
    :arg current_iops: The current IOPS value for the disk
    :arg final_size: The end state size in GB
    :arg final_iops: The final state IOPS count
    :returns: Nothing
    """
    while current_size != final_size or current_iops != final_iops:
        current_max_iops = current_size * MAX_IOPS_PER_GB
        # Handle cases where the user did not specify an IOP count in the playbook
        if not final_iops:
            final_iops = IOPS_MULTIPLIER * final_size
        new_size = int(current_max_iops / IOPS_MULTIPLIER)
        if final_iops != current_iops and current_max_iops != current_iops:
            if current_max_iops < final_iops:
                CORE.get('client').change_iops(disk_id, current_max_iops)
                current_iops = current_max_iops
            else:
                if  not current_iops > final_iops:
                    CORE.get('client').change_iops(disk_id, final_iops)
                    current_iops = final_iops

            wait_result = wait_for_server(CORE.get('module'), CORE.get('client'), CORE.get('name'), CORE.get('datacenter'),
                                          CORE.get('network_domain_id'), 'NORMAL', False, False, 10)
            if not wait_result:
                CORE.get('module').fail_json(msg='Timeout. Could not verify the server update was successful. Check manually')

        if final_size != current_size:
            if new_size < final_size:
                CORE.get('client').expand_disk(server_id=server_id, disk_id=disk_id, disk_size=new_size)
                current_size = new_size
            else:
                if not current_size > final_size:
                    CORE.get('client').expand_disk(server_id=server_id, disk_id=disk_id, disk_size=final_size)
                    current_size = final_size

            wait_result = wait_for_server(CORE.get('module'), CORE.get('client'), CORE.get('name'), CORE.get('datacenter'),
                                          CORE.get('network_domain_id'), 'NORMAL', False, False, 10)
            if not wait_result:
                CORE.get('module').fail_json(msg='Timeout. Could not verify the server update was successful. Check manually')


def validate_disk_iops(disk, disk_size, disk_iops):
    '''
    Validate the IOPS count is correct for the specified disk and disk size

    :arg disk: The disk object
    :arg disk_size: The new disk size in GB
    :arg disk_iops: The new disk IOPS as specified in the argument spec
    :returns: The specified IOPS count if valid or the minimum valid count
    '''
    if disk.get('speed') == 'PROVISIONEDIOPS':
        existing_disk_iops = disk.get('iops')
        if disk_iops:
            if not disk_iops > (disk_size * IOPS_MULTIPLIER):
                disk_iops = disk_size * IOPS_MULTIPLIER
        else:
            if not existing_disk_iops > (disk_size * IOPS_MULTIPLIER):
                disk_iops = disk_size * IOPS_MULTIPLIER
            else:
                disk_iops = existing_disk_iops
    return disk_iops


def get_disk_by_id(server, disk_id):
    '''
    Get a disk object by the UUID

    :arg module: The Ansible module instance
    :arg server: The existing server object
    :arg disk_id: The UUID of the disk
    :returns: The located disk object or None
    '''
    for controller in DISK_CONTROLLER_TYPES:
        try:
            for controller_instance in server.get(controller):
                for disk in controller_instance.get('disk'):
                    if disk_id == disk.get('id'):
                        return disk
        except (IndexError, KeyError, AttributeError):
            pass
    return None

def server_command(module, client, server, command, should_return_data):
    """
    Send a command to a server

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server: The dict containing the server to be updated
    :arg command: The server command
    :arg should_return_data: True/False should the server object be returned
    :returns: The updated server
    """
    return_data = return_object('server')
    return_data['server'] = {}
    name = server['name']
    datacenter = server['datacenterId']
    network_domain_id = server['networkInfo']['networkDomainId']
    wait = module.params['wait']
    command_result = ''
    check_for_start = True
    check_for_stop = False
    # Set a default timer unless a lower one has been provided
    if module.params['wait_poll_interval'] < 15:
        wait_poll_interval = module.params['wait_poll_interval']
    else:
        wait_poll_interval = 15
    # If wait_for_vmtools is selected but not wait - set wait to True
    if CORE.get('wait_for_vmtools'):
        wait = True
        module.params['wait'] = True

    try:
        if command == "start":
            command_result = client.start_server(server_id=server['id'])
        elif command == "reboot":
            command_result = client.reboot_server(server_id=server['id'])
        elif command == "stop":
            command_result = client.shutdown_server(server_id=server['id'])
            check_for_start = False
            check_for_stop = True
        elif command == "hard_stop":
            command_result = client.poweroff_server(server_id=server['id'])
            check_for_start = False
            check_for_stop = True
        if wait:
            wait_result = wait_for_server(module, client, name, datacenter, network_domain_id, 'NORMAL', check_for_start, check_for_stop, wait_poll_interval)
            if not wait_result:
                module.fail_json(msg='Timeout. Could not verify the server command was successful. Check manually')
            msg = 'Command {0} successfully completed on server {1}'.format(command, name)
        else:
            msg = command_result
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not {0} the server - {1}'.format(command, e))
    if should_return_data:
        return_data['server'] = wait_result
        module.exit_json(changed=True, msg=msg, data=return_data)
    module.exit_json(changed=True, msg=msg)


def delete_server(module, client, server):
    """
    Delete a server

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain: The server dict
    :returns: A message
    """
    server_exists = True
    name = server['name']
    datacenter = server['datacenterId']
    network_domain_id = server['networkInfo']['networkDomainId']
    time = 0
    wait_time = module.params['wait_time']
    wait_poll_interval = module.params['wait_poll_interval']
    wait = module.params['wait']

    # Check if the server is running and shut it down
    if server['started']:
        try:
            client.shutdown_server(server_id=server['id'])
            wait_result = wait_for_server(module, client, name, datacenter, network_domain_id, 'NORMAL', False, True, wait_poll_interval)
            if not wait_result:
                module.fail_json(msg='Timeout. Could not verify the server deletion. Check manually')
        except NTTMCPAPIException as e:
            module.fail_json(msg='Could not shutdown the server - {0}'.format(e), exception=traceback.format_exc())

    try:
        client.delete_server(server['id'])
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not delete the server - {0}'.format(e), exception=traceback.format_exc())
    if wait:
        while server_exists and time < wait_time:
            servers = client.list_servers(datacenter=datacenter, network_domain_id=network_domain_id)
            server_exists = [x for x in servers if x.get('id') == server.get('id')]
            sleep(wait_poll_interval)
            time = time + wait_poll_interval

        if server_exists and time >= wait_time:
            module.fail_json(msg='Timeout waiting for the server to be deleted')

    module.exit_json(changed=True, msg='Server {0} has been successfully removed in {1}'.format(name, datacenter))


def wait_for_server(module, client, name, datacenter, network_domain_id, state, check_for_start=False, check_for_stop=False,
                    wait_poll_interval=None):
    """
    Wait for an operation on a server. Polls based on wait_time and wait_poll_interval values.

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg name: The name of the server
    :arg datacenter: The name of a MCP datacenter
    :arg network_domain_id: The UUID of the Cloud Network Domain
    :arg state: The desired state to wait
    :arg check_for_start: Check if the server is started
    :arg check_for_stop: Check if the server is stopped
    :arg wait_poll_interval: The time between polls
    :returns: The server dict
    """
    set_state = False
    actual_state = ''
    start_state = ''
    time = 0
    vmtools_status = False
    wait_for_vmtools = CORE.get('wait_for_vmtools')
    wait_time = module.params.get('wait_time')
    wait_required = False
    if wait_poll_interval is None:
        wait_poll_interval = module.params.get('wait_poll_interval')
    server = []
    while not set_state and time < wait_time:
        try:
            servers = client.list_servers(datacenter=datacenter, network_domain_id=network_domain_id)
        except NTTMCPAPIException as e:
            module.fail_json(msg='Failed to get a list of servers - {0}'.format(e.message), exception=traceback.format_exc())
        server = [x for x in servers if x['name'] == name]
        # Check if VMTools has started - if the user as specified to wait for VMWare Tools to be running
        try:
            if wait_for_vmtools:
                if server[0].get('guest').get('vmTools').get('runningStatus') == 'RUNNING':
                    vmtools_status = True
        except AttributeError:
            pass
        except IndexError:
            module.fail_json(msg='Failed to find the server - {0}'.format(name))
        try:
            actual_state = server[0]['state']
            start_state = server[0]['started']
        except (KeyError, IndexError) as e:
            module.fail_json(msg='Failed to find the server - {0}'.format(name))

        if actual_state != state:
            wait_required = True
        elif check_for_start and not start_state:
            wait_required = True
        elif check_for_stop and start_state:
            wait_required = True
        elif wait_for_vmtools and not vmtools_status:
            wait_required = True
        else:
            wait_required = False

        if wait_required:
            sleep(wait_poll_interval)
            time = time + wait_poll_interval
        else:
            set_state = True

    if server and time >= wait_time:
        return None

    return server[0]


def main():
    """
    Main function

    :returns: Server Information
    """
    ntt_mcp_regions = get_ntt_mcp_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=ntt_mcp_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(default=None, required=False, type='str'),
            vlan=dict(default=None, required=False, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            image=dict(required=False, type='str'),
            cpu=dict(required=False, type='dict'),
            memory_gb=dict(required=False, type='int'),
            network_info=dict(required=False, type='dict'),
            primary_dns=dict(required=False, type='str'),
            secondary_dns=dict(required=False, type='str'),
            ipv4_gw=dict(required=False, type='str'),
            ipv6_gw=dict(required=False, type='str'),
            disks=dict(required=False, type='list'),
            disk_id=dict(required=False, type='str'),
            disk_size=dict(required=False, type='int'),
            disk_iops=dict(required=False, type='int'),
            admin_password=dict(required=False, type='str'),
            ngoc=dict(required=False, default=False, type='bool'),
            start=dict(default=True, type='bool'),
            server_state=dict(default='NORMAL', choices=SERVER_STATES),
            started=dict(required=False, default=True, type='bool'),
            new_name=dict(required=False, default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent', 'start', 'stop', 'hard_stop', 'reboot', 'expand_disk']),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=1800, type='int'),
            wait_poll_interval=dict(required=False, default=30, type='int'),
            wait_for_vmtools=dict(required=False, default=False, type='bool'),
        ),
        supports_check_mode=True
    )

    credentials = get_credentials()
    name = module.params.get('name')
    CORE['name'] = module.params.get('name')
    datacenter = module.params.get('datacenter')
    CORE['datacenter'] = module.params.get('datacenter')
    CORE['region'] = module.params.get('region')
    CORE['wait_for_vmtools'] = module.params.get('wait_for_vmtools')
    state = module.params.get('state')
    network_domain_name = module.params.get('network_domain')
    vlan_name = module.params.get('vlan')
    vlan_id = None
    server_running = True
    start = module.params.get('start')
    server = {}

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND object based on the supplied name
    # This is more complicated in other modules because the network_domain can be supplied in multiple locations on this module
    try:
        if network_domain_name is None:
            try:
                network_domain_name = module.params.get('network_info').get('network_domain')
            except (TypeError, AttributeError):
                module.fail_json(msg='No network_domain or network_info.network_domain was provided')
        if network_domain_name is None:
            module.fail_json(msg='No network_domain or network_info.network_domain was provided')
        network = client.get_network_domain_by_name(datacenter=datacenter, name=network_domain_name)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Failed to find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Get the VLAN object based on the supplied name
    # This is more complicated than other modules because the vlan can be supplied in multiple locations on this module
    if state == 'present':
        try:
            if vlan_name is None:
                try:
                    vlan_name = module.params.get('network_info').get('primary_nic').get('vlan')
                except (TypeError, AttributeError):
                    module.fail_json(msg='No vlan or network_info.vlan was provided')
            if vlan_name is None:
                module.fail_json(msg='No vlan or network_info.vlan was provided')
            vlan = client.get_vlan_by_name(datacenter=datacenter, network_domain_id=network_domain_id, name=vlan_name)
            vlan_id = vlan.get('id')
        except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
            module.fail_json(msg='Failed to find the VLAN - {0}'.format(vlan_name))

    # Check if the Server exists based on the supplied name
    try:
        server = client.get_server_by_name(datacenter, network_domain_id, vlan_id, name)
        if server:
            server_running = server.get('started')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed attempting to locate any existing server - {0}'.format(e))

    # Setup the rest of the CORE dictionary to save passing data around
    CORE['network_domain_id'] = network_domain_id
    CORE['vlan_id'] = vlan_id
    CORE['module'] = module
    CORE['client'] = client
    # Create the Server
    if state == 'present':
        if not server:
            # Implement check_mode
            if module.check_mode:
                module.exit_json(msg='This server will be created', data=module.params)
            create_server(module, client)
        else:
            try:
                if compare_server(module, server):
                    if server_running:
                        module.fail_json(msg='Server cannot be updated while the it is running')
                    update_server(module, client, server)
                if start and not server_running:
                    server_command(module, client, server, 'start', False)
                server = client.get_server_by_name(datacenter, network_domain_id, vlan_id, name)
                module.exit_json(changed=False, data=server)
            except NTTMCPAPIException as e:
                module.fail_json(msg='Failed to update the server - {0}'.format(e))
    # Delete the Server
    elif state == 'absent':
        if not server:
            module.exit_json(msg='Server not found')
        # Implement check_mode
        if module.check_mode:
            module.exit_json(msg='Th server {0} with ID {1} will be removed'.format(server.get('name'), server.get('id')))
        delete_server(module, client, server)
    # Expand the disk on a Server
    elif state == 'expand_disk':
        if not server:
            module.fail_json(msg='Server not found')
        elif server_running:
            module.fail_json(msg='Disk cannot be expanded while the server is running')
        # Implement check_mode
        if module.check_mode:
            if not get_disk_by_id(server, module.params.get('disk_id')):
                module.fail_json(msg='The server {0} has no disk with ID {1}'.format(
                    server.get('name'),
                    module.params.get('disk_id')))
            module.exit_json(msg='The server {0} with ID {1} will have disk {2} expanded to {3}GB'.format(
                server.get('name'),
                server.get('id'),
                module.params.get('disk_id'),
                module.params.get('disk_size')))
        expand_disk(module, client, server)
    # Start a Server
    elif state == 'start':
        if not server:
            module.fail_json(msg='Server not found')
        elif server_running:
            module.exit_json(msg='Server is already running')
        # Implement check_mode
        if module.check_mode:
            module.exit_json(msg='The server {0} is ok to be started'.format(server.get('name')))
        server_command(module, client, server, state, False)
    # Stop a Server
    elif state == 'stop' or state == 'hard_stop':
        if not server:
            module.fail_json(msg='Server not found')
        elif not server_running:
            module.exit_json(msg='Server is already stopped')
        # Implement check_mode
        if module.check_mode:
            module.exit_json(msg='The server {0} is ok to be stopped'.format(server.get('name')))
        server_command(module, client, server, state, False)
    # Reboot a Server
    elif state == 'reboot':
        if not server:
            module.fail_json(msg='Server not found')
        # Implement check_mode
        if module.check_mode:
            module.exit_json(msg='The server {0} is ok to be rebooted'.format(server.get('name')))
        server_command(module, client, server, state, False)


if __name__ == '__main__':
    main()
