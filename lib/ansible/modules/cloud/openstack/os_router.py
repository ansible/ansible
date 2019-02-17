#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_router
short_description: Create or delete routers from OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
author: "David Shrewsbury (@Shrews)"
description:
   - Create or Delete routers from OpenStack. Although Neutron allows
     routers to share the same name, this module enforces name uniqueness
     to be more user friendly.
options:
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   name:
     description:
        - Name to be give to the router
     required: true
   admin_state_up:
     description:
        - Desired admin state of the created or existing router.
     type: bool
     default: 'yes'
   enable_snat:
     description:
        - Enable Source NAT (SNAT) attribute.
     type: bool
   network:
     description:
        - Unique name or ID of the external gateway network.
        - required I(interfaces) or I(enable_snat) are provided.
   project:
     description:
        - Unique name or ID of the project.
     version_added: "2.2"
   external_fixed_ips:
     description:
        - The IP address parameters for the external gateway network. Each
          is a dictionary with the subnet name or ID (subnet) and the IP
          address to assign on the subnet (ip). If no IP is specified,
          one is automatically assigned from that subnet.
   interfaces:
     description:
        - List of subnets to attach to the router internal interface. Default
          gateway associated with the subnet will be automatically attached
          with the router's internal interface.
          In order to provide an ip address different from the default
          gateway,parameters are passed as dictionary with keys as network
          name or ID(net), subnet name or ID (subnet) and the IP of
          port (portip) from the network.
          User defined portip is often required when a multiple router need
          to be connected to a single subnet for which the default gateway has
          been already used.
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements: ["openstacksdk"]
'''

EXAMPLES = '''
# Create a simple router, not attached to a gateway or subnets.
- os_router:
    cloud: mycloud
    state: present
    name: simple_router

# Create a simple router, not attached to a gateway or subnets for a given project.
- os_router:
    cloud: mycloud
    state: present
    name: simple_router
    project: myproj

# Creates a router attached to ext_network1 on an IPv4 subnet and one
# internal subnet interface.
- os_router:
    cloud: mycloud
    state: present
    name: router1
    network: ext_network1
    external_fixed_ips:
      - subnet: public-subnet
        ip: 172.24.4.2
    interfaces:
      - private-subnet

# Create another router with two internal subnet interfaces.One with user defined port
# ip and another with default gateway.
- os_router:
    cloud: mycloud
    state: present
    name: router2
    network: ext_network1
    interfaces:
      - net: private-net
        subnet: private-subnet
        portip: 10.1.1.10
      - project-subnet

# Create another router with two internal subnet interface.One with user defined port
# ip and and another with default gateway.
- os_router:
    cloud: mycloud
    state: present
    name: router2
    network: ext_network1
    interfaces:
      - net: private-net
        subnet: private-subnet
        portip: 10.1.1.10
      - project-subnet

# Create another router with two internal subnet interface. one with  user defined port
# ip and and another  with default gateway.
- os_router:
    cloud: mycloud
    state: present
    name: router2
    network: ext_network1
    interfaces:
      - net: private-net
        subnet: private-subnet
        portip: 10.1.1.10
      - project-subnet

# Update existing router1 external gateway to include the IPv6 subnet.
# Note that since 'interfaces' is not provided, any existing internal
# interfaces on an existing router will be left intact.
- os_router:
    cloud: mycloud
    state: present
    name: router1
    network: ext_network1
    external_fixed_ips:
      - subnet: public-subnet
        ip: 172.24.4.2
      - subnet: ipv6-public-subnet
        ip: 2001:db8::3

# Delete router1
- os_router:
    cloud: mycloud
    state: absent
    name: router1
'''

RETURN = '''
router:
    description: Dictionary describing the router.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Router ID.
            type: str
            sample: "474acfe5-be34-494c-b339-50f06aa143e4"
        name:
            description: Router name.
            type: str
            sample: "router1"
        admin_state_up:
            description: Administrative state of the router.
            type: bool
            sample: true
        status:
            description: The router status.
            type: str
            sample: "ACTIVE"
        tenant_id:
            description: The tenant ID.
            type: str
            sample: "861174b82b43463c9edc5202aadc60ef"
        external_gateway_info:
            description: The external gateway parameters.
            type: dict
            sample: {
                      "enable_snat": true,
                      "external_fixed_ips": [
                         {
                           "ip_address": "10.6.6.99",
                           "subnet_id": "4272cb52-a456-4c20-8f3c-c26024ecfa81"
                         }
                       ]
                    }
        routes:
            description: The extra routes configuration for L3 router.
            type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


