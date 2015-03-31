#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
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
module: os_router_gateway
short_description: set/unset a gateway interface for the router with the specified external network
version_added: "1.10"
extends_documentation_fragment: openstack
description:
   - Creates/Removes a gateway interface from the router, used to associate a external network with a router to route external traffic.
options:
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   router_name:
     description:
        - Name of the router to which the gateway should be attached.
     required: true
     default: None
   network_name:
     description:
        - Name of the external network which should be attached to the router.
     required: true
     default: None
requirements: ["shade"]
'''

EXAMPLES = '''
# Attach an external network with a router to allow flow of external traffic
- os_router_gateway: state=present username=admin password=admin
                     project_name=admin router_name=external_router
                     network_name=external_network
'''


def _get_router_id(module, neutron):
    kwargs = {
            'name': module.params['router_name'],
    }
    try:
        routers = neutron.list_routers(**kwargs)
    except Exception, e:
        module.fail_json(msg = "Error in getting the router list: %s " % e.message)
    if not routers['routers']:
            return None
    return routers['routers'][0]['id']

def _get_net_id(neutron, module):
    kwargs = {
        'name':            module.params['network_name'],
        'router:external': True
    }
    try:
        networks = neutron.list_networks(**kwargs)
    except Exception, e:
        module.fail_json("Error in listing neutron networks: %s" % e.message)
    if not networks['networks']:
        return None
    return networks['networks'][0]['id']

def _get_port_id(neutron, module, router_id, network_id):
    kwargs = {
        'device_id': router_id,
        'network_id': network_id,
    }
    try:
        ports = neutron.list_ports(**kwargs)
    except Exception, e:
        module.fail_json( msg = "Error in listing ports: %s" % e.message)
    if not ports['ports']:
        return None
    return ports['ports'][0]['id']

def _add_gateway_router(neutron, module, router_id, network_id):
    kwargs = {
        'network_id': network_id
    }
    try:
        neutron.add_gateway_router(router_id, kwargs)
    except Exception, e:
        module.fail_json(msg = "Error in adding gateway to router: %s" % e.message)
    return True

def  _remove_gateway_router(neutron, module, router_id):
    try:
        neutron.remove_gateway_router(router_id)
    except Exception, e:
        module.fail_json(msg = "Error in removing gateway to router: %s" % e.message)
    return True

def main():

    argument_spec = openstack_argument_spec(
        router_name        = dict(required=True),
        network_name       = dict(required=True),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)
        neutron = cloud.neutron_client

        router_id = _get_router_id(module, neutron)

        if not router_id:
            module.fail_json(msg="failed to get the router id, please check the router name")

        network_id = _get_net_id(neutron, module)
        if not network_id:
            module.fail_json(msg="failed to get the network id, please check the network name and make sure it is external")

        if module.params['state'] == 'present':
            port_id = _get_port_id(neutron, module, router_id, network_id)
            if not port_id:
                _add_gateway_router(neutron, module, router_id, network_id)
                module.exit_json(changed=True, result="created")
            module.exit_json(changed=False, result="success")

        if module.params['state'] == 'absent':
            port_id = _get_port_id(neutron, module, router_id, network_id)
            if not port_id:
                module.exit_json(changed=False, result="Success")
            _remove_gateway_router(neutron, module, router_id)
            module.exit_json(changed=True, result="Deleted")
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()

