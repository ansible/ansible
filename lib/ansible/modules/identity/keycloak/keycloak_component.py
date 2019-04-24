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
module: keycloak_component
short_description: Configure a component in Keycloak
description:
    - This module creates, removes or update Keycloak component. 
    - It can be use to create a LDAP and AD user federation to a realm in the Keycloak server
version_added: "2.3"
options:
    realm:
        description:
            - The name of the realm in which is the component.
        required: true
    id:
        description:
            - ID of the component when it have already been created and it is known.
        required: false
    name:
        description:
            - Name of the Component
        required: true
    providerId:
        description:
            - ProviderId of the component
        choices: ["ldap","allowed-client-templates","trusted-hosts","allowed-protocol-mappers","max-clients","scope","consent-required","rsa-generated"]
        required: true
    providerType:
        description:
            - Provider type of component
        choices:
            - org.keycloak.storage.UserStorageProvider
            - org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy
            - org.keycloak.keys.KeyProvider
            - authenticatorConfig
            - requiredActions
        required: true
    parentId:
        description:
            - Parent ID of the component. Use the realm name for top level component.
        required: true
    config:
        description:
            - Configuration of the component to create, update or delete.
        required: false
    subComponents:
        description:
            - List of sub components to create inside the component.
            - It can be use to configure group-ldap-mapper for a User Federation.
    syncUserStorage:
        description:
            - Type of user storage synchronization must be triggerd for
            - org.keycloak.storage.UserStorageProvider component. 
            - If the parameter is absent, no sync will be triggered
        required: false
        choices: ["triggerFullSync", "triggerChangedUsersSync"]
    syncLdapMappers:
        description:
            - Type of LDAP mapper synchronization must be triggerd for
            - org.keycloak.storage.ldap.mappers.LDAPStorageMapper/group-ldap-mapper sub components.
            - If the parameter is absent, no sync will be triggered
        required: false
        choices: ["fedToKeycloak", "keycloakToFed"]
    state:
        description:
            - Control if the component must exists or not
        choices: [ "present", "absent" ]
        default: present
        required: false
    force:
        choices: [ "yes", "no" ]
        default: "no"
        description:
            - If yes, allows to remove component and recreate it.
        required: false
extends_documentation_fragment:
    - keycloak
