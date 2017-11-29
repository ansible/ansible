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
module: keycloak_client

short_description: Allows administration of Keycloak clients via Keycloak API

version_added: "2.5"

description:
    - This module allows the administration of Keycloak clients via the Keycloak REST API. It
      requires access to the REST API via OpenID Connect; the user connecting and the client being
      used must have the requisite access rights. In a default Keycloak installation, admin-cli
      and an admin user would work, as would a separate client definition with the scope tailored
      to your needs and a user having the expected roles.

    - The names of module options are snake_cased versions of the camelCase ones found in the
      Keycloak API and its documentation at U(http://www.keycloak.org/docs-api/3.3/rest-api/)

    - The Keycloak API does not always enforce for only sensible settings to be used -- you can set
      SAML-specific settings on an OpenID Connect client for instance and vice versa. Be careful.
      If you do not specify a setting, usually a sensible default is chosen.

options:
    state:
        description:
            - State of the client
            - On C(present), the client will be created (or updated if it exists already).
            - On C(absent), the client will be removed if it exists
        required: false
        choices: ['present', 'absent']
        default: 'present'

    client_id:
        description:
            - Client id of client to be worked on. This is usually an alphanumeric name chosen by
              you. Either this or I(id) is required. If you specify both, I(id) takes precedence.
              This is 'clientId' in the Keycloak REST API.
        required: false

    id:
        description:
            - Id of client to be worked on. This is usually an UUID. Either this or I(client_id)
              is required. If you specify both, this takes precedence.
        required: false

    name:
        description:
            - Name of the client (this is not the same as I(client_id))
        required: false

    description:
        description:
            - Description of the client in Keycloak
        required: false

    root_url:
        description:
            - Root URL appended to relative URLs for this client
              This is 'rootUrl' in the Keycloak REST API.
        required: false

    admin_url:
        description:
            - URL to the admin interface of the client
              This is 'adminUrl' in the Keycloak REST API.
        required: false

    base_url:
        description:
            - Default URL to use when the auth server needs to redirect or link back to the client
              This is 'baseUrl' in the Keycloak REST API.
        required: false

    enabled:
        description:
            - Is this client enabled or not?
        required: false

    client_authenticator_type:
        description:
            - How do clients authenticate with the auth server? Either C(client-secret) or
              C(client-jwt) can be chosen. When using C(client-secret), the module parameter
              I(secret) can set it, while for C(client-jwt), you can use the keys C(use.jwks.url),
              C(jwks.url), and C(jwt.credential.certificate) in the I(attributes) module parameter
              to configure its behavior.
              This is 'clientAuthenticatorType' in the Keycloak REST API.
        required: false
        choices: ['client-secret', 'client-jwt']

    secret:
        description:
            - When using I(client_authenticator_type) C(client-secret) (the default), you can
              specify a secret here (otherwise one will be generated if it does not exit). If
              changing this secret, the module will not register a change currently (but the
              changed secret will be saved).
        required: false

    registration_access_token:
        description:
            - The registration access token provides access for clients to the client registration
              service.
              This is 'registrationAccessToken' in the Keycloak REST API.
        required: false

    default_roles:
        description:
            - list of default roles for this client. If the client roles referenced do not exist
              yet, they will be created.
              This is 'defaultRoles' in the Keycloak REST API.
        required: false

    redirect_uris:
        description:
            - Acceptable redirect URIs for this client.
              This is 'redirectUris' in the Keycloak REST API.
        required: false

    web_origins:
        description:
            - List of allowed CORS origins.
              This is 'webOrigins' in the Keycloak REST API.
        required: false

    not_before:
        description:
            - Revoke any tokens issued before this date for this client (this is a UNIX timestamp).
              This is 'notBefore' in the Keycloak REST API.
        required: false

    bearer_only:
        description:
            - The access type of this client is bearer-only.
              This is 'bearerOnly' in the Keycloak REST API.
        required: false

    consent_required:
        description:
            - If enabled, users have to consent to client access.
              This is 'consentRequired' in the Keycloak REST API.
        required: false

    standard_flow_enabled:
        description:
            - Enable standard flow for this client or not (OpenID connect).
              This is 'standardFlowEnabled' in the Keycloak REST API.
        required: false

    implicit_flow_enabled:
        description:
            - Enable implicit flow for this client or not (OpenID connect).
              This is 'implictFlowEnabled' in the Keycloak REST API.
        required: false

    direct_access_grants_enabled:
        description:
            - Are direct access grants enabled for this client or not (OpenID connect).
              This is 'directAccessGrantsEnabled' in the Keycloak REST API.
        required: false

    service_accounts_enabled:
        description:
            - Are service accounts enabled for this client or not (OpenID connect).
              This is 'serviceAccountsEnabled' in the Keycloak REST API.
        required: false

    authorization_services_enabled:
        description:
            - Are authorization services enabled for this client or not (OpenID connect).
              This is 'authorizationServicesEnabled' in the Keycloak REST API.
        required: false

    public_client:
        description:
            - Is the access type for this client public or not.
              This is 'publicClient' in the Keycloak REST API.
        required: false

    frontchannel_logout:
        description:
            - Is frontchannel logout enabled for this client or not.
              This is 'frontchannelLogout' in the Keycloak REST API.
        required: false

    protocol:
        description:
            - Type of client (either C(openid-connect) or C(saml).
        required: false
        choices: ['openid-connect', 'saml']

    full_scope_allowed:
        description:
            - Is the "Full Scope Allowed" feature set for this client or not.
              This is 'fullScopeAllowed' in the Keycloak REST API.
        required: false

    node_re_registration_timeout:
        description:
            - Cluster node re-registration timeout for this client.
              This is 'nodeReRegistrationTimeout' in the Keycloak REST API.
        required: false

    registered_nodes:
        description:
            - dict of registered cluster nodes (with C(nodename) as the key and last registration
              time as the value).
              This is 'registeredNodes' in the Keycloak REST API.
        required: false

    client_template:
        description:
            - Client template to use for this client. If it does not exist this field will silently
              be dropped.
              This is 'clientTemplate' in the Keycloak REST API.
        required: false

    use_template_config:
        description:
            - Whether or not to use configuration from the I(client_template).
              This is 'useTemplateConfig' in the Keycloak REST API.
        required: false

    use_template_scope:
        description:
            - Whether or not to use scope configuration from the I(client_template).
              This is 'useTemplateScope' in the Keycloak REST API.
        required: false

    use_template_mappers:
        description:
            - Whether or not to use mapper configuration from the I(client_template).
              This is 'useTemplateMappers' in the Keycloak REST API.
        required: false

    surrogate_auth_required:
        description:
            - Whether or not surrogate auth is required.
              This is 'surrogateAuthRequired' in the Keycloak REST API.
        required: false

    authorization_settings:
        description:
            - a data structure defining the authorization settings for this client. For reference,
              please see the Keycloak API docs at U(http://www.keycloak.org/docs-api/3.3/rest-api/index.html#_resourceserverrepresentation).
              This is 'authorizationSettings' in the Keycloak REST API.
        required: false

    protocol_mappers:
        description:
            - a list of dicts defining protocol mappers for this client. An example of one is given
              in the examples section.
              This is 'protocolMappers' in the Keycloak REST API.
        required: false

    attributes:
        description:
            - A dict of further attributes for this client. This can contain various configuration
              settings; an example is given in the examples section.
        required: false

extends_documentation_fragment:
    - keycloak

author:
    - Eike Frost (@eikef)
'''

EXAMPLES = '''
- name: Create or update Keycloak client (minimal example)
  local_action:
    module: keycloak_client
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    client_id: test
    state: present

- name: Delete a Keycloak client
  local_action:
    module: keycloak_client
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    client_id: test
    state: absent

- name: Create or update a Keycloak client (with all the bells and whistles)
  local_action:
    module: keycloak_client
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    state: present
    realm: master
    client_id: test
    id: d8b127a3-31f6-44c8-a7e4-4ab9a3e78d95
    name: this_is_a_test
    description: Description of this wonderful client
    root_url: https://www.example.com/
    admin_url: https://www.example.com/admin_url
    base_url: basepath
    enabled: True
    client_authenticator_type: client-secret
    secret: REALLYWELLKEPTSECRET
    redirect_uris:
      - https://www.example.com/*
      - http://localhost:8888/
    web_origins:
      - https://www.example.com/*
    not_before: 1507825725
    bearer_only: False
    consent_required: False
    standard_flow_enabled: True
    implicit_flow_enabled: False
    direct_access_grants_enabled: False
    service_accounts_enabled: False
    authorization_services_enabled: False
    public_client: False
    frontchannel_logout: False
    protocol: openid-connect
    full_scope_allowed: false
    node_re_registration_timeout: -1
    client_template: test
    use_template_config: False
    use_template_scope: false
    use_template_mappers: no
    registered_nodes:
      node01.example.com: 1507828202
    registration_access_token: eyJWT_TOKEN
    surrogate_auth_required: false
    default_roles:
      - test01
      - test02
    protocol_mappers:
      - config:
          access.token.claim: True
          claim.name: "family_name"
          id.token.claim: True
          jsonType.label: String
          user.attribute: lastName
          userinfo.token.claim: True
        consentRequired: True
        consentText: "${familyName}"
        name: family name
        protocol: openid-connect
        protocolMapper: oidc-usermodel-property-mapper
      - config:
          attribute.name: Role
          attribute.nameformat: Basic
          single: false
        consentRequired: false
        name: role list
        protocol: saml
        protocolMapper: saml-role-list-mapper
    attributes:
      saml.authnstatement: True
      saml.client.signature: True
      saml.force.post.binding: True
      saml.server.signature: True
      saml.signature.algorithm: RSA_SHA256
      saml.signing.certificate: CERTIFICATEHERE
      saml.signing.private.key: PRIVATEKEYHERE
      saml_force_name_id_format: False
      saml_name_id_format: username
      saml_signature_canonicalization_method: "http://www.w3.org/2001/10/xml-exc-c14n#"
      user.info.response.signature.alg: RS256
      request.object.signature.alg: RS256
      use.jwks.url: true
      jwks.url: JWKS_URL_FOR_CLIENT_AUTH_JWT
      jwt.credential.certificate: JWT_CREDENTIAL_CERTIFICATE_FOR_CLIENT_AUTH
'''

RETURN = '''
msg:
  description: Message as to what action was taken
  returned: always
  type: string
  sample: "Client testclient has been updated"

proposed:
    description: client representation of proposed changes to client
    returned: always
    type: dict
    sample: {
      clientId: "test"
    }
existing:
    description: client representation of existing client (sample is truncated)
    returned: always
    type: dict
    sample: {
        "adminUrl": "http://www.example.com/admin_url",
        "attributes": {
            "request.object.signature.alg": "RS256",
        }
    }
end_state:
    description: client representation of client after module execution (sample is truncated)
    returned: always
    type: dict
    sample: {
        "adminUrl": "http://www.example.com/admin_url",
        "attributes": {
            "request.object.signature.alg": "RS256",
        }
    }
'''

from ansible.module_utils.keycloak import KeycloakAPI, camel, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule


def sanitize_cr(clientrep):
    """ Removes probably sensitive details from a client representation

    :param clientrep: the clientrep dict to be sanitized
    :return: sanitized clientrep dict
    """
    result = clientrep.copy()
    if 'secret' in result:
        result['secret'] = 'no_log'
    if 'attributes' in result:
        if 'saml.signing.private.key' in result['attributes']:
            result['attributes']['saml.signing.private.key'] = 'no_log'
    return result


def main():
    """
    Module execution

    :return:
    """
    argument_spec = keycloak_argument_spec()
    meta_args = dict(
        state=dict(default='present', choices=['present', 'absent']),
        realm=dict(type='str', default='master'),

        id=dict(type='str'),
        client_id=dict(type='str'),
        name=dict(type='str'),
        description=dict(type='str'),
        root_url=dict(type='str'),
        admin_url=dict(type='str'),
        base_url=dict(type='str'),
        surrogate_auth_required=dict(type='bool'),
        enabled=dict(type='bool'),
        client_authenticator_type=dict(type='str', choices=['client-secret', 'client-jwt']),
        secret=dict(type='str', no_log=True),
        registration_access_token=dict(type='str'),
        default_roles=dict(type='list'),
        redirect_uris=dict(type='list'),
        web_origins=dict(type='list'),
        not_before=dict(type='int'),
        bearer_only=dict(type='bool'),
        consent_required=dict(type='bool'),
        standard_flow_enabled=dict(type='bool'),
        implicit_flow_enabled=dict(type='bool'),
        direct_access_grants_enabled=dict(type='bool'),
        service_accounts_enabled=dict(type='bool'),
        authorization_services_enabled=dict(type='bool'),
        public_client=dict(type='bool'),
        frontchannel_logout=dict(type='bool'),
        protocol=dict(type='str', choices=['openid-connect', 'saml']),
        attributes=dict(type='dict'),
        full_scope_allowed=dict(type='bool'),
        node_re_registration_timeout=dict(type='int'),
        registered_nodes=dict(type='dict'),
        client_template=dict(type='str'),
        use_template_config=dict(type='bool'),
        use_template_scope=dict(type='bool'),
        use_template_mappers=dict(type='bool'),
        protocol_mappers=dict(type='list'),
        authorization_settings=dict(type='dict'),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['client_id', 'id']]))

    result = dict(changed=False, msg='', diff={}, proposed={}, existing={}, end_state={})

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)

    realm = module.params.get('realm')
    cid = module.params.get('id')
    state = module.params.get('state')

    # convert module parameters to client representation parameters (if they belong in there)
    client_params = [x for x in module.params
                     if x not in list(keycloak_argument_spec().keys()) + ['state', 'realm'] and
                     module.params.get(x) is not None]
    keycloak_argument_spec().keys()
    # See whether the client already exists in Keycloak
    if cid is None:
        before_client = kc.get_client_by_clientid(module.params.get('client_id'), realm=realm)
        if before_client is not None:
            cid = before_client['id']
    else:
        before_client = kc.get_client_by_id(cid, realm=realm)

    if before_client is None:
        before_client = dict()

    # Build a proposed changeset from parameters given to this module
    changeset = dict()

    for client_param in client_params:
        # lists in the Keycloak API are sorted
        new_param_value = module.params.get(client_param)
        if isinstance(new_param_value, list):
            try:
                new_param_value = sorted(new_param_value)
            except TypeError:
                pass
        changeset[camel(client_param)] = new_param_value

    # Whether creating or updating a client, take the before-state and merge the changeset into it
    updated_client = before_client.copy()
    updated_client.update(changeset)

    result['proposed'] = sanitize_cr(changeset)
    result['existing'] = sanitize_cr(before_client)

    # If the client does not exist yet, before_client is still empty
    if before_client == dict():
        if state == 'absent':
            # do nothing and exit
            if module._diff:
                result['diff'] = dict(before='', after='')
            result['msg'] = 'Client does not exist, doing nothing.'
            module.exit_json(**result)

        # create new client
        result['changed'] = True
        if 'clientId' not in updated_client:
            module.fail_json(msg='client_id needs to be specified when creating a new client')

        if module._diff:
            result['diff'] = dict(before='', after=sanitize_cr(updated_client))

        if module.check_mode:
            module.exit_json(**result)

        kc.create_client(updated_client, realm=realm)
        after_client = kc.get_client_by_clientid(updated_client['clientId'], realm=realm)

        result['end_state'] = sanitize_cr(after_client)

        result['msg'] = 'Client %s has been created.' % updated_client['clientId']
        module.exit_json(**result)
    else:
        if state == 'present':
            # update existing client
            result['changed'] = True
            if module.check_mode:
                # We can only compare the current client with the proposed updates we have
                if module._diff:
                    result['diff'] = dict(before=sanitize_cr(before_client),
                                          after=sanitize_cr(updated_client))

                module.exit_json(**result)

            kc.update_client(cid, updated_client, realm=realm)

            after_client = kc.get_client_by_id(cid, realm=realm)
            if before_client == after_client:
                result['changed'] = False
            if module._diff:
                result['diff'] = dict(before=sanitize_cr(before_client),
                                      after=sanitize_cr(after_client))
            result['end_state'] = sanitize_cr(after_client)

            result['msg'] = 'Client %s has been updated.' % updated_client['clientId']
            module.exit_json(**result)
        else:
            # Delete existing client
            result['changed'] = True
            if module._diff:
                result['diff']['before'] = sanitize_cr(before_client)
                result['diff']['after'] = ''

            if module.check_mode:
                module.exit_json(**result)

            kc.delete_client(cid, realm=realm)
            result['proposed'] = dict()
            result['end_state'] = dict()
            result['msg'] = 'Client %s has been deleted.' % before_client['clientId']
            module.exit_json(**result)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
