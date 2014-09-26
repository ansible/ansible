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
    from novaclient.v1_1 import client as nova_client
    try:
        from neutronclient.neutron import client
    except ImportError:
        from quantumclient.quantum import client
    from keystoneclient.v2_0 import client as ksclient
    import time
except ImportError:
    print("failed=True msg='novaclient,keystoneclient and quantumclient (or neutronclient) are required'")

DOCUMENTATION = '''
---
module: quantum_floating_ip
version_added: "1.2"
short_description: Add/Remove floating IP from an instance
description:
   - Add or Remove a floating IP to an instance
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
   network_name:
     description:
        - Name of the network from which IP has to be assigned to VM. Please make sure the network is an external network
     required: true
     default: None
   instance_name:
     description:
        - The name of the instance to which the IP address should be assigned
     required: true
     default: None
   internal_network_name:
     description:
        - The name of the network of the port to associate with the floating ip. Necessary when VM multiple networks.
     required: false
     default: None
     version_added: "1.5"
requirements: ["novaclient", "quantumclient", "neutronclient", "keystoneclient"]
'''

EXAMPLES = '''
# Assign a floating ip to the instance from an external network
- quantum_floating_ip: state=present login_username=admin login_password=admin
                       login_tenant_name=admin network_name=external_network
                       instance_name=vm1 internal_network_name=internal_network
'''

def _get_ksclient(module, kwargs):
    try:
        kclient = ksclient.Client(username=kwargs.get('login_username'),
                                 password=kwargs.get('login_password'),
                                 tenant_name=kwargs.get('login_tenant_name'),
                                 auth_url=kwargs.get('auth_url'))
    except Exception, e:
        module.fail_json(msg = "Error authenticating to the keystone: %s " % e.message)
    global _os_keystone
    _os_keystone = kclient
    return kclient


def _get_endpoint(module, ksclient):
    try:
        endpoint = ksclient.service_catalog.url_for(service_type='network', endpoint_type='publicURL')
    except Exception, e:
        module.fail_json(msg = "Error getting network endpoint: %s" % e.message)
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
        module.fail_json(msg = "Error in connecting to neutron: %s " % e.message)
    return neutron

def _get_server_state(module, nova):
    server_info = None
    server = None
    try:
        for server in nova.servers.list():
            if server:
                info = server._info
                if info['name'] == module.params['instance_name']:
                    if info['status'] != 'ACTIVE' and module.params['state'] == 'present':
                        module.fail_json( msg="The VM is available but not Active. state:" + info['status'])
                    server_info = info
                    break
    except Exception, e:
        module.fail_json(msg = "Error in getting the server list: %s" % e.message)
    return server_info, server

def _get_port_info(neutron, module, instance_id, internal_network_name=None):
    subnet_id = None
    if internal_network_name:
        kwargs = {'name': internal_network_name}
        networks = neutron.list_networks(**kwargs)
        network_id = networks['networks'][0]['id']
        kwargs = {
            'network_id': network_id,
            'ip_version': 4
        }
        subnets = neutron.list_subnets(**kwargs)
        subnet_id = subnets['subnets'][0]['id']
    kwargs = {
            'device_id': instance_id,
    }
    try:
        ports = neutron.list_ports(**kwargs)
    except Exception, e:
        module.fail_json( msg = "Error in listing ports: %s" % e.message)
    if subnet_id:
        port = next(port for port in ports['ports'] if port['fixed_ips'][0]['subnet_id'] == subnet_id)
        port_id = port['id']
        fixed_ip_address = port['fixed_ips'][0]['ip_address']
    else:
        port_id = ports['ports'][0]['id']
        fixed_ip_address = ports['ports'][0]['fixed_ips'][0]['ip_address']
    if not ports['ports']:
        return None, None
    return fixed_ip_address, port_id

def _get_floating_ip(module, neutron, fixed_ip_address):
    kwargs = {
            'fixed_ip_address': fixed_ip_address
    }
    try:
        ips = neutron.list_floatingips(**kwargs)
    except Exception, e:
        module.fail_json(msg = "error in fetching the floatingips's %s" % e.message)
    if not ips['floatingips']:
        return None, None
    return ips['floatingips'][0]['id'], ips['floatingips'][0]['floating_ip_address']

def _create_floating_ip(neutron, module, port_id, net_id, fixed_ip):
    kwargs = {
            'port_id': port_id,
            'floating_network_id': net_id,
            'fixed_ip_address': fixed_ip
    }
    try:
        result = neutron.create_floatingip({'floatingip': kwargs})
    except Exception, e:
        module.fail_json(msg="There was an error in updating the floating ip address: %s" % e.message)
    module.exit_json(changed=True, result=result, public_ip=result['floatingip']['floating_ip_address'])

def _get_net_id(neutron, module):
    kwargs = {
        'name': module.params['network_name'],
    }
    try:
        networks = neutron.list_networks(**kwargs)
    except Exception, e:
        module.fail_json("Error in listing neutron networks: %s" % e.message)
    if not networks['networks']:
        return None
    return networks['networks'][0]['id']

def _update_floating_ip(neutron, module, port_id, floating_ip_id):
    kwargs = {
        'port_id': port_id
    }
    try:
        result = neutron.update_floatingip(floating_ip_id, {'floatingip': kwargs})
    except Exception, e:
        module.fail_json(msg="There was an error in updating the floating ip address: %s" % e.message)
    module.exit_json(changed=True, result=result)


def main():

    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
            network_name                    = dict(required=True),
            instance_name                   = dict(required=True),
            state                           = dict(default='present', choices=['absent', 'present']),
            internal_network_name           = dict(default=None),
    ))
    module = AnsibleModule(argument_spec=argument_spec)

    try:
        nova = nova_client.Client(module.params['login_username'], module.params['login_password'],
            module.params['login_tenant_name'], module.params['auth_url'], service_type='compute')
        neutron = _get_neutron_client(module, module.params)
    except Exception, e:
        module.fail_json(msg="Error in authenticating to nova: %s" % e.message)

    server_info, server_obj = _get_server_state(module, nova)
    if not server_info:
        module.fail_json(msg="The instance name provided cannot be found")

    fixed_ip, port_id = _get_port_info(neutron, module, server_info['id'], module.params['internal_network_name'])
    if not port_id:
        module.fail_json(msg="Cannot find a port for this instance, maybe fixed ip is not assigned")

    floating_id, floating_ip = _get_floating_ip(module, neutron, fixed_ip)

    if module.params['state'] == 'present':
        if floating_ip:
            module.exit_json(changed = False, public_ip=floating_ip)
        net_id = _get_net_id(neutron, module)
        if not net_id:
            module.fail_json(msg = "cannot find the network specified, please check")
        _create_floating_ip(neutron, module, port_id, net_id, fixed_ip)

    if module.params['state'] == 'absent':
        if floating_ip:
            _update_floating_ip(neutron, module, None, floating_id)
        module.exit_json(changed=False)

# this is magic, see lib/ansible/module.params['common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()

