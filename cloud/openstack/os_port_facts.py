#!/usr/bin/python

# Copyright (c) 2016 IBM
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

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
module: os_port_facts
short_description: Retrieve facts about ports within OpenStack.
version_added: "2.1"
author: "David Shrewsbury (@Shrews)"
description:
    - Retrieve facts about ports from OpenStack.
notes:
    - Facts are placed in the C(openstack_ports) variable.
requirements:
    - "python >= 2.6"
    - "shade"
options:
    port:
        description:
            - Unique name or ID of a port.
        required: false
        default: null
    filters:
        description:
            - A dictionary of meta data to use for further filtering. Elements
              of this dictionary will be matched against the returned port
              dictionaries. Matching is currently limited to strings within
              the port dictionary, or strings within nested dictionaries.
        required: false
        default: null
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather facts about all ports
- os_port_facts:
    cloud: mycloud

# Gather facts about a single port
- os_port_facts:
    cloud: mycloud
    port: 6140317d-e676-31e1-8a4a-b1913814a471

# Gather facts about all ports that have device_id set to a specific value
# and with a status of ACTIVE.
- os_port_facts:
    cloud: mycloud
    filters:
      device_id: 1038a010-3a37-4a9d-82ea-652f1da36597
      status: ACTIVE
'''

RETURN = '''
openstack_ports:
    description: List of port dictionaries. A subset of the dictionary keys
                 listed below may be returned, depending on your cloud provider.
    returned: always, but can be null
    type: complex
    contains:
        admin_state_up:
            description: The administrative state of the router, which is
                         up (true) or down (false).
            returned: success
            type: boolean
            sample: true
        allowed_address_pairs:
            description: A set of zero or more allowed address pairs. An
                         address pair consists of an IP address and MAC address.
            returned: success
            type: list
            sample: []
        "binding:host_id":
            description: The UUID of the host where the port is allocated.
            returned: success
            type: string
            sample: "b4bd682d-234a-4091-aa5b-4b025a6a7759"
        "binding:profile":
            description: A dictionary the enables the application running on
                         the host to pass and receive VIF port-specific
                         information to the plug-in.
            returned: success
            type: dict
            sample: {}
        "binding:vif_details":
            description: A dictionary that enables the application to pass
                         information about functions that the Networking API
                         provides.
            returned: success
            type: dict
            sample: {"port_filter": true}
        "binding:vif_type":
            description: The VIF type for the port.
            returned: success
            type: dict
            sample: "ovs"
        "binding:vnic_type":
            description: The virtual network interface card (vNIC) type that is
                         bound to the neutron port.
            returned: success
            type: string
            sample: "normal"
        device_id:
            description: The UUID of the device that uses this port.
            returned: success
            type: string
            sample: "b4bd682d-234a-4091-aa5b-4b025a6a7759"
        device_owner:
            description: The UUID of the entity that uses this port.
            returned: success
            type: string
            sample: "network:router_interface"
        dns_assignment:
            description: DNS assignment information.
            returned: success
            type: list
        dns_name:
            description: DNS name
            returned: success
            type: string
            sample: ""
        extra_dhcp_opts:
            description: A set of zero or more extra DHCP option pairs.
                         An option pair consists of an option value and name.
            returned: success
            type: list
            sample: []
        fixed_ips:
            description: The IP addresses for the port. Includes the IP address
                         and UUID of the subnet.
            returned: success
            type: list
        id:
            description: The UUID of the port.
            returned: success
            type: string
            sample: "3ec25c97-7052-4ab8-a8ba-92faf84148de"
        ip_address:
            description: The IP address.
            returned: success
            type: string
            sample: "127.0.0.1"
        mac_address:
            description: The MAC address.
            returned: success
            type: string
            sample: "fa:16:30:5f:10:f1"
        name:
            description: The port name.
            returned: success
            type: string
            sample: "port_name"
        network_id:
            description: The UUID of the attached network.
            returned: success
            type: string
            sample: "dd1ede4f-3952-4131-aab6-3b8902268c7d"
        port_security_enabled:
            description: The port security status. The status is enabled (true) or disabled (false).
            returned: success
            type: boolean
            sample: false
        security_groups:
            description: The UUIDs of any attached security groups.
            returned: success
            type: list
        status:
            description: The port status.
            returned: success
            type: string
            sample: "ACTIVE"
        tenant_id:
            description: The UUID of the tenant who owns the network.
            returned: success
            type: string
            sample: "51fce036d7984ba6af4f6c849f65ef00"
'''


def main():
    argument_spec = openstack_full_argument_spec(
        port=dict(required=False),
        filters=dict(type='dict', required=False),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    port = module.params.pop('port')
    filters = module.params.pop('filters')

    try:
        cloud = shade.openstack_cloud(**module.params)
        ports = cloud.search_ports(port, filters)
        module.exit_json(changed=False, ansible_facts=dict(
            openstack_ports=ports))

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
