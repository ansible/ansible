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
module: fmgr_fwobj_ippool
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Allows the editing of IP Pool Objects within FortiManager.
description:
  -  Allows users to add/edit/delete IP Pool Objects.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  host:
    description:
      - The FortiManager's address.
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

  type:
    description:
      - IP pool type (overload, one-to-one, fixed port range, or port block allocation).
      - choice | overload | IP addresses in the IP pool can be shared by clients.
      - choice | one-to-one | One to one mapping.
      - choice | fixed-port-range | Fixed port range.
      - choice | port-block-allocation | Port block allocation.
    required: false
    choices: ["overload", "one-to-one", "fixed-port-range", "port-block-allocation"]

  startip:
    description:
      - First IPv4 address (inclusive) in the range for the address pool (format xxx.xxx.xxx.xxx, Default| 0.0.0.0).
    required: false

  source_startip:
    description:
      -  First IPv4 address (inclusive) in the range of the source addresses to be translated (format xxx.xxx.xxx.xxx,
         Default| 0.0.0.0).
    required: false

  source_endip:
    description:
      - Final IPv4 address (inclusive) in the range of the source addresses to be translated (format xxx.xxx.xxx.xxx,
        Default| 0.0.0.0).
    required: false

  permit_any_host:
    description:
      - Enable/disable full cone NAT.
      - choice | disable | Disable full cone NAT.
      - choice | enable | Enable full cone NAT.
    required: false
    choices: ["disable", "enable"]

  pba_timeout:
    description:
      - Port block allocation timeout (seconds).
    required: false

  num_blocks_per_user:
    description:
      - Number of addresses blocks that can be used by a user (1 to 128, default = 8).
    required: false

  name:
    description:
      - IP pool name.
    required: false

  endip:
    description:
      - Final IPv4 address (inclusive) in the range for the address pool (format xxx.xxx.xxx.xxx, Default| 0.0.0.0).
    required: false

  comments:
    description:
      - Comment.
    required: false

  block_size:
    description:
      -  Number of addresses in a block (64 to 4096, default = 128).
    required: false

  associated_interface:
    description:
      - Associated interface name.
    required: false

  arp_reply:
    description:
      - Enable/disable replying to ARP requests when an IP Pool is added to a policy (default = enable).
      - choice | disable | Disable ARP reply.
      - choice | enable | Enable ARP reply.
    required: false
    choices: ["disable", "enable"]

  arp_intf:
    description:
      - Select an interface from available options that will reply to ARP requests. (If blank, any is selected).
    required: false

  dynamic_mapping:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameter.ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  dynamic_mapping_arp_intf:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_arp_reply:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_associated_interface:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_block_size:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_comments:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_endip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_num_blocks_per_user:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_pba_timeout:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_permit_any_host:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false
    choices: ["disable", "enable"]

  dynamic_mapping_source_endip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_source_startip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_startip:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false

  dynamic_mapping_type:
    description:
      - Dynamic Mapping clone of original suffixed parameter.
    required: false
    choices: ["overload", "one-to-one", "fixed-port-range", "port-block-allocation"]


'''

EXAMPLES = '''
- name: ADD FMGR_FIREWALL_IPPOOL Overload
  fmgr_fwobj_ippool:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "add"
    adom: "ansible"
    name: "Ansible_pool4_overload"
    comments: "Created by ansible"
    type: "overload"

    # OPTIONS FOR ALL MODES
    startip: "10.10.10.10"
    endip: "10.10.10.100"
    arp_reply: "enable"

- name: ADD FMGR_FIREWALL_IPPOOL one-to-one
  fmgr_fwobj_ippool:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "add"
    adom: "ansible"
    name: "Ansible_pool4_121"
    comments: "Created by ansible"
    type: "one-to-one"

    # OPTIONS FOR ALL MODES
    startip: "10.10.20.10"
    endip: "10.10.20.100"
    arp_reply: "enable"

- name: ADD FMGR_FIREWALL_IPPOOL FIXED PORT RANGE
  fmgr_fwobj_ippool:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "add"
    adom: "ansible"
    name: "Ansible_pool4_fixed_port"
    comments: "Created by ansible"
    type: "fixed-port-range"

    # OPTIONS FOR ALL MODES
    startip: "10.10.40.10"
    endip: "10.10.40.100"
    arp_reply: "enable"
    # FIXED PORT RANGE OPTIONS
    source_startip: "192.168.20.1"
    source_endip: "192.168.20.20"

