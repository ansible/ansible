#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2013, Benno Joy <benno@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_subnet
short_description: Add/Remove subnet to an OpenStack network
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
   - Add or Remove a subnet to an OpenStack network
options:
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   network_name:
     description:
        - Name of the network to which the subnet should be attached
        - Required when I(state) is 'present'
   name:
     description:
       - The name of the subnet that should be created. Although Neutron
         allows for non-unique subnet names, this module enforces subnet
         name uniqueness.
     required: true
   cidr:
     description:
        - The CIDR representation of the subnet that should be assigned to
          the subnet. Required when I(state) is 'present' and a subnetpool
          is not specified.
   ip_version:
     description:
        - The IP version of the subnet 4 or 6
     default: 4
   enable_dhcp:
     description:
        - Whether DHCP should be enabled for this subnet.
     type: bool
     default: 'yes'
   gateway_ip:
     description:
        - The ip that would be assigned to the gateway for this subnet
   no_gateway_ip:
     description:
        - The gateway IP would not be assigned for this subnet
     type: bool
     default: 'no'
     version_added: "2.2"
   dns_nameservers:
     description:
        - List of DNS nameservers for this subnet.
   allocation_pool_start:
     description:
        - From the subnet pool the starting address from which the IP should
          be allocated.
   allocation_pool_end:
     description:
        - From the subnet pool the last IP that should be assigned to the
          virtual machines.
   host_routes:
     description:
        - A list of host route dictionaries for the subnet.
   ipv6_ra_mode:
     description:
        - IPv6 router advertisement mode
     choices: ['dhcpv6-stateful', 'dhcpv6-stateless', 'slaac']
   ipv6_address_mode:
     description:
        - IPv6 address mode
     choices: ['dhcpv6-stateful', 'dhcpv6-stateless', 'slaac']
   use_default_subnetpool:
     description:
        - Use the default subnetpool for I(ip_version) to obtain a CIDR.
     type: bool
     default: 'no'
   project:
     description:
        - Project name or ID containing the subnet (name admin-only)
     version_added: "2.1"
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
   extra_specs:
     description:
        - Dictionary with extra key/value pairs passed to the API
     required: false
     default: {}
     version_added: "2.7"
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Create a new (or update an existing) subnet on the specified network
- os_subnet:
    state: present
    network_name: network1
    name: net1subnet
    cidr: 192.168.0.0/24
    dns_nameservers:
       - 8.8.8.7
       - 8.8.8.8
    host_routes:
       - destination: 0.0.0.0/0
         nexthop: 12.34.56.78
       - destination: 192.168.0.0/24
         nexthop: 192.168.0.1

# Delete a subnet
- os_subnet:
    state: absent
    name: net1subnet

# Create an ipv6 stateless subnet
- os_subnet:
    state: present
    name: intv6
    network_name: internal
    ip_version: 6
    cidr: 2db8:1::/64
    dns_nameservers:
        - 2001:4860:4860::8888
        - 2001:4860:4860::8844
    ipv6_ra_mode: dhcpv6-stateless
    ipv6_address_mode: dhcpv6-stateless
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _can_update(subnet, module, cloud, filters=None):
    """Check for differences in non-updatable values"""
    network_name = module.params['network_name']
    ip_version = int(module.params['ip_version'])
    ipv6_ra_mode = module.params['ipv6_ra_mode']
    ipv6_a_mode = module.params['ipv6_address_mode']

    if network_name:
        network = cloud.get_network(network_name, filters)
        if network:
            netid = network['id']
        else:
            module.fail_json(msg='No network found for %s' % network_name)
        if netid != subnet['network_id']:
            module.fail_json(msg='Cannot update network_name in existing \
                                      subnet')
    if ip_version and subnet['ip_version'] != ip_version:
        module.fail_json(msg='Cannot update ip_version in existing subnet')
    if ipv6_ra_mode and subnet.get('ipv6_ra_mode', None) != ipv6_ra_mode:
        module.fail_json(msg='Cannot update ipv6_ra_mode in existing subnet')
    if ipv6_a_mode and subnet.get('ipv6_address_mode', None) != ipv6_a_mode:
        module.fail_json(msg='Cannot update ipv6_address_mode in existing \
                              subnet')


def _needs_update(subnet, module, cloud, filters=None):
    """Check for differences in the updatable values."""

    # First check if we are trying to update something we're not allowed to
    _can_update(subnet, module, cloud, filters)

    # now check for the things we are allowed to update
    enable_dhcp = module.params['enable_dhcp']
    subnet_name = module.params['name']
    pool_start = module.params['allocation_pool_start']
    pool_end = module.params['allocation_pool_end']
    gateway_ip = module.params['gateway_ip']
    no_gateway_ip = module.params['no_gateway_ip']
    dns = module.params['dns_nameservers']
    host_routes = module.params['host_routes']
    curr_pool = subnet['allocation_pools'][0]

    if subnet['enable_dhcp'] != enable_dhcp:
        return True
    if subnet_name and subnet['name'] != subnet_name:
        return True
    if pool_start and curr_pool['start'] != pool_start:
        return True
    if pool_end and curr_pool['end'] != pool_end:
        return True
    if gateway_ip and subnet['gateway_ip'] != gateway_ip:
        return True
    if dns and sorted(subnet['dns_nameservers']) != sorted(dns):
        return True
    if host_routes:
        curr_hr = sorted(subnet['host_routes'], key=lambda t: t.keys())
        new_hr = sorted(host_routes, key=lambda t: t.keys())
        if sorted(curr_hr) != sorted(new_hr):
            return True
    if no_gateway_ip and subnet['gateway_ip']:
        return True
    return False


