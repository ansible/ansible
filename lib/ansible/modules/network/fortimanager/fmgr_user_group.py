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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_user_group
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Create/Edit/Delete FGT user groups
description:
  - Create, edit, and delete user groups on a FortiGate via FortiManager

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  host:
    description:
      - The FortiManager's Address.
    required: true

  username:
    description:
      - The username associated with the account.
    required: true

  passwd:
    description:
      - The password associated with the username account.
    required: true

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  user_name:
    description:
      - Enable/disable the guest user name entry.
      - choice | disable | Enable setting.
      - choice | enable | Disable setting.
    required: false
    choices: ["disable", "enable"]

  user_id:
    description:
      - Guest user ID type.
      - choice | email | Email address.
      - choice | auto-generate | Automatically generate.
      - choice | specify | Specify.
    required: false
    choices: ["email", "auto-generate", "specify"]

  sso_attribute_value:
    description:
      - Name of the RADIUS user group that this local user group represents.
    required: false

  sponsor:
    description:
      - Set the action for the sponsor guest user field.
      - choice | optional | Optional.
      - choice | mandatory | Mandatory.
      - choice | disabled | Disabled.
    required: false
    choices: ["optional", "mandatory", "disabled"]

  sms_server:
    description:
      - Send SMS through FortiGuard or other external server.
      - choice | fortiguard | Send SMS by FortiGuard.
      - choice | custom | Send SMS by custom server.
    required: false
    choices: ["fortiguard", "custom"]

  sms_custom_server:
    description:
      - SMS server.
    required: false

  password:
    description:
      - Guest user password type.
      - choice | auto-generate | Automatically generate.
      - choice | specify | Specify.
      - choice | disable | Disable.
    required: false
    choices: ["auto-generate", "specify", "disable"]

  name:
    description:
      - Group name.
    required: false

  multiple_guest_add:
    description:
      - Enable/disable addition of multiple guests.
      - choice | disable | Enable setting.
      - choice | enable | Disable setting.
    required: false
    choices: ["disable", "enable"]

  mobile_phone:
    description:
      - Enable/disable the guest user mobile phone number field.
      - choice | disable | Enable setting.
      - choice | enable | Disable setting.
    required: false
    choices: ["disable", "enable"]

  member:
    description:
      - Names of users, peers, LDAP severs, or RADIUS servers to add to the user group.
    required: false

  max_accounts:
    description:
      - Maximum number of guest accounts that can be created for this group (0 means unlimited).
    required: false

  http_digest_realm:
    description:
      - Realm attribute for MD5-digest authentication.
    required: false

  group_type:
    description:
      - Set the group to be for firewall authentication, FSSO, RSSO, or guest users.
      - choice | firewall | Firewall.
      - choice | fsso-service | Fortinet Single Sign-On Service.
      - choice | guest | Guest.
      - choice | rsso | RADIUS based Single Sign-On Service.
    required: false
    choices: ["firewall", "fsso-service", "guest", "rsso"]

  expire_type:
    description:
      - Determine when the expiration countdown begins.
      - choice | immediately | Immediately.
      - choice | first-successful-login | First successful login.
    required: false
    choices: ["immediately", "first-successful-login"]

  expire:
    description:
      - Time in seconds before guest user accounts expire. (1 - 31536000 sec)
    required: false

  email:
    description:
      - Enable/disable the guest user email address field.
      - choice | disable | Enable setting.
      - choice | enable | Disable setting.
    required: false
    choices: ["disable", "enable"]

  company:
    description:
      - Set the action for the company guest user field.
      - choice | optional | Optional.
      - choice | mandatory | Mandatory.
      - choice | disabled | Disabled.
    required: false
    choices: ["optional", "mandatory", "disabled"]

  authtimeout:
    description:
      - Authentication timeout in minutes for this user group. 0 to use the global user setting auth-timeout.
    required: false

  auth_concurrent_value:
    description:
      - Maximum number of concurrent authenticated connections per user (0 - 100).
    required: false

  auth_concurrent_override:
    description:
      - Enable/disable overriding the global number of concurrent authentication sessions for this user group.
      - choice | disable | Disable auth-concurrent-override.
      - choice | enable | Enable auth-concurrent-override.
    required: false
    choices: ["disable", "enable"]

  guest:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  guest_comment:
    description:
      - Comment.
    required: false

  guest_company:
    description:
      - Set the action for the company guest user field.
    required: false

  guest_email:
    description:
      - Email.
    required: false

  guest_expiration:
    description:
      - Expire time.
    required: false

  guest_mobile_phone:
    description:
      - Mobile phone.
    required: false

  guest_name:
    description:
      - Guest name.
    required: false

  guest_password:
    description:
      - Guest password.
    required: false

  guest_sponsor:
    description:
      - Set the action for the sponsor guest user field.
    required: false

  guest_user_id:
    description:
      - Guest ID.
    required: false

  match:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  match_group_name:
    description:
      - Name of matching group on remote auththentication server.
    required: false

  match_server_name:
    description:
      - Name of remote auth server.
    required: false


