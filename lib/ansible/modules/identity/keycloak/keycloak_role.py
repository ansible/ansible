#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Philippe Gauthier INSPQ <philippe.gauthier@inspq.qc.ca>
#
# This file is not part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
author: "Philippe Gauthier (philippe.gauthier@inspq.qc.ca"
module: keycloak_role
short_description: Configure a role in Keycloak
description:
    - This module creates, removes or update Keycloak realm level role.
    - For client level role, use keycloak_client module.
version_added: "2.8"
options:
    realm:
        description:
            - The name of the realm in which is the role.
        required: true
        default: master
    name:
        description:
            - Name for the realm level role.
        required: true
    description:
        description:
            - Description of the role.
        required: false
    clientRole:
        description: 
            - This parameter indicate if the role is a client role.
            - For a ream role, this parameter must be false.
        default: false
        required: false
    containerId:
        description:
            - Id for the container of the role. For a realm role, it must be the realm name
        default: "{{ realm }}"
        required: false
    composite:
        description:
            - If true, the role is a composition of other realm and/or client role.
        default: false
        required: false
    composites:
        description:
            - List of roles to include to the composite realm role.
            - If the composite role is a client role, the clientId (not id of the client) must be specified.
        required: false
        subOptions:
            name:
                description:
                    - Name of the role. This can be the name of a REALM role or a client role.
                type: str
            clientId:
                description:
                    - Client ID if the role is a client role. Do not include this option for a REALM role.
                    - Use the client id we can see in the Keycloak console, not the technical id of the client.
                type: str
    state:
        description:
            - Control if the role must exists or not
        choices: [ "present", "absent" ]
        default: present
        required: false
    force:
        choices: [ "yes", "no" ]
        default: "no"
        description:
            - If yes, allows to remove role and recreate it.
        required: false
extends_documentation_fragment:
    - keycloak
notes:
    - module does not modify role name.
'''

EXAMPLES = '''
    - name: Create the composite realm role role1 with composite roles.
      keycloak_role:
        url: http://localhost:8080
        username: admin
        password: password
        realm: master
        name: role1
        description: Super composite role
        composite: true
        composites:
          - clientId: realm-management
            name: "manage-clients"
          - name: uma_authorization
        state: present

    - name: Re-create realm role role1
      keycloak_role:
        url: http://localhost:8080
        username: admin
        password: password
        realm: master
        name: role1
        description: Super composite role
        composite: true
        composites:
          - clientId: realm-management
            name: "manage-clients"
          - name: uma_authorization
        state: present
        force: yes

    - name: Remove realm role role1.
      keycloak_role:
        url: http://localhost:8080
        username: admin
        password: admin
        realm: master
        name: role1
        state: absent
'''

RETURN = '''
role:
  description: JSON representation for the role.
  returned: on success
  type: dict
composites:
  description: Composites JSON representation for the role.
  returned: on success
  type: list
msg:
  description: Error message if it is the case
  returned: on error
  type: str
changed:
  description: Return True if the operation changed the role on the keycloak server, false otherwise.
  returned: always
  type: bool
'''
from ansible.module_utils.keycloak_utils import isDictEquals
from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule

def main():
    argument_spec = keycloak_argument_spec()

    composites_spec = dict(
        name=dict(type='str', required=True),
        clientId= dict(type='str')
    )
    meta_args =  dict(
        realm=dict(type='str', default='master'),
        name=dict(type='str', required=True),
        description = dict(type='str', default=None),
        composite=dict(type='bool',default=False),
        clientRole = dict(type='bool',default=False),
        containerId = dict(type='str', required=False),
        composites = dict(type='list', default=[], options=composites_spec),
        state=dict(choices=["absent", "present"], default='present'),
        force=dict(type='bool', default=False),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['name']]))

    result = dict(changed=False, msg='', role={}, composites=None)

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)

    realm = module.params.get('realm')
    state = module.params.get('state')
    force = module.params.get('force')
    newComposites = None
    
    # Create representation for the new role
    newRoleRepresentation = {}
    newRoleRepresentation["name"] = module.params.get('name')
    if module.params.get('description') is not None:
        newRoleRepresentation["description"] = module.params.get('description')
    newRoleRepresentation["composite"] = module.params.get('composite')
    newRoleRepresentation["clientRole"] = module.params.get('clientRole')
    newRoleRepresentation["containerId"] = module.params.get('containerId') if module.params.get('containerId') is not None else realm
    if module.params.get('composites') is not None:
        newComposites = module.params.get('composites')
    
    changed = False

    # Search the role on Keycloak server.
    roleRepresentation = kc.search_realm_role_by_name(name=newRoleRepresentation["name"], realm=realm)
    if roleRepresentation == {}: # If role does not exists
        if (state == 'present'): # If desired state is present
            # Create Role
            kc.create_realm_role(newRoleRepresentation=newRoleRepresentation, realm=realm)
            # Create composites
            kc.create_or_update_realm_role_composites(newComposites=newComposites, newRoleRepresentation=newRoleRepresentation, realm=realm)
            # Get created role
            roleRepresentation = kc.get_realm_role(name=newRoleRepresentation["name"], realm=realm)
            # Get created composites
            composites = kc.get_realm_role_composites_with_client_id(name=newRoleRepresentation["name"], realm=realm)
            changed = True
            result['role'] = roleRepresentation
            result['composites'] = composites
        elif state == 'absent': # If desired state is absent
            result["msg"] = "Realm role %s is absent in realm %s" % (newRoleRepresentation["name"],realm)
                
    else:  # If role already exists
        if (state == 'present'): # If desired state is present
            if force: # If force option is true
                # Delete the existing role
                kc.delete_realm_role(name=roleRepresentation["name"], realm=realm)
                # Create role again
                kc.create_realm_role(newRoleRepresentation=newRoleRepresentation, realm=realm)
                changed = True
            else: # If force option is false
                # Compare roles
                if not (isDictEquals(newRoleRepresentation, roleRepresentation)): # If new role introduce changes
                    # Update the role
                    kc.update_realm_role(newRoleRepresentation=newRoleRepresentation, realm=realm)
                    changed = True
            # Manage composites
            if kc.create_or_update_realm_role_composites(newComposites=newComposites, newRoleRepresentation=newRoleRepresentation, realm=realm):
                changed = True
            # Get created role
            roleRepresentation = kc.get_realm_role(name=newRoleRepresentation["name"], realm=realm)
            # Get composites
            composites = kc.get_realm_role_composites_with_client_id(name=newRoleRepresentation["name"], realm=realm)
            result["role"] = roleRepresentation
            result["composites"] = composites
        elif state == 'absent': # If desired state is absent
            # Delete role
            kc.delete_realm_role(name=newRoleRepresentation["name"], realm=realm)
            changed = True
            result["msg"] = "Realm role %s is deleted in realm %s" % (newRoleRepresentation["name"],realm)
    result['changed'] = changed
    module.exit_json(**result)

if __name__ == '__main__':
    main()
