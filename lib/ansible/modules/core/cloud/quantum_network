#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013, Benno Joy <benno@ansible.com>
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
    try:
        from neutronclient.neutron import client
    except ImportError:
        from quantumclient.quantum import client
    from keystoneclient.v2_0 import client as ksclient
except ImportError:
    print("failed=True msg='quantumclient (or neutronclient) and keystone client are required'")

DOCUMENTATION = '''
---
module: quantum_network
version_added: "1.4"
short_description: Creates/Removes networks from OpenStack
description:
   - Add or Remove network from OpenStack.
options:
   login_username:
     description:
        - login username to authenticate to keystone
     required: true
     default: admin
   login_password:
     description:
        - Password of login user
     required: true
     default: 'yes'
   login_tenant_name:
     description:
        - The tenant name of the login user
     required: true
     default: 'yes'
   tenant_name:
     description:
        - The name of the tenant for whom the network is created
     required: false
     default: None
   auth_url:
     description:
        - The keystone url for authentication
     required: false
     default: 'http://127.0.0.1:35357/v2.0/'
   region_name:
     description:
        - Name of the region
     required: false
     default: None
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   name:
     description:
        - Name to be assigned to the nework
     required: true
     default: None
   provider_network_type:
     description:
        - The type of the network to be created, gre, vlan, local. Available types depend on the plugin. The Quantum service decides if not specified.
     required: false
     default: None
   provider_physical_network:
     description:
        - The physical network which would realize the virtual network for flat and vlan networks.
     required: false
     default: None
   provider_segmentation_id:
     description:
        - The id that has to be assigned to the network, in case of vlan networks that would be vlan id and for gre the tunnel id
     required: false
     default: None
   router_external:
     description:
        - If 'yes', specifies that the virtual network is a external network (public).
     required: false
     default: false
   shared:
     description:
        - Whether this network is shared or not
     required: false
     default: false
   admin_state_up:
     description:
        - Whether the state should be marked as up or down
     required: false
     default: true
requirements: ["quantumclient", "neutronclient", "keystoneclient"]

'''

EXAMPLES = '''
# Create a GRE backed Quantum network with tunnel id 1 for tenant1
- quantum_network: name=t1network tenant_name=tenant1 state=present
                   provider_network_type=gre provider_segmentation_id=1
                   login_username=admin login_password=admin login_tenant_name=admin

# Create an external network
- quantum_network: name=external_network state=present
                   provider_network_type=local router_external=yes
                   login_username=admin login_password=admin login_tenant_name=admin
'''

_os_keystone = None
_os_tenant_id = None

def _get_ksclient(module, kwargs):
    try:
        kclient = ksclient.Client(username=kwargs.get('login_username'),
                                 password=kwargs.get('login_password'),
                                 tenant_name=kwargs.get('login_tenant_name'),
                                 auth_url=kwargs.get('auth_url'))
    except Exception, e:
        module.fail_json(msg = "Error authenticating to the keystone: %s" %e.message)
    global _os_keystone
    _os_keystone = kclient
    return kclient


def _get_endpoint(module, ksclient):
    try:
        endpoint = ksclient.service_catalog.url_for(service_type='network', endpoint_type='publicURL')
    except Exception, e:
        module.fail_json(msg = "Error getting network endpoint: %s " %e.message)
    return endpoint

def _get_neutron_client(module, kwargs):
    _ksclient = _get_ksclient(module, kwargs)
    token = _ksclient.auth_token
    endpoint = _get_endpoint(module, _ksclient)
    kwargs = {
            'token': token,
            'endpoint_url': endpoint
    }
    try:
        neutron = client.Client('2.0', **kwargs)
    except Exception, e:
        module.fail_json(msg = " Error in connecting to neutron: %s " %e.message)
    return neutron

