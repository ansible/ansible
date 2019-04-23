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
module: keycloak_authentication
short_description: Configure authentication in Keycloak
description:
    - This module actually can only make a copy of an existing authentication flow, add an execution to it and configure it.
    - It can also delete the flow.
version_added: "2.3"
options:
    url:
        description:
            - The url of the Keycloak server.
        default: http://localhost:8080    
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
            - The name of the realm in which is the authentication.
        required: true
    alias:
        description:
            - Alias for the authentication flow
        required: true
    providerId:
        description:
            - providerId for the new flow when not copied from an existing flow.
        required: false
    copyForm:
        description:
            - flowAlias of the authentication flow to use for the copy.
        required: false
    authenticationExecutions:
        description:
            - Configuration structure for the executions
        required: false
    state:
        description:
            - Control if the authentication flow must exists or not
        choices: [ "present", "absent" ]
        default: present
        required: false
    force:
        choices: [ "yes", "no" ]
        default: "no"
        description:
            - If yes, allows to remove the authentication flow and recreate it.
        required: false
notes:
    - This module has very limited functions at the moment. Please contribute if you need more...
'''

EXAMPLES = '''
    - name: Create an authentication flow from first broker login and add an execution to it.
      keycloak_authentication:
        url: http://localhost:8080
        username: admin
        password: password
        realm: master
        alias: "Copy of first broker login"
        copyFrom: "first broker login"
        authenticationExecutions:
          - providerId: "test-execution1"
            requirement: "REQUIRED"
            authenticationConfig: 
              alias: "test.execution1.property"
              config: 
                test1.property: "value"
          - providerId: "test-execution2"
            requirement: "REQUIRED"
            authenticationConfig: 
              alias: "test.execution2.property"
              config: 
                test2.property: "value"
        state: present

    - name: Re-create the authentication flow
      keycloak_authentication:
        url: http://localhost:8080
        username: admin
        password: password
        realm: master
        alias: "Copy of first broker login"
        copyFrom: "first broker login"
        authenticationExecutions:
          - providerId: "test-provisioning"
            requirement: "REQUIRED"
            authenticationConfig: 
              alias: "test.provisioning.property"
              config: 
                test.provisioning.property: "value"
        state: present
        force: yes

    - name: Remove authentication.
      keycloak_authentication:
        url: http://localhost:8080
        username: admin
        password: admin
        realm: master
        alias: "Copy of first broker login"
        state: absent
'''

RETURN = '''
ansible_facts:
  description: JSON representation for the authentication.
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
  description: Return True if the operation changed the authentication on the keycloak server, false otherwise.
  returned: always
  type: bool
