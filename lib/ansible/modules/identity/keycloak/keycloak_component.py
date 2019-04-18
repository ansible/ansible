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
    url:
        description:
            - The url of the Keycloak server.
        default: http://localhost:8080/auth    
        required: true    
    username:
        description:
            - The username to logon to the master realm.
        required: true
    password:
        description:
            - The password for the user to logon the master realm.
        required: true
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
'''

EXAMPLES = '''
    - name: Create a LDAP User Storage provider. A full sync of users and a fedToKeycloak sync for group mappers will be triggered.
      keycloak_component:
        url: http://localhost:8080
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
        url: http://localhost:8080
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
        url: http://localhost:8080
        username: admin
        password: admin
        realm: master
        name: ActiveDirectory
        providerId: ldap
        providerType: org.keycloak.storage.UserStorageProvider
        state: absent
'''

RETURN = '''
ansible_facts:
  description: JSON representation for the component.
  returned: on success
  type: dict
stderr:
  description: Error message if it is the case
  returned: on error
  type: str
rc:
  description: return code, 0 if success, 1 otherwise.
  returned: always
  type: bool
changed:
  description: Return True if the operation changed the component on the keycloak server, false otherwise.
  returned: always
  type: bool
'''
import requests
import json
from ansible.module_utils.keycloak_utils import *
# import module snippets
from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec = dict(
            url=dict(type='str', required=True),
            username=dict(type='str', required=True),
            password=dict(required=True),
            realm=dict(type='str', required=True),
            id=dict(type='str'),
            name=dict(type='str', required=True),
            providerId=dict(choices=["ldap","allowed-client-templates","trusted-hosts","allowed-protocol-mappers","max-clients","scope","consent-required","rsa-generated"], required=True),
            providerType=dict(choices=["org.keycloak.storage.UserStorageProvider", "org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy","org.keycloak.keys.KeyProvider","authenticatorConfig","requiredActions"], required=True),
            parentId=dict(type='str'),
            config=dict(type='dict'),
            subComponents=dict(type='dict'),
            syncUserStorage=dict(choices=["triggerFullSync", "triggerChangedUsersSync"]),
            syncLdapMappers=dict(choices=["fedToKeycloak", "keycloakToFed"]),
            state=dict(choices=["absent", "present"], default='present'),
            force=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
    )
    params = module.params.copy()
    params['force'] = module.boolean(module.params['force'])
    
    result = dict(changed=False, msg='', diff={}, component='', subComponents='')
    #result = component(params)
    
    url = params['url']
    username = params['username']
    password = params['password']
    realm = params['realm']
    state = params['state']
    force = params['force']
    
    # Créer un représentation du component recu en paramètres
    newComponent = {}
    if "id" in params and params["id"] is not None:
        newComponent["id"] = params['id'].decode("utf-8")
    if "name" in params and params["name"] is not None:
        newComponent["name"] = params['name'].decode("utf-8")
    if "providerId" in params and params["providerId"] is not None:
        newComponent["providerId"] = params['providerId'].decode("utf-8")
    if "providerType" in params and params["providerType"] is not None:
        newComponent["providerType"] = params['providerType'].decode("utf-8")
    newComponent["parentId"] = params['parentId'].decode("utf-8") if "parentId" in params and params["parentId"] is not None else realm
    if "config" in params:
        newComponent["config"] = params["config"]
    newSubComponents = params["subComponents"] if "subComponents" in params else None
    syncUserStorage = params['syncUserStorage'].decode("utf-8") if "syncUserStorage" in params and params["syncUserStorage"] is not None and params["syncUserStorage"].decode("utf-8") in ["triggerFullSync", "triggerChangedUsersSync"] else "no"    
    syncLdapMappers = params['syncLdapMappers'].decode("utf-8") if "syncLdapMappers" in params and params["syncLdapMappers"] is not None and params["syncLdapMappers"].decode("utf-8") in ["fedToKeycloak", "keycloakToFed"] else "no"    

    componentSvcBaseUrl = url + "/auth/admin/realms/" + realm + "/components/"
    userStorageUrl = url + "/auth/admin/realms/" + realm + "/user-storage/"
    
    rc = 0
    #result = dict()
    changed = False
    component = None
    try:
        headers = loginAndSetHeaders(url, username, password)
    except Exception, e:
#        result = dict(
#            stderr   = 'login: ' + str(e),
#            rc       = 1,
#            changed  = changed
#            )            
#        return result
        result['msg'] = 'login: ' + str(e)
        result['changed'] = changed
        module.fail_json(**result)
    try: 
        # Vérifier si le composant existe sur le serveur Keycloak
        getResponse = requests.get(componentSvcBaseUrl, headers=headers, params={"name": newComponent["name"],"type": newComponent["providerType"], "parent": newComponent["parentId"]})
        components = getResponse.json()
        for component in components:
            if "providerId" in component and component["providerId"] == newComponent["providerId"]:
                break
    except Exception, e:
#        result = dict(
#            stderr   = 'first client get: ' + str(e),
#            rc       = 1,
#            changed  = changed
#            )
#        return result
        result['msg'] = 'first component get: ' + str(e)
        result['changed'] = changed
        module.fail_json(msg=result['msg'], **result)
        
    if component is None: # Le composant n'existe pas
        # Creer le client
        
        if (state == 'present'): # Si le status est présent
            try:
                # Stocker le composant dans un body prêt a être posté
                data=json.dumps(newComponent)
                # Créer le composant
                postResponse = requests.post(componentSvcBaseUrl, headers=headers, data=data)
                # Obtenir le nouveau composant créé
                getResponse = requests.get(componentSvcBaseUrl, headers=headers, params={"name": newComponent["name"],"type": newComponent["providerType"], "parent": newComponent["parentId"]})
                components = getResponse.json()
                for component in components:
                    if "providerId" in component and component["providerId"] == newComponent["providerId"]:
                        break
                # Si des sous composants ont été défini
                if newSubComponents is not None:
                    # Créer les sous-composants
                    createNewSubcomponents(component, newSubComponents, syncLdapMappers, headers, componentSvcBaseUrl, userStorageUrl)
                    
                # Vérifier si on doit faire la synchronisation des usagers du LDAP
                if newComponent["providerType"] == "org.keycloak.storage.UserStorageProvider" and syncUserStorage is not "no":
                    # Faire la synchronisation des utilisateurs du LDAP
                    postResponse = requests.post(userStorageUrl + component["id"] + "/sync", headers=headers, params={"action": syncUserStorage})
                    # User sync can be longer than the access_token validity. Re-authenticate
                    headers = loginAndSetHeaders(url, username, password)
                # Obtenir les sous composants
                getResponse = requests.get(componentSvcBaseUrl, headers=headers, params={"parent": component["id"]})
                subComponents = getResponse.json()
                changed = True
#                fact = dict(
#                    component = component,
#                    subComponents = subComponents
#                    )
#                result = dict(
#                    ansible_facts = fact,
#                    rc = 0,
#                    changed = changed
#                    )
                result['component'] = component
                result['subComponents'] = subComponents
                result['changed'] = changed

            except requests.exceptions.RequestException, e:
#                fact = dict(
#                    component = newComponent)
#                result = dict(
#                    ansible_facts= fact,
#                    stderr   = 'post component: ' + newComponent["name"] + ' erreur: ' + str(e),
#                    rc       = 1,
#                    changed  = changed
#                    )
                result['msg'] = 'post component: ' + newComponent["name"] + ' erreur: ' + str(e)
                result['component'] = newComponent
                result['changed'] = changed
                module.fail_json(msg=result['msg'], **result)
            except ValueError, e:
#                fact = dict(
#                    component = newComponent)
#                result = dict(
#                    ansible_facts = fact,
#                    stderr   = 'post component: ' + newComponent["name"] + ' erreur: ' + str(e),
#                    rc       = 1,
#                    changed  = changed
#                    )
                result['msg'] = 'post component: ' + newComponent["name"] + ' error: ' + str(e)
                result['component'] = newComponent
                result['changed'] = changed
                module.fail_json(msg=result['msg'], **result)
        elif state == 'absent': # Sinon, le status est absent
            result = dict(
                stdout   = newComponent["name"] + ' absent',
                rc       = 0,
                changed  = changed
            )
            result['msg'] = newComponent["name"] + ' absent'
            result['component'] = newComponent
            result['changed'] = changed
               
    else:  # Le component existe déjà
        try:
            if (state == 'present'): # si le status est présent
                if force: # Si l'option force est sélectionné
                    # Supprimer le client existant
                    deleteResponse = requests.delete(componentSvcBaseUrl + component["id"], headers=headers)
                    changed = True
                    # Stocker le client dans un body prêt a être posté
                    data=json.dumps(newComponent)
                    # Créer le nouveau client
                    postResponse = requests.post(componentSvcBaseUrl, headers=headers, data=data)
                else: # Si l'option force n'est pas sélectionné
                    excludes = []
                    #if "bindCredential" in newComponent["config"]:
                    #    excludes.append("bindCredential")
                    excludes.append("bindCredential")
                    # Comparer les components
                    if not isDictEquals(newComponent, component, excludes): # Si le nouveau composant introduit des modifications
                        # Stocker le client dans un body prêt a être posté
                        data=json.dumps(newComponent)
                        # Mettre à jour le client sur le serveur Keycloak
                        updateResponse = requests.put(componentSvcBaseUrl + component["id"], headers=headers, data=data)
                        changed = True
                # Obtenir le composant
                getResponse = getResponse = requests.get(componentSvcBaseUrl + component["id"], headers=headers)
                component = getResponse.json()
                # Obtenir les sous composants
                getResponse = requests.get(componentSvcBaseUrl, headers=headers, params={"parent": component["id"]})
                subComponents = getResponse.json()
                
                if newSubComponents is not None:
                    updateSubcomponents(component, subComponents, newSubComponents, syncLdapMappers, headers, componentSvcBaseUrl, userStorageUrl)
                # Mettre à jour la liste des sous composants
                getResponse = requests.get(componentSvcBaseUrl, headers=headers, params={"parent": component["id"]})
                subComponents = getResponse.json()
                # Vérifier si on doit faire la synchronisation des usagers du LDAP
                if newComponent["providerType"] == "org.keycloak.storage.UserStorageProvider" and syncUserStorage is not "no":
                    # Faire la synchronisation des utilisateurs du LDAP
                    postResponse = requests.post(userStorageUrl + component["id"] + "/sync", headers=headers, params={"action": syncUserStorage})
                    # User sync can be longer than the access_token validity. Re-authenticate
                    headers = loginAndSetHeaders(url, username, password)
#                fact = dict(
#                    component = component,
#                    subComponents = subComponents)
#                result = dict(
#                    ansible_facts = fact,
#                    rc = 0,
#                    changed = changed
#                    )
                result['component'] = component
                result['subComponents'] = subComponents
                result['changed'] = changed
                    
            elif state == 'absent': # Le status est absent
                # Supprimer le composant incluant ses sous-composants
                deleteResponse = requests.delete(componentSvcBaseUrl + component['id'], headers=headers)
                changed = True
#                result = dict(
#                    stdout   = 'deleted',
#                    rc       = 0,
#                    changed  = changed
#                )
                result['msg'] = newComponent["name"] + ' deleted'
                result['changed'] = changed

        except requests.exceptions.RequestException, e:
            #result = dict(
            #    stderr   = 'put or delete component: ' + newComponent['id'] + ' error: ' + str(e),
            #    rc       = 1,
            #    changed  = changed
            #    )
            result['msg'] = 'put or delete component: ' + newComponent['id'] + ' error: ' + str(e)
            result['component'] = newComponent
            result['changed'] = changed
            module.fail_json(msg=result['msg'], **result)
        except ValueError, e:
#            result = dict(
#                stderr   = 'put or delete component: ' + newComponent['id'] + ' error: ' + str(e),
#                rc       = 1,
#                changed  = changed
#                )
            result['msg'] = 'put or delete component: ' + newComponent['id'] + ' error: ' + str(e)
            result['component'] = newComponent
            result['changed'] = changed
            module.fail_json(msg=result['msg'], **result)
#    if result['rc'] != 0:
#        module.fail_json(msg='non-zero return code', **result)
#    else:
    module.exit_json(**result)

def createNewSubcomponents(component, newSubComponents, syncLdapMappers, headers, componentSvcBaseUrl, userStorageUrl):
    for componentType in newSubComponents.keys():
        for newSubComponent in newSubComponents[componentType]:
            newSubComponent["providerType"] = componentType
            newSubComponent["parentId"] = component["id"]
            data=json.dumps(newSubComponent)
            # Créer le sous composant
            postResponse = requests.post(componentSvcBaseUrl, headers=headers, data=data)
            # Vérifier si on doit faire la synchronisation des groupes ou roles du LDAP
            if component["providerType"] == "org.keycloak.storage.UserStorageProvider" and syncLdapMappers is not "no":
                # Obtenir le id du sous-composant
                getResponse = requests.get(componentSvcBaseUrl, headers=headers, params={"name": newSubComponent["name"],"type": newSubComponent["providerType"], "parent": component["id"]})
                subComponents = getResponse.json()
                # Si le sous composant a été trouvé
                for subComponent in subComponents:
                    # Faire la synchronisation du sous-composant
                    postResponse = requests.post(userStorageUrl + subComponent["parentId"] + "/mappers/" + subComponent["id"] + "/sync", headers=headers, params={"direction": syncLdapMappers})

def updateSubcomponents(component, subComponents, newSubComponents, syncLdapMappers, headers, componentSvcBaseUrl, userStorageUrl):
    # Parcourir les sous-composants à créer ou mettre à jour recu en paramètre
    for componentType in newSubComponents.keys():
        for newSubComponent in newSubComponents[componentType]:
            newSubComponent["providerType"] = componentType
            # Le rechercher parmis les sous-composants existant
            newSubComponentFound = False
            for subComponent in subComponents:
                # Si le sous composant existant a le même nom que celui à créer ou modifier
                if subComponent["name"] == newSubComponent["name"]:
                    # Vérifier s'il y a un changement à apporter
                    if not isDictEquals(newSubComponent, subComponent):
                        # Alimenter les Id
                        newSubComponent["parentId"] = subComponent["parentId"]
                        newSubComponent["id"] = subComponent["id"]
                        #print ("Modification sous-composant: " + str(subComponent))
                        #print ("Pour: " + str(newSubComponent))
                        # Modifier le sous-composant
                        data=json.dumps(newSubComponent)
                        updateResponse = requests.put(componentSvcBaseUrl + subComponent["id"], headers=headers, data=data)
                        changed = True
                    newSubComponentFound = True
                    # Vérifier si on doit faire la synchronisation des groupes ou roles du LDAP
                    if component["providerType"] == "org.keycloak.storage.UserStorageProvider" and syncLdapMappers is not "no":
                        # Faire la synchronisation du sous-composant
                        postResponse = requests.post(userStorageUrl + subComponent["parentId"] + "/mappers/" + subComponent["id"] + "/sync", headers=headers, params={"direction": syncLdapMappers})
                    break
            # Si le sous composant a créer n'existe pas sur le serveur Keycloak
            if not newSubComponentFound:
                # Alimenter le parentId
                newSubComponent["parentId"] = component["id"]
                #print ("Creation sous-composant: " + str(newSubComponent))
                # Créer le sous composant
                data=json.dumps(newSubComponent)
                postResponse = requests.post(componentSvcBaseUrl, headers=headers, data=data)
                changed = True
                # Vérifier si on doit faire la synchronisation des groupes ou roles du LDAP
                if component["providerType"] == "org.keycloak.storage.UserStorageProvider" and syncLdapMappers is not "no":
                    # Obtenir le id du sous-composant
                    getResponse = requests.get(componentSvcBaseUrl, headers=headers, params={"name": newSubComponent["name"],"type": newSubComponent["providerType"], "parent": component["id"]})
                    subComponents = getResponse.json()
                    # Si le sous composant a été trouvé
                    for subComponent in subComponents:
                        # Faire la synchronisation du sous-composant
                        postResponse = requests.post(userStorageUrl + subComponent["parentId"] + "/mappers/" + subComponent["id"] + "/sync", headers=headers, params={"direction": syncLdapMappers})

if __name__ == '__main__':
    main()
