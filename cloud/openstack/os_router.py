#!/usr/bin/python
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
     required: false
     default: true
   enable_snat:
     description:
        - Enable Source NAT (SNAT) attribute.
     required: false
     default: true
   network:
     description:
        - Unique name or ID of the external gateway network.
     type: string
     required: true when I(interfaces) or I(enable_snat) are provided,
               false otherwise.
     default: None
   interfaces:
     description:
        - List of subnets to attach to the router. Each is a dictionary with
          the subnet name or ID (subnet) and the IP address to assign on that
          subnet (ip). If no IP is specified, one is automatically assigned from
          that subnet.
     required: false
     default: None
requirements: ["shade"]
'''

EXAMPLES = '''
# Create a simple router, not attached to a gateway or subnets.
- os_router:
    cloud: mycloud
    state: present
    name: simple_router

# Creates a router attached to ext_network1 and one subnet interface.
# An IP address from subnet1's IP range will automatically be assigned
# to that interface.
- os_router:
    cloud: mycloud
    state: present
    name: router1
    network: ext_network1
    interfaces:
      - subnet: subnet1

# Update existing router1 to include subnet2 (10.5.5.0/24), specifying
# the IP address within subnet2's IP range we'd like for that interface.
- os_router:
    cloud: mycloud
    state: present
    name: router1
    network: ext_network1
    interfaces:
      - subnet: subnet1
      - subnet: subnet2
        ip: 10.5.5.1

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
    type: dictionary
    contains:
        id:
            description: Router ID.
            type: string
            sample: "474acfe5-be34-494c-b339-50f06aa143e4"
        name:
            description: Router name.
            type: string
            sample: "router1"
        admin_state_up:
            description: Administrative state of the router.
            type: boolean
            sample: true
        status:
            description: The router status.
            type: string
            sample: "ACTIVE"
        tenant_id:
            description: The tenant ID.
            type: string
            sample: "861174b82b43463c9edc5202aadc60ef"
        external_gateway_info:
            description: The external gateway parameters.
            type: dictionary
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


def _needs_update(cloud, module, router, network):
    """Decide if the given router needs an update.
    """
    if router['admin_state_up'] != module.params['admin_state_up']:
        return True
    if router['external_gateway_info']['enable_snat'] != module.params['enable_snat']:
        return True
    if network:
        if router['external_gateway_info']['network_id'] != network['id']:
            return True

    # check subnet interfaces
    for new_iface in module.params['interfaces']:
        subnet = cloud.get_subnet(new_iface['subnet'])
        if not subnet:
            module.fail_json(msg='subnet %s not found' % new_iface['subnet'])
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

    return False

def _system_state_change(cloud, module, router, network):
    """Check if the system state would be changed."""
    state = module.params['state']
    if state == 'absent' and router:
        return True
    if state == 'present':
        if not router:
            return True
        return _needs_update(cloud, module, router, network)
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
        kwargs['enable_snat'] = module.params['enable_snat']

    if module.params['interfaces']:
        kwargs['ext_fixed_ips'] = []
        for iface in module.params['interfaces']:
            subnet = cloud.get_subnet(iface['subnet'])
            if not subnet:
                module.fail_json(msg='subnet %s not found' % iface['subnet'])
            d = {'subnet_id': subnet['id']}
            if 'ip' in iface:
                d['ip_address'] = iface['ip']
            kwargs['ext_fixed_ips'].append(d)

    return kwargs

def main():
    argument_spec = openstack_full_argument_spec(
        state=dict(default='present', choices=['absent', 'present']),
        name=dict(required=True),
        admin_state_up=dict(type='bool', default=True),
        enable_snat=dict(type='bool', default=True),
        network=dict(default=None),
        interfaces=dict(type='list', default=None)
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    name = module.params['name']
    network = module.params['network']

    if module.params['interfaces'] and not network:
        module.fail_json(msg='network is required when supplying interfaces')

    try:
        cloud = shade.openstack_cloud(**module.params)
        router = cloud.get_router(name)

        net = None
        if network:
            net = cloud.get_network(network)
            if not net:
                module.fail_json(msg='network %s not found' % network)

        if module.check_mode:
            module.exit_json(
                changed=_system_state_change(cloud, module, router, net)
            )

        if state == 'present':
            changed = False

            if not router:
                kwargs = _build_kwargs(cloud, module, router, net)
                router = cloud.create_router(**kwargs)
                changed = True
            else:
                if _needs_update(cloud, module, router, net):
                    kwargs = _build_kwargs(cloud, module, router, net)
                    router = cloud.update_router(**kwargs)
                    changed = True

            module.exit_json(changed=changed, router=router)

        elif state == 'absent':
            if not router:
                module.exit_json(changed=False)
            else:
                cloud.delete_router(name)
                module.exit_json(changed=True)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