'''

EXAMPLES = '''
    - name: Create a LDAP User Storage provider. A full sync of users and a fedToKeycloak sync for group mappers will be triggered.
      keycloak_component:
        url: http://localhost:8080/auth
        username: admin
        password: admin
        realm: master
        name: ActiveDirectory
        providerId: ldap
        providerType: org.keycloak.storage.UserStorageProvider
        config:
          vendor:
          - "ad"
          usernameLDAPAttribute:
          - "sAMAccountName"
          rdnLDAPAttribute:
          - "cn"
          uuidLDAPAttribute:
          - "objectGUID"
          userObjectClasses:
          - "person"
          - "organizationalPerson"
          - "user"
          connectionUrl:
          - "ldap://ldap.server.com:389"
          usersDn:
          - "OU=USERS,DC=server,DC=com"
          authType: 
          - "simple"
          bindDn:
          - "CN=keycloak,OU=USERS,DC=server,DC=com"
          bindCredential:
          - "UnTresLongMotDePasseQuePersonneNeConnait"
          changedSyncPeriod:
          - "86400"
          fullSyncPeriod:
          - "604800"  
        subComponents:
          org.keycloak.storage.ldap.mappers.LDAPStorageMapper: 
          - name: "groupMapper"
            providerId: "group-ldap-mapper"
            config: 
              mode: 
                - "READ_ONLY"
              membership.attribute.type:
                - "DN"
              user.roles.retrieve.strategy: 
                - "LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"
              group.name.ldap.attribute: 
                - "cn"
              membership.ldap.attribute: 
                - "member"
              preserve.group.inheritance: 
                - "true"
              membership.user.ldap.attribute: 
                - "uid"
              group.object.classes: 
                - "groupOfNames"
              groups.dn: 
                - "cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"
              drop.non.existing.groups.during.sync: 
                - "false"
        syncUserStorage: triggerFullSync
        syncLdapMappers: fedToKeycloak
        state: present

    - name: Re-create LDAP User Storage provider.
      keycloak_component:
        url: http://localhost:8080/auth
        username: admin
        password: admin
        realm: master
        name: ActiveDirectory
        providerId: ldap
        providerType: org.keycloak.storage.UserStorageProvider
        config:
          vendor:
          - "ad"
          usernameLDAPAttribute:
          - "sAMAccountName"
          rdnLDAPAttribute:
          - "cn"
          uuidLDAPAttribute:
          - "objectGUID"
          userObjectClasses:
          - "person"
          - "organizationalPerson"
          - "user"
          connectionUrl:
          - "ldap://ldap.server.com:389"
          usersDn:
          - "OU=USERS,DC=server,DC=com"
          authType: 
          - "simple"
          bindDn:
          - "CN=keycloak,OU=USERS,DC=server,DC=com"
          bindCredential:
          - "UnTresLongMotDePasseQuePersonneNeConnait"
          changedSyncPeriod:
          - "86400"
          fullSyncPeriod:
          - "604800"  
        subComponents:
          org.keycloak.storage.ldap.mappers.LDAPStorageMapper: 
          - name: "groupMapper"
            providerId: "group-ldap-mapper"
            config: 
              mode: 
                - "READ_ONLY"
              membership.attribute.type:
                - "DN"
              user.roles.retrieve.strategy: 
                - "LOAD_GROUPS_BY_MEMBER_ATTRIBUTE"
              group.name.ldap.attribute: 
                - "cn"
              membership.ldap.attribute: 
                - "member"
              preserve.group.inheritance: 
                - "true"
              membership.user.ldap.attribute: 
                - "uid"
              group.object.classes: 
                - "groupOfNames"
              groups.dn: 
                - "cn=groups,OU=SEC,DC=SANTEPUBLIQUE,DC=RTSS,DC=QC,DC=CA"
              drop.non.existing.groups.during.sync: 
                - "false"
        state: present
        force: yes
        
    - name: Remove User Storage Provider.
      keycloak_component:
        url: http://localhost:8080/auth
        username: admin
        password: admin
        realm: master
        name: ActiveDirectory
        providerId: ldap
        providerType: org.keycloak.storage.UserStorageProvider
        state: absent
'''

RETURN = '''
component:
  description: JSON representation for the component.
  returned: on success
  type: dict
subComponents:
  description: JSON representation of the sub components list.
  returned: on success
  type: list
msg:
  description: Error message if it is the case
  returned: on error
  type: str
changed:
  description: Return True if the operation changed the component on the keycloak server, false otherwise.
  returned: always
  type: bool
