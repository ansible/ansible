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
module: sx5_sp_config_system
short_description: Configure a system application in SX5 SP DB  
description:
    - This module creates, creat or update system application in SX5 SP DB.
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
    spConfigUrl:
        description:
            - sx5-config DB REST services URL.
        required: true
    spConfigClient_id:
        description:
            - Sx5-sp-Config Client ID.
        required: true
    spConfigClient_secret:
        description:
            - Sx5-sp-Config Client Secret.
        required: false
    systemShortName:
        description:
            - System Short Name acronym without espace.
        required: false
    systemName:
        description:
            - System name of Client ID.
        required: true
    clients:
        description:
            - list of OIDC Client ID for the client in Keycloak.
        required: true
    clientRoles:
        description:
            - list of role in keycloak.
        default: 
        required: false
    sadu_principal:
        description:
            - Princidal provisioning services URL.
        default: 
        required: false
    sadu_secondary:
        description:
            - list of secondary provisioning services URL.
        default: 
        required: false
    clientRoles_mapper:
        description:
            - list of role correspondance between keycloak roles end SADU roles.
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
      sx5_sp_config_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        spRealm: Master
        spConfigUrl: http://localhost:8089/config
        spConfigClient_id: sx5spconfig
        spConfigClient_secret: client_string
        systemName: system1
        systemShortName: S1
        sadu_principal: http://localhost:8088/sadu1
        sadu_secondary:
        - adresse: http://localhost:8088/sadu2
        - adresse: http://localhost:8088/sadu3
        clients: 
        - clientId: client1
        - clientId: client2
        clientRoles_mapper:
        - spClientRole: roleInSp1
          eq_sadu_role: roleSadu1
        - spClientRole: roleInSp2
          eq_sadu_role: roleSadu2
        clientRoles:
        - spClientRoleId: roleId1
          spClientRoleName: roleName1
          spClientRoleDescription: roleDescription1
        - spClientRoleId: roleId2
          spClientRoleName: roleName2
          spClientRoleDescription: roleDescription2
        state: present
    
    - name: Re-create a system system1 with default settings.
      sx5_sp_config_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        spRealm: Master
        spConfigUrl: http://localhost:8089/config
        spConfigClient_id: sx5spconfig
        spConfigClient_secret: client_string
        systemName: system1
        systemShortName: S1
        sadu_principal: http://localhost:8088/sadu1
        sadu_secondary:
        - adresse: http://localhost:8088/sadu2
        - adresse: http://localhost:8088/sadu3
        clients: 
        - clientId: client1
        - clientId: client2
        clientRoles_mapper:
        - spClientRole: roleInSp1
          eq_sadu_role: roleSadu1
        - spClientRole: roleInSp2
          eq_sadu_role: roleSadu2
        clientRoles:
        - spClientRoleId: roleId1
          spClientRoleName: roleName1
          spClientRoleDescription: roleDescription1
        - spClientRoleId: roleId2
          spClientRoleName: roleName2
          spClientRoleDescription: roleDescription2
        state: present
        force: yes
    
    - name: Remove system1.
      sx5_sp_config_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        spRealm: Master
        spConfigUrl: http://localhost:8089/config
        spConfigClient_id: sx5spconfig
        spConfigClient_secret: client_string
        systemName: system1
        systemShortName: S1
        sadu_principal: http://localhost:8088/sadu1
        state: adsent

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
from ansible.module_utils.sx5_sp_config_system_utils import *
from __builtin__ import isinstance    

