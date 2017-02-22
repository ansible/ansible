#!/usr/bin/python
#
# This file is part of Ansible
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
#


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: cyberark_authentication
short_description: "Module for CyberArk Vault Authentication using Privileged Account Security Web Services SDK"
author: "Edward Nunez (@enunez-cyberark)"
version_added: "2.3"
description:
    - "Authenticates to CyberArk Vault using Privileged Account Security Web Services SDK and
       creates a session fact that can be used by other modules. It returns an Ansible fact
       called I(cyberarkSession). Every module can use this fact as C(cyberarkSession) parameter."


options:
    state:
        default: present
        choices: ['present', 'absent']
        description:
            - Specifies if an authentication logon/logoff and a cyberarkSession should be added/removed
    userName:
        description:
            - The name of the user who will logon to the Vault
    password:
        description:
            - The password of the user
    newPassword:
        description:
            - The new password of the user. This parameter is optional, and enables you to change a password
    apiBaseUrl:
        description:
            - A string containing the base URL of the server hosting CyberArk's Privileged Account Security Web Services SDK
    validate_certs:
        default: true
        description:
            - If C(false), SSL certificates will not be validated.  This should only
              set to C(false) used on personally controlled sites using self-signed
              certificates.
    useSharedLogonAuthentication:
        default: false
        description:
            - Whether or not Shared Logon Authentication will be used.
    useRadiusAuthentication:
        default: false
        description:
            - Whether or not users will be authenticated via a RADIUS server. Valid values are true/false
    cyberarkSession:
        description:
            - Dictionary set by a CyberArk authentication containing the different values to perform actions on a logged-on CyberArk session
'''

EXAMPLES = '''
- name: Logon to CyberArk Vault using PAS Web Services SDK - UseSharedLogonAuthentication
  cyberark_authentication:
    apiBaseUrl: "{{ WebServicesBaseURL }}"
    useSharedLogonAuthentication: true

- name: Logon to CyberArk Vault using PAS Web Services SDK - Not UseSharedLogonAuthentication
  cyberark_authentication:
    apiBaseUrl: "{{ WebServicesBaseURL }}"
    username: "{{ PasswordObject.password }}"
    password: "{{ PasswordObject.passprops.username }}"
    useSharedLogonAuthentication: false

- name: Logoff from CyberArk Vault
  cyberark_authentication:
    state: absent
    cyberarkSession: "{{ cyberarkSession }}"
'''

RETURN = '''
cyberarkSession:
    description: Authentication facts.
    returned: success
    type: dictionary
    contains:
        token:
            description: Session Token returned by the logon operation
            returned: success
            type: string
            sample: "AAEAAAD/////AQAAAAA......NiNWMtNDhhNy00ZDc5LWE2MTQtMmRlMTBjMWI1ZWQ2BgYAAAABNAs="
        apiBaseUrl:
            description: A string containing the base URL of the server hosting CyberArk's Privileged Account Security Web Services SDK.
            returned: success
            type: string
            sample: "https://<IIS_Server_PVWA>"
        validate_certs:
            description: Whether SSL certificates will be validated.
            returned: success
            type: bool
            sample: true
        useSharedLogonAuthentication:
            description: Whether or not Shared Logon Authentication will be used.
            returned: success
            type: bool
            sample: true
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
import urllib
import httplib
import traceback
import sys
import json


