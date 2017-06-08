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
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: cyberark_authentication
short_description: "Module for CyberArk Vault Authentication using Privileged Account Security Web Services SDK"
author: "Edward Nunez (@enunez-cyberark)"
version_added: "2.4"
description:
    - "Authenticates to CyberArk Vault using Privileged Account Security Web Services SDK and
       creates a session fact that can be used by other modules. It returns an Ansible fact
       called I(cyberark_session). Every module can use this fact as C(cyberark_session) parameter."


options:
    state:
        default: present
        choices: ['present', 'absent']
        description:
            - Specifies if an authentication logon/logoff and a cyberark_session should be added/removed.
    username:
        description:
            - The name of the user who will logon to the Vault.
    password:
        description:
            - The password of the user.
    new_password:
        description:
            - The new password of the user. This parameter is optional, and enables you to change a password.
    api_base_url:
        description:
            - A string containing the base URL of the server hosting CyberArk's Privileged Account Security Web Services SDK.
    validate_certs:
        default: true
        description:
            - If C(false), SSL certificates will not be validated.  This should only
              set to C(false) used on personally controlled sites using self-signed
              certificates.
    use_shared_logon_authentication:
        default: false
        description:
            - Whether or not Shared Logon Authentication will be used.
    use_radius_authentication:
        default: false
        description:
            - Whether or not users will be authenticated via a RADIUS server. Valid values are true/false.
    cyberark_session:
        description:
            - Dictionary set by a CyberArk authentication containing the different values to perform actions on a logged-on CyberArk session.
'''

EXAMPLES = '''
- name: Logon to CyberArk Vault using PAS Web Services SDK - use_shared_logon_authentication
  cyberark_authentication:
    api_base_url: "{{ web_services_base_url }}"
    use_shared_logon_authentication: true

- name: Logon to CyberArk Vault using PAS Web Services SDK - Not use_shared_logon_authentication
  cyberark_authentication:
    api_base_url: "{{ web_services_base_url }}"
    username: "{{ password_object.password }}"
    password: "{{ password_object.passprops.username }}"
    use_shared_logon_authentication: false

- name: Logoff from CyberArk Vault
  cyberark_authentication:
    state: absent
    cyberark_session: "{{ cyberark_session }}"