def main():
    module = AnsibleModule(
        argument_spec = dict(
            spUrl=dict(type='str', required=True),
            spUsername=dict(type='str', required=True),
            spPassword=dict(required=True),
            spRealm=dict(type='str', required=True),
            spConfigUrl = dict(type='str', required=True),
            spConfigClient_id=dict(type='str', required=True),
            spConfigClient_secret=dict(type='str', required=False),
            systemName=dict(type='str', required=True),
            systemShortName=dict(type='str', required=True),
            sadu_principal = dict(type='str', required=False),
            sadu_secondary = dict(type='list', default=[]),
            clients=dict(type='list', default=[]),
            clientRoles=dict(type='list', default=[]),
            clientRoles_mapper = dict(type='list', default=[]),
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
    clientid = params['spConfigClient_id']
    if "spConfigClient_secret" in params and params['spConfigClient_secret'] is not None:
        clientSecret = params['spConfigClient_secret']
    else:
        clientSecret = ''
    realm = params['spRealm']
    force = params['force']
    spConfigUrl = params['spConfigUrl']
    state = params['state']
        
    # Créer un représentation du system pour BD SP config
    newSystemDBRepresentation = {}
    if "spRealm" in params and params["spRealm"] is not None:
        newSystemDBRepresentation["spRealm"] = params['spRealm'].decode("utf-8")
    newSystemDBRepresentation["systemName"] = params['systemName'].decode("utf-8")
    if "systemShortName" in params and params['systemShortName'] is not None:
        newSystemDBRepresentation["systemShortName"] = params['systemShortName']
    newSystemDBRepresentation["spConfigUrl"] = params['spConfigUrl'].decode("utf-8")
    if "sadu_principal" in params and params['sadu_principal'] is not None:
        newSystemDBRepresentation["sadu_principal"] = params['sadu_principal'].decode("utf-8")
    if "sadu_secondary" in params and params['sadu_secondary'] is not None:
        newSystemDBRepresentation["sadu_secondary"] = params['sadu_secondary']
    if "clients" in params and params['clients'] is not None:
        newSystemDBRepresentation["clients"] = params['clients']
    if "clientRoles_mapper" in params and params['clientRoles_mapper'] is not None:
        newSystemDBRepresentation["clientRoles_mapper"] = params['clientRoles_mapper']
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
                getResponse = requests.get(spConfigUrl+"/systemes/"+newSystemDBRepresentation["systemShortName"], headers=headers)
                if getResponse.status_code == 200:#systeme existe, on le supprime et on le recree
                    dataResponse = getResponse.json()
                    adresse = []
                    rolemapper = []
                    if "sadu_principal" in params and params['sadu_principal'] is not None:
                        adresseP={
                            "principale": True,
                            "adresse": newSystemDBRepresentation["sadu_principal"]
                        }
                        adresse.append(adresseP)
                        for sadu_secondary in newSystemDBRepresentation["sadu_secondary"]:
                            if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                                adresseS={
                                    "principale": False,
                                    "adresse": sadu_secondary["adresse"]
                                }
                                adresse.append(adresseS)
                       
                        for clientRoles_mapper in newSystemDBRepresentation["clientRoles_mapper"]:
                            if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                                role={
                                    "roleKeycloak": clientRoles_mapper["spClientRole"],
                                    "roleSysteme": clientRoles_mapper["eq_sadu_role"]
                                }
                                rolemapper.append(role)
                    client = []
                    for clientKeycloak in newSystemDBRepresentation["clients"]:
                        getResponseKeycloak = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientKeycloak["clientid"]})
                        clientS={}
                        if getResponseKeycloak.status_code == 200:
                            dataResponseKeycloak = getResponseKeycloak.json()
                            if not dataResponseKeycloak:
                                clientS={
                                    "nom": "",
                                    "uuidKeycloak":"",
                                    "clientId": clientKeycloak["clientid"],
                                    "description": "",
                                    "roles": []
                                }
                            else:
                                for dataKeycloak in dataResponseKeycloak:
                                    if dataKeycloak["clientId"] == clientKeycloak["clientId"]:
                                        role = []
                                        getResponseKeycloakClientRoles = requests.get(clientSvcBaseUrl+dataKeycloak["id"]+"/roles", headers=headers)
                                        if getResponseKeycloakClientRoles.status_code == 200:
                                            dataResponseroles = getResponseKeycloakClientRoles.json()
                                            for dataKeycloakrole in dataResponseroles:
                                                for clientRoles in newSystemDBRepresentation["clientRoles"]:
                                                    if dataKeycloakrole["name"] == clientRoles["spClientRoleId"]:
                                                        roleS={"uuidRoleKeycloak": dataKeycloakrole["id"],"nom": clientRoles["spClientRoleId"],"description": clientRoles["spClientRoleDescription"]}
                                                        role.append(roleS)
                                        clientS={
                                            "nom": dataKeycloak["name"],
                                            "uuidKeycloak": dataKeycloak["id"],
                                            "clientId": dataKeycloak["clientId"],
                                            "description": dataKeycloak["description"],
                                            "roles": role
                                        }
                        client.append(clientS)
                    bodySystem = {
                            "nom": newSystemDBRepresentation["systemName"],
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "composants": client
                        }
                    bodyAdressesApprovisionnement = {
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "entreesAdressesApprovisionnement": adresse
                        }
                    bodyTableCorrespondance = {
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "entreesTableCorrespondance": rolemapper
                        }
                        #suite
                    try:
                        requests.delete(spConfigUrl+"/systemes/"+dataResponse["cleUnique"],headers=headers)
                        requests.post(spConfigUrl+"/systemes/",headers=headers,json=bodySystem)
                        getResponseSystem = requests.get(spConfigUrl+"/systemes/"+dataResponse["cleUnique"], headers=headers)
                        if getResponseSystem.status_code == 200:
                            dataResponseSystem = getResponseSystem.json()
                            requests.put(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/adressesApprovisionnement",headers=headers,json=bodyAdressesApprovisionnement)
                            requests.put(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/tableCorrespondance",headers=headers,json=bodyTableCorrespondance)
                            getResponsetableCorrespondance = requests.get(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/tableCorrespondance", headers=headers)
                            dataResponsetableCorrespondance = getResponsetableCorrespondance.json()
                            getResponseadressesApprovisionnement = requests.get(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/adressesApprovisionnement", headers=headers)
                            dataResponseadressesApprovisionnement = getResponseadressesApprovisionnement.json()
                            changed = True
                            fact = dict(
                                systemes = dataResponseSystem,
                                entreesAdressesApprovisionnement = dataResponseadressesApprovisionnement,
                                entreesTableCorrespondance = dataResponsetableCorrespondance
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
                    adresse = []
                    rolemapper = []
                    if "sadu_principal" in params and params['sadu_principal'] is not None:
                        adresseP={
                            "principale": True,
                            "adresse": newSystemDBRepresentation["sadu_principal"]
                        }
                        adresse.append(adresseP)
                        for sadu_secondary in newSystemDBRepresentation["sadu_secondary"]:
                            if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                                adresseS={
                                    "principale": False,
                                    "adresse": sadu_secondary["adresse"]
                                }
                                adresse.append(adresseS)
                        
                        for clientRoles_mapper in newSystemDBRepresentation["clientRoles_mapper"]:
                            if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                                role={
                                    "roleKeycloak": clientRoles_mapper["spClientRole"],
                                    "roleSysteme": clientRoles_mapper["eq_sadu_role"]
                                }
                                rolemapper.append(role)
                    client = []
                    for clientKeycloak in newSystemDBRepresentation["clients"]:
                        getResponseKeycloak = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientKeycloak["clientId"]})
                        clientS={}
                        if getResponseKeycloak.status_code == 200:
                            dataResponseKeycloak = getResponseKeycloak.json()
                            if not dataResponseKeycloak:
                                clientS={
                                    "nom": "",
                                    "uuidKeycloak":"",
                                    "clientId": clientKeycloak["clientId"],
                                    "description": "",
                                    "roles": []
                                }
                            else:
                                for dataKeycloak in dataResponseKeycloak:
                                    if dataKeycloak["clientId"] == clientKeycloak["clientId"]:
                                        role = []
                                        getResponseKeycloakClientRoles = requests.get(clientSvcBaseUrl+dataKeycloak["id"]+"/roles", headers=headers)
                                        if getResponseKeycloakClientRoles.status_code == 200:
                                            dataResponseroles = getResponseKeycloakClientRoles.json()
                                            for dataKeycloakrole in dataResponseroles:
                                                for clientRoles in newSystemDBRepresentation["clientRoles"]:
                                                    if dataKeycloakrole["name"] == clientRoles["spClientRoleId"]:
                                                        roleS={"uuidRoleKeycloak": dataKeycloakrole["id"],"nom": clientRoles["spClientRoleId"],"description": clientRoles["spClientRoleDescription"]}
                                                        role.append(roleS)
                                        clientS={
                                            "nom": dataKeycloak["name"],
                                            "uuidKeycloak": dataKeycloak["id"],
                                            "clientId": dataKeycloak["clientId"],
                                            "description": dataKeycloak["description"],
                                            "roles": role
                                        }
                        client.append(clientS)

                    bodySystem = {
                            "nom": newSystemDBRepresentation["systemName"],
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "composants": client
                        }
                    bodyAdressesApprovisionnement = {
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "entreesAdressesApprovisionnement": adresse
                        }
                    bodyTableCorrespondance = {
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "entreesTableCorrespondance": rolemapper
                        }
                    try:
                        requests.post(spConfigUrl+"/systemes/",headers=headers,json=bodySystem)
                        getResponseSystem = requests.get(spConfigUrl+"/systemes/"+newSystemDBRepresentation["systemShortName"], headers=headers)
                        if getResponseSystem.status_code == 200:
                            dataResponseSystem = getResponseSystem.json()
                            requests.put(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/adressesApprovisionnement",headers=headers,json=bodyAdressesApprovisionnement)
                            requests.put(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/tableCorrespondance",headers=headers,json=bodyTableCorrespondance)
                            getResponsetableCorrespondance = requests.get(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/tableCorrespondance", headers=headers)
                            dataResponsetableCorrespondance = getResponsetableCorrespondance.json()
                            getResponseadressesApprovisionnement = requests.get(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/adressesApprovisionnement", headers=headers)
                            dataResponseadressesApprovisionnement = getResponseadressesApprovisionnement.json()
                            changed = True
                            fact = dict(
                                systemes = dataResponseSystem,
                                entreesAdressesApprovisionnement = dataResponseadressesApprovisionnement,
                                entreesTableCorrespondance = dataResponsetableCorrespondance
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
                getResponse = requests.get(spConfigUrl+"/systemes/"+newSystemDBRepresentation["systemShortName"], headers=headers)
                if getResponse.status_code == 200:#systeme exist
                    dataResponse = getResponse.json()
                    adresse = []
                    rolemapper = []
                    if "sadu_principal" in params and params['sadu_principal'] is not None:
                        adresseP={
                            "principale": True,
                            "adresse": newSystemDBRepresentation["sadu_principal"]
                        }
                        adresse.append(adresseP)
                        for sadu_secondary in newSystemDBRepresentation["sadu_secondary"]:
                            if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                                adresseS={
                                    "principale": False,
                                    "adresse": sadu_secondary["adresse"]
                                }
                                adresse.append(adresseS)
                        
                        for clientRoles_mapper in newSystemDBRepresentation["clientRoles_mapper"]:
                            if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                                role={
                                    "roleKeycloak": clientRoles_mapper["spClientRole"],
                                    "roleSysteme": clientRoles_mapper["eq_sadu_role"]
                                }
                                rolemapper.append(role)
                    client = []
                    keycloakClients = []
                    for keycloakClient in dataResponse["composants"]:
                            keycloakClients.append(keycloakClient)

                    for newKeycloakClient in newSystemDBRepresentation["clients"]:
                            keycloakClientFound = False
                            for existingKeycloakClient in keycloakClients:
                                if newKeycloakClient['clientId'] == existingKeycloakClient['clientId']:
                                    keycloakClientFound = True
                            if not keycloakClientFound:
                                keycloakClients.append(newKeycloakClient)

                    for clientKeycloak in keycloakClients:
                        getResponseKeycloak = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientKeycloak["clientId"]})
                        clientS={}
                        if getResponseKeycloak.status_code == 200:
                            dataResponseKeycloak = getResponseKeycloak.json()
                            if not dataResponseKeycloak:
                                clientS={
                                    "nom": "",
                                    "uuidKeycloak":"",
                                    "clientId": clientKeycloak["clientId"],
                                    "description": "",
                                    "roles": []
                                }
                            else:
                                for dataKeycloak in dataResponseKeycloak:
                                    if dataKeycloak["clientId"] == clientKeycloak["clientId"]:
                                        role = []
                                        getResponseKeycloakClientRoles = requests.get(clientSvcBaseUrl+dataKeycloak["id"]+"/roles", headers=headers)
                                        if getResponseKeycloakClientRoles.status_code == 200:
                                            dataResponseroles = getResponseKeycloakClientRoles.json()
                                            for dataKeycloakrole in dataResponseroles:
                                                for clientRoles in newSystemDBRepresentation["clientRoles"]:
                                                    if dataKeycloakrole["name"] == clientRoles["spClientRoleId"]:
                                                        roleS={"uuidRoleKeycloak": dataKeycloakrole["id"],"nom": clientRoles["spClientRoleId"],"description": clientRoles["spClientRoleDescription"]}
                                                        role.append(roleS)
                                        clientS={
                                            "nom": dataKeycloak["name"],
                                            "uuidKeycloak": dataKeycloak["id"],
                                            "clientId": dataKeycloak["clientId"],
                                            "description": dataKeycloak["description"],
                                            "roles": role
                                        }
                        client.append(clientS)
                    bodySystem = {
                            "nom": newSystemDBRepresentation["systemName"],
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "composants": client
                        }
                    bodyAdressesApprovisionnement = {
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "entreesAdressesApprovisionnement": adresse
                        }
                    bodyTableCorrespondance = {
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "entreesTableCorrespondance": rolemapper
                        }
                    getResponsetableCorrespondance = requests.get(spConfigUrl+"/systemes/"+dataResponse["cleUnique"]+"/tableCorrespondance", headers=headers)
                    dataResponsetableCorrespondance = getResponsetableCorrespondance.json()
                    getResponseadressesApprovisionnement = requests.get(spConfigUrl+"/systemes/"+dataResponse["cleUnique"]+"/adressesApprovisionnement", headers=headers)
                    dataResponseadressesApprovisionnement = getResponseadressesApprovisionnement.json()
                    if bodySystem["composants"] == dataResponse["composants"] and bodyAdressesApprovisionnement["entreesAdressesApprovisionnement"] == dataResponseadressesApprovisionnement["entreesAdressesApprovisionnement"] and bodyTableCorrespondance["entreesTableCorrespondance"] == dataResponsetableCorrespondance["entreesTableCorrespondance"]:
                        changed = False
                        fact = dict(
                            systemes = dataResponse,
                            entreesAdressesApprovisionnement = dataResponseadressesApprovisionnement,
                            entreesTableCorrespondance = dataResponsetableCorrespondance
                            )
                        result = dict(
                            ansible_facts = fact,
                            rc = 0,
                            changed = changed
                            )
                    else:
                        try:
                            requests.put(spConfigUrl+"/systemes/"+dataResponse["cleUnique"], headers=headers,json=bodySystem)
                            getResponsesystem = requests.get(spConfigUrl+"/systemes/"+dataResponse["cleUnique"], headers=headers)
                            dataResponsesystem = getResponsesystem.json()
                            requests.put(spConfigUrl+"/systemes/"+dataResponsesystem["cleUnique"]+"/adressesApprovisionnement",headers=headers,json=bodyAdressesApprovisionnement)
                            requests.put(spConfigUrl+"/systemes/"+dataResponsesystem["cleUnique"]+"/tableCorrespondance",headers=headers,json=bodyTableCorrespondance)
                            getResponsetableCorrespondance = requests.get(spConfigUrl+"/systemes/"+dataResponsesystem["cleUnique"]+"/tableCorrespondance", headers=headers)
                            dataResponsetableCorrespondance = getResponsetableCorrespondance.json()
                            getResponseadressesApprovisionnement = requests.get(spConfigUrl+"/systemes/"+dataResponsesystem["cleUnique"]+"/adressesApprovisionnement", headers=headers)
                            dataResponseadressesApprovisionnement = getResponseadressesApprovisionnement.json()
                            changed = True
                            fact = dict(
                                systemes = dataResponsesystem,
                                entreesAdressesApprovisionnement = dataResponseadressesApprovisionnement,
                                entreesTableCorrespondance = dataResponsetableCorrespondance
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
                    adresse = []
                    rolemapper = []
                    if "sadu_principal" in params and params['sadu_principal'] is not None:
                        adresseP={
                            "principale": True,
                            "adresse": newSystemDBRepresentation["sadu_principal"]
                        }
                        adresse.append(adresseP)
                        for sadu_secondary in newSystemDBRepresentation["sadu_secondary"]:
                            if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                                adresseS={
                                    "principale": False,
                                    "adresse": sadu_secondary["adresse"]
                                }
                                adresse.append(adresseS)
                        
                        for clientRoles_mapper in newSystemDBRepresentation["clientRoles_mapper"]:
                            if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                                role={
                                    "roleKeycloak": clientRoles_mapper["spClientRole"],
                                    "roleSysteme": clientRoles_mapper["eq_sadu_role"]
                                }
                                rolemapper.append(role)
                    client = []
                    for clientKeycloak in newSystemDBRepresentation["clients"]:
                        getResponseKeycloak = requests.get(clientSvcBaseUrl, headers=headers, params={'clientId': clientKeycloak["clientId"]})
                        clientS={}
                        if getResponseKeycloak.status_code == 200:
                            dataResponseKeycloak = getResponseKeycloak.json()
                            if not dataResponseKeycloak:
                                clientS={
                                    "nom": "",
                                    "uuidKeycloak":"",
                                    "clientId": clientKeycloak["clientId"],
                                    "description": "",
                                    "roles": []
                                }
                            else:
                                for dataKeycloak in dataResponseKeycloak:
                                    if dataKeycloak["clientId"] == clientKeycloak["clientId"]:
                                        role = []
                                        getResponseKeycloakClientRoles = requests.get(clientSvcBaseUrl+dataKeycloak["id"]+"/roles", headers=headers)
                                        if getResponseKeycloakClientRoles.status_code == 200:
                                            dataResponseroles = getResponseKeycloakClientRoles.json()
                                            for dataKeycloakrole in dataResponseroles:
                                                for clientRoles in newSystemDBRepresentation["clientRoles"]:
                                                    if dataKeycloakrole["name"] == clientRoles["spClientRoleId"]:
                                                        roleS={"uuidRoleKeycloak": dataKeycloakrole["id"],"nom": clientRoles["spClientRoleId"],"description": clientRoles["spClientRoleDescription"]}
                                                        role.append(roleS)
                                        clientS={
                                            "nom": dataKeycloak["name"],
                                            "uuidKeycloak": dataKeycloak["id"],
                                            "clientId": dataKeycloak["clientId"],
                                            "description": dataKeycloak["description"],
                                            "roles": role
                                        }
                        client.append(clientS)

                    bodySystem = {
                            "nom": newSystemDBRepresentation["systemName"],
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "composants": client
                        }
                    bodyAdressesApprovisionnement = {
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "entreesAdressesApprovisionnement": adresse
                        }
                    bodyTableCorrespondance = {
                            "cleUnique": newSystemDBRepresentation["systemShortName"],
                            "entreesTableCorrespondance": rolemapper
                        }
                    try:
                        requests.post(spConfigUrl+"/systemes/",headers=headers,json=bodySystem)
                        getResponseSystem = requests.get(spConfigUrl+"/systemes/"+newSystemDBRepresentation["systemShortName"], headers=headers)
                        if getResponseSystem.status_code == 200:
                            dataResponseSystem = getResponseSystem.json()
                            requests.put(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/adressesApprovisionnement",headers=headers,json=bodyAdressesApprovisionnement)
                            requests.put(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/tableCorrespondance",headers=headers,json=bodyTableCorrespondance)
                            getResponsetableCorrespondance = requests.get(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/tableCorrespondance", headers=headers)
                            dataResponsetableCorrespondance = getResponsetableCorrespondance.json()
                            getResponseadressesApprovisionnement = requests.get(spConfigUrl+"/systemes/"+dataResponseSystem["cleUnique"]+"/adressesApprovisionnement", headers=headers)
                            dataResponseadressesApprovisionnement = getResponseadressesApprovisionnement.json()
                            changed = True
                            fact = dict(
                                systemes = dataResponseSystem,
                                entreesAdressesApprovisionnement = dataResponseadressesApprovisionnement,
                                entreesTableCorrespondance = dataResponsetableCorrespondance
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
            getResponse = requests.get(spConfigUrl+"/systemes/"+newSystemDBRepresentation["systemShortName"], headers=headers)
            if getResponse.status_code == 200:
                dataResponse = getResponse.json()
                try:
                    deleteResponse = requests.delete(spConfigUrl+"/systemes/"+newSystemDBRepresentation["systemShortName"])
                    changed = True
                    result = dict(
                            stdout   = 'deleted',
                            rc       = 0,
                            changed  = changed
                        )
                except requests.exceptions.RequestException, e:
                    fact = dict(
                        systemes = newSystemDBRepresentation)
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