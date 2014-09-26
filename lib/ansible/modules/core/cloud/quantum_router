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
module: quantum_router
version_added: "1.2"
short_description: Create or Remove router from openstack
description:
   - Create or Delete routers from OpenStack
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
   name:
     description:
        - Name to be give to the router
     required: true
     default: None
   tenant_name:
     description:
        - Name of the tenant for which the router has to be created, if none router would be created for the login tenant.
     required: false
     default: None
   admin_state_up:
     description:
        - desired admin state of the created router .
     required: false
     default: true
requirements: ["quantumclient", "neutronclient", "keystoneclient"]
'''

EXAMPLES = '''
# Creates a router for tenant admin
- quantum_router: state=present
                login_username=admin
                login_password=admin
                login_tenant_name=admin
                name=router1"
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

def _set_tenant_id(module):
    global _os_tenant_id
    if not module.params['tenant_name']:
        login_tenant_name = module.params['login_tenant_name']
    else:
        login_tenant_name = module.params['tenant_name']

    for tenant in _os_keystone.tenants.list():
        if tenant.name == login_tenant_name:
            _os_tenant_id = tenant.id
            break
    if not _os_tenant_id:
            module.fail_json(msg = "The tenant id cannot be found, please check the parameters")


def _get_router_id(module, neutron):
    kwargs = {
            'name': module.params['name'],
            'tenant_id': _os_tenant_id,
    }
    try:
        routers = neutron.list_routers(**kwargs)
    except Exception, e:
        module.fail_json(msg = "Error in getting the router list: %s " % e.message)
    if not routers['routers']:
        return None
    return routers['routers'][0]['id']

def _create_router(module, neutron):
    router = {
            'name': module.params['name'],
            'tenant_id': _os_tenant_id,
            'admin_state_up': module.params['admin_state_up'],
    }
    try:
        new_router = neutron.create_router(dict(router=router))
    except Exception, e:
        module.fail_json( msg = "Error in creating router: %s" % e.message)
    return new_router['router']['id']

def _delete_router(module, neutron, router_id):
    try:
        neutron.delete_router(router_id)
    except:
        module.fail_json("Error in deleting the router")
    return True

def main():
    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
        name                            = dict(required=True),
        tenant_name                     = dict(default=None),
        state                           = dict(default='present', choices=['absent', 'present']),
        admin_state_up                  = dict(type='bool', default=True),
    ))
    module = AnsibleModule(argument_spec=argument_spec)

    neutron = _get_neutron_client(module, module.params)
    _set_tenant_id(module)

    if module.params['state'] == 'present':
        router_id = _get_router_id(module, neutron)
        if not router_id:
            router_id = _create_router(module, neutron)
            module.exit_json(changed=True, result="Created", id=router_id)
        else:
            module.exit_json(changed=False, result="success" , id=router_id)

    else:
        router_id = _get_router_id(module, neutron)
        if not router_id:
            module.exit_json(changed=False, result="success")
        else:
            _delete_router(module, neutron, router_id)
            module.exit_json(changed=True, result="deleted")

# this is magic, see lib/ansible/module.params['common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()

