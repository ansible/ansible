#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017, Eike Frost <ei@kefro.st>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: keycloak_scope

short_description: Allows administration of Keycloak scope mappings via the Keycloak REST API

version_added: "2.6"

description:
    - This module allows the administration of Keycloak scope mappings through the Keycloak REST
      API. It requires access to the REST API via OpenID Connect; the user connecting and the client
      being used must have the requisite access rights. In a default Keycloak installation,
      admin-cli and an admin user would work, as would a separate client definition with the scope
      tailored to your needs and a user having the expected roles.

options:
    state:
        description:
            - State of the scope mapping.
            - On C(present), the scope mapping will be created or updated/extended.
            - On C(absent), the scope mapping will be removed if it exists.
            - On C(exclusive), the scope mapping is exclusive and removes all roles not explicitly
              listed from scope
        choices: ['present', 'absent', 'exclusive']
        default: 'present'

    target:
        description:
            - Scope mappings can be acted upon for either clients or client mappings. Choose one
              here; the default ist C(client).
        default: 'client'
        choices: ['client', 'client-template']

    id:
        description:
            - id of client or client template to work on scope mappings on. Either this or one of
              I(client_id)/I(name) are required.

    name:
        description:
            - name of client template to work on (if I(target) is C('clienttemplate')). Either this
              or I(id) is required.

    realm:
        description:
            - realm this scope mapping belongs to.

    client_id:
        description:
            - client_id of client to work on (if I(target) is C('client')). Either this or I(id)
              is required.

    type:
        description:
            - Type of scope mapping.
            - On C(realm), the scope mappings are for realm scopes. (In this case C(roles) is
              required)
            - On C(client), the scope mappings are for client scopes. (In this case C(clientroles)
              is required)
        choices: ['realm', 'client']
        default: 'realm'

    roles:
        description:
            - A list of role representations (in dict-form) to be acted on. Usually, only C(name) is
              required. Either C(roles) or C(clientroles) is required, depending on C(type).
              U(http://www.keycloak.org/docs-api/3.3/rest-api/index.html#_rolerepresentation) can be
              referenced for the structure. Roles need to exist already to be put in scopes.
        suboptions:
            name:
                description:
                    - Name of the role
                required: true

            clientRole:
                description:
                    - Boolean specifying whether this is a clientRole

            composite:
                description:
                    - Boolean specifying whether this is a composite role. If so, I(composites)
                      contains its definition.

            composites:
                description:
                    - if I(composite) is set to True, this defines the composite role definition through
                      a dict. The set of all the rolenames specified therein is the set of roles this
                      composite role is comprised of. The dict contains the keys I(client) and I(realm).
                    - I(client) contains another dict with client names as keys and lists of client
                      role names as values.
                    - I(realm) contains a list of realm role names.

            containerId:
                description:
                    - Container id of this role - usually the realmname.

            description:
                description:
                    - Description of this role.

            id:
                description:
                    - Unique id of this role.

            scopeParamRequired:
                description:
                    - Boolean specifying whether this role is only granted when a scope parameter
                      with this role name is used during the auth/token request.

    clientroles:
        description:
            - A dict of lists of role representations (in dict-form) to be acted on. At minimum,
              C(name) is required in a role representation. The dict's keys are the client-role
              scopes for the attached roles representations. There is an example below. Either
              C(roles) or C(clientroles) is required, depending on C(type). More information on
              valid role representations is provided in the documentation for I(roles). Roles need
              to exist already to be put in scopes.


extends_documentation_fragment:
    - keycloak

author:
    - Eike Frost (@eikef)
'''

EXAMPLES = '''
- name: Add realm roles to a client scope mapping (using implicit default of acting on a client and setting realm scope mappings)
  local_action:
    module: keycloak_scope
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    realm: testrealm
    state: present
    client_id: testclient
    roles:
      - name: testrole01
      - name: testrole02
      - name: testrole03

- name: Add client roles to a client-template scope mapping
  local_action:
    module: keycloak_scope
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    realm: testrealm
    target: client-template
    state: present
    type: client
    name: testclienttemplate
    clientroles:
      testclient01:
        - name: testrole01
      testclient02:
        - name: testrole02

- name: Remove client role testrole01 for testclient01 from testclienttemplate
  local_action:
    module: keycloak_scope
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    realm: testrealm
    target: client-template
    state: absent
    type: client
    name: testclienttemplate
    clientroles:
      testclient01:
        - name: testrole01

- name: Remove all client roles from testclient01 using exclusive and an empty client role dict
  local_action:
    module: keycloak_scope
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    realm: testrealm
    state: exclusive
    type: client
    client_id: testclient01
    clientroles:
'''

RETURN = '''
msg:
  description: Message as to what action was taken
  returned: always
  type: string
  sample: "Added/Updated 0 scope mapping(s), removed 0 scope mapping(s)."

proposed:
  description: Proposed changes after evaluation by module
  returned: always
  type: dict
  sample: {
        "realm": [
            {
                "id": "16538ff1-7a92-4cef-a31c-b52c3543d8e9",
                "name": "testrole01"
            },
            {
                "id": "88663e7d-a16a-4e51-a476-4fe68e48549f",
                "name": "testrole02"
            },
            {
                "id": "23e55337-0f17-4e76-88c1-81b29d8a46ae",
                "name": "testrole03"
            }
        ]
        }
existing:
  description: Existing scope mappings on Keycloak's side before anything is changed
  returned: always
  type: dict
  sample: {
        "testclient01": [
            {
                "clientRole": true,
                "composite": false,
                "containerId": "9442a1fb-2508-43f0-8392-e38354d66586",
                "id": "1903be17-7a10-40f8-941f-902c45be036b",
                "name": "testrole01",
                "scopeParamRequired": false
            }
        ]
    }
end_state:
  description: State after changes have been applied, as seen by Keycloak
  returned: always
  type: dict
  sample: {
        "realm": [
            {
                "clientRole": false,
                "composite": false,
                "containerId": "testrealm",
                "id": "fc0bf800-d373-4c18-a5b4-4a53d4ff023c",
                "name": "test_role",
                "scopeParamRequired": false
            }
        ]
    }
'''

import json
from copy import deepcopy
from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec, check_role_representation
from ansible.module_utils.basic import AnsibleModule


def contains_role(roles, rolename):
    """
    Checks whether a given role is included in a list of role-representations.

    :param roles: list of role representations
    :param rolename: name of role to check for
    :return: boolean
    """
    if isinstance(roles, list):
        for role in roles:
            if role['name'] == rolename:
                return True
    return False


def main():
    """
    Module execution

    :return:
    """
    argument_spec = keycloak_argument_spec()

    meta_args = dict(
        realm=dict(type='str'),
        target=dict(default='client', choices=['client', 'client-template']),
        id=dict(type='str'),
        name=dict(type='str'),
        client_id=dict(type='str'),
        state=dict(default='present', choices=['present', 'absent', 'exclusive']),
        type=dict(default='realm', choices=['realm', 'client']),
        roles=dict(type='list', elements='dict'),
        clientroles=dict(type='dict'),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['id', 'name', 'client_id'], ['roles', 'clientroles']]))

    result = dict(changed=False, msg='', diff={}, proposed={}, existing={}, end_state={})

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)

    # Initialize some general variables
    realm = module.params.get('realm')
    state = module.params.get('state')
    target = module.params.get('target')
    roletype = module.params.get('type')
    roles = module.params.get('roles')
    clientroles = module.params.get('clientroles')

    if roletype == 'realm' and clientroles is not None:
        module.fail_json(msg='You cannot specify clientroles when type is "realm"')
    if roletype == 'client' and roles is not None:
        module.fail_json(msg='You cannot specify roles when type is "client"')

    if roles is None:
        roles = []
    if clientroles is None:
        clientroles = {}

    for role in roles:
        checkresult, msg = check_role_representation(role)
        if not checkresult:
            module.fail_json(msg=msg)
    for client in clientroles:
        if isinstance(clientroles[client], list):
            for role in clientroles[client]:
                checkresult, msg = check_role_representation(role)
                if not checkresult:
                    module.fail_json(msg=msg)

    # obtain ID of client or client template when given client_id or name
    cid = module.params.get('id')
    if cid is None:
        if target == 'client':
            if module.params.get('client_id') is not None:
                cid = kc.get_client_id(module.params.get('client_id'), realm=realm)
            else:
                module.fail_json(msg='When target is client, you need to specify an id or client_id.')
        else:
            if module.params.get('name') is not None:
                cid = kc.get_client_template_id(module.params.get('name'), realm=realm)
            else:
                module.fail_json(msg='When target is client-template, you need to specify an id or a name.')
    if cid is None:
        module.fail_json(msg='Could not obtain valid client(-template) id to work on.')

    if roletype == 'realm':
        # in this case, the loop below needs to be run once with a None item
        scope_clients = [None]
    if roletype == 'client':
        scope_clients = list(clientroles.keys())
        if state == 'exclusive':
            # when exclusive is set, we want to delete already existing scope mappings regarding all
            # clients, so add existing mappings' client-names to list of clients to iterate over
            # (with an empty scope mapping)
            currentmappings = kc.get_scope_mappings(cid, target=target, realm=realm)
            if 'clientMappings' in currentmappings:
                currentmappings = currentmappings['clientMappings']
            else:
                currentmappings = dict()

            for mapping in currentmappings.keys():
                if mapping not in scope_clients:
                    scope_clients.append(mapping)

    # Let's do some bookkeeping
    removed_roles = 0
    updated_roles = 0
    for scope_client in scope_clients:
        if scope_client is not None:
            # If this is a client scope mapping as opposed to a realm scope mapping
            if scope_client in clientroles:
                roles = clientroles[scope_client]
            else:
                roles = []
            scope_client_id = kc.get_client_id(scope_client, realm=realm)
        else:
            scope_client_id = scope_client

        if roles is None:
            roles = []

        # obtain current roles
        current = kc.get_scope_mapping(cid, id_client=scope_client_id, target=target, realm=realm)
        proposed = deepcopy(current)
        end_state = []

        to_delete = []
        if state == 'absent':
            for role in current:
                if contains_role(roles, role['name']):
                    to_delete.append(role)
                    proposed = [x for x in proposed if x['name'] != role['name']]

        if state == 'exclusive':
            to_delete = []
            for role in current:
                if not contains_role(roles, role['name']):
                    to_delete.append(role)
                    proposed = [x for x in proposed if x['name'] != role['name']]

        if len(to_delete) > 0:
            if not module.check_mode:
                kc.delete_scope_mapping(cid, to_delete, id_client=scope_client_id, target=target, realm=realm)
            removed_roles += len(to_delete)
            result['changed'] = True

        available_roles = kc.get_available_roles(cid, id_client=scope_client_id, target=target, realm=realm)
        to_update = []
        if state == 'present' or state == 'exclusive':
            for role in roles:
                # only add roles not already present
                if not contains_role(current, role['name']):
                    proposed.append(role)
                    # obtain role id if it was not supplied
                    if 'id' not in role:
                        candidate = [x for x in available_roles if x['name'] == role['name']]
                        if len(candidate) < 1:
                            module.fail_json(msg="Could not find role '%s'" % role['name'])
                        role['id'] = candidate[0]['id']
                    to_update.append(role)

        if len(to_update) > 0:
            if not module.check_mode:
                kc.create_scope_mapping(cid, to_update, id_client=scope_client_id, target=target, realm=realm)
            result['changed'] = True
            if len(result['msg']) > 0:
                result['msg'] += ' '
            updated_roles += len(to_update)

        # obtain state of mappings after update/delete calls have been completed
        end_state = kc.get_scope_mapping(cid, id_client=scope_client_id, target=target, realm=realm)

        # only add things to result dict if they are non-empty; removes output of empty lists
        if len(end_state) > 0:
            result['end_state'][scope_client or 'realm'] = end_state
        if len(current) > 0:
            result['existing'][scope_client or 'realm'] = current
        if len(proposed) > 0:
            result['proposed'][scope_client or 'realm'] = proposed

    if module._diff:
        result['diff'] = dict(before=json.dumps(result['existing'], sort_keys=True, indent=4) + '\n',
                              after=json.dumps(result['proposed' if module.check_mode else 'end_state'],
                              sort_keys=True, indent=4) + '\n')

    result['msg'] = 'Added/Updated %s scope mapping(s), removed %s scope mapping(s).' % (updated_roles, removed_roles)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
