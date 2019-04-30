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
author: "Etienne Sadio (etienne.sadio@inspq.qc.ca)"
module: keycloak_user
short_description: create and Configure a user in Keycloak
description:
    - This module creates, removes or update Keycloak users.
version_added: "2.8"
options:
    realm:
        description:
            - The name of the realm in which is the client.
        default: master
    username:
        description:
            - username for the user.
        required: false
    enabled:
        description:
            - Enabled user.
        required: false
    emailVerified:
        description:
            - check the validity of user email.
        default: false
        required: false
    firstName:
        description:
            - User firstName.
        required: false
    lastName:
        description:
            - User lastName.
        required: false
    email:
        description:
            - User email.
        required: false
    federationLink:
        description:
            - Federation Link.
        required: false
    serviceAccountClientId:
        description:
            - Description of the client Application.
        required: false
    realmRoles:
        description:
            - List of ClientRoles for the user.
        required: false
    clientRoles:
        description:
            - List of ClientRoles for the user.
        required: false
    clientConsents:
        description: 
            - client Authenticator Type.
        required: false
        type: list
        subOptions:
            clientId:
                description:
                - Client ID of the client role. Not the technical id of the client.
                type: str
                required: true
            roles:
                description:
                - List of client roles to assign to the user
                type: list
                required: true
    groups:
        description:
            - List of groups for the user.
        required: true
    credentials:
        description:
            - User credentials.
        required: false
    consentRequired:
        description:
            - consent Required.
        required: false
    requiredActions:
        description:
            - requiredActions user Auth.
        required: false
    federatedIdentities:
        description:
            - list of IDP of user. 
        required: false
    attributes:
        description:
            - list user attributes. 
        required: false
    access:
        description:
            - list user access. 
        required: false
    disableableCredentialTypes:
        description:
            - list user Credential Type. 
        required: false
    origin:
        description:
            - user origin. 
        required: false
    self:
        description:
            - user self administration. 
        required: false
    state:
        description:
            - Control if the user must exists or not
        choices: [ "present", "absent" ]
        default: present
        required: false
    force:
        description:
            - If yes, allows to remove user and recreate it.
        choices: [ "yes", "no" ]
        default: "no"
        required: false
extends_documentation_fragment:
    - keycloak
notes:
    - module does not modify userId.
'''

EXAMPLES = '''
    - name: Create a user user1
      keycloak_user:
        url: http://localhost:8080
        masterUsername: admin
        masterpassword: password
        realm: master
        username: user1
        firstName: user1
        lastName: user1
        email: user1
        enabled: true
        emailVerified: false
        credentials:
          - type: password
            value: password
            temporary: false
        attributes:
          attr1: 
            - value1
          attr2: 
            - value2
        clientRoles:
          - clientId: client1 
            roles:  
            - role1
          - clientId: client2 
            roles:
            - role2
        groups:
          - group1
        realmRoles:
          - Role1
        state: present

    - name: Re-create a User
      keycloak_user:
        url: http://localhost:8080
        masterUsername: admin
        masterpassword: password
        realm: master
        username: user1
        firstName: user1
        lastName: user1
        email: user1
        enabled: true
        emailVerified: false
        credentials:
          - type: password
            value: password
            temporary: false
        attributes:
          attr1: 
            - value1
          attr2: 
            - value2
        clientRoles:
          - clientId: client1 
            roles:  
            - role1
          - clientId: client2 
            roles:
            - role2
        groups:
          - group1
        realmRoles:
          - Roles1
        state: present
        force: yes

    - name: Remove User.
      keycloak_user:
        url: http://localhost:8080
        masterUsername: admin
        masterpassword: password
        realm: master
        username: user1
        state: absent
'''

RETURN = '''
user:
  description: JSON representation for the user.
  returned: on success
  type: dict
msg:
  description: Message if it is the case
  returned: always
  type: str
changed:
  description: Return True if the operation changed the client on the keycloak server, false otherwise.
  returned: always
  type: bool
