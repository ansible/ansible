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
author: "Philippe Gauthier (philippe.gauthier@inspq.qc.ca)"
module: keycloak_identity_provider
short_description: Configure an identity provider in Keycloak
description:
  - This module creates, removes or update Keycloak identity provider.
version_added: "1.1"
options:
  realm:
    description:
    - The name of the realm in which is the identity provider.
    required: true
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
    required: False
    default: False
  config:
    description:
    - Detailed configuration of the identity provider. 
    required: false
  mappers:
    description:
    - List of mappers for the Identity provider.
    required: false
  state:
    description:
    - Control if the realm exists.
    choices: [ "present", "absent" ]
    default: present
    required: false
  force:
    choices: [ "yes", "no" ]
    default: "no"
    description:
    - If yes, allows to remove realm and recreate it.
    required: false
extends_documentation_fragment:
    - keycloak
notes:
  - module does not modify identity provider alias.
'''

EXAMPLES = '''
    - name: Create IdP1 fully configured with idp user attribute mapper and a role mapper
      keycloak_identity_provider:
        realm: "master"
        url: "http://localhost:8080/auth"
        username: "admin"
        password: "password"  
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
        realm: "master"
        url: "http://localhost:8080/auth"
        username: "admin"
        password: "password"  
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
        realm: "master"
        url: "http://localhost:8080/auth"
        username: "admin"
        password: "password"  
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
  returnd: on success
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
from ansible.module_utils.keycloak_utils import isDictEquals
from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule

def main():
    argument_spec = keycloak_argument_spec()

    meta_args = dict(
        realm=dict(type='str', default='master'),
        alias=dict(type='str', required=True),
        displayName=dict(type='str'),
        providerId=dict(type='str'),
        enabled = dict(type='bool', default=True),
        updateProfileFirstLoginMode=dict(type='str'),
        trustEmail=dict(type='bool'),
        storeToken = dict(type='bool', default=True),
        addReadTokenRoleOnCreate = dict(type='bool'),
        authenticateByDefault = dict(type='bool'),
        firstBrokerLoginFlowAlias = dict(type='str'),
        postBrokerLoginFlowAlias = dict(type='str'),
        linkOnly = dict(type='bool', default=False),
        config = dict(type='dict'),
        mappers = dict(type='list'),
        state=dict(choices=["absent", "present"], default='present'),
        force=dict(type='bool', default=False),
    )
    
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['alias']]))

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
        if 'openIdConfigurationUrl' in newIdPConfig:
            del(newIdPConfig['openIdConfigurationUrl'])
  
    if 'providerId' in newIdPRepresentation and newIdPRepresentation["providerId"] == 'google' and 'userIp' in module.params.get("config"):
        newIdPConfig["userIp"] = module.params.get("config")["userIp"]
    
    newIdPMappers = module.params.get('mappers')
    
    if newIdPConfig is not None:
            if module.params.get('config') is not None and 'openIdConfigurationUrl' in module.params.get('config') and module.params.get("config")['openIdConfigurationUrl'] is not None:
                kc.add_idp_endpoints(newIdPConfig, module.params.get("config")['openIdConfigurationUrl'])
            newIdPRepresentation["config"] = newIdPConfig
    
    # Search the Idp on Keycloak server.
    # By its alias        
    idPRepresentation = kc.search_idp_by_alias(alias=newIdPRepresentation["alias"], realm=realm)
    # If no Idp have been found by alias, search by client id if there is one in the config.
    #if idPRepresentation == {} and 'config' in newIdPRepresentation and newIdPRepresentation["config"] is not None and 'clientId' in newIdPRepresentation["config"] and newIdPRepresentation["config"]["clientId"] is not None:
    #    idPRepresentation = kc.search_idp_by_client_id(client_id=newIdPRepresentation["config"]["clientId"], realm=realm)
    
    if idPRepresentation == {}: # IdP does not exist on Keycloak server
        if (state == 'present'): # If desired state is present
            # Create IdP
            changed = True
            idPRepresentation = kc.create_idp(newIdPRepresentation=newIdPRepresentation, realm=realm)
            result["idp"] = idPRepresentation
            if newIdPMappers is not None and len(newIdPMappers) > 0:
                kc.create_or_update_idp_mappers(alias=newIdPRepresentation["alias"], idPMappers=newIdPMappers, realm=realm)
            mappersRepresentation = kc.get_idp_mappers(alias=newIdPRepresentation["alias"], realm=realm)
            result["mappers"] = mappersRepresentation    
        else: # Sinon, le status est absent
            result["msg"] = newIdPRepresentation["alias"] + ' absent'
    else:  # if IdP already exists
        alias = idPRepresentation['alias']
        if (state == 'present'): # if desired state is present
            if force: # If force option is true
                # Delete all idp's mappers
                kc.delete_all_idp_mappers(alias=alias, realm=realm)
                # Delete the existing IdP
                kc.delete_idp(alias=alias, realm=realm)
                # Re-create the IdP
                idPRepresentation = kc.create_idp(newIdPRepresentation=newIdPRepresentation, realm=realm)
                changed = True
            else: # if force option is false
                # Compare the new Idp with the existing IdP
                if not isDictEquals(newIdPRepresentation, idPRepresentation, ["clientSecret", "openIdConfigurationUrl", "mappers"]) or ("config" in newIdPRepresentation and "clientSecret" in newIdPRepresentation["config"] and newIdPRepresentation["config"]["clientSecret"] is not None): 
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
                    changed=True
            mappersRepresentation = kc.get_idp_mappers(alias=newIdPRepresentation["alias"], realm=realm)
            result["idp"] = idPRepresentation
            result["mappers"] = mappersRepresentation
        else: # If desired state is absent
            # Delete all idp's mappers
            kc.delete_all_idp_mappers(alias=alias, realm=realm)
            # Delete the existing IdP
            kc.delete_idp(alias=alias, realm=realm)
            changed=True
            result["msg"] = 'IdP %s is deleted' % (alias)

    result["changed"] = changed
    module.exit_json(**result)
        
if __name__ == '__main__':
    main()