'''

EXAMPLES = '''
- name: EDIT FMGR_USER_GROUP
  fmgr_user_group:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    passwd: "{{ passwd }}"
    mode:
    adom:
    user_name:
    user_id:
    sso_attribute_value:
    sponsor:
    sms_server:
    sms_custom_server:
    password:
    name:
    multiple_guest_add:
    mobile_phone:
    member:
    max_accounts:
    http_digest_realm:
    group_type:
    expire_type:
    expire:
    email:
    company:
    authtimeout:
    auth_concurrent_value:
    auth_concurrent_override:
    guest_comment:
    guest_company:
    guest_email:
    guest_expiration:
    guest_mobile_phone:
    guest_name:
    guest_password:
    guest_sponsor:
    guest_user_id:
    match_group_name:
    match_server_name:
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False

###############
# START METHODS
###############


def fmgr_user_group_addsetdelete(fmg, paramgram):

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/user/group'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/user/group/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if mode == "set":
        response = fmg.set(url, datagram)
    # IF MODE = UPDATE -- USER THE 'UPDATE' API CALL MODE
    elif mode == "update":
        response = fmg.update(url, datagram)
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    elif mode == "add":
        response = fmg.add(url, datagram)
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    elif mode == "delete":
        response = fmg.delete(url, datagram)

    return response