'''

from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec
from ansible.module_utils.keycloak_utils import isDictEquals
# import module snippets
from ansible.module_utils.basic import AnsibleModule

def main():
    argument_spec = keycloak_argument_spec()
    meta_args = dict(
        id=dict(type='str'),
        name=dict(type='str', required=True),
        realm=dict(type='str', default='master'),
        providerId=dict(choices=["ldap","allowed-client-templates","trusted-hosts","allowed-protocol-mappers","max-clients","scope","consent-required","rsa-generated"], required=True),
        providerType=dict(choices=["org.keycloak.storage.UserStorageProvider", "org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy","org.keycloak.keys.KeyProvider","authenticatorConfig","requiredActions"], required=True),
        parentId=dict(type='str'),
        config=dict(type='dict'),
        subComponents=dict(type='dict'),
        syncUserStorage=dict(choices=["triggerFullSync", "triggerChangedUsersSync"]),
        syncLdapMappers=dict(choices=["fedToKeycloak", "keycloakToFed"]),
        state=dict(choices=["absent", "present"], default='present'),
        force=dict(type='bool', default=False),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['name', 'providerId', 'providerType']]))
        
    result = dict(changed=False, msg='', diff={}, component='', subComponents='')

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)
    
    realm = module.params.get('realm')
    state = module.params.get('state')
    force = module.params.get('force')
    
    # Créer un représentation du component recu en paramètres
    newComponent = {}
    #if "id" in params and params["id"] is not None:
    newComponent["id"] = module.params.get('id')
    #if "name" in params and params["name"] is not None:
    newComponent["name"] = module.params.get('name')
    #if "providerId" in params and params["providerId"] is not None:
    newComponent["providerId"] =module.params.get('providerId')
    #if "providerType" in params and params["providerType"] is not None:
    newComponent["providerType"] = module.params.get('providerType')
    newComponent["parentId"] = module.params.get('parentId') if module.params.get('parentId') is not None else realm
    #if "config" in params:
    newComponent["config"] = module.params.get("config")
    newSubComponents = module.params.get("subComponents")
    syncUserStorage = module.params.get('syncUserStorage') if module.params.get('syncUserStorage') is not None else "no"    
    syncLdapMappers = module.params.get('syncLdapMappers') if module.params.get('syncLdapMappers') is not None else "no"    

    changed = False
    
    component = kc.get_component_by_name_provider_and_parent(name=newComponent["name"], provider_type=newComponent["providerType"], provider_id=newComponent["providerId"], parent_id=newComponent["parentId"], realm=realm)
        
    if component == {}: # If component does not exist
        if (state == 'present'): # If desired stat is present
            # Create the component and it's sub-components
            component = kc.create_component(newComponent=newComponent, newSubComponents=newSubComponents, syncLdapMappers=syncLdapMappers, realm=realm)
            subComponents = kc.get_all_sub_components(parent_id=component["id"], realm=realm)
            if syncUserStorage != 'no': # If user synchronization is needed
                kc.sync_user_storage(component_id=component['id'], action=syncUserStorage, realm=realm)
                result['component'] = component
            changed = True
            result['component'] = component
            result['subComponents'] = subComponents
            result['changed'] = changed
        elif state == 'absent': # Id desired state is absent, return absent and do nothing.
            result['msg'] = newComponent["name"] + ' absent'
            result['component'] = newComponent
            result['changed'] = changed
               
    else:  # If component already exist
        if (state == 'present'): # if desired state is present
            if force: # If force option is true
                # Delete the existing component
                kc.delete_component(component_id=component["id"], realm=realm)
                changed = True
                # Re-create the component.
                component = kc.create_component(newComponent=newComponent, newSubComponents=newSubComponents, syncLdapMappers=syncLdapMappers, realm=realm)
            else: # If force option is false
                # Copy existing id in new component
                newComponent['id'] = component['id']
                newComponent['parentId'] = component['parentId']
                excludes = []
                # Compare the new component with the existing
                excludes.append("bindCredential")
                #excludes.append("id")
                if not isDictEquals(newComponent, component, excludes): # If the component need to be changed
                    # Update the component
                    component = kc.update_component(newComponent=newComponent, realm=realm)
                    changed = True
                # Update sub components
                if kc.update_sub_components(component=newComponent, newSubComponents=newSubComponents, syncLdapMappers=syncLdapMappers, realm=realm):
                    changed=True
            if syncUserStorage != 'no': # If user synchronization is needed
                kc.sync_user_storage(component_id=component['id'], action=syncUserStorage, realm=realm)
            
            result['component'] = component
            result['subComponents'] = kc.get_all_sub_components(parent_id=component["id"], realm=realm)
            result['changed'] = changed
                
        elif state == 'absent': # if desired state is absent
            # Delete the component
            kc.delete_component(component_id=component['id'], realm=realm)
            changed = True
            result['msg'] = newComponent["name"] + ' deleted'
            result['changed'] = changed

    module.exit_json(**result)

if __name__ == '__main__':
    main()
