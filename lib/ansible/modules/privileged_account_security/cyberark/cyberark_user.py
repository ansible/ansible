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
module: cyberark_user
short_description: "Module for CyberArk User Management using Privileged Account
                    Security Web Services SDK"
author: "Edward Nunez (@enunez-cyberark)"
version_added: "2.3"
description:
    - "CyberArk User Management using PAS Web Services SDK.
       It currently supports the following actions: Get User Details, Add User,
       Update User, Delete User.
       It requires C(cyberarkSession) parameter to be passed as a current
       session established by logon/logoff using cyberark_authentication.module"


options:
    userName:
        required: True
        description:
            - The name of the user who will be queried (for details), added, updated or deleted.
    state:
        default: details
        choices: ['details', 'present', 'update', 'absent']
        description:
            - Specifies the state (defining the action to follow) needed for the user.
              'details' for query user details, 'present' for create user,
              'update' for update user (even the password), 'delete' for delete user.
    cyberarkSession:
        required: True
        description:
            - Dictionary set by a CyberArk authentication containing the different values to perform actions on a logged-on CyberArk session
    initialPassword:
        required: False
        description:
            - The password that the new user will use to log on the first time. This password must meet the password policy requirements.
              this parameter is required when state is 'present' (Add User)
    newPassword:
        required: False
        description:
            - The user's updated password. Make sure that this password meets the password policy requirements.
    email:
        required: False
        description:
            - The user's email address.
    firstName:
        required: False
        description:
            - The user's first name.
    lastName:
        required: False
        description:
            - The user's last name.
    changePasswordOnTheNextLogon:
        required: False
        default: false
        description:
            - Whether or not the user must change their password in their next logon.
              Valid values = true/false.
    expiryDate:
        required: False
        description:
            - The date and time when the user's account will expire and become disabled.
    userTypeName:
        required: False
        default: EPVUser
        description:
            - The type of user.
    disabled:
        required: False
        default: false
        description:
            - Whether or not the user will be disabled. Valid values = true/false.
    location:
        required: False
        description:
            - The Vault Location for the user.
'''

EXAMPLES = '''
- name: Logon to CyberArk Vault using PAS Web Services SDK
  cyberark_authentication:
    apiBaseUrl: "https://components.cyberark.local"
    useSharedLogonAuthentication: true

- name: Get Users Details
  cyberark_user:
    userName: "Username"
    state: details
    cyberarkSession: "{{ cyberarkSession }}"

- name: Create user
  cyberark_user:
    userName: "Username"
    initialPassword: "password"
    userTypeName: "EPVUser"
    changePasswordOnTheNextLogon: false
    state: present
    cyberarkSession: "{{ cyberarkSession }}"

  - name: Reset user credential
    cyberark_user:
      userName: "Username"
      newPassword: "password"
      disabled: false
      state: update
      cyberarkSession: "{{ cyberarkSession }}"

- name: Logoff from CyberArk Vault
  cyberark_authentication:
    state: absent
    cyberarkSession: "{{ cyberarkSession }}"
'''

RETURN = '''
cyberarkUser:
    description: Dictionary containing result property.
    returned: success
    type: dictionary
    contains:
        result:
            description: properties of the result user (either added/updated).
            type: dictionary
            sample: {
                        "AgentUser": false,
                        "Disabled": false,
                        "Email": "",
                        "Expired": false,
                        "ExpiryDate": null,
                        "FirstName": "",
                        "LastName": "",
                        "Location": "Applications",
                        "Source": "Internal",
                        "Suspended": false,
                        "UserName": "Prov_centos01",
                        "UserTypeName": "AppProvider"
                    }
status_code:
    description: Result HTTP Status code
    returned: success
    type: int
    sample: 200
