#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Nicolas Duclert <nicolas.duclert@metronlab.com>
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

version_added: "2.9"

description:
    - This module allows the administration of Keycloak clients via the Keycloak REST API. It
      requires access to the REST API via OpenID Connect; the user connecting and the client being
      used must have the requisite access rights. In a default Keycloak installation, admin-cli
      and an admin user would work, as would a separate client definition with the scope tailored
      to your needs and a user having the expected roles.

    - The names of module options are snake_cased versions of the camelCase ones found in the
      Keycloak API and its documentation at U(https://www.keycloak.org/docs-api/4.8/rest-api/index.html/).
      Aliases are provided so camelCased versions can be used as well. If they are in conflict
      with ansible names or previous used names, they will be prefixed by "keycloak".

options:
    state:
        description:
            - State of the user
            - On C(present), the user will be created (or updated if it exists already).
            - On C(absent), the user will be removed if it exists
        choices: [ present, absent ]
        default: present
        type: str

    realm:
        description:
            - The realm to create the user in.
        default: master
        type: str

    attributes:
        description:
            – a dictionary with the key and the value to put in keycloak.
            Keycloak will always return the value in a list of one element.
            Keys and values are converted into string.
        required: false
        type: dict

    user_id:
        description:
            - user_id of client to be worked on. This is usually an UUID. This and I(client_username)
              are mutually exclusive.
        aliases: [ userId ]
        type: str

    keycloak_username:
        description:
            - username of user to be worked on. This and I(user_id) are mutually exclusive.
            - keycloak lower the username
        aliases: [ keycloakUsername ]
        type: str

    email_verified:
        description:
            - show if the user email have been verified
        required: false
        type: bool
        aliases: [ emailVerified ]

    enabled:
        description:
            - show if the user can logged in
        required: false
        type: bool

    email:
        description:
            - the user email
            - this module does not check the validity of the email
            - when using the api, there is no check about the validity of the email in keycloak
            - but with manual action, the format is checked
        required: false
        type: str

    required_actions:
        description:
            - a list of actions to be done by the user
            - each element must be in the choices
        choices: [ UPDATE_PROFILE, VERIFY_EMAIL, UPDATE_PASSWORD, CONFIGURE_TOTP ]
        aliases: [ requiredActions ]
        type: list

    first_name:
        description:
            - the user first name
        aliases: [ firstName ]
        type: str

    last_name:
        description:
            - the user last name
        aliases: [ lastName ]
        type: str

    credentials:
        description:
            - a dictionary setting the user password.
        type: dict

extends_documentation_fragment:
    - keycloak

author:
    - Nicolas Duclert (@ndclt) <nicolas.duclert@metronlab.com>
'''

EXAMPLES = '''
# Pass in a message
- name: Create or update Keycloak users template (minimal)
  keycloak_user:
    auth_client_id: admin-cli
    auth_keycloak_url: http://localhost:8080/auth
    auth_realm: master
    auth_username: admin_test
    auth_password: admin_password
    keycloak_username: userTest1
- name: Delete previous user
  keycloak_user:
    auth_client_id: admin-cli
    auth_keycloak_url: http://localhost:8080/auth
    auth_realm: master
    auth_username: admin_test
    auth_password: admin_password
    keycloak_username: userTest1
    state: absent
- name: Update keycloak user with all options
  keycloak_user:
    auth_client_id: admin-cli
    auth_keycloak_url: http://localhost:8080/auth
    auth_realm: master
    auth_username: admin_test
    auth_password: admin_password
    keycloak_username: userTest1
    email_verified: yes
    enabled: yes
    email: userTest@domain.org
    first_name: user
    last_name: test
    required_actions: [ UPDATE_PROFILE, CONFIGURE_TOTP ]
    attributes: {'one key': 'one value', 'another key': 42}
    credentials: {'type': 'password', 'user_secret'}
'''

RETURN = '''
msg:
  description: Message as to what action was taken
  returned: always
  type: str
  sample: "User usertest1 has been updated"

proposed:
    description: user representation of proposed changes to user
    returned: always
    type: dict
    sample: {
      "email": "userTest1@domain.org",
      "attributes": {"onekey": "RS256"}
    }
existing:
    description: client representation of existing client (sample is truncated)
    returned: always
    type: dict
    sample: {
        "enabled": false,
        "attributes": {
            "onekey": ["RS256"],
        }
    }
end_state:
    description: client representation of client after module execution (sample is truncated)
    returned: always
    type: dict
    sample: {
        "enabled": false,
        "attributes": {
            "onekey": ["RS256"],
        }
    }
'''

from ansible.module_utils.keycloak import KeycloakAPI, camel, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule


AUTHORIZED_REQUIRED_ACTIONS = [
    'CONFIGURE_TOTP', 'UPDATE_PASSWORD', 'UPDATE_PROFILE', 'VERIFY_EMAIL']
# is this compatible with native string stategy?
AUTHORIZED_ATTRIBUTE_VALUE_TYPE = (str, int, float, bool)


def sanitize_user_representation(user_representation):
    """ Removes probably sensitive details from a user representation

    :param userrep: the userrep dict to be sanitized
    :return: sanitized userrep dict
    """
    result = user_representation.copy()
    if 'credentials' in result:
        # check if this value are to sanitize
        for credential_key in ['hashedSaltedValue', 'salt']:
            if credential_key in result['credentials']:
                result['credentials'][credential_key] = 'no_log'
    return result


def run_module():
    argument_spec = keycloak_argument_spec()
    meta_args = dict(
        state=dict(default='present', choices=['present', 'absent']),
        realm=dict(default='master'),

        keycloak_username=dict(type='str', aliases=['keycloakUsername']),
        user_id=dict(type='str', aliases=['userId']),

        email_verified=dict(type='bool', aliases=['emailVerified']),
        enabled=dict(type='bool'),
        attributes=dict(type='dict'),
        email=dict(type='str'),
        first_name=dict(type='str', aliases=['firstName']),
        last_name=dict(type='str', aliases=['lastName']),
        required_actions=dict(type='list', aliases=['requiredActions'],
                              choices=AUTHORIZED_REQUIRED_ACTIONS),
        credentials=dict(type='dict'),
    )

    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['keycloak_username', 'user_id']]),
                           mutually_exclusive=[['keycloak_username', 'user_id']]
                           )

    realm = module.params.get('realm')
    state = module.params.get('state')
    given_user_id = {'name': module.params.get('keycloak_username')}
    if not given_user_id['name']:
        given_user_id.update({'id': module.params.get('user_id')})
        given_user_id.pop('name')
    else:
        given_user_id.update({'name': given_user_id['name'].lower()})

    if not attributes_format_is_correct(module.params.get('attributes')):
        module.fail_json(msg=(
            'Attributes are not in the correct format. Should be a dictionary with '
            'one value per key as string, integer and boolean'))

    kc = KeycloakAPI(module)
    before_user = get_initial_user(given_user_id, kc, realm)

    result = create_result(before_user, module)

    # If the user does not exist yet, before_user is still empty
    if before_user == dict():
        if state == 'absent':
            do_nothing_and_exit(kc, result)

        create_user(kc, result, realm, given_user_id)
    else:
        if state == 'present':
            updating_user(kc, result, realm, given_user_id)
        else:
            deleting_user(kc, result, realm, given_user_id)


def attributes_format_is_correct(given_attributes):
    if not given_attributes:
        return True
    for one_value in given_attributes.values():
        if isinstance(one_value, list):
            if not attribute_as_list_format_is_correct(one_value):
                return False
            continue
        if isinstance(one_value, dict):
            return False
        if not isinstance(one_value, AUTHORIZED_ATTRIBUTE_VALUE_TYPE):
            return False
    return True


def attribute_as_list_format_is_correct(one_value, first_call=True):
    if isinstance(one_value, list) and first_call:
        if len(one_value) > 1:
            return False
        return attribute_as_list_format_is_correct(one_value[0], False)
    else:
        if not isinstance(one_value, AUTHORIZED_ATTRIBUTE_VALUE_TYPE):
            return False
    return True


def get_initial_user(given_user_id, kc, realm):
    if 'name' in given_user_id:
        before_user = kc.get_user_by_name(given_user_id['name'], realm=realm)
    else:
        before_user = kc.get_user_by_id(given_user_id['id'], realm=realm)
    if before_user is None:
        before_user = dict()
    return before_user


def create_result(before_user, module):
    changeset = create_changeset(module)
    result = dict(changed=False, msg='', diff={}, proposed={}, existing={},
                  end_state={})
    result['proposed'] = changeset
    result['existing'] = before_user
    return result


def create_changeset(module):
    user_params = [
        x for x in module.params
        if x not in list(keycloak_argument_spec().keys()) + ['state', 'realm'] and
        module.params.get(x) is not None]
    changeset = dict()
    for user_param in user_params:
        new_param_value = module.params.get(user_param)

        # some lists in the Keycloak API are sorted, some are not.
        if isinstance(new_param_value, list):
            if user_param in ['attributes']:
                try:
                    new_param_value = sorted(new_param_value)
                except TypeError:
                    pass

        changeset[camel(user_param)] = new_param_value
    return changeset


def do_nothing_and_exit(kc, result):
    module = kc.module
    if module._diff:
        result['diff'] = dict(before='', after='')
    result['msg'] = 'User does not exist, doing nothing.'
    module.exit_json(**result)


def create_user(kc, result, realm, given_user_id):
    module = kc.module
    user_to_create = result['proposed']
    result['changed'] = True

    if module._diff:
        result['diff'] = dict(before='',
                              after=sanitize_user_representation(user_to_create))
    if module.check_mode:
        module.exit_json(**result)

    response = kc.create_user(user_to_create, realm=realm)
    after_user = kc.get_json_from_url(response.headers.get('Location'))
    result['end_state'] = sanitize_user_representation(after_user)
    result['msg'] = 'User %s has been created.' % given_user_id['name']
    module.exit_json(**result)


def updating_user(kc, result, realm, given_user_id):
    module = kc.module
    changeset = result['proposed']
    before_user = result['existing']
    updated_user = before_user.copy()
    updated_user.update(changeset)
    result['changed'] = True

    if module.check_mode:
        # We can only compare the current user with the proposed updates we have
        if module._diff:
            result['diff'] = dict(
                before=sanitize_user_representation(before_user),
                after=sanitize_user_representation(updated_user))
        result['changed'] = (before_user != updated_user)
        module.exit_json(**result)

    if 'name' in given_user_id.keys():
        asked_id = kc.get_user_id(given_user_id['name'], realm=realm)
    else:
        asked_id = given_user_id['id']
    kc.update_user(asked_id, changeset, realm=realm)
    after_user = kc.get_user_by_id(asked_id, realm=realm)
    if before_user == after_user:
        result['changed'] = False

    if module._diff:
        result['diff'] = dict(
            before=sanitize_user_representation(before_user),
            after=sanitize_user_representation(after_user))

    result['end_state'] = sanitize_user_representation(after_user)
    result['msg'] = 'User %s has been updated.' % list(given_user_id.values())[0]
    module.exit_json(**result)


def deleting_user(kc, result, realm, given_user_id):
    module = kc.module
    before_user = result['existing']
    result['proposed'] = {}
    result['changed'] = True
    if module._diff:
        result['diff']['before'] = sanitize_user_representation(
            before_user)
        result['diff']['after'] = ''
    if module.check_mode:
        module.exit_json(**result)
    if 'name' in given_user_id:
        asked_id = kc.get_user_id(given_user_id['name'], realm=realm)
    else:
        asked_id = given_user_id['id']
    kc.delete_user(asked_id, realm=realm)
    result['proposed'] = dict()
    result['end_state'] = dict()
    result['msg'] = 'User %s has been deleted.' % list(given_user_id.values())[0]
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
