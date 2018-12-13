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
module: fmgr_user_device
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage devices in FortiGate with FortiManager
description:
  - Create, edit, and delete devices to be identified by FortiGate within FortiManager

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

  user:
    description:
      - User name.
    required: false

  type:
    description:
      - Device type.
      - choice | ipad | iPad Tablets.
      - choice | iphone | iPhone and iPod Touch devices.
      - choice | gaming-console | Gaming consoles (Xbox, PS2, PS3, Wii, PSP).
      - choice | blackberry-phone | BlackBerry phones.
      - choice | blackberry-playbook | BlackBerry tablets.
      - choice | linux-pc | Linux PC.
      - choice | mac | Mac computers.
      - choice | windows-pc | Windows PC.
      - choice | android-phone | Android-based phones.
      - choice | android-tablet | Android-based tablets.
      - choice | media-streaming | Other media streaming devices.
      - choice | windows-phone | Windows-based phones.
      - choice | fortinet-device | Other Fortinet devices.
      - choice | ip-phone | VoIP phones.
      - choice | router-nat-device | Router and/or NAT devices.
      - choice | other-network-device | All other identified devices.
      - choice | windows-tablet | Windows-based tablets.
      - choice | printer | Printing devices.
      - choice | forticam | FortiCam.
      - choice | fortifone | FortiFone.
      - choice | unknown | Device type not yet determined.
    required: false
    choices: ["ipad","iphone","gaming-console","blackberry-phone","blackberry-playbook","linux-pc","mac","windows-pc",
      "android-phone","android-tablet","media-streaming","windows-phone","fortinet-device","ip-phone",
      "router-nat-device","other-network-device","windows-tablet","printer","forticam","fortifone","unknown"]

  master_device:
    description:
      - Master device (optional).
    required: false

  mac:
    description:
      - Device MAC address(es).
    required: false

  comment:
    description:
      - Comment.
    required: false

  category:
    description:
      - Device category.
      - choice | none | No specific category.
      - choice | android-device | Android devices.
      - choice | blackberry-device | BlackBerry devices.
      - choice | fortinet-device | Fortinet devices.
      - choice | ios-device | Devices running Apple iOS.
      - choice | windows-device | Devices running Microsoft Windows.
      - choice | amazon-device | Amazon devices.
    required: false
    choices: ["none","android-device","blackberry-device","fortinet-device","ios-device","windows-device",
      "amazon-device"]

  avatar:
    description:
      - Image file for avatar (maximum 4K base64 encoded).
    required: false

  alias:
    description:
      - Device alias.
    required: false

  dynamic_mapping:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  dynamic_mapping_avatar:
    description:
      - Dynamic mapping for avatar images
    required: false

  dynamic_mapping_category:
    description:
      - Dynamic mapping categories for devices.
      - choice | none
      - choice | android-device
      - choice | blackberry-device
      - choice | fortinet-device
      - choice | ios-device
      - choice | windows-device
      - choice | amazon-device
    required: false
    choices: ["none","android-device","blackberry-device","fortinet-device","ios-device","windows-device",
      "amazon-device"]

  dynamic_mapping_comment:
    description:
      - Dynamic mapping comments
    required: false

  dynamic_mapping_mac:
    description:
      - Dynmaic mapping MAC
    required: false

  dynamic_mapping_master_device:
    description:
      - Dynamic mapping for a master device
    required: false

  dynamic_mapping_tags:
    description:
      - Dynamic mapping tags
    required: false

  dynamic_mapping_type:
    description:
      - Dynamic mapping types
      - choice | ipad
      - choice | iphone
      - choice | gaming-console
      - choice | blackberry-phone
      - choice | blackberry-playbook
      - choice | linux-pc
      - choice | mac
      - choice | windows-pc
      - choice | android-phone
      - choice | android-tablet
      - choice | media-streaming
      - choice | windows-phone
      - choice | fortinet-device
      - choice | ip-phone
      - choice | router-nat-device
      - choice | other-network-device
      - choice | windows-tablet
      - choice | printer
      - choice | forticam
      - choice | fortifone
      - choice | unknown
    required: false
    choices: ["ipad","iphone","gaming-console","blackberry-phone","blackberry-playbook","linux-pc","mac","windows-pc",
      "android-phone","android-tablet","media-streaming","windows-phone","fortinet-device","ip-phone",
      "router-nat-device","other-network-device","windows-tablet","printer","forticam","fortifone","unknown"]

  dynamic_mapping_user:
    description:
      - Dynamic mapping users
    required: false

  tagging:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  tagging_category:
    description:
      - Tag category.
    required: false

  tagging_name:
    description:
      - Tagging entry name.
    required: false

  tagging_tags:
    description:
      - Tags.
    required: false