ROUTER_INTERFACE_OWNERS = set([
    'network:router_interface',
    'network:router_interface_distributed',
    'network:ha_router_replicated_interface'
])


def _router_internal_interfaces(cloud, router):
    for port in cloud.list_router_interfaces(router, 'internal'):
        if port['device_owner'] in ROUTER_INTERFACE_OWNERS:
            yield port


def _needs_update(cloud, module, router, network, internal_subnet_ids, internal_port_ids, filters=None):
    """Decide if the given router needs an update.
    """
    if router['admin_state_up'] != module.params['admin_state_up']:
        return True
    if router['external_gateway_info']:
        # check if enable_snat is set in module params
        if module.params['enable_snat'] is not None:
            if router['external_gateway_info'].get('enable_snat', True) != module.params['enable_snat']:
                return True
    if network:
        if not router['external_gateway_info']:
            return True
        elif router['external_gateway_info']['network_id'] != network['id']:
            return True

    # check external interfaces
    if module.params['external_fixed_ips']:
        for new_iface in module.params['external_fixed_ips']:
            subnet = cloud.get_subnet(new_iface['subnet'], filters)
            exists = False

            # compare the requested interface with existing, looking for an existing match
            for existing_iface in router['external_gateway_info']['external_fixed_ips']:
                if existing_iface['subnet_id'] == subnet['id']:
                    if 'ip' in new_iface:
                        if existing_iface['ip_address'] == new_iface['ip']:
                            # both subnet id and ip address match
                            exists = True
                            break
                    else:
                        # only the subnet was given, so ip doesn't matter
                        exists = True
                        break

            # this interface isn't present on the existing router
            if not exists:
                return True

    # check internal interfaces
    if module.params['interfaces']:
        existing_subnet_ids = []
        for port in _router_internal_interfaces(cloud, router):
            if 'fixed_ips' in port:
                for fixed_ip in port['fixed_ips']:
                    existing_subnet_ids.append(fixed_ip['subnet_id'])

        for iface in module.params['interfaces']:
            if isinstance(iface, dict):
                for p_id in internal_port_ids:
                    p = cloud.get_port(name_or_id=p_id)
                    if 'fixed_ips' in p:
                        for fip in p['fixed_ips']:
                            internal_subnet_ids.append(fip['subnet_id'])

        if set(internal_subnet_ids) != set(existing_subnet_ids):
            internal_subnet_ids = []
            return True

    return False


def _system_state_change(cloud, module, router, network, internal_ids, internal_portids, filters=None):
    """Check if the system state would be changed."""
    state = module.params['state']
    if state == 'absent' and router:
        return True
    if state == 'present':
        if not router:
            return True
        return _needs_update(cloud, module, router, network, internal_ids, internal_portids, filters)
    return False


def _build_kwargs(cloud, module, router, network):
    kwargs = {
        'admin_state_up': module.params['admin_state_up'],
    }

    if router:
        kwargs['name_or_id'] = router['id']
    else:
        kwargs['name'] = module.params['name']

    if network:
        kwargs['ext_gateway_net_id'] = network['id']
        # can't send enable_snat unless we have a network
        if module.params.get('enable_snat') is not None:
            kwargs['enable_snat'] = module.params['enable_snat']

    if module.params['external_fixed_ips']:
        kwargs['ext_fixed_ips'] = []
        for iface in module.params['external_fixed_ips']:
            subnet = cloud.get_subnet(iface['subnet'])
            d = {'subnet_id': subnet['id']}
            if 'ip' in iface:
                d['ip_address'] = iface['ip']
            kwargs['ext_fixed_ips'].append(d)

    return kwargs


