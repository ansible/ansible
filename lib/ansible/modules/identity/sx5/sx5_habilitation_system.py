#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, INSPQ Team SX5
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
author: "Etienne Sadio (etienne.sadio@inspq.qc.ca)"
module: sx5_habilitation_system
short_description: Configure a system application in SX5 Habiliataion DB 
description:
    - This module creates, creat or update system application in habilitation DB.
version_added: "2.3"
options:
    spUrl:
        description:
            - The url of the Keycloak server. used to check the presence of the client in services provider
        default:    
        required: true
    spUsername:
        description:
            - The username to logon in Keycloak.
        required: true
    spPassword:
        description:
            - The password for the user to logon in Keycloak.
        required: true
    spRealm:
        description:
            - The name of the Keycloak realm in which is the client.
        required: true
    habilitationClient_id:
        description:
            - Habilitation ui Client ID.
        required: true
    habilitationClient_secret:
        description:
            - Habilitation ui Client Secret.
        required: false
    habilitationUrl:
        description:
            - sx5habilitation DB REST services URL.
        required: true
    systemName:
        description:
            - System name of Client ID.
        required: true
    clientKeycloak:
        description:
            - list of OIDC Client ID for the client in Keycloak.
        required: true
    clientRoles:
        description:
            - list of role in keycloak.
        default: 
        required: false
    force:
        choices: [ "yes", "no" ]
        default: "no"
        description:
            - If yes, allows to remove client and recreate it.
        required: false
    state:
        description:
            - Control if the client must exists or not
        choices: [ "present", "absent" ]
        default: present
        required: false
notes:
    - module does not modify clientId in keycloak.
'''

EXAMPLES = '''
    - name: Create a system system1 with default settings.
      sx5_habilitation_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        spRealm: Master
        habilitationClient_id: sx5habilitation
        habilitationClient_secret: client_string
        habilitationUrl: http://localhost:8089/config
        systemName: systemName
        clientKeycloak:
        - spClient: client1
        - spClient: client2
        clientRoles:
        - spClientRoleId: roleId1
          spClientRoleName: roleName1
          spClientRoleDescription: roleDescription1
        - spClientRoleId: roleId2
          spClientRoleName: roleName2
          spClientRoleDescription: roleDescription2
        state: present

    - name: Create a system system1 with default settings.
      sx5_habilitation_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        spRealm: Master
        habilitationClient_id: sx5habilitation
        habilitationClient_secret: client_string
        habilitationUrl: http://localhost:8089/config
        systemName: systemName
        clientKeycloak:
        - spClient: client1
        - spClient: client2
        clientRoles:
        - spClientRoleId: roleId1
          spClientRoleName: roleName1
          spClientRoleDescription: roleDescription1
        - spClientRoleId: roleId2
          spClientRoleName: roleName2
          spClientRoleDescription: roleDescription2
        state: present
        force: yes
        
    - name: Create a system system1 with default settings.
      sx5_habilitation_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        spRealm: Master
        habilitationClient_id: sx5habilitation
        habilitationClient_secret: client_string
        habilitationUrl: http://localhost:8089/config
        systemName: systemName
        clientKeycloak:
        - spClient: client1
        - spClient: client2
        state: absent

'''

RETURN = '''
ansible_facts:
  description: JSON representation for the system.
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
  description: Return True if the operation changed the system on the SX5 DB, false otherwise.
  returned: always
  type: bool