'''

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
import sys


def userDetails(userModule):

    username = userModule.params["userName"]
    cyberarkSession = userModule.params["cyberarkSession"]

    apiBaseUrl = cyberarkSession["apiBaseUrl"]
    validateCerts = cyberarkSession["validateCerts"]
    useSharedLogonAuthentication = cyberarkSession[
        "useSharedLogonAuthentication"]

    if userModule.check_mode:
        userModule.exit_json(change=False)

    result = {}
    endPoint = "/PasswordVault/WebServices/PIMServices.svc/Users/{0}".format(
        username)
    changed = False

    headers = {'Content-Type': 'application/json'}
    headers["Authorization"] = cyberarkSession["token"]

    try:

        response = open_url(
            apiBaseUrl + endPoint,
            method="GET",
            headers=headers,
            validate_certs=validateCerts)
        result = {"result": json.loads(response.read())}

        return (changed, result, response.getcode())

    except Exception:
        t, e = sys.exc_info()[:2]
        userModule.fail_json(
            msg=str(e),
            exception=traceback.format_exc(),
            status_code=e.code)


def userAddOrUpdate(userModule, HTTPMethod):

    username = userModule.params["userName"]
    cyberarkSession = userModule.params["cyberarkSession"]

    apiBaseUrl = cyberarkSession["apiBaseUrl"]
    validateCerts = cyberarkSession["validateCerts"]
    useSharedLogonAuthentication = cyberarkSession[
        "useSharedLogonAuthentication"]

    if userModule.check_mode:
        userModule.exit_json(change=False)

    result = {}
    payload = {}

    if HTTPMethod == "POST":
        endPoint = "/PasswordVault/WebServices/PIMServices.svc/Users"
        payload["UserName"] = username
    elif HTTPMethod == "PUT":
        endPoint = "/PasswordVault/WebServices/PIMServices.svc/Users/{0}"
        endPoint = endPoint.format(username)

    changed = False

    headers = {'Content-Type': 'application/json',
               "Authorization": cyberarkSession["token"]}

    if "initialPassword" in userModule.params:
        payload["InitialPassword"] = userModule.params["initialPassword"]

    if "newPassword" in userModule.params:
        payload["NewPassword"] = userModule.params["newPassword"]

    if "email" in userModule.params:
        payload["Email"] = userModule.params["email"]

    if "firstName" in userModule.params:
        payload["FirstName"] = userModule.params["firstName"]

    if "lastName" in userModule.params:
        payload["LastName"] = userModule.params["lastName"]

    if "changePasswordOnTheNextLogon" in userModule.params:
        if userModule.params["changePasswordOnTheNextLogon"]:
            payload["ChangePasswordOnTheNextLogon"] = "true"
        else:
            payload["ChangePasswordOnTheNextLogon"] = "false"

    if "expiryDate" in userModule.params:
        payload["ExpiryDate"] = userModule.params["expiryDate"]

    if "userTypeName" in userModule.params:
        payload["UserTypeName"] = userModule.params["userTypeName"]

    if "disabled" in userModule.params:
        if userModule.params["disabled"]:
            payload["Disabled"] = "true"
        else:
            payload["Disabled"] = "false"

    if "location" in userModule.params:
        payload["Location"] = userModule.params["location"]

    try:

        response = open_url(
            apiBaseUrl + endPoint,
            method=HTTPMethod,
            headers=headers,
            data=json.dumps(payload),
            validate_certs=validateCerts)
        result = {"result": json.loads(response.read())}

        return (changed, result, response.getcode())

    except Exception:
        t, e = sys.exc_info()[:2]
        userModule.fail_json(
            msg=str(e),
            exception=traceback.format_exc(),
            status_code=e.code)


def userDelete(userModule):

    username = userModule.params["userName"]
    cyberarkSession = userModule.params["cyberarkSession"]

    apiBaseUrl = cyberarkSession["apiBaseUrl"]
    validateCerts = cyberarkSession["validateCerts"]
    useSharedLogonAuthentication = cyberarkSession[
        "useSharedLogonAuthentication"]

    if userModule.check_mode:
        userModule.exit_json(change=False)

    result = {}
    endPoint = "/PasswordVault/WebServices/PIMServices.svc/Users/{0}".format(
        username)
    changed = False

    headers = {'Content-Type': 'application/json'}
    headers["Authorization"] = cyberarkSession["token"]

    try:

        response = open_url(
            apiBaseUrl + endPoint,
            method="DELETE",
            headers=headers,
            validate_certs=validateCerts)
        result = {"result": {}}

        return (changed, result, response.getcode())

    except Exception:
        t, e = sys.exc_info()[:2]
        userModule.fail_json(
            msg=str(e),
            exception=traceback.format_exc(),
            status_code=e.code)


def main():

    fields = {
        "userName": {"required": True, "type": "str"},
        "state": {"required": False, "type": "str",
                  "choices": ["details", "present", "update", "absent"],
                  "default": "details"},
        "cyberarkSession": {"required": True, "type": "dict"},
        "initialPassword": {"required": False, "type": "str"},
        "newPassword": {"required": False, "type": "str"},
        "email": {"required": False, "type": "str"},
        "firstName": {"required": False, "type": "str"},
        "lastName": {"required": False, "type": "str"},
        "changePasswordOnTheNextLogon": {"required": False, "type": "bool"},
        "expiryDate": {"required": False, "type": "str"},
        "userTypeName": {"required": False, "type": "str"},
        "disabled": {"required": False, "type": "bool"},
        "location": {"required": False, "type": "str"},
    }

    required_if = [
        ("state", "present", ["initialPassword"]),
    ]

    module = AnsibleModule(argument_spec=fields, required_if=required_if)

    state = module.params["state"]

    changed = False
    result = {}

    if (state == "details"):
        (changed, result, status_code) = userDetails(module)
    elif (state == "present"):
        (changed, result, status_code) = userAddOrUpdate(module, "POST")
    elif (state == "update"):
        (changed, result, status_code) = userAddOrUpdate(module, "PUT")
    elif (state == "absent"):
        (changed, result, status_code) = userDelete(module)

    module.exit_json(
        changed=changed,
        cyberarkUser=result,
        status_code=status_code)


if __name__ == '__main__':
    main()