'''
from ansible.module_utils.keycloak_utils import isDictEquals
from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule

def main():
    argument_spec = keycloak_argument_spec()

    client_role_spec = dict(
        clientId=dict(type='str',required=True),
        roles=dict(type='list', required=True),
    )
    meta_args = dict(
        realm=dict(type='str', default='master'),
        self=dict(type='str'),
        id=dict(type='str'),
        username=dict(type='str', required=True),
        firstName=dict(type='str'),
        lastName=dict(type='str'),
        email=dict(type='str'),
        enabled=dict(type='bool', default=True),
        emailVerified=dict(type='bool', default=False),
        federationLink=dict(type='str'),
        serviceAccountClientId=dict(type='str'),
        attributes=dict(type='dict'),
        access=dict(type='dict'),
        clientRoles=dict(type='list', default=[], options=client_role_spec),
        realmRoles=dict(type='list', default=[]),
        groups=dict(type='list', default=[]),
        disableableCredentialTypes=dict(type='list', default=[]),
        requiredActions=dict(type='list', default=[]),
        credentials=dict(type='list', default=[]),
        federatedIdentities=dict(type='list', default=[]),
        clientConsents=dict(type='list', default=[]),
        origin=dict(type='str'),
        state=dict(choices=["absent", "present"], default='present'),
        force=dict(type='bool', default=False),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['username']]))

    result = dict(changed=False, msg='', user={})

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)

    realm = module.params.get('realm')
    state = module.params.get('state')
    force = module.params.get('force')
    # Create a representation of the user received in parameters
    newUserRepresentation = {}
    newUserClientRolesRepresentation = {}
    newUserRepresentation["username"] = module.params.get('username')
    if module.params.get('self') is not None:
        newUserRepresentation["self"] = module.params.get('self')
    if module.params.get('id') is not None:
        newUserRepresentation["id"] = module.params.get('id')
    newUserRepresentation["enabled"] = module.params.get('enabled')
    newUserRepresentation["emailVerified"] = module.params.get('emailVerified')
    if module.params.get('firstName') is not None:
        newUserRepresentation["firstName"] = module.params.get('firstName')
    if module.params.get('lastName') is not None:
        newUserRepresentation["lastName"] = module.params.get('lastName')
    if module.params.get('email') is not None:
        newUserRepresentation["email"] = module.params.get('email')
    if module.params.get('federationLink') is not None:
        newUserRepresentation["federationLink"] = module.params.get('federationLink')
    if module.params.get('serviceAccountClientId') is not None:
        newUserRepresentation["serviceAccountClientId"] = module.params.get('serviceAccountClientId')
    if module.params.get('origin') is not None:
        newUserRepresentation["origin"] = module.params.get('origin')
    if module.params.get('credentials') is not None:
        newUserRepresentation["credentials"] = module.params.get('credentials')
    if module.params.get('disableableCredentialTypes') is not None:
        newUserRepresentation["disableableCredentialTypes"] = module.params.get('disableableCredentialTypes')
    if module.params.get('federatedIdentities') is not None:
        newUserRepresentation["federatedIdentities"] = module.params.get('federatedIdentities')
    if module.params.get('requiredActions') is not None:
        newUserRepresentation["requiredActions"] = module.params.get('requiredActions')
    if module.params.get('clientConsents') is not None:
        newUserRepresentation["clientConsents"] = module.params.get('clientConsents')
    if module.params.get('attributes') is not None:
        newUserRepresentation["attributes"] = module.params.get('attributes')
    if module.params.get('access') is not None:
        newUserRepresentation["access"] = module.params.get('access')
    if module.params.get('clientRoles') is not None:
        newUserClientRolesRepresentation["clientRoles"] = module.params.get('clientRoles')
    if module.params.get('realmRoles') is not None:
        newUserRepresentation["realmRoles"] = module.params.get('realmRoles')
    if module.params.get('groups') is not None:
        newUserRepresentation["groups"] = module.params.get('groups')
    
    changed = False
    userRepresentation = kc.search_user_by_username(username=newUserRepresentation["username"], realm=realm)

    if userRepresentation == {}: # The user does not exist
        # Create the user
        if (state == 'present'): # If state is present
            # Create the user
            userRepresentation = kc.create_user(newUserRepresentation=newUserRepresentation, realm=realm)
            # Add user ID to new representation
            newUserRepresentation['id'] = userRepresentation["id"]
            # Assign roles to user
            kc.assing_roles_to_user(user_id=newUserRepresentation["id"], userRealmRoles=newUserRepresentation['realmRoles'], userClientRoles=newUserClientRolesRepresentation['clientRoles'], realm=realm)
            #set user groups
            kc.update_user_groups_membership(newUserRepresentation=newUserRepresentation, realm=realm)
            # Get the updated user realm roles
            userRepresentation["realmRoles"] = kc.get_user_realm_roles(user_id=userRepresentation["id"],realm=realm)
            # Get the user clientRoles
            userRepresentation["clientRoles"] =  kc.get_user_client_roles(user_id=userRepresentation["id"], realm=realm)
            # Get the user groups
            userRepresentation["groups"] = kc.get_user_groups(user_id=userRepresentation["id"],realm=realm)
            changed = True
            result["user"] = userRepresentation
        elif state == 'absent': # Otherwise, the status is absent
            result["msg"] = 'User %s is absent' % (newUserRepresentation["username"])
                
    else:  # the user already exists
        if (state == 'present'): # if desired state is present
            if force == True: # If the force option is set to true
                # Delete the existing user
                kc.delete_user(user_id=userRepresentation["id"],realm=realm)
                changed = True
                # Recreate the user
                userRepresentation = kc.create_user(newUserRepresentation=newUserRepresentation, realm=realm)
                # Add user ID to new representation
                newUserRepresentation['id'] = userRepresentation["id"]
            else: # If the force option is false
                excludes = ["access","notBefore","createdTimestamp","totp","credentials","disableableCredentialTypes","realmRoles","clientRoles","groups","clientConsents","federatedIdentities","requiredActions"]
                # Add user ID to new representation
                newUserRepresentation['id'] = userRepresentation["id"]
                # Compare users
                if not (isDictEquals(newUserRepresentation, userRepresentation, excludes)): # If the new user does not introduce a change to the existing user
                    # Update the user
                    userRepresentation = kc.update_user(newUserRepresentation=newUserRepresentation, realm=realm)
                    changed = True
            # Assign roles to user
            if kc.assing_roles_to_user(user_id=newUserRepresentation["id"], userRealmRoles=newUserRepresentation['realmRoles'], userClientRoles=newUserClientRolesRepresentation['clientRoles'], realm=realm):
                changed = True
            #set user groups
            if kc.update_user_groups_membership(newUserRepresentation=newUserRepresentation, realm=realm):
                changed = True
            # Get the updated user realm roles
            userRepresentation["realmRoles"] = kc.get_user_realm_roles(user_id=userRepresentation["id"],realm=realm)
            # Get the user clientRoles
            userRepresentation["clientRoles"] =  kc.get_user_client_roles(user_id=userRepresentation["id"], realm=realm)
            # Get the user groups
            userRepresentation["groups"] = kc.get_user_groups(user_id=userRepresentation["id"],realm=realm)
            result["user"] = userRepresentation
        elif state == 'absent': # Status is absent
            # Delete user
            kc.delete_user(user_id=userRepresentation['id'], realm=realm)
            result["msg"] = 'User %s deleted' % (userRepresentation['id'])
            changed = True
    
    result['changed'] = changed
    module.exit_json(**result)
    
    
"""
def createOrUpdateGroups(userGroups,userRepresentation, userSvcBaseUrl, groupSvcBaseUrl, headers):
    changed = False
    # Get groups Available
    try:
        getResponse = requests.get(groupSvcBaseUrl, headers=headers)
        groups = getResponse.json()
        for group in groups:
            if "name" in group and group["name"] == userGroups:
                requests.put(userSvcBaseUrl + userRepresentation["id"] + '/groups/'+group["id"], headers=headers)
                changed = True
    except Exception ,e :
        raise e
    return changed

def getUserRealmRoles(userSvcBaseUrl, headers, userId):
    realmRoles = []
    getResponse = requests.get(userSvcBaseUrl + userId + '/role-mappings', headers=headers)
    for roleMapping in getResponse.json()["realmMappings"]:
        realmRoles.append(roleMapping["name"])
    return realmRoles

def getUserClientRoles(userSvcBaseUrl, headers, userId):
    clientRoles = []
    getResponse = requests.get(userSvcBaseUrl + userId + '/role-mappings', headers=headers)
    userMappings = getResponse.json()
    for clientMapping in userMappings["clientMappings"].keys():
        clientRole = {}
        clientRole["clientId"] = userMappings["clientMappings"][clientMapping]["client"]
        roles = []
        for role in userMappings["clientMappings"][clientMapping]["mappings"]:
            roles.append(role["name"])
        clientRole["roles"] = roles
        clientRoles.append(clientRole)
    return clientRoles

def getUserGroups(userSvcBaseUrl, headers, userId):
    groups = []
    getResponse = requests.get(userSvcBaseUrl + userId + '/groups', headers=headers)
    for clientGroup in getResponse.json():
        groups.append(clientGroup["name"])
    return groups

def assingRolestoUser(headers, userRepresentation, userRealmRoles, userClientRoles, userSvcBaseUrl, roleSvcBaseUrl, clientSvcBaseUrl):
    changed = False
    # Assing Realm Roles
    realmRolesRepresentation = []
    # Get all realm roles
    getResponse = requests.get(roleSvcBaseUrl, headers=headers)
    allRealmRoles = getResponse.json()
    for realmRole in userRealmRoles:
        # Look for existing role into user representation
        if not realmRole in userRepresentation["realmRoles"]:
            roleid = None
            # Find the role id
            for role in allRealmRoles:
                if role["name"] == realmRole:
                    roleid = role["id"]
                    break
            if roleid is not None:
                realmRoleRepresentation = {}
                realmRoleRepresentation["id"] = roleid
                realmRoleRepresentation["name"] = realmRole
                realmRolesRepresentation.append(realmRoleRepresentation)
    if len(realmRolesRepresentation) > 0 :
        data=json.dumps(realmRolesRepresentation)
        # Assing Role
        requests.post(userSvcBaseUrl + userRepresentation["id"] + "/role-mappings/realm", headers=headers, data=data)
        changed = True
    # Assing clients roles            
    for clientToAssingRole in userClientRoles:
        # Get the client id
        getResponse = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientToAssingRole["clientId"]})
        if len(getResponse.json()) > 0 and "id" in getResponse.json()[0]:
            clientId = getResponse.json()[0]["id"]
            # Get the client roles
            getResponse = requests.get(clientSvcBaseUrl + clientId + '/roles', headers=headers)
            clientRoles = getResponse.json()
            # Check if user already have this client roles
            if not isDictEquals(clientToAssingRole, userRepresentation["clientRoles"]):
                rolesToAssing = []
                for roleToAssing in clientToAssingRole["roles"]:
                    newRole = {}
                    # Find his Id
                    for clientRole in clientRoles:
                        if clientRole["name"] == roleToAssing:
                            newRole["id"] = clientRole["id"]
                            newRole["name"] = roleToAssing
                            rolesToAssing.append(newRole)
                if len(rolesToAssing) > 0:
                    # Delete exiting client Roles
                    requests.delete(userSvcBaseUrl + userRepresentation["id"] + "/role-mappings/clients/" + clientId, headers=headers)
                    data=json.dumps(rolesToAssing)
                    # Assing Role
                    requests.post(userSvcBaseUrl + userRepresentation["id"] + "/role-mappings/clients/" + clientId, headers=headers, data=data)
                    changed = True
            
    return changed             


# import module snippets
from ansible.module_utils.basic import *
"""
if __name__ == '__main__':
    main()