def _validate_subnets(module, cloud, filters=None):
    external_subnet_ids = []
    internal_subnet_ids = []
    internal_port_ids = []
    existing_port_ips = []
    existing_port_ids = []
    if module.params['external_fixed_ips']:
        for iface in module.params['external_fixed_ips']:
            subnet = cloud.get_subnet(iface['subnet'])
            if not subnet:
                module.fail_json(msg='subnet %s not found' % iface['subnet'])
            external_subnet_ids.append(subnet['id'])

    if module.params['interfaces']:
        for iface in module.params['interfaces']:
            if isinstance(iface, str):
                subnet = cloud.get_subnet(iface, filters)
                if not subnet:
                    module.fail_json(msg='subnet %s not found' % iface)
                internal_subnet_ids.append(subnet['id'])
            elif isinstance(iface, dict):
                subnet = cloud.get_subnet(iface['subnet'], filters)
                if not subnet:
                    module.fail_json(msg='subnet %s not found' % iface['subnet'])
                net = cloud.get_network(iface['net'])
                if not net:
                    module.fail_json(msg='net %s not found' % iface['net'])
                if "portip" not in iface:
                    internal_subnet_ids.append(subnet['id'])
                elif not iface['portip']:
                    module.fail_json(msg='put an ip in portip or  remove it from list to assign default port to router')
                else:
                    for existing_port in cloud.list_ports(filters={'network_id': net.id}):
                        for fixed_ip in existing_port['fixed_ips']:
                            if iface['portip'] == fixed_ip['ip_address']:
                                internal_port_ids.append(existing_port.id)
                                existing_port_ips.append(fixed_ip['ip_address'])
                    if iface['portip'] not in existing_port_ips:
                        p = cloud.create_port(network_id=net.id, fixed_ips=[{'ip_address': iface['portip'], 'subnet_id': subnet.id}])
                        if p:
                            internal_port_ids.append(p.id)

    return external_subnet_ids, internal_subnet_ids, internal_port_ids


def main():
    argument_spec = openstack_full_argument_spec(
        state=dict(default='present', choices=['absent', 'present']),
        name=dict(required=True),
        admin_state_up=dict(type='bool', default=True),
        enable_snat=dict(type='bool'),
        network=dict(default=None),
        interfaces=dict(type='list', default=None),
        external_fixed_ips=dict(type='list', default=None),
        project=dict(default=None)
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    state = module.params['state']
    name = module.params['name']
    network = module.params['network']
    project = module.params['project']

    if module.params['external_fixed_ips'] and not network:
        module.fail_json(msg='network is required when supplying external_fixed_ips')

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

        router = cloud.get_router(name, filters=filters)
        net = None
        if network:
            net = cloud.get_network(network)
            if not net:
                module.fail_json(msg='network %s not found' % network)

        # Validate and cache the subnet IDs so we can avoid duplicate checks
        # and expensive API calls.
        external_ids, subnet_internal_ids, internal_portids = _validate_subnets(module, cloud, filters)
        if module.check_mode:
            module.exit_json(
                changed=_system_state_change(cloud, module, router, net, subnet_internal_ids, internal_portids, filters)
            )

        if state == 'present':
            changed = False

            if not router:
                kwargs = _build_kwargs(cloud, module, router, net)
                if project_id:
                    kwargs['project_id'] = project_id
                router = cloud.create_router(**kwargs)
                for int_s_id in subnet_internal_ids:
                    cloud.add_router_interface(router, subnet_id=int_s_id)
                changed = True
                # add interface by port id as well
                for int_p_id in internal_portids:
                    cloud.add_router_interface(router, port_id=int_p_id)
                changed = True
            else:
                if _needs_update(cloud, module, router, net, subnet_internal_ids, internal_portids, filters):
                    kwargs = _build_kwargs(cloud, module, router, net)
                    updated_router = cloud.update_router(**kwargs)

                    # Protect against update_router() not actually
                    # updating the router.
                    if not updated_router:
                        changed = False

                    # On a router update, if any internal interfaces were supplied,
                    # just detach all existing internal interfaces and attach the new.
                    if internal_portids or subnet_internal_ids:
                        router = updated_router
                        ports = _router_internal_interfaces(cloud, router)
                        for port in ports:
                            cloud.remove_router_interface(router, port_id=port['id'])
                    if internal_portids:
                        external_ids, subnet_internal_ids, internal_portids = _validate_subnets(module, cloud, filters)
                        for int_p_id in internal_portids:
                            cloud.add_router_interface(router, port_id=int_p_id)
                        changed = True
                    if subnet_internal_ids:
                        for s_id in subnet_internal_ids:
                            cloud.add_router_interface(router, subnet_id=s_id)
                        changed = True

            module.exit_json(changed=changed,
                             router=router,
                             id=router['id'])

        elif state == 'absent':
            if not router:
                module.exit_json(changed=False)
            else:
                # We need to detach all internal interfaces on a router before
                # we will be allowed to delete it.
                ports = _router_internal_interfaces(cloud, router)
                router_id = router['id']
                for port in ports:
                    cloud.remove_router_interface(router, port_id=port['id'])
                cloud.delete_router(router_id)
                module.exit_json(changed=True)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
