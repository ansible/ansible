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
module: os_router
short_description: Create or Delete routers from OpenStack
extends_documentation_fragment: openstack
version_added: "1.10"
description:
   - Create or Delete routers from OpenStack
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
        - desired admin state of the created router .
     required: false
     default: true
requirements: ["shade"]
'''

EXAMPLES = '''
# Creates a router for tenant admin
- os_router: state=present
             username=admin
             password=admin
             project_name=admin
             name=router1"
'''

def _get_router_id(module, neutron):
    kwargs = {
            'name': module.params['name'],
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
    argument_spec = openstack_full_argument_spec(
        name                            = dict(required=True),
        state                           = dict(default='present', choices=['absent', 'present']),
        admin_state_up                  = dict(type='bool', default=True),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)
        neutron = cloud.neutron_client


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
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