'''
import requests
import json
import urllib
from ansible.module_utils.sx5_idm_system_utils import *
from __builtin__ import isinstance    

def main():
    module = AnsibleModule(
        argument_spec = dict(
            spUrl=dict(type='str', required=True),
            spUsername=dict(type='str', required=True),
            spPassword=dict(required=True),
            spRealm=dict(type='str', required=True),
            habilitationClient_id=dict(type='str', required=True),
            habilitationClient_secret=dict(type='str', required=False),
            habilitationUrl = dict(type='str', required=True),
            systemName=dict(type='str', required=True),
            clientKeycloak=dict(type='list', default=[]),
            clientRoles=dict(type='list', default=[]),
            force=dict(type='bool', default=False),
            state=dict(choices=["absent", "present"], default='present'),
        ),
        supports_check_mode=True,
    )
    params = module.params.copy()
    params['force'] = module.boolean(module.params['force'])
    
    result = system(params)
    
    if result['rc'] != 0:
        module.fail_json(msg='non-zero return code', **result)
    else:
        module.exit_json(**result)
    
def system(params):
    spUrl = params['spUrl']
    username = params['spUsername']
    password = params['spPassword']
    clientid = params['habilitationClient_id']
    if "habilitationClient_secret" in params and params['habilitationClient_secret'] is not None:
        clientSecret = params['habilitationClient_secret']
    else:
        clientSecret = ''
    realm = params['spRealm']
    force = params['force']
    habilitationUrl = params['habilitationUrl']
    state = params['state']
        
    # Créer un représentation du system pour BD Habilitation
    newSystemDBRepresentation = {}
    newSystemDBRepresentation["spRealm"] = params['spRealm'].decode("utf-8")
    if "clients" in params and params['clients'] is not None:
        newSystemDBRepresentation["clients"] = params['clients']
    newSystemDBRepresentation["systemName"] = params['systemName'].decode("utf-8")
    newSystemDBRepresentation["habilitationUrl"] = params['habilitationUrl'].decode("utf-8")
    if "clientKeycloak" in params and params['clientKeycloak'] is not None:
        newSystemDBRepresentation["clientKeycloak"] = params['clientKeycloak']
    if "clientRoles" in params and params['clientRoles'] is not None:
        newSystemDBRepresentation["clientRoles"] = params['clientRoles']
    rc = 0
    result = dict()
    changed = False
    clientSvcBaseUrl = spUrl + "/auth/admin/realms/" + realm + "/clients/"
    try:
        headers = loginAndSetHeaders(spUrl, realm, username, password, clientid, clientSecret)
    except Exception, e:
        result = dict(
            stderr   = 'login: ' + str(e),
            rc       = 1,
            changed  = changed
            )
        return result
    if state == 'present':# Si le status est présent
        if force: # Si force est de yes modifier le systeme meme s'il existe
            try:
                getResponse = requests.get(habilitationUrl+"/systemeConfigurations/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
                if getResponse.status_code == 200:#systeme existe, on le supprime et on le recree
                    dataResponse = getResponse.json()
                    client = []
                    for clientKeycloak in newSystemDBRepresentation["clientKeycloak"]:
                        getResponseKeycloak = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientKeycloak["spClient"]})
                        clientS={}
                        if getResponseKeycloak.status_code == 200:
                            dataResponseKeycloak = getResponseKeycloak.json()
                            if not dataResponseKeycloak:
                                clientS={
                                    "nom": clientKeycloak["spClient"],
                                    "uuidKeycloak":"",
                                    "clientid": "",
                                    "description": "",
                                    "roles": []
                                }
                            else:
                                for dataKeycloak in dataResponseKeycloak:
                                    if dataKeycloak["clientId"] == clientKeycloak["spClient"]:
                                        role = []
                                        getResponseKeycloakClientRoles = requests.get(clientSvcBaseUrl+dataKeycloak["id"]+"/roles", headers=headers)
                                        if getResponseKeycloakClientRoles.status_code == 200:
                                            dataResponseroles = getResponseKeycloakClientRoles.json()
                                            for dataKeycloakrole in dataResponseroles:
                                                for clientRoles in newSystemDBRepresentation["clientRoles"]:
                                                    if dataKeycloakrole["name"] == clientRoles["spClientRoleId"]:
                                                        roleS={"roleId": dataKeycloakrole["id"],"nom": clientRoles["spClientRoleId"],"description": clientRoles["spClientRoleDescription"]}
                                                        role.append(roleS)
                                        clientS={
                                            "nom": dataKeycloak["name"],
                                            "uuidKeycloak": dataKeycloak["id"],
                                            "clientid": dataKeycloak["clientId"],
                                            "description": dataKeycloak["description"],
                                            "roles": role
                                        }
                            client.append(clientS)
                    body = {"nom": newSystemDBRepresentation["systemName"],"composants": client}
                    try:
                        requests.delete(dataResponse["_links"]["self"]["href"],headers=headers)
                        requests.post(habilitationUrl+"/systemes/",headers=headers,json=body)
                        getResponse = requests.get(habilitationUrl+"/systemeConfigurations/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
                        dataResponse = getResponse.json()
                        changed = True
                        fact = dict(
                            systemes = dataResponse
                            )
                        result = dict(
                            ansible_facts = fact,
                            rc = 0,
                            changed = changed
                            )
                    except requests.exceptions.RequestException, e:
                        fact = dict(
                            systemes = newSystemDBRepresentation)
                        result = dict(
                            ansible_facts= fact,
                            stderr   = 'Update systemes: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                            rc       = 1,
                            changed  = changed
                            )
                    except ValueError, e:
                        fact = dict(
                            systemes = newSystemDBRepresentation)
                        result = dict(
                            ansible_facts= fact,
                            stderr   = 'Update systemes: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                            rc       = 1,
                            changed  = changed
                            )
                elif getResponse.status_code == 404: #systeme n'existe pas, le creer
                    client = []
                    for clientKeycloak in newSystemDBRepresentation["clientKeycloak"]:
                        getResponseKeycloak = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientKeycloak["spClient"]})
                        clientS={}
                        if getResponseKeycloak.status_code == 200:
                            dataResponseKeycloak = getResponseKeycloak.json()
                            if not dataResponseKeycloak:
                                clientS={
                                    "nom": clientKeycloak["spClient"],
                                    "uuidKeycloak":"",
                                    "clientid": "",
                                    "description": "",
                                    "roles": []
                                }
                            else:
                                for dataKeycloak in dataResponseKeycloak:
                                    if dataKeycloak["clientId"] == clientKeycloak["spClient"]:
                                        role = []
                                        getResponseKeycloakClientRoles = requests.get(clientSvcBaseUrl+dataKeycloak["id"]+"/roles", headers=headers)
                                        if getResponseKeycloakClientRoles.status_code == 200:
                                            dataResponseroles = getResponseKeycloakClientRoles.json()
                                            for dataKeycloakrole in dataResponseroles:
                                                for clientRoles in newSystemDBRepresentation["clientRoles"]:
                                                    if dataKeycloakrole["name"] == clientRoles["spClientRoleId"]:
                                                        roleS={"roleId": dataKeycloakrole["id"],"nom": clientRoles["spClientRoleId"],"description": clientRoles["spClientRoleDescription"]}
                                                        role.append(roleS)
                                        clientS={
                                            "nom": dataKeycloak["name"],
                                            "uuidKeycloak": dataKeycloak["id"],
                                            "clientid": dataKeycloak["clientId"],
                                            "description": dataKeycloak["description"],
                                            "roles": role
                                        }
                            client.append(clientS)
                    body = {"nom": newSystemDBRepresentation["systemName"],"composants": client}
                    try:
                        requests.delete(dataResponse["_links"]["self"]["href"],headers=headers)
                        requests.post(habilitationUrl+"/systemes/",headers=headers,json=body)
                        dataResponse = getResponse.json()
                        changed = True
                        fact = dict(
                            systemes = dataResponse
                            )
                        result = dict(
                            ansible_facts = fact,
                            rc = 0,
                            changed = changed
                            )
                    except requests.exceptions.RequestException, e:
                        fact = dict(
                            systemes = newSystemDBRepresentation)
                        result = dict(
                            ansible_facts= fact,
                            stderr   = 'Update systemes: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                            rc       = 1,
                            changed  = changed
                            )
                    except ValueError, e:
                        fact = dict(
                            systemes = newSystemDBRepresentation)
                        result = dict(
                            ansible_facts= fact,
                            stderr   = 'Update systemes: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                            rc       = 1,
                            changed  = changed
                            )
            except requests.exceptions.RequestException, e:
                fact = dict(
                    systemes = newSystemDBRepresentation)
                result = dict(
                    ansible_facts= fact,
                    stderr   = 'Get systeme: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                    rc       = 1,
                    changed  = changed
                    )
            except ValueError, e:
                fact = dict(
                    systemes = newSystemDBRepresentation)
                result = dict(
                    ansible_facts= fact,
                    stderr   = 'Get systeme: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                    rc       = 1,
                    changed  = changed
                    )
        # Si force est de no modifier le systeme s'il change
        else:
            try:
                getResponse = requests.get(habilitationUrl+"/systemeConfigurations/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
                if getResponse.status_code == 200:#systeme exist
                    dataResponse = getResponse.json()
                    client = []
                    for clientKeycloak in newSystemDBRepresentation["clientKeycloak"]:
                        getResponseKeycloak = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientKeycloak["spClient"]})
                        clientS={}
                        if getResponseKeycloak.status_code == 200:
                            dataResponseKeycloak = getResponseKeycloak.json()
                            for dataKeycloak in dataResponseKeycloak:
                                role = []
                                getResponseKeycloakClientRoles = requests.get(clientSvcBaseUrl+dataKeycloak["id"]+"/roles", headers=headers)
                                if getResponseKeycloakClientRoles.status_code == 200:
                                    dataResponseroles = getResponseKeycloakClientRoles.json()
                                    for dataKeycloakrole in dataResponseroles:
                                        for clientRoles in newSystemDBRepresentation["clientRoles"]:
                                            if dataKeycloakrole["name"] == clientRoles["spClientRoleId"]:
                                                roleS={"roleId": dataKeycloakrole["id"],"nom": clientRoles["spClientRoleId"],"description": clientRoles["spClientRoleDescription"]}
                                                role.append(roleS)    
                                clientS={
                                    "nom": dataKeycloak["name"],
                                    "uuidKeycloak": dataKeycloak["id"],
                                    "clientid": dataKeycloak["clientId"],
                                    "description": dataKeycloak["description"],
                                    "roles": role
                                }
                                client.append(clientS)
                    bodyClear = {"nom": newSystemDBRepresentation["systemName"],"composants": []}
                    body = {"nom": newSystemDBRepresentation["systemName"],"composants": client}
                    excludes = []
                    excludes.append("_links")
                    getResponse = requests.get(dataResponse["_links"]["self"]["href"], headers=headers)
                    dataResponseS = getResponse.json()
                    if isDictEquals(body, dataResponseS,excludes):
                    #if body["nom"] == dataResponse["nom"] and body["composants"] == dataResponse["composants"]:
                        changed = False
                        fact = dict(
                            systemes = dataResponse["composants"]
                            )
                        result = dict(
                            ansible_facts = fact,
                            rc = 0,
                            changed = changed
                            )
                    else:
                        try:
                            requests.put(dataResponse["_links"]["self"]["href"],headers=headers,json=bodyClear)
                            requests.put(dataResponse["_links"]["self"]["href"],headers=headers,json=body)
                            getResponse = requests.get(habilitationUrl+"/systemeConfigurations/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
                            dataResponse = getResponse.json()
                            changed = True
                            fact = dict(
                                systemes = dataResponse
                                )
                            result = dict(
                                ansible_facts = fact,
                                rc = 0,
                                changed = changed
                                )
                        except requests.exceptions.RequestException, e:
                            fact = dict(
                                systemes = newSystemDBRepresentation)
                            result = dict(
                                ansible_facts= fact,
                                stderr   = 'Update systemes: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                                rc       = 1,
                                changed  = changed
                                )
                        except ValueError, e:
                            fact = dict(
                                systemes = newSystemDBRepresentation)
                            result = dict(
                                ansible_facts= fact,
                                stderr   = 'Update systemes: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                                rc       = 1,
                                changed  = changed
                                )
                elif getResponse.status_code == 404: #systeme n'existe pas, le creer
                    client = []
                    for clientKeycloak in newSystemDBRepresentation["clientKeycloak"]:
                        getResponseKeycloak = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientKeycloak["spClient"]})
                        clientS={}
                        if getResponseKeycloak.status_code == 200:
                            dataResponseKeycloak = getResponseKeycloak.json()
                            if not dataResponseKeycloak:
                                clientS={
                                    "nom": clientKeycloak["spClient"],
                                    "uuidKeycloak":"",
                                    "clientid": "",
                                    "description": "",
                                    "roles": []
                                }
                            else:
                                for dataKeycloak in dataResponseKeycloak:
                                    if dataKeycloak["clientId"] == clientKeycloak["spClient"] and "clientRoles" in params and params['clientRoles'] is not None:
                                        role = []
                                        getResponseKeycloakClientRoles = requests.get(clientSvcBaseUrl+dataKeycloak["id"]+"/roles", headers=headers)
                                        if getResponseKeycloakClientRoles.status_code == 200:
                                            dataResponseroles = getResponseKeycloakClientRoles.json()
                                            for dataKeycloakrole in dataResponseroles:
                                                for clientRoles in newSystemDBRepresentation["clientRoles"]:
                                                    if dataKeycloakrole["name"] == clientRoles["spClientRoleId"]:
                                                        roleS={"roleId": dataKeycloakrole["id"],"nom": clientRoles["spClientRoleId"],"description": clientRoles["spClientRoleDescription"]}
                                                        role.append(roleS)
                                        clientS={
                                            "nom": dataKeycloak["name"],
                                            "uuidKeycloak": dataKeycloak["id"],
                                            "clientid": dataKeycloak["clientId"],
                                            "description": dataKeycloak["description"],
                                            "roles": role
                                        }
                            client.append(clientS)
                    body = {"nom": newSystemDBRepresentation["systemName"],"composants": client}
                    try:
                        requests.post(habilitationUrl+"/systemeConfigurations/",headers=headers,json=body)
                        getResponse = requests.get(habilitationUrl+"/systemeConfigurations/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
                        dataResponse = getResponse.json()
                        changed = True
                        fact = dict(
                            systemes = dataResponse
                            )
                        result = dict(
                            ansible_facts = fact,
                            rc = 0,
                            changed = changed
                            )
                    except requests.exceptions.RequestException, e:
                        fact = dict(
                            systemes = newSystemDBRepresentation)
                        result = dict(
                            ansible_facts= fact,
                            stderr   = 'Update systemes: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                            rc       = 1,
                            changed  = changed
                            )
                    except ValueError, e:
                        fact = dict(
                            systemes = newSystemDBRepresentation)
                        result = dict(
                            ansible_facts= fact,
                            stderr   = 'Update systemes: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                            rc       = 1,
                            changed  = changed
                            )
            except requests.exceptions.RequestException, e:
                fact = dict(
                    systemes = newSystemDBRepresentation)
                result = dict(
                    ansible_facts= fact,
                    stderr   = 'Get systeme: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                    rc       = 1,
                    changed  = changed
                    )
            except ValueError, e:
                fact = dict(
                    systemes = newSystemDBRepresentation)
                result = dict(
                    ansible_facts= fact,
                    stderr   = 'Get systeme: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                    rc       = 1,
                    changed  = changed
                    )
    elif state == 'absent':# Supprimer le systeme
        try:
            getResponse = requests.get(habilitationUrl+"/systemeConfigurations/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
            if getResponse.status_code == 200:
                dataResponse = getResponse.json()
                try:
                    deleteResponse = requests.delete(dataResponse["_links"]["self"]["href"],headers=headers)
                    changed = True
                    result = dict(
                            stdout   = 'deleted',
                            rc       = 0,
                            changed  = changed
                        )
                except requests.exceptions.RequestException, e:
                    fact = dict(
                        clientSx5 = dataResponse)
                    result = dict(
                        ansible_facts= fact,
                        stderr   = 'Delete system: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                        rc       = 1,
                        changed  = changed
                        )
                except ValueError, e:
                    fact = dict(
                        clientSx5 = dataResponse)
                    result = dict(
                        ansible_facts = fact,
                        stderr   = 'Delete system: ' + newSystemDBRepresentation["systemName"] + ' erreur: ' + str(e),
                        rc       = 1,
                        changed  = changed
                        )
            else:
                result = dict(
                        stdout   = 'system or realm not fond',
                        rc       = 0,
                        changed  = changed
                    )
        except Exception, e:
            result = dict(
                stderr   = 'Client get in state = absent : ' + str(e),
                rc       = 1,
                changed  = changed
                )
    return result
        
# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
