#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Nicolas Duclert <nicolas.duclert@metronlab.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: keycloak_user

short_description: Allows administration of Keycloak users via Keycloak API

version_added: "2.10"

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
            - a dictionary with the key and the value to put in keycloak.
              Keycloak will always return the value in a list of one element.
              Keys and values are converted into string.
        type: dict

    user_id:
        description:
            - user_id of client to be worked on. This is usually an UUID. This and I(client_username)
              are mutually exclusive.
        aliases: [ userId ]
        type: str

    user_username:
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
        type: bool

    email:
        description:
            - the user email
            - this module does not check the validity of the email
            - when using the api, there is no check about the validity of the email in keycloak
            - but with manual action, the format is checked
        type: str

    required_actions:
        description:
            - a list of actions to be done by the user after the account creation
            - the possible actions are
              - C(UPDATE_PROFILE), an update of the profile,
              - C(VERIFY_EMAIL), an email is sent to the address with a link to click,
              - C(UPDATE_PASSWORD), update the default password,
              - C(CONFIGURE_TOTP), user must configure a one-time password generator on their mobile
                device using either the Free OTP or Google Authenticator application.
        choices: [ UPDATE_PROFILE, VERIFY_EMAIL, UPDATE_PASSWORD, CONFIGURE_TOTP ]
        elements: str
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

    user_password:
        description:
            - the password set to the user
            - this value is not given by the Keycloak API when requesting the user. When given, it
              reset the user password with the given one and put the C(changed) to True
        aliases: [ userPassword ]
        type: str

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
    user_username: userTest1
- name: Delete previous user
  keycloak_user:
    auth_client_id: admin-cli
    auth_keycloak_url: http://localhost:8080/auth
    auth_realm: master
    auth_username: admin_test
    auth_password: admin_password
    user_username: userTest1
    state: absent
- name: Update keycloak user with all options
  keycloak_user:
    auth_client_id: admin-cli
    auth_keycloak_url: http://localhost:8080/auth
    auth_realm: master
    auth_username: admin_test
    auth_password: admin_password
    user_username: userTest1
    email_verified: yes
    enabled: yes
    email: userTest@domain.org
    first_name: user
    last_name: test
    required_actions: [ UPDATE_PROFILE, CONFIGURE_TOTP ]
    attributes: {'one key': 'one value', 'another key': 42}
    user_password: userTest1secret
'''

RETURN = '''
msg:
  description: Message as to what action was taken
  returned: always
  type: str
  sample: "User usertest1 has been updated"

changed:
  description: whether the user state has changed
  returned: always
  type: bool
  sample: True

user:
    description: user representation the user at the end of the moudel (sample is truncated)
    returned: always
    type: dict
    sample: {
        "enabled": false,
        "attributes": {
            "onekey": ["RS256"],
        }
    }
