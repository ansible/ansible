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
module: sx5_idm_system
short_description: Configure a system application provisioning url in SX5 DB 
description:
    - This module creates, creat or update system application provisioning url.
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
    idmClient_id:
        description:
            - IDM Client ID.
        required: true
    idmClient_secret:
        description:
            - IDM Client Secret.
        required: false
    systemName:
        description:
            - System name of Client ID.
        required: true
    clients:
        description:
            - list of OIDC Client ID for the client in Keycloak.
        required: true
    sx5IdmUrl:
        description:
            - sx5Idm DB REST services URL.
        default: 
        required: true
    sadu_principal:
        description:
            - Princidal provisioning services URL.
        default: 
        required: true
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
      sx5_idm_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        spRealm: Master
        idmClient_id: sx5idm
        idmClient_secret: client_string
        clients: 
        - nom: client1
        - nom: client2
        systemName: systemName
        sx5IdmUrl: http://localhost/client1
        sadu_principal: http://localhost:8088/sadu1
        sadu_secondary:
        - adresse: http://localhost:8088/sadu2
        - adresse: http://localhost:8088/sadu3
        clientRoles_mapper:
        - spClientRole: roleInSp1
          eq_sadu_role: roleSadu1
        - spClientRole: roleInSp2
          eq_sadu_role: roleSadu2
        state: present

    - name: Re-create system1
      sx5_idm_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        idpRealm: Master
        idmClient_id: sx5idm
        idmClient_secret: client_string
        clients: 
        - nom: client1
        - nom: client2
        systemName: systemName
        sx5IdmUrl: http://localhost/client1
        sadu_principal: http://localhost:8088/sadu1
        sadu_secondary:
        - adresse: http://localhost:8088/sadu2
        - adresse: http://localhost:8088/sadu3
        clientRoles_mapper:
        - spClientRole: roleInSp1
          eq_sadu_role: roleSadu1
        - spClientRole: roleInSp2
          eq_sadu_role: roleSadu2
        state: present
        force: yes
        
    - name: Remove system1
      sx5_idm_system:
        spUrl: http://localhost:8080/auth
        spUsername: admin
        spPassword: admin
        spRealm: Master
        idmClient_id: sx5idm
        idmClient_secret: client_string
        systemName: systemName
        sx5IdmUrl: http://localhost/client1
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
from ansible.module_utils.sx5_idm_system_utils import *
from __builtin__ import isinstance    

