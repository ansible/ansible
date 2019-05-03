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
module: keycloak_identity_provider
short_description: Configure an identity provider in Keycloak
description:
  - This module creates, removes or update Keycloak identity provider.
version_added: "2.9"
options:
  realm:
    description:
    - The name of the realm in which is the identity provider.
    default: master
  alias:
    description:
    - The alias of the identity provider.
    required: true
  displayName:
    description:
    - The display name of the realm.
    required: false
  providerId:
    description:
    - Type of identity provider.
    required: false
  enabled:
    description:
    - enabled.
    required: false
    default: true
  updateProfileFirstLoginMode:
    description:
    - update Profile First Login Mode.
    required: false
  trustEmail:
    description:
    - trust Email.
    required: false
  storeToken:
    description:
    - store Token.
    required: false
    default: true
  addReadTokenRoleOnCreate:
    description:
    - add Read Token Role On Create.
    required: false
  authenticateByDefault:
    description:
    - authenticate By Default.
    required: false
  firstBrokerLoginFlowAlias:
    description:
    - first Broker Login Flow Alias.
    required: false
  postBrokerLoginFlowAlias:
    description:
    - post Broker Login Flow Alias.
    required: false
  linkOnly:
    description:
    - Link only option for identity provider
    default: False
  config:
    description:
    - Detailed configuration of the identity provider.
    required: false
    type: dict
    suboptions:
        openIdConfigurationUrl:
            description:
                - Open ID configuration URL of the IdP to configure. Will be used to configure IdP endpoints.
            type: str
        clientId:
            description:
                - Client ID used to authenticate Keycloak on this IdP
            type: str
        clientSecret:
            description:
                - Client secret to authenticate client on the IdP.
            type: str
        disableUserInfo:
            description:
                - Do we need to disable user info endpoint query. Default value is False.
                - Must be set to true when IdP is Microsoft ADFS.
            type: str
            choices:
                - true
                - false
            default: false
        defaultScope:
            description:
                - Default scope supported with this IdP
            type: str
        guiOrder:
            description:
                - Order to display the IdP button on login screen. Lower's first.
            type: int
        backchannelSupported:
            description:
                - Is back channel logout is supported by the IdP.
            type: str
            choices:
                - true
                - false
            default: true
  mappers:
    description:
    - List of mappers for the Identity provider.
    required: false
    type: list
    suboptions:
        name:
            description:
                - Name of the mapper
            type: str
        identityProviderMapper:
            description:
                - Type of identity provider mapper.
            type: str
            choices:
                - oidc-user-attribute-idp-mapper
                - oidc-role-idp-mapper
        config:
            description:
                - Configuration for this mapper.
            type: dict
            suboptions:
                claim:
                    description:
                        - Name of the claim to map.
                    type: str
                user.attribute:
                    description:
                        - This option is for oidc-user-attribute-idp-mapper
                        - User attribute to copy the claim value to.
                    type: str
                claim.value:
                    description:
                        - This option is for oidc-role-idp-mapper
                        - Role will be granted to the user only if the claim match this value.
                    type: str
                role:
                    description:
                        - This option is for oidc-role-idp-mapper
                        - Role to be granted to the user if the claim match claim.value.
                    type: str
  state:
    description:
    - Control if the realm exists.
    choices: [ "present", "absent" ]
    default: present
  force:
    description:
    - If true, allows to remove realm and recreate it.
    type: bool
    default: false
extends_documentation_fragment:
    - keycloak
notes:
  - module does not modify identity provider alias.
author:
    - Philippe Gauthier (@elfelip)
'''

EXAMPLES = '''
    - name: Create IdP1 fully configured with idp user attribute mapper and a role mapper
      keycloak_identity_provider:
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
        realm: "master"
        alias: "IdP1"
        displayName: "My super dooper IdP"
        providerId: "oidc"
        config:
          openIdConfigurationUrl: https://my.idp.com/auth
          clientId: ClientIdMyIdpGaveMe
          clientSecret: ClientSecretMyIdpGaveMe
          disableUserInfo: False
          defaultScope: "openid email profile"
          guiOrder: 1
          backchannelSupported: True
        mappers:
          - name: ClaimMapper
            identityProviderMapper: oidc-user-attribute-idp-mapper
            config:
              claim: claim1
              user.attribute: attr1
            state: present
          - name: MyRoleMapper
            identityProviderMapper: oidc-role-idp-mapper
            config:
              claim: claimName
              claim.value: valueThatGiveRole
              role: roleName
            state: absent
        state: present

    - name: Re-create the Idp1 without mappers. The existing Idp will be deleted.
      keycloak_identity_provider:
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
        realm: "master"
        alias: "IdP1"
        displayName: "My super dooper IdP"
        providerId: "oidc"
        config:
          openIdConfigurationUrl: https://my.idp.com/auth
          clientId: ClientIdMyIdpGaveMe
          clientSecret: ClientSecretMyIdpGaveMe
          disableUserInfo: False
          defaultScope: "openid email profile"
          guiOrder: 2
          backchannelSupported: True
        state: present
        force: yes

    - name: Remove a the Idp IdP1.
      keycloak_identity_provider:
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
        realm: "master"
        alias: IdP1
        state: absent