'''

RETURN = '''
cyberark_session:
    description: Authentication facts.
    returned: success
    type: dictionary
    contains:
        token:
            description: Session Token returned by the logon operation.
            returned: success
            type: string
            sample: "AAEAAAD/////AQAAAAA......NiNWMtNDhhNy00ZDc5LWE2MTQtMmRlMTBjMWI1ZWQ2BgYAAAABNAs="
        api_base_url:
            description: A string containing the base URL of the server hosting CyberArk's Privileged Account Security Web Services SDK.
            returned: success
            type: string
            sample: "https://<IIS_Server_PVWA>"
        validate_certs:
            description: Whether SSL certificates will be validated.
            returned: success
            type: bool
            sample: true
        use_shared_logon_authentication:
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

    # Getting parameters from module

    api_base_url = module.params["api_base_url"]
    validate_certs = module.params["validate_certs"]
    username = module.params["username"]
    password = module.params["password"]
    new_password = module.params["new_password"]
    use_shared_logon_authentication = module.params[
        "use_shared_logon_authentication"]
    use_radius_authentication = module.params["use_radius_authentication"]
    state = module.params["state"]
    cyberark_session = module.params["cyberark_session"]

    # if in check mode it will not perform password changes
    if module.check_mode and new_password is not None:
        new_password = None

    # Defining initial values for open_url call
    headers = {'Content-Type': 'application/json'}
    payload = ""

    if state == "present":  # Logon Action

        # Different end_points based on the use of shared logon authentication
        if use_shared_logon_authentication:

            end_point = "/PasswordVault/WebServices/auth/Shared/RestfulAuthenticationService.svc/Logon"

        else:

            end_point = "/PasswordVault/WebServices/auth/Cyberark/CyberArkAuthenticationService.svc/Logon"

            # The payload will contain username, password
            # and optionally use_radius_authentication and new_password
            payload_dict = {"username": username, "password": password}

            if use_radius_authentication:
                payload_dict["useRadiusAuthentication"] = use_radius_authentication

            if new_password is not None:
                payload_dict["newPassword"] = new_password

            payload = json.dumps(payload_dict)

    else:  # Logoff Action

        # Get values from cyberark_session already established
        api_base_url = cyberark_session["api_base_url"]
        validate_certs = cyberark_session["validate_certs"]
        use_shared_logon_authentication = cyberark_session[
            "use_shared_logon_authentication"]
        headers["Authorization"] = cyberark_session["token"]

        # Different end_points based on the use of shared logon authentication
        if use_shared_logon_authentication:
            end_point = "/PasswordVault/WebServices/auth/Shared/RestfulAuthenticationService.svc/Logoff"
        else:
            end_point = "/PasswordVault/WebServices/auth/Cyberark/CyberArkAuthenticationService.svc/Logoff"

    result = None
    changed = False
    response = None

    try:

        response = open_url(
            api_base_url + end_point,
            method="POST",
            headers=headers,
            data=payload,
            validate_certs=validate_certs)

    except httplib.HTTPException as e:

        module.fail_json(
            msg="end_point=" +
            api_base_url +
            end_point,
            payload=payload,
            headers=headers,
            exception=to_text(e),
            status_code=e.code)

    except Exception as e:

        module.fail_json(
            msg="end_point=" +
            api_base_url +
            end_point,
            payload=payload,
            headers=headers,
            exception=to_text(e),
            status_code=-1)

    if response.getcode() == 200:  # Success

        if state == "present":  # Logon Action

            # Result token from REST Api uses a different key based
            # the use of shared logon authentication
            if use_shared_logon_authentication:
                token = json.loads(response.read())["LogonResult"]
            else:
                token = json.loads(response.read())["CyberArkLogonResult"]

            # Preparing result of the module
            result = {
                "cyberark_session": {
                    "token": token,
                    "api_base_url": api_base_url,
                    "validate_certs": validate_certs,
                    "use_shared_logon_authentication":
                    use_shared_logon_authentication},
            }

            if new_password is not None:
                # Only marks change if new_password was received resulting
                # in a password change
                changed = True

        else:  # Logoff Action clears cyberark_session

            result = {
                "cyberark_session": {}
            }

        return (changed, result, response.getcode())

    else:
        module.fail_json(
            msg="error in end_point=>" +
            end_point,
            headers=headers)


def main():

    fields = {
        "api_base_url": {"type": "str"},
        "validate_certs": {"type": "bool",
                           "default": "true"},
        "username": {"type": "str"},
        "password": {"type": "str", "no_log": True},
        "new_password": {"type": "str", "no_log": True},
        "use_shared_logon_authentication": {"default": False, "type": "bool"},
        "use_radius_authentication": {"default": False, "type": "bool"},
        "state": {"type": "str",
                  "choices": ["present", "absent"],
                  "default": "present"},
        "cyberark_session": {"type": "dict"},
    }

    mutually_exclusive = [
        ["use_shared_logon_authentication", "use_radius_authentication"],
        ["use_shared_logon_authentication", "new_password"],
        ["api_base_url", "cyberark_session"],
        ["cyberark_session", "username", "use_shared_logon_authentication"]
    ]

    required_if = [
        ("state", "present", ["api_base_url"]),
        ("state", "absent", ["cyberark_session"])
    ]

    required_together = [
        ["username", "password"]
    ]

    module = AnsibleModule(
        argument_spec=fields,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
        required_together=required_together,
        supports_check_mode=True)

    (changed, result, status_code) = processAuthentication(module)

    module.exit_json(
        changed=changed,
        ansible_facts=result,
        status_code=status_code)


if __name__ == '__main__':
    main()
