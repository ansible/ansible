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
module: fmgr_secprof_profile_group
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage security profiles within FortiManager
description:
  - Manage security profile group which allows you to create a group of security profiles and apply that to a policy.

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
      - Allows use of soft-adds instead of overwriting existing values.
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  webfilter_profile:
    type: str
    description:
      - Name of an existing Web filter profile.
    required: false

  waf_profile:
    type: str
    description:
      - Name of an existing Web application firewall profile.
    required: false

  voip_profile:
    type: str
    description:
      - Name of an existing VoIP profile.
    required: false

  ssl_ssh_profile:
    type: str
    description:
      - Name of an existing SSL SSH profile.
    required: false

  ssh_filter_profile:
    type: str
    description:
      - Name of an existing SSH filter profile.
    required: false

  spamfilter_profile:
    type: str
    description:
      - Name of an existing Spam filter profile.
    required: false

  profile_protocol_options:
    type: str
    description:
      - Name of an existing Protocol options profile.
    required: false

  name:
    type: str
    description:
      - Profile group name.
    required: false

  mms_profile:
    type: str
    description:
      - Name of an existing MMS profile.
    required: false

  ips_sensor:
    type: str
    description:
      - Name of an existing IPS sensor.
    required: false

  icap_profile:
    type: str
    description:
      - Name of an existing ICAP profile.
    required: false

  dnsfilter_profile:
    type: str
    description:
      - Name of an existing DNS filter profile.
    required: false

  dlp_sensor:
    type: str
    description:
      - Name of an existing DLP sensor.
    required: false

  av_profile:
    type: str
    description:
      - Name of an existing Antivirus profile.
    required: false

  application_list:
    type: str
    description:
      - Name of an existing Application list.
    required: false


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_profile_group:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_TEST_Profile_Group"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_profile_group:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_TEST_Profile_Group"
      mode: "set"
      av_profile: "Ansible_AV_Profile"
      profile_protocol_options: "default"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
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


def fmgr_firewall_profile_group_addsetdelete(fmg, paramgram):
    """
    fmgr_firewall_profile_group -- Your Description here, bruh
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    url = ""
    datagram = {}

    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/firewall/profile-group'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/firewall/profile-group/{name}'.format(adom=adom, name=paramgram["name"])
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
# FUNCTION/METHOD FOR LOGGING OUT AND ANALYZING ERROR CODES
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """

    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except BaseException:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except BaseException:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

            if results[0] not in good_codes:
                if logout_on_fail:
                    fmg.logout()
                    module.fail_json(msg=msg, **results[1])
                else:
                    return msg
            else:
                if logout_on_success:
                    fmg.logout()
                    module.exit_json(msg=msg, **results[1])
                else:
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

        webfilter_profile=dict(required=False, type="str"),
        waf_profile=dict(required=False, type="str"),
        voip_profile=dict(required=False, type="str"),
        ssl_ssh_profile=dict(required=False, type="str"),
        ssh_filter_profile=dict(required=False, type="str"),
        spamfilter_profile=dict(required=False, type="str"),
        profile_protocol_options=dict(required=False, type="str"),
        name=dict(required=False, type="str"),
        mms_profile=dict(required=False, type="str"),
        ips_sensor=dict(required=False, type="str"),
        icap_profile=dict(required=False, type="str"),
        dnsfilter_profile=dict(required=False, type="str"),
        dlp_sensor=dict(required=False, type="str"),
        av_profile=dict(required=False, type="str"),
        application_list=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "webfilter-profile": module.params["webfilter_profile"],
        "waf-profile": module.params["waf_profile"],
        "voip-profile": module.params["voip_profile"],
        "ssl-ssh-profile": module.params["ssl_ssh_profile"],
        "ssh-filter-profile": module.params["ssh_filter_profile"],
        "spamfilter-profile": module.params["spamfilter_profile"],
        "profile-protocol-options": module.params["profile_protocol_options"],
        "name": module.params["name"],
        "mms-profile": module.params["mms_profile"],
        "ips-sensor": module.params["ips_sensor"],
        "icap-profile": module.params["icap_profile"],
        "dnsfilter-profile": module.params["dnsfilter_profile"],
        "dlp-sensor": module.params["dlp_sensor"],
        "av-profile": module.params["av_profile"],
        "application-list": module.params["application_list"],

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

    results = fmgr_firewall_profile_group_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
