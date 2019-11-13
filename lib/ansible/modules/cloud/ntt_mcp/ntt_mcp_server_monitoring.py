#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Ken Sinfield <ken.sinfield@cis.ntt.com>
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
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_server_monitoring
short_description: Add or remove a disk controller configuration for an existing server
description:
    - Add or remove a disk controller configuration for an existing server
version_added: 2.10
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        type: str
        default: na
    datacenter:
        description:
            - The datacenter name
        required: true
        type: str
    network_domain:
        description:
            - The name of the Cloud Network Domain
        required: true
        type: str
    server:
        description:
            - The name of the server
        required: true
        type: str
    plan:
        description:
            - The type of monitoring plan
        required: false
        type: str
    state:
        description:
            - The action to be performed
        required: true
        type: str
        default: present
        choices:
            - present
            - absent
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Enable/Update Monitoring on a Server
    ntt_mcp_server_monitoring:
      region: na
      datacenter: NA12
      network_domain: myCND
      server: myServer01
      plan: ADVANCED
      state: present

  - name: Disable Monitoring on a Server
    ntt_mcp_server_monitoring:
      region: na
      datacenter: NA12
      network_domain: myCND
      server: myServer01
      state: absent
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
            returned: when state == present
        guest:
            description: Information about the guest OS
            type: complex
            returned: when state == present
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
                    description: Operating System information
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
            returned: when state == present
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
            returned: when state == present
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
            returned: when state == present
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
            returned: when state == present
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
            returned: when state == present
            sample: "2019-01-14T11:12:31.000Z"
        datacenterId:
            description: Datacenter id/location
            type: str
            returned: when state == present
            sample: NA9
        scsiController:
            description: List of the SCSI controllers and disk configuration for the image
            type: complex
            returned: when state == present
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
            returned: when state == present
            sample: NORMAL
        tag:
            description: List of informational tags associated with the server
            type: complex
            returned: when state == present
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
            returned: when state == present
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
            returned: when state == present
            sample: 4
        id:
            description: The UUID of the server
            type: str
            returned: when state == present
            sample:  b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
        sataController:
            description: List of SATA controllers on the server
            type: list
            returned: when state == present
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
            returned: when state == present
            contains:
                coresPerSocket:
                    description: The number of cores per CPU socket
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
            returned: when state == present
        name:
            description: The name of the server
            type: str
            returned: when state == present
            sample: my_server
        monitoring:
            description: Monitoring service
            type: complex
            returned: when state == present
            contains:
                monitoringId:
                    description: The ID of the monitoring instance
                    type: str
                    sample: "188"
                servicePlan:
                    description: The monitoring service plan
                    type: str
                    sample: ADVANCED
                state:
                    description: The state of the monitoring service
                    type: str
                    sample: NORMAL
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def add_monitoring(module, client, update, server_id):
    """
    Add monitoring to an existing server

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg update: Is this an update to an existing service
    :arg server_id: The UUID of the server to be updated
    :returns: The updated server
    """
    plan = module.params.get('plan')

    try:
        if update:
            client.enable_server_monitoring(True, server_id, plan)
        else:
            client.enable_server_monitoring(False, server_id, plan)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not configure server monitoring - {0}'.format(e))


def remove_monitoring(module, client, server_id):
    """
    Remove monitoring from an existing server

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg server_id: The UUID of the server to be updated
    :returns: The updated server
    """

    try:
        client.disable_server_monitoring(server_id)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could remove the server monitoring - {0}'.format(e))


def main():
    """
    Main function

    :returns: Server Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            server=dict(required=True, type='str'),
            plan=dict(required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    name = module.params.get('server')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    network_domain_name = module.params.get('network_domain')
    server = {}

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    try:
        client = NTTMCPClient(credentials, module.params.get('region'))
    except NTTMCPAPIException as e:
        module.fail_json(msg=e.msg)

    # Get the CND object based on the supplied name
    try:
        if network_domain_name is None:
            module.fail_json(msg='No network_domain or network_info.network_domain was provided')
        network = client.get_network_domain_by_name(datacenter=datacenter, name=network_domain_name)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Failed to find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if the Server exists based on the supplied name
    try:
        server = client.get_server_by_name(datacenter, network_domain_id, None, name)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed attempting to locate any existing server - {0}'.format(e))

    monitoring = server.get('monitoring', {})

    if state == 'present':
        # Implement Check Mode
        if module.check_mode:
            if not monitoring.get('servicePlan') == module.params.get('plan'):
                module.exit_json(msg='Monitoring of type {0} will be applied to server with ID {1}'.format(
                    module.params.get('plan'),
                    server.get('id')))
            else:
                module.exit_json(msg='No changes are required')
        if not monitoring:
            add_monitoring(module, client, False, server.get('id'))
        else:
            if monitoring.get('servicePlan') != module.params.get('plan'):
                add_monitoring(module, client, True, server.get('id'))
            else:
                module.exit_json(changed=False, data=server)
        try:
            server = client.get_server_by_name(datacenter, None, name)
        except NTTMCPAPIException:
            pass
        module.exit_json(changed=True, data=server)
    elif state == 'absent':
        try:
            if not monitoring:
                module.exit_json(msg='Server {0} does not currently have monitoring enabled'.format(
                    server.get('name')))
            # Implement Check Mode
            if module.check_mode:
                module.exit_json(msg='Monitoring of type {0} will be removed from the server with ID {1}'.format(
                    module.params.get('plan'),
                    server.get('id')))
            remove_monitoring(module, client, server.get('id'))
            try:
                server = client.get_server_by_name(datacenter, network_domain_id, None, name)
            except NTTMCPAPIException:
                pass
            module.exit_json(changed=True, data=server)
        except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
            module.fail_json(msg='Could not remove the monitoring from server {0} - {0}'.format(
                module.params.get('name'),
                e))


if __name__ == '__main__':
    main()