'''
import json
import urllib
from ansible.module_utils.keycloak_utils import isDictEquals
from ansible.module_utils.keycloak import KeycloakAPI, camel, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule

#def copyAuthFlow(url, config, headers):
#    
#    copyFrom = config["copyFrom"]
#    
#    newName = dict(
#        newName = config["alias"]
#    )
    
#    data = json.dumps(newName)
#    requests.post(url + "flows/" + urllib.quote(config["copyFrom"]) + "/copy", headers=headers, data=data)
#    getResponse = requests.get(url + "flows/", headers = headers)
#    flowList = getResponse.json()
#    for flow in flowList:
#        if flow["alias"] == config["alias"]:
#            return flow
#    return None

#def createEmptyAuthFlow(url, config, headers):
#    
#    newFlow = dict(
#        alias = config["alias"],
#        providerId = config["providerId"],
#        topLevel = True
#    )
#    data = json.dumps(newFlow)
#    requests.post(url + "flows", headers=headers, data=data)
#    getResponse = requests.get(url + "flows/", headers = headers)
#    flowList = getResponse.json()
#    for flow in flowList:
#        if flow["alias"] == config["alias"]:
#            return flow
#    return None

#def createOrUpdateExecutions(url, config, headers):
#    changed = False
#
#    if "authenticationExecutions" in config:
#        for newExecution in config["authenticationExecutions"]:
#            # Get existing executions on the Keycloak server for this alias
#            getResponse = requests.get(url + "flows/" + urllib.quote(config["alias"]) + "/executions", headers=headers)
#            existingExecutions = getResponse.json()
#            executionFound = False
#            for existingExecution in existingExecutions:
#                if "providerId" in existingExecution and existingExecution["providerId"] == newExecution["providerId"]:
#                    executionFound = True
#                    break
#            if executionFound:
#                # Replace config id of the execution config by it's complete representation
#                if "authenticationConfig" in existingExecution:
#                    execConfigId = existingExecution["authenticationConfig"]
#                    getResponse = requests.get(url + "config/" + execConfigId, headers=headers)
#                    execConfig = getResponse.json()
#                    existingExecution["authenticationConfig"] = execConfig
#
#                # Compare the executions to see if it need changes
#                if not isDictEquals(newExecution, existingExecution):
#                    changed = True
#            else:
#                # Create the new execution
#                newExec = {}
#                newExec["provider"] = newExecution["providerId"]
#                newExec["requirement"] = newExecution["requirement"]
#                data = json.dumps(newExec)
#                requests.post(url + "flows/" + urllib.quote(config["alias"]) + "/executions/execution", headers=headers, data=data)
#                changed = True
#            if changed:
#                # Get existing executions on the Keycloak server for this alias
#                getResponse = requests.get(url + "flows/" + urllib.quote(config["alias"]) + "/executions", headers=headers)
#                existingExecutions = getResponse.json()
#                executionFound = False
#                for existingExecution in existingExecutions:
#                    if "providerId" in existingExecution and existingExecution["providerId"] == newExecution["providerId"]:
#                        executionFound = True
#                        break
#                if executionFound:
#                    # Update the existing execution
#                    updatedExec = {}
#                    updatedExec["id"] = existingExecution["id"]
#                    for key in newExecution:
#                        # create the execution configuration
#                        if key == "authenticationConfig":
#                            # Add the autenticatorConfig to the execution
#                            data = json.dumps(newExecution["authenticationConfig"])
#                            requests.post(url + "executions/" + existingExecution["id"] + "/config", headers=headers, data=data)
#                        else:
#                            updatedExec[key] = newExecution[key]
#                    data = json.dumps(updatedExec)
#                    requests.put(url + "flows/" + urllib.quote(config["alias"]) + "/executions", headers=headers, data=data)
#    return changed

#def getExecutionsRepresentation(url, config, headers):
#    # Get executions created
#    getResponse = requests.get(url + "flows/" + urllib.quote(config["alias"]) + "/executions", headers=headers)
#    executions = getResponse.json()
#    for execution in executions:
#        if "authenticationConfig" in execution:
#            execConfigId = execution["authenticationConfig"]
#            getResponse = requests.get(url + "config/" + execConfigId, headers=headers)
#            execConfig = getResponse.json()
#            execution["authenticationConfig"] = execConfig
#    return executions
        

def main():
    """
    Module execution
    
    :returm:
    """
    argument_spec = keycloak_argument_spec()
    meta_args = dict(
            url=dict(type='str', required=True),
            username=dict(type='str', required=True),
            password=dict(required=True),
            realm=dict(type='str', required=True),
            alias=dict(type='str', required=True),
            providerId=dict(type='str'),
            copyFrom = dict(type='str'),
            authenticationExecutions=dict(type='list'),
            state=dict(choices=["absent", "present"], default='present'),
            force=dict(type='bool', default=False),
        )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['alias']]))

    result = dict(changed=False, msg='', flow={})
    kc = KeycloakAPI(module)

    realm = module.params.get('realm')
    state = module.params.get('state')
    force = module.params.get('force')
    
    # Créer un représentation du authentication recu en paramètres
    newAuthenticationRepresentation = {}
    newAuthenticationRepresentation["alias"] = module.params.get("alias")
    #if "copyFrom" in params and params["copyFrom"] is not None:
    newAuthenticationRepresentation["copyFrom"] = module.params.get("copyFrom")
    #if "providerId" in params and params["providerId"] is not None:
    newAuthenticationRepresentation["providerId"] = module.params.get("providerId")
    #if "authenticationExecutions" in params and params["authenticationExecutions"] is not None:
    newAuthenticationRepresentation["authenticationExecutions"] = module.params.get("authenticationExecutions")
   
    #authenticationSvcBaseUrl = url + "/auth/admin/realms/" + realm + "/authentication/"
    
    changed = False

    authenticationRepresentation = kc.get_authentication_flow_by_alias(alias=newAuthenticationRepresentation["alias"], realm=realm)
        
    if authenticationRepresentation == {}: # Authentication flow does not exist        
        if (state == 'present'): # If desired state is prenset
            # If copyFrom is defined, create authentication flow from a copy
            if "copyFrom" in newAuthenticationRepresentation and newAuthenticationRepresentation["copyFrom"] is not None:
                #authenticationRepresentation = copyAuthFlow(authenticationSvcBaseUrl, newAuthenticationRepresentation, headers)
                authenticationRepresentation = kc.copy_auth_flow(config=newAuthenticationRepresentation, realm=realm)
            else: # Create an empty authentication flow
                #authenticationRepresentation = createEmptyAuthFlow(authenticationSvcBaseUrl, newAuthenticationRepresentation, headers)
                authenticationRepresentation = kc.create_empty_auth_flow(config=newAuthenticationRepresentation, realm=realm)
            # If the authentication still not exist on the server, raise an exception.
            if authenticationRepresentation is None:
                result['msg'] = "Authentication just created not found: " + str(newAuthenticationRepresentation)
                module.fail_json(**result)
            # Configure the executions for the flow
            #createOrUpdateExecutions(authenticationSvcBaseUrl, newAuthenticationRepresentation, headers)
            kc.create_or_update_executions(config=newAuthenticationRepresentation, realm=realm)
            changed = True
            # Get executions created
            #executionsRepresentation = getExecutionsRepresentation(authenticationSvcBaseUrl, newAuthenticationRepresentation, headers)
            executionsRepresentation = kc.get_executions_representation(config=newAuthenticationRepresentation, realm=realm)
            if executionsRepresentation is not None:
                authenticationRepresentation["authenticationExecutions"] = executionsRepresentation
                
            result['changed'] = changed
            result['flow'] = authenticationRepresentation
        elif state == 'absent': # Sinon, le status est absent
            result['msg'] = newAuthenticationRepresentation["alias"] + ' absent'
                
    else:  # The authentication flow already exist
        if (state == 'present'): # if desired state is present
            if force: # If force option is true
                #requests.delete(authenticationSvcBaseUrl + "flows/" + authenticationRepresentation["id"], headers=headers)
                # Delete the actual authentication flow
                kc.delete_authentication_flow_by_id(id=authenticationRepresentation["id"], realm=realm)
                changed = True
                # If copyFrom is defined, create authentication flow from a copy
                if "copyFrom" in newAuthenticationRepresentation and newAuthenticationRepresentation["copyFrom"] is not None:
                    #authenticationRepresentation = copyAuthFlow(authenticationSvcBaseUrl, newAuthenticationRepresentation, headers)
                    authenticationRepresentation = kc.copy_auth_flow(config=newAuthenticationRepresentation, realm=realm)
                else: # Create an empty authentication flow
                    #authenticationRepresentation = createEmptyAuthFlow(authenticationSvcBaseUrl, newAuthenticationRepresentation, headers)
                    authenticationRepresentation = kc.create_empty_auth_flow(config=newAuthenticationRepresentation, realm=realm)
                # If the authentication still not exist on the server, raise an exception.
                if authenticationRepresentation is None:
                    result['msg'] = "Authentication just created not found: " + str(newAuthenticationRepresentation)
                    result['changed'] = changed
                    module.fail_json(**result)
            # Configure the executions for the flow
            #changed = createOrUpdateExecutions(authenticationSvcBaseUrl, newAuthenticationRepresentation, headers)
            if kc.create_or_update_executions(config=newAuthenticationRepresentation, realm=realm):
                changed = True
            # Get executions created
            #executionsRepresentation = getExecutionsRepresentation(authenticationSvcBaseUrl, newAuthenticationRepresentation, headers)
            executionsRepresentation = kc.get_executions_representation(config=newAuthenticationRepresentation, realm=realm)
            if executionsRepresentation is not None:
                authenticationRepresentation["authenticationExecutions"] = executionsRepresentation
            result['flow'] = authenticationRepresentation
            result['changed'] = changed
        elif state == 'absent': # If desired state is absent
            # Delete the authentication flow alias.
            #requests.delete(authenticationSvcBaseUrl + "flows/" + authenticationRepresentation["id"], headers=headers)
            kc.delete_authentication_flow_by_id(id=authenticationRepresentation["id"], realm=realm)
            changed = True
            result['msg'] = 'Authentication flow: ' + newAuthenticationRepresentation['alias'] + ' id: ' + authenticationRepresentation["id"] + ' is deleted'
            result['changed'] = changed
    
    module.exit_json(**result)
    
    
if __name__ == '__main__':
    main()