# ADDITIONAL COMMON FUNCTIONS
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """
    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

        if results[0] not in good_codes:
            if logout_on_fail:
                fmg.logout()
                module.fail_json(msg=msg, **results[1])
        else:
            if logout_on_success:
                fmg.logout()
                module.exit_json(msg="API Called worked, but logout handler has been asked to logout on success",
                                 **results[1])
    return msg


# FUNCTION/METHOD FOR CONVERTING CIDR TO A NETMASK
# DID NOT USE IP ADDRESS MODULE TO KEEP INCLUDES TO A MINIMUM
def fmgr_cidr_to_netmask(cidr):
    cidr = int(cidr)
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    return(str((0xff000000 & mask) >> 24) + '.' +
           str((0x00ff0000 & mask) >> 16) + '.' +
           str((0x0000ff00 & mask) >> 8) + '.' +
           str((0x000000ff & mask)))


# utility function: removing keys wih value of None, nothing in playbook for that key
def fmgr_del_none(obj):
    if isinstance(obj, dict):
        return type(obj)((fmgr_del_none(k), fmgr_del_none(v))
                         for k, v in obj.items() if k is not None and (v is not None and not fmgr_is_empty_dict(v)))
    else:
        return obj


# utility function: remove keys that are need for the logic but the FMG API won't accept them
def fmgr_prepare_dict(obj):
    list_of_elems = ["mode", "adom", "host", "username", "passwd"]
    if isinstance(obj, dict):
        obj = dict((key, fmgr_prepare_dict(value)) for (key, value) in obj.items() if key not in list_of_elems)
    return obj


def fmgr_is_empty_dict(obj):
    return_val = False
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, dict):
                    if len(v) == 0:
                        return_val = True
                    elif len(v) > 0:
                        for k1, v1 in v.items():
                            if v1 is None:
                                return_val = True
                            elif v1 is not None:
                                return_val = False
                                return return_val
                elif v is None:
                    return_val = True
                elif v is not None:
                    return_val = False
                    return return_val
        elif len(obj) == 0:
            return_val = True

    return return_val


def fmgr_split_comma_strings_into_lists(obj):
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, str):
                    new_list = list()
                    if "," in v:
                        new_items = v.split(",")
                        for item in new_items:
                            new_list.append(item.strip())
                        obj[k] = new_list

    return obj


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        host=dict(required=True, type="str"),
        passwd=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        user_name=dict(required=False, type="str", choices=["disable", "enable"]),
        user_id=dict(required=False, type="str", choices=["email", "auto-generate", "specify"]),
        sso_attribute_value=dict(required=False, type="str"),
        sponsor=dict(required=False, type="str", choices=["optional", "mandatory", "disabled"]),
        sms_server=dict(required=False, type="str", choices=["fortiguard", "custom"]),
        sms_custom_server=dict(required=False, type="str"),
        password=dict(required=False, type="str", choices=["auto-generate", "specify", "disable"]),
        name=dict(required=False, type="str"),
        multiple_guest_add=dict(required=False, type="str", choices=["disable", "enable"]),
        mobile_phone=dict(required=False, type="str", choices=["disable", "enable"]),
        member=dict(required=False, type="str"),
        max_accounts=dict(required=False, type="int"),
        http_digest_realm=dict(required=False, type="str"),
        group_type=dict(required=False, type="str", choices=["firewall", "fsso-service", "guest", "rsso"]),
        expire_type=dict(required=False, type="str", choices=["immediately", "first-successful-login"]),
        expire=dict(required=False, type="int"),
        email=dict(required=False, type="str", choices=["disable", "enable"]),
        company=dict(required=False, type="str", choices=["optional", "mandatory", "disabled"]),
        authtimeout=dict(required=False, type="int"),
        auth_concurrent_value=dict(required=False, type="int"),
        auth_concurrent_override=dict(required=False, type="str", choices=["disable", "enable"]),
        guest=dict(required=False, type="list"),
        guest_comment=dict(required=False, type="str"),
        guest_company=dict(required=False, type="str"),
        guest_email=dict(required=False, type="str"),
        guest_expiration=dict(required=False, type="str"),
        guest_mobile_phone=dict(required=False, type="str"),
        guest_name=dict(required=False, type="str"),
        guest_password=dict(required=False, type="str", no_log=True),
        guest_sponsor=dict(required=False, type="str"),
        guest_user_id=dict(required=False, type="str"),
        match=dict(required=False, type="list"),
        match_group_name=dict(required=False, type="str"),
        match_server_name=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "user-name": module.params["user_name"],
        "user-id": module.params["user_id"],
        "sso-attribute-value": module.params["sso_attribute_value"],
        "sponsor": module.params["sponsor"],
        "sms-server": module.params["sms_server"],
        "sms-custom-server": module.params["sms_custom_server"],
        "password": module.params["password"],
        "name": module.params["name"],
        "multiple-guest-add": module.params["multiple_guest_add"],
        "mobile-phone": module.params["mobile_phone"],
        "member": module.params["member"],
        "max-accounts": module.params["max_accounts"],
        "http-digest-realm": module.params["http_digest_realm"],
        "group-type": module.params["group_type"],
        "expire-type": module.params["expire_type"],
        "expire": module.params["expire"],
        "email": module.params["email"],
        "company": module.params["company"],
        "authtimeout": module.params["authtimeout"],
        "auth-concurrent-value": module.params["auth_concurrent_value"],
        "auth-concurrent-override": module.params["auth_concurrent_override"],
        "guest": {
            "comment": module.params["guest_comment"],
            "company": module.params["guest_company"],
            "email": module.params["guest_email"],
            "expiration": module.params["guest_expiration"],
            "mobile-phone": module.params["guest_mobile_phone"],
            "name": module.params["guest_name"],
            "password": module.params["guest_password"],
            "sponsor": module.params["guest_sponsor"],
            "user-id": module.params["guest_user_id"],
        },
        "match": {
            "group-name": module.params["match_group_name"],
            "server-name": module.params["match_server_name"],
        }
    }

    list_overrides = ['guest', 'match']
    for list_variable in list_overrides:
        override_data = list()
        try:
            override_data = module.params[list_variable]
        except:
            pass
        try:
            if override_data:
                del paramgram[list_variable]
                paramgram[list_variable] = override_data
        except:
            pass

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    password = module.params["passwd"]
    username = module.params["username"]
    if host is None or username is None or password is None:
        module.fail_json(msg="Host and username and password are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["passwd"])

    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    results = fmgr_user_group_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