def processAuthentication(module):

    apiBaseUrl = module.params["apiBaseUrl"]
    validate_certs = module.params["validate_certs"]
    username = module.params["username"]
    password = module.params["password"]
    newPassword = module.params["newPassword"]
    useSharedLogonAuthentication = module.params[
        "useSharedLogonAuthentication"]
    useRadiusAuthentication = module.params["useRadiusAuthentication"]
    state = module.params["state"]
    cyberarkSession = module.params["cyberarkSession"]

    headers = {'Content-Type': 'application/json'}
    payload = ""

    if state == "present":

        if (not useSharedLogonAuthentication and (
                username is None or password is None)):
            module.fail_json(
                msg="with state=%s and useSharedLogonAuthentication=%s, " +
                "both username and password are required" %
                (state, useSharedLogonAuthentication))

        if cyberarkSession is not None:
            module.fail_json(
                msg="with state=%s you cannot specify cyberarkSession" %
                (state))

        if apiBaseUrl is None:
            module.fail_json(
                msg="with state=%s apiBaseUrl is required" % (state))

        if useSharedLogonAuthentication:
            endPoint = "/PasswordVault/WebServices/auth/Shared/RestfulAuthenticationService.svc/Logon"
        else:
            endPoint = "/PasswordVault/WebServices/auth/Cyberark/CyberArkAuthenticationService.svc/Logon"
            payload = json.dumps({"username": module.params.get(
                "username"), "password": module.params.get("password")})

    else:

        if cyberarkSession is None:
            module.fail_json(
                msg="with state=%s cyberarkSession is required" %
                (state))

        if apiBaseUrl is None:
            apiBaseUrl = cyberarkSession["apiBaseUrl"]
            validate_certs = cyberarkSession["validate_certs"]
            useSharedLogonAuthentication = cyberarkSession[
                "useSharedLogonAuthentication"]
            headers["Authorization"] = cyberarkSession["token"]

        if useSharedLogonAuthentication:
            endPoint = "/PasswordVault/WebServices/auth/Shared/RestfulAuthenticationService.svc/Logoff"
        else:
            endPoint = "/PasswordVault/WebServices/auth/Cyberark/CyberArkAuthenticationService.svc/Logoff"

    try:

        response = open_url(
            apiBaseUrl + endPoint,
            method="POST",
            headers=headers,
            data=payload,
            validate_certs=validate_certs)

        result = None
        changed = False

        if response.getcode() == 200:

            if state == "present":

                if useSharedLogonAuthentication:
                    token = json.loads(response.read())["LogonResult"]
                else:
                    token = json.loads(response.read())["CyberArkLogonResult"]

                result = {
                    "cyberarkSession": {
                        "token": token,
                        "apiBaseUrl": apiBaseUrl,
                        "validate_certs": validate_certs,
                        "useSharedLogonAuthentication":
                        useSharedLogonAuthentication},
                }

                if newPassword is not None:
                    changed = True

            else:
                result = {
                    "cyberarkSession": {}
                }

            return (changed, result, response.getcode())
        else:
            module.fail_json(
                msg="error in endpoint=>" +
                endPoint +
                json.dumps(headers))

    except httplib.HTTPException:
        t, e = sys.exc_info()[:2]
        module.fail_json(
            msg="EndPoint=" +
            apiBaseUrl +
            endPoint +
            " headers=[" +
            json.dumps(headers) +
            "] ===>" +
            str(e),
            exception=traceback.format_exc(),
            status_code=e.code)
    except Exception:
        t, e = sys.exc_info()[:2]
        module.fail_json(
            msg="EndPoint=" +
            apiBaseUrl +
            endPoint +
            " headers=[" +
            json.dumps(headers) +
            "] ===>" +
            str(e),
            exception=traceback.format_exc(),
            status_code=-1)


def main():

    fields = {
        "apiBaseUrl": {"required": False, "type": "str"},
        "validate_certs": {"required": False, "type": "bool",
                          "default": "true"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "newPassword": {"required": False, "type": "str", "no_log": True},
        "useSharedLogonAuthentication": {"default": False, "type": "bool"},
        "useRadiusAuthentication": {"default": False, "type": "bool"},
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"],
                  "default": "present"},
        "cyberarkSession": {"required": False, "type": "dict"},
    }

    required_if = [
        ("state", "present", ["apiBaseUrl"]),
        ("state", "absent", ["cyberarkSession"])
    ]

    required_together = [
        ["username", "password"]
    ]

    module = AnsibleModule(
        argument_spec=fields,
        required_if=required_if,
        required_together=required_together,
        supports_check_mode=True)

    if module.check_mode:
        module.exit_json(change=False)

    (changed, result, status_code) = processAuthentication(module)

    module.exit_json(
        changed=changed,
        ansible_facts=result,
        status_code=status_code)


if __name__ == '__main__':
    main()
