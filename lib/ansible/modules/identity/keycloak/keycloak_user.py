#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, INSPQ <philippe.gauthier@inspq.qc.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: keycloak_user
short_description: create and Configure a user in Keycloak
description:
    - This module creates, removes or update Keycloak users.
version_added: "2.9"
options:
    realm:
        description:
            - The name of the realm in which is the client.
        default: master
    username:
        description:
            - username for the user.
        required: true
    id:
        description:
            - ID of the user on the keycloak server if known
        type: str
    enabled:
        description:
            - Enabled user.
        default: true
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
        suboptions:
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
            - If true, allows to remove user and recreate it.
        type: bool
        default: false
extends_documentation_fragment:
    - keycloak
notes:
    - module does not modify userId.
author:
    - Philippe Gauthier (@elfelip)
'''

EXAMPLES = '''
    - name: Create a user user1
      keycloak_user:
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
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
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
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
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
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
from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec, isDictEquals
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = keycloak_argument_spec()

    client_role_spec = dict(
        clientId=dict(type='str', required=True),
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
                           supports_check_mode=True)

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

    if userRepresentation == {}:  # The user does not exist
        # Create the user
        if (state == 'present'):  # If state is present
            # Create the user
            userRepresentation = kc.create_user(newUserRepresentation=newUserRepresentation, realm=realm)
            # Add user ID to new representation
            newUserRepresentation['id'] = userRepresentation["id"]
            # Assign roles to user
            kc.assing_roles_to_user(
                user_id=newUserRepresentation["id"],
                userRealmRoles=newUserRepresentation['realmRoles'],
                userClientRoles=newUserClientRolesRepresentation['clientRoles'],
                realm=realm)
            # set user groups
            kc.update_user_groups_membership(newUserRepresentation=newUserRepresentation, realm=realm)
            # Get the updated user realm roles
            userRepresentation["realmRoles"] = kc.get_user_realm_roles(user_id=userRepresentation["id"], realm=realm)
            # Get the user clientRoles
            userRepresentation["clientRoles"] = kc.get_user_client_roles(user_id=userRepresentation["id"], realm=realm)
            # Get the user groups
            userRepresentation["groups"] = kc.get_user_groups(user_id=userRepresentation["id"], realm=realm)
            changed = True
            result["user"] = userRepresentation
        elif state == 'absent':  # Otherwise, the status is absent
            result["msg"] = 'User %s is absent' % (newUserRepresentation["username"])

    else:  # the user already exists
        if (state == 'present'):  # if desired state is present
            if force:  # If the force option is set to true
                # Delete the existing user
                kc.delete_user(user_id=userRepresentation["id"], realm=realm)
                changed = True
                # Recreate the user
                userRepresentation = kc.create_user(newUserRepresentation=newUserRepresentation, realm=realm)
                # Add user ID to new representation
                newUserRepresentation['id'] = userRepresentation["id"]
            else:  # If the force option is false
                excludes = [
                    "access",
                    "notBefore",
                    "createdTimestamp",
                    "totp",
                    "credentials",
                    "disableableCredentialTypes",
                    "realmRoles",
                    "clientRoles",
                    "groups",
                    "clientConsents",
                    "federatedIdentities",
                    "requiredActions"]
                # Add user ID to new representation
                newUserRepresentation['id'] = userRepresentation["id"]
                # Compare users
                if not (isDictEquals(newUserRepresentation, userRepresentation, excludes)):  # If the new user does not introduce a change to the existing user
                    # Update the user
                    userRepresentation = kc.update_user(newUserRepresentation=newUserRepresentation, realm=realm)
                    changed = True
            # Assign roles to user
            if kc.assing_roles_to_user(
                    user_id=newUserRepresentation["id"],
                    userRealmRoles=newUserRepresentation['realmRoles'],
                    userClientRoles=newUserClientRolesRepresentation['clientRoles'],
                    realm=realm):
                changed = True
            # set user groups
            if kc.update_user_groups_membership(newUserRepresentation=newUserRepresentation, realm=realm):
                changed = True
            # Get the updated user realm roles
            userRepresentation["realmRoles"] = kc.get_user_realm_roles(user_id=userRepresentation["id"], realm=realm)
            # Get the user clientRoles
            userRepresentation["clientRoles"] = kc.get_user_client_roles(user_id=userRepresentation["id"], realm=realm)
            # Get the user groups
            userRepresentation["groups"] = kc.get_user_groups(user_id=userRepresentation["id"], realm=realm)
            result["user"] = userRepresentation
        elif state == 'absent':  # Status is absent
            # Delete user
            kc.delete_user(user_id=userRepresentation['id'], realm=realm)
            result["msg"] = 'User %s deleted' % (userRepresentation['id'])
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