'''

from ansible.module_utils.identity.keycloak.crud import crud_with_instance
from ansible.module_utils.identity.keycloak.keycloak import (
    camel,
    keycloak_argument_spec,
    get_token,
    KeycloakError,
    get_on_url,
    put_on_url,
    post_on_url,
    delete_on_url,
)
from ansible.module_utils.common.dict_transformations import recursive_diff, dict_merge
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils.basic import AnsibleModule


URL_USERS = "{url}/admin/realms/{realm}/users"
URL_USER = "{url}/admin/realms/{realm}/users/{id}"
URL_FOR_PASSWORD = "{url}/admin/realms/{realm}/users/{id}/reset-password"
AUTHORIZED_REQUIRED_ACTIONS = [
    'CONFIGURE_TOTP',
    'UPDATE_PASSWORD',
    'UPDATE_PROFILE',
    'VERIFY_EMAIL',
]
# is this compatible with native string stategy?
AUTHORIZED_ATTRIBUTE_VALUE_TYPE = (str, int, float, bool)


class KeycloakUser(object):
    def __init__(self, module, connection_header):
        self.module = module
        if not self.attributes_format_is_correct(self.module.params.get('attributes')):
            self.module.fail_json(
                msg=(
                    'Attributes are not in the correct format. Should be a dictionary with '
                    'one value or a list of value per key as string, integer and boolean'
                )
            )
        self.new_password = self.module.params.get('user_password')
        self.restheaders = connection_header
        self.uuid = self.module.params.get('user_id')
        self.initial_representation = self.get_user()
        self.description = 'user {given_id}'.format(given_id=self.given_id)
        try:
            self.uuid = self.initial_representation['id']
        except KeyError:
            pass

    def attributes_format_is_correct(self, given_attributes):
        if not given_attributes:
            return True
        for one_value in given_attributes.values():
            if isinstance(one_value, list):
                if not self.attribute_as_list_format_is_correct(one_value):
                    return False
                continue
            if isinstance(one_value, dict):
                return False
            if not isinstance(one_value, AUTHORIZED_ATTRIBUTE_VALUE_TYPE):
                return False
        return True

    def attribute_as_list_format_is_correct(self, one_value, first_call=True):
        if isinstance(one_value, list) and first_call:
            for one_element in one_value:
                if not self.attribute_as_list_format_is_correct(one_element, False):
                    return False
            return self.attribute_as_list_format_is_correct(one_value[0], False)
        else:
            if not isinstance(one_value, AUTHORIZED_ATTRIBUTE_VALUE_TYPE):
                return False
        return True

    def _get_user_url(self):
        """Create the url in order to get the federation from the given argument (uuid or name)
        :return: the url as string
        :rtype: str
        """
        if self.uuid:
            return URL_USER.format(
                url=self.module.params.get('auth_keycloak_url'),
                realm=quote(self.module.params.get('realm')),
                id=quote(self.uuid),
            )
        return URL_USERS.format(
            url=self.module.params.get('auth_keycloak_url'),
            realm=quote(self.module.params.get('realm')),
        ) + '?username={username}'.format(
            username=self.module.params.get('user_username').lower()
        )

    def get_user(self):
        json_user = get_on_url(
            url=self._get_user_url(),
            restheaders=self.restheaders,
            module=self.module,
            description='user {given_id}'.format(given_id=self.given_id),
        )
        if json_user:
            if self.uuid:
                return json_user
            user_name = self.module.params.get('user_username').lower()
            if user_name:
                for one_user in json_user:
                    if user_name == one_user['username']:
                        return one_user
            return json_user
        return {}

    @property
    def given_id(self):
        """Get the asked id given by the user.
        :return the asked id given by the user as a name or an uuid.
        :rtype: str
        """
        if self.module.params.get('user_username'):
            return self.module.params.get('user_username')
        return self.module.params.get('user_id')

    @property
    def representation(self):
        return self.get_user()

    def delete(self):
        """Delete the federation"""
        user_url = self._get_user_url()
        delete_on_url(user_url, self.restheaders, self.module, 'user %s' % self.given_id)

    def update(self, check=False):
        if not self._arguments_update_representation():
            return {}
        payload = self._create_payload()
        if check:
            return payload
        put_on_url(self._get_user_url(), self.restheaders, self.module, self.description, payload)
        if self.module.params.get('user_password'):
            self._set_new_password()
        return payload

    def _set_new_password(self, user_id=''):
        password_payload = {
            "type": "password",
            "value": self.module.params.get('user_password'),
            "temporary": False,
        }
        if not user_id:
            uuid = self.uuid
        else:
            uuid = user_id
        put_on_url(
            url=URL_FOR_PASSWORD.format(
                url=self.module.params.get('auth_keycloak_url'),
                realm=quote(self.module.params.get('realm')),
                id=quote(uuid),
            ),
            restheaders=self.restheaders,
            module=self.module,
            description=self.description,
            representation=password_payload,
        )

    def _arguments_update_representation(self):
        if self.module.params.get('user_password'):
            return True
        clean_payload = self._create_payload()
        payload_diff, not_used = recursive_diff(clean_payload, self.initial_representation)
        if not payload_diff:
            return False
        return True

    def create(self):
        """Create the federation from the given arguments.
        Before create the federation, there is a check concerning the mandatory
        arguments waited by keycloak.
        If asked by the user, before creating the federation, the connection or
        the authentication can be tested.
        :return: the representation of the updated federation
        :rtype: dict
        """
        user_payload = self._create_payload()
        post_url = URL_USERS.format(
            url=self.module.params.get('auth_keycloak_url'),
            realm=quote(self.module.params.get('realm')),
        )
        post_on_url(
            post_url, self.restheaders, self.module, 'user %s' % self.given_id, user_payload,
        )
        if self.module.params.get('user_password'):
            user_id = self.representation['id']
            self._set_new_password(user_id)
        return user_payload

    def _create_payload(self):
        user_params = [
            x
            for x in self.module.params
            if x not in list(keycloak_argument_spec().keys()) + ['state', 'realm', 'user_password']
            and self.module.params.get(x) is not None
        ]
        payload = {}
        for user_param in user_params:
            new_param_value = self.module.params.get(user_param)
            # some lists in the Keycloak API are sorted, some are not.

            if user_param == 'attributes':
                new_attributes = {}
                for key, value in new_param_value.items():
                    if not isinstance(value, list):
                        new_attributes.update({key: [value]})
                    else:
                        new_attributes.update({key: value})
                new_param_value = new_attributes
            if user_param == 'user_id':
                payload['id'] = new_param_value
            elif user_param == 'user_username':
                payload['username'] = new_param_value
            else:
                payload[camel(user_param)] = new_param_value
        new_payload = dict_merge(self.initial_representation, payload)
        if 'id' in new_payload:
            try:
                new_payload.pop('username')
            except KeyError:
                pass
        return new_payload


def run_module():
    argument_spec = keycloak_argument_spec()
    meta_args = dict(
        state=dict(default='present', choices=['present', 'absent']),
        realm=dict(default='master'),
        user_username=dict(type='str', aliases=['keycloakUsername']),
        user_id=dict(type='str', aliases=['userId']),
        email_verified=dict(type='bool', aliases=['emailVerified']),
        enabled=dict(type='bool'),
        attributes=dict(type='dict'),
        email=dict(type='str'),
        first_name=dict(type='str', aliases=['firstName']),
        last_name=dict(type='str', aliases=['lastName']),
        required_actions=dict(
            type='list', aliases=['requiredActions'], choices=AUTHORIZED_REQUIRED_ACTIONS
        ),
        user_password=dict(type='str', aliases=['userPassword']),
    )

    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=([['user_username', 'user_id']]),
        mutually_exclusive=[['user_username', 'user_id']],
    )

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
        keycloak_user = KeycloakUser(module, connection_header)
        result = crud_with_instance(keycloak_user, 'user')
    except KeycloakError as e:
        module.fail_json(msg=str(e), changed=False, user={})
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
