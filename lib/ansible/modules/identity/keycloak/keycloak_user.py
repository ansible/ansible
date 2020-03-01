#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Sylvère Richard <sylvere.richard@gmail.com>
# based on the work of Adam Goossens <adam.goossens@gmail.com>
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
module: keycloak_user

short_description: Allows administration of Keycloak users via Keycloak API

description:
    - This module allows you to add, remove or modify Keycloak users via the Keycloak REST API.
      It requires access to the REST API via OpenID Connect; the user connecting and the client being
      used must have the requisite access rights. In a default Keycloak installation, admin-cli
      and an admin user would work, as would a separate client definition with the scope tailored
      to your needs and a user having the expected roles.

    - The names of module options are snake_cased versions of the camelCase ones found in the
      Keycloak API and its documentation at U(http://www.keycloak.org/docs-api/9.0/rest-api/).

    - Attributes are multi-valued in the Keycloak API. All attributes are lists of individual values and will
      be returned that way by this module. You may pass single values for attributes when calling the module,
      and this will be translated into a list suitable for the API.

    - When updating a user, where possible provide the user ID to the module. This removes a lookup
      to the API to translate the username into the user ID.

version_added: "2.10"

options:
    state:
        description:
            - State of the user.
            - On C(present), the user will be created if it does not yet exist, or updated with the parameters you provide.
            - On C(absent), the user will be removed if it exists.
        default: 'present'
        type: str
        choices:
            - present
            - absent

    user_username:
        type: str
        description:
            - Username of the user.
            - This parameter is required only when creating or updating the user.

    first_name:
        type: str
        description:
            - Firstname of the user.
        aliases:
            - firstName

    last_name:
        type: str
        description:
            - lastname of the user.
        aliases:
            - lastName

    email:
        type: str
        description:
            - email of the user.

    email_verified:
        type: bool
        description:
            - whether the user email is verified or not.
        aliases:
            - emailVerified

    enabled:
        type: bool
        description:
            - whether the user is enabled or not.

    required_actions:
        type: list
        description:
            - A list of required actions for the user.
        choices:
            - VERIFY_EMAIL
            - UPDATE_PROFILE
            - CONFIGURE_TOTP
            - UPDATE_PASSWORD
            - terms_and_conditions
            - update_user_locale
        aliases:
            - requiredActions
        elements: str

    credentials:
        type: list
        description:
            - A list of credentials for the user.
            - Values must conform to the CredentialRepresentation.
            - See U(https://www.keycloak.org/docs-api/9.0/javadocs/org/keycloak/representations/idm/CredentialRepresentation.html).
        elements: dict

    realm:
        type: str
        description:
            - They Keycloak realm under which this user resides.
        default: 'master'

    id:
        type: str
        description:
            - The unique identifier for this user.
            - This parameter is not required for updating or deleting a user but
              providing it will reduce the number of API calls required.

    attributes:
        type: dict
        description:
            - A dict of key/value pairs to set as custom attributes for the user.
            - Values may be single values (e.g. a string) or a list of strings.


extends_documentation_fragment:
    - keycloak

author:
    - Sylvère Richard (@Nowheresly)
'''

EXAMPLES = '''
- name: Create a Keycloak user
  keycloak_user:
    user_username: my-new-kc-user
    realm: MyCustomRealm
    first_name: John
    last_name: Doe
    email: user-1@domain.com
    email_verified: True
    enabled: True
    credentials:
      - temporary: False
        value: pass
        priority: 1
        type: password
    required_actions:
      - UPDATE_PROFILE
      - terms_and_conditions
      - update_user_locale
    state: present
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
  delegate_to: localhost

- name: Delete a keycloak user
  keycloak_user:
    id: '9d59aa76-2755-48c6-b1af-beb70a82c3cd'
    state: absent
    realm: MyCustomRealm
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
  delegate_to: localhost

- name: Delete a Keycloak user based on username
  keycloak_user:
    user_username: my-username-for-deletion
    state: absent
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
  delegate_to: localhost

- name: Update the username of a Keycloak user
  keycloak_user:
    id: '9d59aa76-2755-48c6-b1af-beb70a82c3cd'
    user_username: an-updated-kc-user-username
    state: present
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
  delegate_to: localhost

- name: Create a keycloak user with some custom attributes
  keycloak_user:
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    user_username: my-new_user
    attributes:
        attrib1: value1
        attrib2: value2
        attrib3:
            - with
            - numerous
            - individual
            - list
            - items
  delegate_to: localhost
'''

RETURN = '''
user:
  description: User representation of the user after module execution (sample is truncated).
  returned: always
  type: complex
  contains:
    id:
      description: GUID that identifies the user
      type: str
      returned: always
      sample: 23f38145-3195-462c-97e7-97041ccea73e
    username:
      description: Username of the user
      type: str
      returned: always
      sample: user-test-123
    firstName:
      description: Firstname of the user
      type: str
      returned: always
      sample: John
    lastName:
      description: Lastname of the user
      type: str
      returned: always
      sample: Doe
    enabled:
      description: Whether the user is enabled
      type: bool
      returned: always
      sample: True
    emailVerified:
      description: Whether the user email is verified
      type: bool
      returned: always
      sample: True
    requiredActions:
      description: List of required actions for the user
      type: list
      returned: always
      sample: ['UPDATE_PROFILE']
    attributes:
      description: Attributes applied to this user
      type: dict
      returned: always
      sample:
        attr1: ["val1", "val2", "val3"]
    email:
      description: Email of the user
      type: str
      returned: always
      sample: john@test.com
    access:
      description: A dict describing the accesses you have to this user based on the credentials used.
      type: dict
      returned: always
      sample:
        manage: true
        manageMembership: true
        view: true
'''

from ansible.module_utils.identity.keycloak.keycloak import KeycloakAPI, camel, \
    keycloak_argument_spec, get_token, KeycloakError
from ansible.module_utils.basic import AnsibleModule


def main():
    """
    Module execution

    :return:
    """
    argument_spec = keycloak_argument_spec()
    meta_args = dict(
        state=dict(default='present', choices=['present', 'absent']),
        realm=dict(default='master'),
        id=dict(type='str'),
        user_username=dict(type='str'),
        email=dict(type='str'),
        emailVerified=dict(type='bool', aliases=['email_verified']),
        enabled=dict(type='bool'),
        firstName=dict(type='str', aliases=['first_name']),
        lastName=dict(type='str', aliases=['last_name']),
        credentials=dict(type='list', no_log=True, elements='dict'),
        requiredActions=dict(type='list', aliases=['required_actions'], elements='str',
                             choices=['VERIFY_EMAIL', 'UPDATE_PROFILE', 'CONFIGURE_TOTP', 'UPDATE_PASSWORD',
                                      'terms_and_conditions', 'update_user_locale']
                             ),
        attributes=dict(type='dict')
    )

    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['id', 'user_username']]))

    result = dict(changed=False, msg='', diff={}, user='')

    # Obtain access token, initialize API
    try:
        connection_header = get_token(
            base_url=module.params.get('auth_keycloak_url'),
            validate_certs=module.params.get('validate_certs'),
            auth_realm=module.params.get('auth_realm'),
            client_id=module.params.get('auth_client_id'),
            auth_username=module.params.get('auth_username'),
            auth_password=module.params.get('auth_password'),
            client_secret=module.params.get('auth_client_secret'),
        )
    except KeycloakError as e:
        module.fail_json(msg=str(e))
    kc = KeycloakAPI(module, connection_header)

    realm = module.params.get('realm')
    state = module.params.get('state')
    uid = module.params.get('id')
    username = module.params.get('user_username')
    attributes = module.params.get('attributes')

    before_user = None         # current state of the user, for merging.

    # does the user already exist?
    if uid is None:
        before_user = kc.get_user_by_username(username, realm=realm)
    else:
        before_user = kc.get_user_by_userid(uid, realm=realm)

    before_user = {} if before_user is None else before_user

    # attributes in Keycloak have their values returned as lists
    # via the API. attributes is a dict, so we'll transparently convert
    # the values to lists.
    if attributes is not None:
        for key, val in module.params['attributes'].items():
            module.params['attributes'][key] = [val] if not isinstance(val, list) else val

    user_params = [x for x in module.params
                   if x not in list(keycloak_argument_spec().keys()) + ['state', 'realm'] and
                   module.params.get(x) is not None]

    # build a changeset
    changeset = {}
    for param in user_params:
        new_param_value = module.params.get(param)
        old_value = before_user[param] if param in before_user else None
        if new_param_value != old_value:
            changeset[camel(param)] = new_param_value

    # because 'username' is used by all ansible keycloak modules to identify the username of the rest admin user
    # while 'username' is used in keycloak to identify the user to create/update/delete
    if 'userUsername' in changeset:
        changeset['username'] = changeset['userUsername']
        del changeset['userUsername']

    # prepare the new user
    updated_user = before_user.copy()
    updated_user.update(changeset)

    # if before_user is none, the user doesn't exist.
    if before_user == {}:
        if state == 'absent':
            # nothing to do.
            if module._diff:
                result['diff'] = dict(before='', after='')
            result['msg'] = 'User does not exist; doing nothing.'
            result['user'] = dict()
            module.exit_json(**result)

        # for 'present', create a new user.
        result['changed'] = True
        if username is None:
            module.fail_json(msg='username must be specified when creating a new user')

        if module._diff:
            result['diff'] = dict(before='', after=updated_user)

        if module.check_mode:
            module.exit_json(**result)

        # do it for real!
        kc.create_user(updated_user, realm=realm)
        after_user = kc.get_user_by_username(username, realm)

        result['user'] = after_user
        result['msg'] = 'User {username} has been created with ID {id}'.format(username=after_user['username'],
                                                                               id=after_user['id'])

    else:
        if state == 'present':
            # no changes
            if updated_user == before_user:
                result['changed'] = False
                result['user'] = updated_user
                result['msg'] = "No changes required to user {username}.".format(username=before_user['username'])
                module.exit_json(**result)

            # update the existing user
            result['changed'] = True

            if module._diff:
                result['diff'] = dict(before=before_user, after=updated_user)

            if module.check_mode:
                module.exit_json(**result)

            # do the update
            kc.update_user(updated_user, realm=realm)

            after_user = kc.get_user_by_userid(updated_user['id'], realm=realm)

            result['user'] = after_user
            result['msg'] = "User {id} has been updated".format(id=after_user['id'])

            module.exit_json(**result)

        elif state == 'absent':
            result['user'] = dict()

            if module._diff:
                result['diff'] = dict(before=before_user, after='')

            if module.check_mode:
                module.exit_json(**result)

            # delete for real
            uid = before_user['id']
            kc.delete_user(userid=uid, realm=realm)

            result['changed'] = True
            result['msg'] = "User {username} has been deleted".format(username=before_user['username'])

            module.exit_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