def _set_tenant_id(module):
    global _os_tenant_id
    if not module.params['tenant_name']:
        tenant_name = module.params['login_tenant_name']
    else:
        tenant_name = module.params['tenant_name']

    for tenant in _os_keystone.tenants.list():
        if tenant.name == tenant_name:
            _os_tenant_id = tenant.id
            break
    if not _os_tenant_id:
        module.fail_json(msg = "The tenant id cannot be found, please check the parameters")


def _get_net_id(neutron, module):
    kwargs = {
            'tenant_id': _os_tenant_id,
            'name': module.params['name'],
    }
    try:
        networks = neutron.list_networks(**kwargs)
    except Exception, e:
        module.fail_json(msg = "Error in listing neutron networks: %s" % e.message)
    if not networks['networks']:
        return None
    return networks['networks'][0]['id']

def _create_network(module, neutron):

    neutron.format = 'json'

    network = {
        'name':                      module.params.get('name'),
        'tenant_id':                 _os_tenant_id,
        'provider:network_type':     module.params.get('provider_network_type'),
        'provider:physical_network': module.params.get('provider_physical_network'),
        'provider:segmentation_id':  module.params.get('provider_segmentation_id'),
        'router:external':           module.params.get('router_external'),
        'shared':                    module.params.get('shared'),
        'admin_state_up':            module.params.get('admin_state_up'),
    }

    if module.params['provider_network_type'] == 'local':
        network.pop('provider:physical_network', None)
        network.pop('provider:segmentation_id', None)

    if module.params['provider_network_type'] == 'flat':
        network.pop('provider:segmentation_id', None)

    if module.params['provider_network_type'] == 'gre':
        network.pop('provider:physical_network', None)

    if module.params['provider_network_type'] is None:
        network.pop('provider:network_type', None)
        network.pop('provider:physical_network', None)
        network.pop('provider:segmentation_id', None)

    try:
        net = neutron.create_network({'network':network})
    except Exception, e:
        module.fail_json(msg = "Error in creating network: %s" % e.message)
    return net['network']['id']

def _delete_network(module, net_id, neutron):

    try:
        id = neutron.delete_network(net_id)
    except Exception, e:
        module.fail_json(msg = "Error in deleting the network: %s" % e.message)
    return True

def main():

    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
            name                            = dict(required=True),
            tenant_name                     = dict(default=None),
            provider_network_type           = dict(default=None, choices=['local', 'vlan', 'flat', 'gre']),
            provider_physical_network       = dict(default=None),
            provider_segmentation_id        = dict(default=None),
            router_external                 = dict(default=False, type='bool'),
            shared                          = dict(default=False, type='bool'),
            admin_state_up                  = dict(default=True, type='bool'),
            state                           = dict(default='present', choices=['absent', 'present'])
    ))
    module = AnsibleModule(argument_spec=argument_spec)

    if module.params['provider_network_type'] in ['vlan' , 'flat']:
            if not module.params['provider_physical_network']:
                module.fail_json(msg = " for vlan and flat networks, variable provider_physical_network should be set.")

    if module.params['provider_network_type']  in ['vlan', 'gre']:
            if not module.params['provider_segmentation_id']:
                module.fail_json(msg = " for vlan & gre networks, variable provider_segmentation_id should be set.")

    neutron = _get_neutron_client(module, module.params)

    _set_tenant_id(module)

    if module.params['state'] == 'present':
        network_id = _get_net_id(neutron, module)
        if not network_id:
            network_id = _create_network(module, neutron)
            module.exit_json(changed = True, result = "Created", id = network_id)
        else:
            module.exit_json(changed = False, result = "Success", id = network_id)

    if module.params['state'] == 'absent':
        network_id = _get_net_id(neutron, module)
        if not network_id:
            module.exit_json(changed = False, result = "Success")
        else:
            _delete_network(module, network_id, neutron)
            module.exit_json(changed = True, result = "Deleted")

# this is magic, see lib/ansible/module.params['common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()

