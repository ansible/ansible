#!/usr/bin/python

# Copyright (c) 2016 IBM
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: os_port_info
short_description: Retrieve information about ports within OpenStack.
version_added: "2.1"
author: "David Shrewsbury (@Shrews)"
description:
    - Retrieve information about ports from OpenStack.
    - This module was called C(os_port_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(os_port_info) module no longer returns C(ansible_facts)!
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
    port:
        description:
            - Unique name or ID of a port.
    filters:
        description:
            - A dictionary of meta data to use for further filtering. Elements
              of this dictionary will be matched against the returned port
              dictionaries. Matching is currently limited to strings within
              the port dictionary, or strings within nested dictionaries.
    availability_zone:
      description:
        - Ignored. Present for backwards compatibility
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
# Gather information about all ports
- os_port_info:
    cloud: mycloud
  register: result

- debug:
    msg: "{{ result.openstack_ports }}"

# Gather information about a single port
- os_port_info:
    cloud: mycloud
    port: 6140317d-e676-31e1-8a4a-b1913814a471

# Gather information about all ports that have device_id set to a specific value
# and with a status of ACTIVE.
- os_port_info:
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
            type: bool
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
            type: str
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
            type: str
            sample: "normal"
        device_id:
            description: The UUID of the device that uses this port.
            returned: success
            type: str
            sample: "b4bd682d-234a-4091-aa5b-4b025a6a7759"
        device_owner:
            description: The UUID of the entity that uses this port.
            returned: success
            type: str
            sample: "network:router_interface"
        dns_assignment:
            description: DNS assignment information.
            returned: success
            type: list
        dns_name:
            description: DNS name
            returned: success
            type: str
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
            type: str
            sample: "3ec25c97-7052-4ab8-a8ba-92faf84148de"
        ip_address:
            description: The IP address.
            returned: success
            type: str
            sample: "127.0.0.1"
        mac_address:
            description: The MAC address.
            returned: success
            type: str
            sample: "00:00:5E:00:53:42"
        name:
            description: The port name.
            returned: success
            type: str
            sample: "port_name"
        network_id:
            description: The UUID of the attached network.
            returned: success
            type: str
            sample: "dd1ede4f-3952-4131-aab6-3b8902268c7d"
        port_security_enabled:
            description: The port security status. The status is enabled (true) or disabled (false).
            returned: success
            type: bool
            sample: false
        security_groups:
            description: The UUIDs of any attached security groups.
            returned: success
            type: list
        status:
            description: The port status.
            returned: success
            type: str
            sample: "ACTIVE"
        tenant_id:
            description: The UUID of the tenant who owns the network.
            returned: success
            type: str
            sample: "51fce036d7984ba6af4f6c849f65ef00"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def main():
    argument_spec = openstack_full_argument_spec(
        port=dict(required=False),
        filters=dict(type='dict', required=False),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)
    is_old_facts = module._name == 'os_port_facts'
    if is_old_facts:
        module.deprecate("The 'os_port_facts' module has been renamed to 'os_port_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    port = module.params.get('port')
    filters = module.params.get('filters')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        ports = cloud.search_ports(port, filters)
        if is_old_facts:
            module.exit_json(changed=False, ansible_facts=dict(
                openstack_ports=ports))
        else:
            module.exit_json(changed=False, openstack_ports=ports)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
