#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, INSPQ <philippe.gauthier@inspq.qc.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: keycloak_authentication
short_description: Configure authentication in Keycloak
description:
    - This module actually can only make a copy of an existing authentication flow, add an execution to it and configure it.
    - It can also delete the flow.
version_added: "2.9"
options:
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
    copyFrom:
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
        type: bool
        default: false
        description:
            - If true, allows to remove the authentication flow and recreate it.
        required: false
extends_documentation_fragment:
    - keycloak

author:
    - Philippe Gauthier (@elfelip)
'''

EXAMPLES = '''
    - name: Create an authentication flow from first broker login and add an execution to it.
      keycloak_authentication:
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
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
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
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
        auth_keycloak_url: http://localhost:8080/auth
        auth_sername: admin
        auth_password: password
        realm: master
        alias: "Copy of first broker login"
        state: absent
'''

RETURN = '''
flow:
  description: JSON representation for the authentication.
  returned: on success
  type: dict
msg:
  description: Error message if it is the case
  returned: on error
  type: str
changed:
  description: Return True if the operation changed the authentication on the keycloak server, false otherwise.
  returned: always
  type: bool
'''
from ansible.module_utils.keycloak import KeycloakAPI, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    """
    Module execution
    :returm:
    """
    argument_spec = keycloak_argument_spec()
    meta_args = dict(
        realm=dict(type='str', required=True),
        alias=dict(type='str', required=True),
        providerId=dict(type='str'),
        copyFrom=dict(type='str'),
        authenticationExecutions=dict(type='list'),
        state=dict(choices=["absent", "present"], default='present'),
        force=dict(type='bool', default=False),
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = dict(changed=False, msg='', flow={})
    kc = KeycloakAPI(module)

    realm = module.params.get('realm')
    state = module.params.get('state')
    force = module.params.get('force')

    newAuthenticationRepresentation = {}
    newAuthenticationRepresentation["alias"] = module.params.get("alias")
    newAuthenticationRepresentation["copyFrom"] = module.params.get("copyFrom")
    newAuthenticationRepresentation["providerId"] = module.params.get("providerId")
    newAuthenticationRepresentation["authenticationExecutions"] = module.params.get("authenticationExecutions")

    changed = False

    authenticationRepresentation = kc.get_authentication_flow_by_alias(alias=newAuthenticationRepresentation["alias"], realm=realm)

    if authenticationRepresentation == {}:  # Authentication flow does not exist
        if (state == 'present'):  # If desired state is prenset
            # If copyFrom is defined, create authentication flow from a copy
            if "copyFrom" in newAuthenticationRepresentation and newAuthenticationRepresentation["copyFrom"] is not None:
                authenticationRepresentation = kc.copy_auth_flow(config=newAuthenticationRepresentation, realm=realm)
            else:  # Create an empty authentication flow
                authenticationRepresentation = kc.create_empty_auth_flow(config=newAuthenticationRepresentation, realm=realm)
            # If the authentication still not exist on the server, raise an exception.
            if authenticationRepresentation is None:
                result['msg'] = "Authentication just created not found: " + str(newAuthenticationRepresentation)
                module.fail_json(**result)
            # Configure the executions for the flow
            kc.create_or_update_executions(config=newAuthenticationRepresentation, realm=realm)
            changed = True
            # Get executions created
            executionsRepresentation = kc.get_executions_representation(config=newAuthenticationRepresentation, realm=realm)
            if executionsRepresentation is not None:
                authenticationRepresentation["authenticationExecutions"] = executionsRepresentation
            result['changed'] = changed
            result['flow'] = authenticationRepresentation
        elif state == 'absent':  # If desired state is absent.
            result['msg'] = newAuthenticationRepresentation["alias"] + ' absent'
    else:  # The authentication flow already exist
        if (state == 'present'):  # if desired state is present
            if force:  # If force option is true
                # Delete the actual authentication flow
                kc.delete_authentication_flow_by_id(id=authenticationRepresentation["id"], realm=realm)
                changed = True
                # If copyFrom is defined, create authentication flow from a copy
                if "copyFrom" in newAuthenticationRepresentation and newAuthenticationRepresentation["copyFrom"] is not None:
                    authenticationRepresentation = kc.copy_auth_flow(config=newAuthenticationRepresentation, realm=realm)
                else:  # Create an empty authentication flow
                    authenticationRepresentation = kc.create_empty_auth_flow(config=newAuthenticationRepresentation, realm=realm)
                # If the authentication still not exist on the server, raise an exception.
                if authenticationRepresentation is None:
                    result['msg'] = "Authentication just created not found: " + str(newAuthenticationRepresentation)
                    result['changed'] = changed
                    module.fail_json(**result)
            # Configure the executions for the flow
            if kc.create_or_update_executions(config=newAuthenticationRepresentation, realm=realm):
                changed = True
            # Get executions created
            executionsRepresentation = kc.get_executions_representation(config=newAuthenticationRepresentation, realm=realm)
            if executionsRepresentation is not None:
                authenticationRepresentation["authenticationExecutions"] = executionsRepresentation
            result['flow'] = authenticationRepresentation
            result['changed'] = changed
        elif state == 'absent':  # If desired state is absent
            # Delete the authentication flow alias.
            kc.delete_authentication_flow_by_id(id=authenticationRepresentation["id"], realm=realm)
            changed = True
            result['msg'] = 'Authentication flow: ' + newAuthenticationRepresentation['alias'] + ' id: ' + authenticationRepresentation["id"] + ' is deleted'
            result['changed'] = changed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