def _system_state_change(module, subnet, cloud, filters=None):
    state = module.params['state']
    if state == 'present':
        if not subnet:
            return True
        return _needs_update(subnet, module, cloud, filters)
    if state == 'absent' and subnet:
        return True
    return False


def main():
    ipv6_mode_choices = ['dhcpv6-stateful', 'dhcpv6-stateless', 'slaac']
    argument_spec = openstack_full_argument_spec(
        name=dict(type='str', required=True),
        network_name=dict(type='str'),
        cidr=dict(type='str'),
        ip_version=dict(type='str', default='4', choices=['4', '6']),
        enable_dhcp=dict(type='bool', default=True),
        gateway_ip=dict(type='str'),
        no_gateway_ip=dict(type='bool', default=False),
        dns_nameservers=dict(type='list', default=None),
        allocation_pool_start=dict(type='str'),
        allocation_pool_end=dict(type='str'),
        host_routes=dict(type='list', default=None),
        ipv6_ra_mode=dict(type='str', choice=ipv6_mode_choices),
        ipv6_address_mode=dict(type='str', choice=ipv6_mode_choices),
        use_default_subnetpool=dict(type='bool', default=False),
        extra_specs=dict(type='dict', default=dict()),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        project=dict(type='str'),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           required_together=[
                               ['allocation_pool_end', 'allocation_pool_start'],
                           ],
                           **module_kwargs)

    state = module.params['state']
    network_name = module.params['network_name']
    cidr = module.params['cidr']
    ip_version = module.params['ip_version']
    enable_dhcp = module.params['enable_dhcp']
    subnet_name = module.params['name']
    gateway_ip = module.params['gateway_ip']
    no_gateway_ip = module.params['no_gateway_ip']
    dns = module.params['dns_nameservers']
    pool_start = module.params['allocation_pool_start']
    pool_end = module.params['allocation_pool_end']
    host_routes = module.params['host_routes']
    ipv6_ra_mode = module.params['ipv6_ra_mode']
    ipv6_a_mode = module.params['ipv6_address_mode']
    use_default_subnetpool = module.params['use_default_subnetpool']
    project = module.params.pop('project')
    extra_specs = module.params['extra_specs']

    # Check for required parameters when state == 'present'
    if state == 'present':
        if not module.params['network_name']:
            module.fail_json(msg='network_name required with present state')
        if (not module.params['cidr'] and not use_default_subnetpool and
                not extra_specs.get('subnetpool_id', False)):
            module.fail_json(msg='cidr or use_default_subnetpool or '
                                 'subnetpool_id required with present state')

    if pool_start and pool_end:
        pool = [dict(start=pool_start, end=pool_end)]
    else:
        pool = None

    if no_gateway_ip and gateway_ip:
        module.fail_json(msg='no_gateway_ip is not allowed with gateway_ip')

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if project is not None:
            proj = cloud.get_project(project)
            if proj is None:
                module.fail_json(msg='Project %s could not be found' % project)
            project_id = proj['id']
            filters = {'tenant_id': project_id}
        else:
            project_id = None
            filters = None

        subnet = cloud.get_subnet(subnet_name, filters=filters)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, subnet,
                                                          cloud, filters))

        if state == 'present':
            if not subnet:
                kwargs = dict(
                    cidr=cidr,
                    ip_version=ip_version,
                    enable_dhcp=enable_dhcp,
                    subnet_name=subnet_name,
                    gateway_ip=gateway_ip,
                    disable_gateway_ip=no_gateway_ip,
                    dns_nameservers=dns,
                    allocation_pools=pool,
                    host_routes=host_routes,
                    ipv6_ra_mode=ipv6_ra_mode,
                    ipv6_address_mode=ipv6_a_mode,
                    tenant_id=project_id)
                dup_args = set(kwargs.keys()) & set(extra_specs.keys())
                if dup_args:
                    raise ValueError('Duplicate key(s) {0} in extra_specs'
                                     .format(list(dup_args)))
                if use_default_subnetpool:
                    kwargs['use_default_subnetpool'] = use_default_subnetpool
                kwargs = dict(kwargs, **extra_specs)
                subnet = cloud.create_subnet(network_name, **kwargs)
                changed = True
            else:
                if _needs_update(subnet, module, cloud, filters):
                    cloud.update_subnet(subnet['id'],
                                        subnet_name=subnet_name,
                                        enable_dhcp=enable_dhcp,
                                        gateway_ip=gateway_ip,
                                        disable_gateway_ip=no_gateway_ip,
                                        dns_nameservers=dns,
                                        allocation_pools=pool,
                                        host_routes=host_routes)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed,
                             subnet=subnet,
                             id=subnet['id'])

        elif state == 'absent':
            if not subnet:
                changed = False
            else:
                changed = True
                cloud.delete_subnet(subnet_name)
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