'''

EXAMPLES = '''
- name: EDIT FMGR_USER_DEVICE
  fmgr_user_device:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode:
    adom:
    user:
    type:
    master_device:
    mac:
    comment:
    category:
    avatar:
    alias:
    dynamic_mapping_avatar:
    dynamic_mapping_category:
    dynamic_mapping_comment:
    dynamic_mapping_mac:
    dynamic_mapping_master_device:
    dynamic_mapping_tags:
    dynamic_mapping_type:
    dynamic_mapping_user:
    tagging_category:
    tagging_name:
    tagging_tags:
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


def fmgr_user_device_addsetdelete(fmg, paramgram):

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/user/device'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE

        url = '/pm/config/adom/{adom}/obj/user/device/{name}'.format(adom=adom, name=paramgram["alias"])
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
        adom=dict(type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        user=dict(required=False, type="str"),
        type=dict(required=False, type="str", choices=["ipad",
                                                       "iphone",
                                                       "gaming-console",
                                                       "blackberry-phone",
                                                       "blackberry-playbook",
                                                       "linux-pc",
                                                       "mac",
                                                       "windows-pc",
                                                       "android-phone",
                                                       "android-tablet",
                                                       "media-streaming",
                                                       "windows-phone",
                                                       "fortinet-device",
                                                       "ip-phone",
                                                       "router-nat-device",
                                                       "other-network-device",
                                                       "windows-tablet",
                                                       "printer",
                                                       "forticam",
                                                       "fortifone",
                                                       "unknown"]),
        master_device=dict(required=False, type="str"),
        mac=dict(required=False, type="str"),
        comment=dict(required=False, type="str"),
        category=dict(required=False, type="str", choices=["none",
                                                           "android-device",
                                                           "blackberry-device",
                                                           "fortinet-device",
                                                           "ios-device",
                                                           "windows-device",
                                                           "amazon-device"]),
        avatar=dict(required=False, type="str"),
        alias=dict(required=False, type="str"),
        dynamic_mapping=dict(required=False, type="list"),
        dynamic_mapping_avatar=dict(required=False, type="str"),
        dynamic_mapping_category=dict(required=False, type="str", choices=["none",
                                                                           "android-device",
                                                                           "blackberry-device",
                                                                           "fortinet-device",
                                                                           "ios-device",
                                                                           "windows-device",
                                                                           "amazon-device"]),
        dynamic_mapping_comment=dict(required=False, type="str"),
        dynamic_mapping_mac=dict(required=False, type="str"),
        dynamic_mapping_master_device=dict(required=False, type="str"),
        dynamic_mapping_tags=dict(required=False, type="str"),
        dynamic_mapping_type=dict(required=False, type="str", choices=["ipad",
                                                                       "iphone",
                                                                       "gaming-console",
                                                                       "blackberry-phone",
                                                                       "blackberry-playbook",
                                                                       "linux-pc",
                                                                       "mac",
                                                                       "windows-pc",
                                                                       "android-phone",
                                                                       "android-tablet",
                                                                       "media-streaming",
                                                                       "windows-phone",
                                                                       "fortinet-device",
                                                                       "ip-phone",
                                                                       "router-nat-device",
                                                                       "other-network-device",
                                                                       "windows-tablet",
                                                                       "printer",
                                                                       "forticam",
                                                                       "fortifone",
                                                                       "unknown"]),
        dynamic_mapping_user=dict(required=False, type="str"),
        tagging=dict(required=False, type="list"),
        tagging_category=dict(required=False, type="str"),
        tagging_name=dict(required=False, type="str"),
        tagging_tags=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "user": module.params["user"],
        "type": module.params["type"],
        "master-device": module.params["master_device"],
        "mac": module.params["mac"],
        "comment": module.params["comment"],
        "category": module.params["category"],
        "avatar": module.params["avatar"],
        "alias": module.params["alias"],
        "dynamic_mapping": {
            "avatar": module.params["dynamic_mapping_avatar"],
            "category": module.params["dynamic_mapping_category"],
            "comment": module.params["dynamic_mapping_comment"],
            "mac": module.params["dynamic_mapping_mac"],
            "master-device": module.params["dynamic_mapping_master_device"],
            "tags": module.params["dynamic_mapping_tags"],
            "type": module.params["dynamic_mapping_type"],
            "user": module.params["dynamic_mapping_user"],
        },
        "tagging": {
            "category": module.params["tagging_category"],
            "name": module.params["tagging_name"],
            "tags": module.params["tagging_tags"],
        }
    }

    list_overrides = ['dynamic_mapping', 'tagging']
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
    password = module.params["password"]
    username = module.params["username"]
    if host is None or username is None or password is None:
        module.fail_json(msg="Host and username and password are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])

    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    results = fmgr_user_device_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
