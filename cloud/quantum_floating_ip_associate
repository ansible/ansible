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
    print "failed=True msg='novaclient, keystone, and quantumclient (or neutronclient) client are required'"

DOCUMENTATION = '''
---
module: quantum_floating_ip_associate
version_added: "1.2"
short_description: Associate or disassociate a particular floating IP with an instance
description:
   - Associates or disassociates a specific floating IP with a particular instance
options:
   login_username:
     description:
        - login username to authenticate to keystone
     required: true
     default: admin
   login_password:
     description:
        - password of login user
     required: true
     default: 'yes'
   login_tenant_name:
     description:
        - the tenant name of the login user
     required: true
     default: true
   auth_url:
     description:
        - the keystone url for authentication
     required: false
     default: 'http://127.0.0.1:35357/v2.0/'
   region_name:
     description:
        - name of the region
     required: false
     default: None
   state:
     description:
        - indicates the desired state of the resource
     choices: ['present', 'absent']
     default: present
   instance_name:
     description:
        - name of the instance to which the public IP should be assigned
     required: true
     default: None
   ip_address:
     description:
        - floating ip that should be assigned to the instance
     required: true
     default: None
requirements: ["quantumclient", "neutronclient", "keystoneclient"]
'''

EXAMPLES = '''
# Associate a specific floating IP with an Instance
- quantum_floating_ip_associate:
           state=present
           login_username=admin
           login_password=admin
           login_tenant_name=admin
           ip_address=1.1.1.1
           instance_name=vm1
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
                        module.fail_json(msg="The VM is available but not Active. state:" + info['status'])
                    server_info = info
                    break
    except Exception, e:
            module.fail_json(msg = "Error in getting the server list: %s" % e.message)
    return server_info, server

def _get_port_id(neutron, module, instance_id):
    kwargs = dict(device_id = instance_id)
    try:
        ports = neutron.list_ports(**kwargs)
    except Exception, e:
        module.fail_json( msg = "Error in listing ports: %s" % e.message)
    if not ports['ports']:
        return None
    return ports['ports'][0]['id']

def _get_floating_ip_id(module, neutron):
    kwargs = {
        'floating_ip_address': module.params['ip_address']
    }
    try:
        ips = neutron.list_floatingips(**kwargs)
    except Exception, e:
        module.fail_json(msg = "error in fetching the floatingips's %s" % e.message)
    if not ips['floatingips']:
        module.fail_json(msg = "Could find the ip specified in parameter, Please check")
    ip = ips['floatingips'][0]['id']
    if not ips['floatingips'][0]['port_id']:
        state = "detached"
    else:
        state = "attached"
    return state, ip

def _update_floating_ip(neutron, module, port_id, floating_ip_id):
    kwargs = {
        'port_id': port_id
    }
    try:
        result = neutron.update_floatingip(floating_ip_id, {'floatingip': kwargs})
    except Exception, e:
        module.fail_json(msg = "There was an error in updating the floating ip address: %s" % e.message)
    module.exit_json(changed = True, result = result, public_ip=module.params['ip_address'])

def main():

    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
            ip_address                      = dict(required=True),
            instance_name                   = dict(required=True),
            state                           = dict(default='present', choices=['absent', 'present'])
    ))
    module = AnsibleModule(argument_spec=argument_spec)

    try:
        nova = nova_client.Client(module.params['login_username'], module.params['login_password'],
                                 module.params['login_tenant_name'], module.params['auth_url'], service_type='compute')
    except Exception, e:
        module.fail_json( msg = " Error in authenticating to nova: %s" % e.message)
    neutron = _get_neutron_client(module, module.params)
    state, floating_ip_id = _get_floating_ip_id(module, neutron)
    if module.params['state'] == 'present':
        if state == 'attached':
            module.exit_json(changed = False, result = 'attached', public_ip=module.params['ip_address'])
        server_info, server_obj = _get_server_state(module, nova)
        if not server_info:
            module.fail_json(msg = " The instance name provided cannot be found")
        port_id = _get_port_id(neutron, module, server_info['id'])
        if not port_id:
            module.fail_json(msg = "Cannot find a port for this instance, maybe fixed ip is not assigned")
        _update_floating_ip(neutron, module, port_id, floating_ip_id)

    if module.params['state'] == 'absent':
        if state == 'detached':
            module.exit_json(changed = False, result = 'detached')
        if state == 'attached':
            _update_floating_ip(neutron, module, None, floating_ip_id)
        module.exit_json(changed = True, result = "detached")

# this is magic, see lib/ansible/module.params['common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()