'''

RETURN = '''
idp:
  description: JSON representation for the identity provider.
  returned: on success
  type: dict
mappers:
  description: List of idp's mappers
  returned: on success
  type: list
msg:
  description: Error message if it is the case
  returned: on error
  type: str
changed:
  description: Return True if the operation changed the identity provider on the keycloak server, false otherwise.
  returned: on success
  type: bool
'''
import copy
from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec, isDictEquals, remove_arguments_with_value_none
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = keycloak_argument_spec()
    idpconfig_spec = {
        "openIdConfigurationUrl": {
            "type": "str"
        },
        "clientId": {
            "type": "str"
        },
        "clientSecret": {
            "type": "str"
        },
        "disableUserInfo": {
            "type": "str",
            "default": "false",
            "choices": ["true", "false"]
        },
        "defaultScope": {
            "type": "str"
        },
        "guiOrder": {
            "type": "int"
        },
        "backchannelSupported": {
            "type": "str",
            "default": "true",
            "choices": ["true", "false"]
        }
    }
    mapperconfig_args = {
        "claim": {
            "type": "str"
        },
        "user.attribute": {
            "type": "str"
        },
        "claim.value": {
            "type": "str"
        },
        "role": {
            "type": "str"
        }
    }
    mapper_spec = {
        "name": {
            "type": "str"
        },
        "identityProviderMapper": {
            "type": "str",
            "choices": [
                "oidc-user-attribute-idp-mapper",
                "oidc-role-idp-mapper"
            ]
        },
        "config": {
            "type": "dict",
            "options": mapperconfig_args
        }
    }
    meta_args = dict(
        realm=dict(type='str', default='master'),
        alias=dict(type='str', required=True),
        displayName=dict(type='str'),
        providerId=dict(type='str'),
        enabled=dict(type='bool', default=True),
        updateProfileFirstLoginMode=dict(type='str'),
        trustEmail=dict(type='bool'),
        storeToken=dict(type='bool', default=True),
        addReadTokenRoleOnCreate=dict(type='bool'),
        authenticateByDefault=dict(type='bool'),
        firstBrokerLoginFlowAlias=dict(type='str'),
        postBrokerLoginFlowAlias=dict(type='str'),
        linkOnly=dict(type='bool', default=False),
        config=dict(type='dict', options=idpconfig_spec),
        mappers=dict(type='list', options=mapper_spec),
        state=dict(choices=["absent", "present"], default='present'),
        force=dict(type='bool', default=False),
    )

    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = dict(changed=False, msg='', idp={}, mappers=[])

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)
    realm = module.params.get('realm')
    state = module.params.get('state')
    force = module.params.get('force')
    changed = False
    # Créer un représentation du realm recu en paramètres
    newIdPRepresentation = {}
    newIdPRepresentation["alias"] = module.params.get('alias')
    newIdPRepresentation["displayName"] = module.params.get('displayName')
    newIdPRepresentation["providerId"] = module.params.get('providerId')
    newIdPRepresentation["enabled"] = module.params.get('enabled')
    if module.params.get('updateProfileFirstLoginMode') is not None:
        newIdPRepresentation["updateProfileFirstLoginMode"] = module.params.get('updateProfileFirstLoginMode')
    if module.params.get('trustEmail') is not None:
        newIdPRepresentation["trustEmail"] = module.params.get('trustEmail')
    if module.params.get('storeToken') is not None:
        newIdPRepresentation["storeToken"] = module.params.get('storeToken')
    if module.params.get('addReadTokenRoleOnCreate') is not None:
        newIdPRepresentation["addReadTokenRoleOnCreate"] = module.params.get('addReadTokenRoleOnCreate')
    if module.params.get("authenticateByDefault") is not None:
        newIdPRepresentation["authenticateByDefault"] = module.params.get('authenticateByDefault')
    if module.params.get('firstBrokerLoginFlowAlias') is not None:
        newIdPRepresentation["firstBrokerLoginFlowAlias"] = module.params.get('firstBrokerLoginFlowAlias')
    if module.params.get('postBrokerLoginFlowAlias') is not None:
        newIdPRepresentation["postBrokerLoginFlowAlias"] = module.params.get('postBrokerLoginFlowAlias')

    newIdPConfig = None
    if module.params.get('config') is not None:
        newIdPConfig = module.params.get('config').copy()
        remove_arguments_with_value_none(newIdPConfig)
        if 'openIdConfigurationUrl' in newIdPConfig:
            del(newIdPConfig['openIdConfigurationUrl'])

    if 'providerId' in newIdPRepresentation and newIdPRepresentation["providerId"] == 'google' and 'userIp' in module.params.get("config"):
        newIdPConfig["userIp"] = module.params.get("config")["userIp"]

    newIdPMappers = module.params.get('mappers')
    remove_arguments_with_value_none(newIdPMappers)

    if newIdPConfig is not None:
        if (module.params.get('config') is not None and
                'openIdConfigurationUrl' in module.params.get('config') and
                module.params.get("config")['openIdConfigurationUrl'] is not None):
            kc.add_idp_endpoints(newIdPConfig, module.params.get("config")['openIdConfigurationUrl'])
        newIdPRepresentation["config"] = newIdPConfig

    # Search the Idp on Keycloak server.
    # By its alias
    idPRepresentation = kc.search_idp_by_alias(alias=newIdPRepresentation["alias"], realm=realm)

    if idPRepresentation == {}:  # IdP does not exist on Keycloak server
        if (state == 'present'):  # If desired state is present
            # Create IdP
            changed = True
            idPRepresentation = kc.create_idp(newIdPRepresentation=newIdPRepresentation, realm=realm)
            result["idp"] = idPRepresentation
            if newIdPMappers is not None and len(newIdPMappers) > 0:
                kc.create_or_update_idp_mappers(alias=newIdPRepresentation["alias"], idPMappers=newIdPMappers, realm=realm)
            mappersRepresentation = kc.get_idp_mappers(alias=newIdPRepresentation["alias"], realm=realm)
            result["mappers"] = mappersRepresentation
        else:  # Sinon, le status est absent
            result["msg"] = newIdPRepresentation["alias"] + ' absent'
    else:  # if IdP already exists
        alias = idPRepresentation['alias']
        if (state == 'present'):  # if desired state is present
            if force:  # If force option is true
                # Delete all idp's mappers
                kc.delete_all_idp_mappers(alias=alias, realm=realm)
                # Delete the existing IdP
                kc.delete_idp(alias=alias, realm=realm)
                # Re-create the IdP
                idPRepresentation = kc.create_idp(newIdPRepresentation=newIdPRepresentation, realm=realm)
                changed = True
            else:  # if force option is false
                # Compare the new Idp with the existing IdP
                if (not isDictEquals(newIdPRepresentation, idPRepresentation, ["clientSecret", "openIdConfigurationUrl", "mappers"]) or
                    ("config" in newIdPRepresentation and "clientSecret" in newIdPRepresentation["config"] and
                     newIdPRepresentation["config"]["clientSecret"] is not None)):
                    # If they are different
                    # Create an updated representation of the IdP
                    updatedIdP = copy.deepcopy(idPRepresentation)
                    updatedIdP.update(newIdPRepresentation)
                    if "config" in newIdPRepresentation and newIdPRepresentation["config"] is not None:
                        updatedConfig = idPRepresentation["config"]
                        updatedConfig.update(newIdPRepresentation["config"])
                        updatedIdP["config"] = updatedConfig
                    # Update the IdP
                    idPRepresentation = kc.update_idp(newIdPRepresentation=updatedIdP, realm=realm)
                    changed = True
            if newIdPMappers is not None and len(newIdPMappers) > 0:
                if kc.create_or_update_idp_mappers(alias=newIdPRepresentation["alias"], idPMappers=newIdPMappers, realm=realm):
                    changed = True
            mappersRepresentation = kc.get_idp_mappers(alias=newIdPRepresentation["alias"], realm=realm)
            result["idp"] = idPRepresentation
            result["mappers"] = mappersRepresentation
        else:  # If desired state is absent
            # Delete all idp's mappers
            kc.delete_all_idp_mappers(alias=alias, realm=realm)
            # Delete the existing IdP
            kc.delete_idp(alias=alias, realm=realm)
            changed = True
            result["msg"] = 'IdP %s is deleted' % (alias)

    result["changed"] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