- name: ADD FMGR_FIREWALL_IPPOOL PORT BLOCK ALLOCATION
  fmgr_fwobj_ippool:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "add"
    adom: "ansible"
    name: "Ansible_pool4_port_block_allocation"
    comments: "Created by ansible"
    type: "port-block-allocation"

    # OPTIONS FOR ALL MODES
    startip: "10.10.30.10"
    endip: "10.10.30.100"
    arp_reply: "enable"
    # PORT BLOCK ALLOCATION OPTIONS
    block_size: "128"
    num_blocks_per_user: "1"
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


def fmgr_fwobj_ippool_addsetdelete(fmg, paramgram):
    """
    fmgr_firewall_ippool -- Allows add/update/set/delete of Firewall IP Pool Objects
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    # INIT A BASIC OBJECTS
    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/firewall/ippool'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/firewall/ippool/{name}'.format(adom=adom, name=paramgram["name"])
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

        type=dict(required=False, type="str", choices=["overload",
                                                       "one-to-one",
                                                       "fixed-port-range",
                                                       "port-block-allocation"]),
        startip=dict(required=False, type="str"),
        source_startip=dict(required=False, type="str"),
        source_endip=dict(required=False, type="str"),
        permit_any_host=dict(required=False, type="str", choices=["disable", "enable"]),
        pba_timeout=dict(required=False, type="int"),
        num_blocks_per_user=dict(required=False, type="int"),
        name=dict(required=False, type="str"),
        endip=dict(required=False, type="str"),
        comments=dict(required=False, type="str"),
        block_size=dict(required=False, type="int"),
        associated_interface=dict(required=False, type="str"),
        arp_reply=dict(required=False, type="str", choices=["disable", "enable"]),
        arp_intf=dict(required=False, type="str"),
        dynamic_mapping=dict(required=False, type="list"),
        dynamic_mapping_arp_intf=dict(required=False, type="str"),
        dynamic_mapping_arp_reply=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_associated_interface=dict(required=False, type="str"),
        dynamic_mapping_block_size=dict(required=False, type="int"),
        dynamic_mapping_comments=dict(required=False, type="str"),
        dynamic_mapping_endip=dict(required=False, type="str"),
        dynamic_mapping_num_blocks_per_user=dict(required=False, type="int"),
        dynamic_mapping_pba_timeout=dict(required=False, type="int"),
        dynamic_mapping_permit_any_host=dict(required=False, type="str", choices=["disable", "enable"]),
        dynamic_mapping_source_endip=dict(required=False, type="str"),
        dynamic_mapping_source_startip=dict(required=False, type="str"),
        dynamic_mapping_startip=dict(required=False, type="str"),
        dynamic_mapping_type=dict(required=False, type="str", choices=["overload",
                                                                       "one-to-one",
                                                                       "fixed-port-range",
                                                                       "port-block-allocation"]),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "type": module.params["type"],
        "startip": module.params["startip"],
        "source-startip": module.params["source_startip"],
        "source-endip": module.params["source_endip"],
        "permit-any-host": module.params["permit_any_host"],
        "pba-timeout": module.params["pba_timeout"],
        "num-blocks-per-user": module.params["num_blocks_per_user"],
        "name": module.params["name"],
        "endip": module.params["endip"],
        "comments": module.params["comments"],
        "block-size": module.params["block_size"],
        "associated-interface": module.params["associated_interface"],
        "arp-reply": module.params["arp_reply"],
        "arp-intf": module.params["arp_intf"],
        "dynamic_mapping": {
            "arp-intf": module.params["dynamic_mapping_arp_intf"],
            "arp-reply": module.params["dynamic_mapping_arp_reply"],
            "associated-interface": module.params["dynamic_mapping_associated_interface"],
            "block-size": module.params["dynamic_mapping_block_size"],
            "comments": module.params["dynamic_mapping_comments"],
            "endip": module.params["dynamic_mapping_endip"],
            "num-blocks-per-user": module.params["dynamic_mapping_num_blocks_per_user"],
            "pba-timeout": module.params["dynamic_mapping_pba_timeout"],
            "permit-any-host": module.params["dynamic_mapping_permit_any_host"],
            "source-endip": module.params["dynamic_mapping_source_endip"],
            "source-startip": module.params["dynamic_mapping_source_startip"],
            "startip": module.params["dynamic_mapping_startip"],
            "type": module.params["dynamic_mapping_type"],
        }
    }

    list_overrides = ['dynamic_mapping']
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

    results = fmgr_fwobj_ippool_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0, -2, -3])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
