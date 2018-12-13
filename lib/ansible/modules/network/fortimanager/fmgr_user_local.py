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
module: fmgr_user_local
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Create local users in FortiManager
description: 
  - Creating local FGT users via FortiManager Ansible modules 

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

  password:
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

  workstation:
    description:
      - Name of the remote user workstation, if you want to limit the user to authenticate only from a particular work
      - station.
    required: false

  type:
    description:
      - Authentication method.
      - choice | password | Password authentication.
      - choice | radius | RADIUS server authentication.
      - choice | tacacs+ | TACACS+ server authentication.
      - choice | ldap | LDAP server authentication.
    required: false
    choices: ["password", "radius", "tacacs+", "ldap"]

  two_factor:
    description:
      - Enable/disable two-factor authentication.
      - choice | disable | 
      - choice | fortitoken | FortiToken
      - choice | email | Email authentication code.
      - choice | sms | SMS authentication code.
    required: false
    choices: ["disable", "fortitoken", "email", "sms"]

  tacacs_server:
    description:
      - Name of TACACS+ server with which the user must authenticate.
    required: false

  status:
    description:
      - Enable/disable allowing the local user to authenticate with the FortiGate unit.
      - choice | disable | Disable user.
      - choice | enable | Enable user.
    required: false
    choices: ["disable", "enable"]

  sms_server:
    description:
      - Send SMS through FortiGuard or other external server.
      - choice | fortiguard | Send SMS by FortiGuard.
      - choice | custom | Send SMS by custom server.
    required: false
    choices: ["fortiguard", "custom"]

  sms_phone:
    description:
      - Two-factor recipient's mobile phone number.
    required: false

  sms_custom_server:
    description:
      - Two-factor recipient's SMS server.
    required: false

  radius_server:
    description:
      - Name of RADIUS server with which the user must authenticate.
    required: false

  ppk_secret:
    description:
      - IKEv2 Postquantum Preshared Key (ASCII string or hexadecimal encoded with a leading 0x).
    required: false

  ppk_identity:
    description:
      - IKEv2 Postquantum Preshared Key Identity.
    required: false

  passwd_policy:
    description:
      - Password policy to apply to this user, as defined in config user password-policy.
    required: false

  passwd:
    description:
      - User's password.
    required: false

  name:
    description:
      - User name.
    required: false

  ldap_server:
    description:
      - Name of LDAP server with which the user must authenticate.
    required: false

  fortitoken:
    description:
      - Two-factor recipient's FortiToken serial number.
    required: false

  email_to:
    description:
      - Two-factor recipient's email address.
    required: false

  authtimeout:
    description:
      - Time in minutes before the authentication timeout for a user is reached.
    required: false

  auth_concurrent_value:
    description:
      - Maximum number of concurrent logins permitted from the same user.
    required: false

  auth_concurrent_override:
    description:
      - Enable/disable overriding the policy-auth-concurrent under config system global.
      - choice | disable | Disable auth-concurrent-override.
      - choice | enable | Enable auth-concurrent-override.
    required: false
    choices: ["disable", "enable"]


'''

EXAMPLES = '''
- name: EDIT FMGR_USER_LOCAL
  fmgr_user_local:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode:
    adom:
    workstation:
    type:
    two_factor:
    tacacs_server:
    status:
    sms_server:
    sms_phone:
    sms_custom_server:
    radius_server:
    ppk_secret:
    ppk_identity:
    passwd_policy:
    passwd:
    name:
    ldap_server:
    fortitoken:
    email_to:
    authtimeout:
    auth_concurrent_value:
    auth_concurrent_override:
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


def fmgr_user_local_addsetdelete(fmg, paramgram):
    """
    fmgr_user_local -- Your Description here, bruh
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
     # INIT A BASIC OBJECTS
    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/user/local'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/user/local/{name}'.format(adom=adom, name=paramgram["name"])
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
    list_of_elems = ["mode", "adom", "host", "username", "password"]
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
        adom=dict(required=False, type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        workstation=dict(required=False, type="str"),
        type=dict(required=False, type="str", choices=["password", "radius", "tacacs+", "ldap"]),
        two_factor=dict(required=False, type="str", choices=["disable", "fortitoken", "email", "sms"]),
        tacacs_server=dict(required=False, type="str"),
        status=dict(required=False, type="str", choices=["disable", "enable"]),
        sms_server=dict(required=False, type="str", choices=["fortiguard", "custom"]),
        sms_phone=dict(required=False, type="str"),
        sms_custom_server=dict(required=False, type="str"),
        radius_server=dict(required=False, type="str"),
        ppk_secret=dict(required=False, type="str", no_log=True),
        ppk_identity=dict(required=False, type="str"),
        passwd_policy=dict(required=False, type="str"),
        passwd=dict(required=False, type="str", no_log=True),
        name=dict(required=False, type="str"),
        ldap_server=dict(required=False, type="str"),
        fortitoken=dict(required=False, type="str"),
        email_to=dict(required=False, type="str"),
        authtimeout=dict(required=False, type="int"),
        auth_concurrent_value=dict(required=False, type="int"),
        auth_concurrent_override=dict(required=False, type="str", choices=["disable", "enable"]),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "workstation": module.params["workstation"],
        "type": module.params["type"],
        "two-factor": module.params["two_factor"],
        "tacacs+-server": module.params["tacacs_server"],
        "status": module.params["status"],
        "sms-server": module.params["sms_server"],
        "sms-phone": module.params["sms_phone"],
        "sms-custom-server": module.params["sms_custom_server"],
        "radius-server": module.params["radius_server"],
        "ppk-secret": module.params["ppk_secret"],
        "ppk-identity": module.params["ppk_identity"],
        "passwd-policy": module.params["passwd_policy"],
        "passwd": module.params["passwd"],
        "name": module.params["name"],
        "ldap-server": module.params["ldap_server"],
        "fortitoken": module.params["fortitoken"],
        "email-to": module.params["email_to"],
        "authtimeout": module.params["authtimeout"],
        "auth-concurrent-value": module.params["auth_concurrent_value"],
        "auth-concurrent-override": module.params["auth_concurrent_override"],

    }

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    password = module.params["password"]
    username = module.params["username"]
    if host is None or username is None or password is None:
        module.fail_json(msg="Host and username and password are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])

    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    results = fmgr_user_local_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