def main():
    module = AnsibleModule(
        argument_spec = dict(
            spUrl=dict(type='str', required=True),
            spUsername=dict(type='str', required=True),
            spPassword=dict(required=True),
            spRealm=dict(type='str', required=True),
            idmClient_id=dict(type='str', required=True),
            idmClient_secret=dict(type='str', required=False),
            clients=dict(type='list', default=[]),
            systemName=dict(type='str', required=True),
            force=dict(type='bool', default=False),
            state=dict(choices=["absent", "present"], default='present'),
            sx5IdmUrl = dict(type='str', required=True),
            sadu_principal = dict(type='str', required=True),
            sadu_secondary = dict(type='list', default=[]),
            clientRoles_mapper = dict(type='list', default=[]),
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
    spUrl = None
    if "spUrl" in params and params["spUrl"] is not None:
        spUrl = params['spUrl']
    if "spUsername" in params and params["spUsername"] is not None:
        username = params['spUsername']
    if "spPassword" in params and params["spPassword"] is not None:
        password = params['spPassword']
    if "idmClient_id" in params and params["idmClient_id"] is not None:
        clientid = params['idmClient_id']
    if "idmClient_secret" in params and params['idmClient_secret'] is not None:
        clientSecret = params['idmClient_secret']
    else:
        clientSecret = ''
    force = params['force']
    sx5IdmUrl = params['sx5IdmUrl']
    state = params['state']
        
    # Créer un représentation du system pour BD IDM
    newSystemDBRepresentation = {}
    if "spRealm" in params and params["spRealm"] is not None:
        realm = params['spRealm']
        newSystemDBRepresentation["spRealm"] = params['spRealm'].decode("utf-8")
    if "clients" in params and params['clients'] is not None:
        newSystemDBRepresentation["clients"] = params['clients']
    newSystemDBRepresentation["systemName"] = params['systemName'].decode("utf-8")
    newSystemDBRepresentation["sx5IdmUrl"] = params['sx5IdmUrl'].decode("utf-8")
    newSystemDBRepresentation["sadu_principal"] = params['sadu_principal'].decode("utf-8")
    if "sadu_secondary" in params and params['sadu_secondary'] is not None:
        newSystemDBRepresentation["sadu_secondary"] = params['sadu_secondary']
    if "clientRoles_mapper" in params and params['clientRoles_mapper'] is not None:
        newSystemDBRepresentation["clientRoles_mapper"] = params['clientRoles_mapper']
    rc = 0
    result = dict()
    changed = False
    
    headers=''
    if spUrl:
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
                getResponse = requests.get(sx5IdmUrl+"/systemes/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
                if getResponse.status_code == 200:#systeme existe, on le supprime et on le recree
                    dataResponse = getResponse.json()
                    adresse = []
                    adresseP={
                        "principal": True,
                        "adresse": newSystemDBRepresentation["sadu_principal"]
                    }
                    adresse.append(adresseP)
                    for sadu_secondary in newSystemDBRepresentation["sadu_secondary"]:
                        if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                            adresseS={
                                "principal": False,
                                "adresse": sadu_secondary["adresse"]
                            }
                            adresse.append(adresseS)
                    rolemapper = []
                    for clientRoles_mapper in newSystemDBRepresentation["clientRoles_mapper"]:
                        if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                            role={
                                "roleKeycloak": clientRoles_mapper["spClientRole"],
                                "roleSysteme": clientRoles_mapper["eq_sadu_role"]
                            }
                            rolemapper.append(role)
                    body = {
                            "nom": newSystemDBRepresentation["systemName"],
                            "adressesApprovisionnement": adresse,
                            "correspondancesRoles": rolemapper,
                            "clientsKeycloak": newSystemDBRepresentation["clients"]
                        }
                    try:
                        requests.delete(dataResponse["_links"]["self"]["href"],headers=headers)
                        requests.post(sx5IdmUrl+"/systemes/",headers=headers,json=body)
                        getResponse = requests.get(sx5IdmUrl+"/systemes/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
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
                    adresse = []
                    adresseP={
                        "principal": True,
                        "adresse": newSystemDBRepresentation["sadu_principal"]
                    }
                    adresse.append(adresseP)
                    for sadu_secondary in newSystemDBRepresentation["sadu_secondary"]:
                        if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                            adresseS={
                                "principal": False,
                                "adresse": sadu_secondary["adresse"]
                            }
                            adresse.append(adresseS)
                    rolemapper = []
                    for clientRoles_mapper in newSystemDBRepresentation["clientRoles_mapper"]:
                        if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                            role={
                                "roleKeycloak": clientRoles_mapper["spClientRole"],
                                "roleSysteme": clientRoles_mapper["eq_sadu_role"]
                            }
                            rolemapper.append(role)
                    body = {
                            "nom": newSystemDBRepresentation["systemName"],
                            "adressesApprovisionnement": adresse,
                            "correspondancesRoles": rolemapper,
                            "clientsKeycloak": newSystemDBRepresentation["clients"]
                        }
                    try:
                        requests.post(sx5IdmUrl+"/systemes/",headers=headers,json=body)
                        getResponse = requests.get(sx5IdmUrl+"/systemes/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
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
                getResponse = requests.get(sx5IdmUrl+"/systemes/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
                if getResponse.status_code == 200:#systeme exist
                    dataResponse = getResponse.json()
                    adresse = []
                    adresseP={
                        "principal": True,
                        "adresse": newSystemDBRepresentation["sadu_principal"]
                    }
                    adresse.append(adresseP)
                    for sadu_secondary in newSystemDBRepresentation["sadu_secondary"]:
                        if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                            adresseS={
                                "principal": False,
                                "adresse": sadu_secondary["adresse"]
                            }
                            adresse.append(adresseS)
                    rolemapper = []
                    for clientRoles_mapper in newSystemDBRepresentation["clientRoles_mapper"]:
                        if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                            role={
                                "roleKeycloak": clientRoles_mapper["spClientRole"],
                                "roleSysteme": clientRoles_mapper["eq_sadu_role"]
                            }
                            rolemapper.append(role)
                    keycloakClients = []
                    for keycloakClient in dataResponse["clientsKeycloak"]:
                        keycloakClients.append(keycloakClient)
                        
                    for newKeycloakClient in newSystemDBRepresentation["clients"]:
                        keycloakClientFound = False
                        for existingKeycloakClient in keycloakClients:
                            if newKeycloakClient['nom'] == existingKeycloakClient['nom']:
                                keycloakClientFound = True
                        if not keycloakClientFound:
                            keycloakClients.append(newKeycloakClient)
                    body = {
                            "nom": newSystemDBRepresentation["systemName"],
                            "adressesApprovisionnement": adresse,
                            "correspondancesRoles": rolemapper,
                            "clientsKeycloak": keycloakClients
                        }
                    
                    if body["adressesApprovisionnement"] == dataResponse["adressesApprovisionnement"] and body["clientsKeycloak"] == dataResponse["clientsKeycloak"] and body["correspondancesRoles"] == dataResponse["correspondancesRoles"]:
                        changed = False
                        fact = dict(
                            systemes = dataResponse
                            )
                        result = dict(
                            ansible_facts = fact,
                            rc = 0,
                            changed = changed
                            )
                    else:
                        try:
                            requests.put(dataResponse["_links"]["self"]["href"],headers=headers,json=body)
                            getResponse = requests.get(sx5IdmUrl+"/systemes/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
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
                    adresse = []
                    adresseP={
                        "principal": True,
                        "adresse": newSystemDBRepresentation["sadu_principal"]
                    }
                    adresse.append(adresseP)
                    for sadu_secondary in newSystemDBRepresentation["sadu_secondary"]:
                        if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                            adresseS={
                                "principal": False,
                                "adresse": sadu_secondary["adresse"]
                            }
                            adresse.append(adresseS)
                    rolemapper = []
                    for clientRoles_mapper in newSystemDBRepresentation["clientRoles_mapper"]:
                        if "sadu_secondary" in params and params['sadu_secondary'] is not None:
                            role={
                                "roleKeycloak": clientRoles_mapper["spClientRole"],
                                "roleSysteme": clientRoles_mapper["eq_sadu_role"]
                            }
                            rolemapper.append(role)
                    body = {
                            "nom": newSystemDBRepresentation["systemName"],
                            "adressesApprovisionnement": adresse,
                            "correspondancesRoles": rolemapper,
                            "clientsKeycloak": newSystemDBRepresentation["clients"]
                        }
                    try:
                        requests.post(sx5IdmUrl+"/systemes/",headers=headers,json=body)
                        getResponse = requests.get(sx5IdmUrl+"/systemes/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
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
            getResponse = requests.get(sx5IdmUrl+"/systemes/search/findByNom?nom="+newSystemDBRepresentation["systemName"], headers=headers)
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
