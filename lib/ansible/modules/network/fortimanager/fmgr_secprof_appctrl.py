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
module: fmgr_secprof_appctrl
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage application control security profiles
description:
  -  Manage application control security profiles within FortiManager

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

  unknown_application_log:
    description:
      - Enable/disable logging for unknown applications.
      - choice | disable | Disable logging for unknown applications.
      - choice | enable | Enable logging for unknown applications.
    required: false
    choices: ["disable", "enable"]

  unknown_application_action:
    description:
      - Pass or block traffic from unknown applications.
      - choice | pass | Pass or allow unknown applications.
      - choice | block | Drop or block unknown applications.
    required: false
    choices: ["pass", "block"]

  replacemsg_group:
    description:
      - Replacement message group.
    required: false

  p2p_black_list:
    description:
      - NO DESCRIPTION PARSED ENTER MANUALLY
      - FLAG Based Options. Specify multiple in list form.
      - flag | skype | Skype.
      - flag | edonkey | Edonkey.
      - flag | bittorrent | Bit torrent.
    required: false
    choices: ["skype", "edonkey", "bittorrent"]

  other_application_log:
    description:
      - Enable/disable logging for other applications.
      - choice | disable | Disable logging for other applications.
      - choice | enable | Enable logging for other applications.
    required: false
    choices: ["disable", "enable"]

  other_application_action:
    description:
      - Action for other applications.
      - choice | pass | Allow sessions matching an application in this application list.
      - choice | block | Block sessions matching an application in this application list.
    required: false
    choices: ["pass", "block"]

  options:
    description:
      - NO DESCRIPTION PARSED ENTER MANUALLY
      - FLAG Based Options. Specify multiple in list form.
      - flag | allow-dns | Allow DNS.
      - flag | allow-icmp | Allow ICMP.
      - flag | allow-http | Allow generic HTTP web browsing.
      - flag | allow-ssl | Allow generic SSL communication.
      - flag | allow-quic | Allow QUIC.
    required: false
    choices: ["allow-dns", "allow-icmp", "allow-http", "allow-ssl", "allow-quic"]

  name:
    description:
      - List name.
    required: false

  extended_log:
    description:
      - Enable/disable extended logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  deep_app_inspection:
    description:
      - Enable/disable deep application inspection.
      - choice | disable | Disable deep application inspection.
      - choice | enable | Enable deep application inspection.
    required: false
    choices: ["disable", "enable"]

  comment:
    description:
      - comments
    required: false

  app_replacemsg:
    description:
      - Enable/disable replacement messages for blocked applications.
      - choice | disable | Disable replacement messages for blocked applications.
      - choice | enable | Enable replacement messages for blocked applications.
    required: false
    choices: ["disable", "enable"]

  entries:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED. This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, OMIT THE USE OF THIS PARAMETER 
      - AND USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  entries_action:
    description:
      - Pass or block traffic, or reset connection for traffic from this application.
      - choice | pass | Pass or allow matching traffic.
      - choice | block | Block or drop matching traffic.
      - choice | reset | Reset sessions for matching traffic.
    required: false
    choices: ["pass", "block", "reset"]

  entries_application:
    description:
      - ID of allowed applications.
    required: false

  entries_behavior:
    description:
      - Application behavior filter.
    required: false

  entries_category:
    description:
      - Category ID list.
    required: false

  entries_log:
    description:
      - Enable/disable logging for this application list.
      - choice | disable | Disable logging.
      - choice | enable | Enable logging.
    required: false
    choices: ["disable", "enable"]

  entries_log_packet:
    description:
      - Enable/disable packet logging.
      - choice | disable | Disable packet logging.
      - choice | enable | Enable packet logging.
    required: false
    choices: ["disable", "enable"]

  entries_per_ip_shaper:
    description:
      - Per-IP traffic shaper.
    required: false

  entries_popularity:
    description:
      - Application popularity filter (1 - 5, from least to most popular).
      - FLAG Based Options. Specify multiple in list form.
      - flag | 1 | Popularity level 1.
      - flag | 2 | Popularity level 2.
      - flag | 3 | Popularity level 3.
      - flag | 4 | Popularity level 4.
      - flag | 5 | Popularity level 5.
    required: false
    choices: ["1", "2", "3", "4", "5"]

  entries_protocols:
    description:
      - Application protocol filter.
    required: false

  entries_quarantine:
    description:
      - Quarantine method.
      - choice | none | Quarantine is disabled.
      - choice | attacker | Block all traffic sent from attacker's IP address. 
      - The attacker's IP address is also added to the banned user list. The target's address is not affected.
    required: false
    choices: ["none", "attacker"]

  entries_quarantine_expiry:
    description:
      - Duration of quarantine. (Format ###d##h##m, minimum 1m, maximum 364d23h59m, default = 5m). 
      - Requires quarantine set to attacker.
    required: false

  entries_quarantine_log:
    description:
      - Enable/disable quarantine logging.
      - choice | disable | Disable quarantine logging.
      - choice | enable | Enable quarantine logging.
    required: false
    choices: ["disable", "enable"]

  entries_rate_count:
    description:
      - Count of the rate.
    required: false

  entries_rate_duration:
    description:
      - Duration (sec) of the rate.
    required: false

  entries_rate_mode:
    description:
      - Rate limit mode.
      - choice | periodical | Allow configured number of packets every rate-duration.
      - choice | continuous | Block packets once the rate is reached.
    required: false
    choices: ["periodical", "continuous"]

  entries_rate_track:
    description:
      - Track the packet protocol field.
      - choice | none |
      - choice | src-ip | Source IP.
      - choice | dest-ip | Destination IP.
      - choice | dhcp-client-mac | DHCP client.
      - choice | dns-domain | DNS domain.
    required: false
    choices: ["none", "src-ip", "dest-ip", "dhcp-client-mac", "dns-domain"]

  entries_risk:
    description:
      - Risk, or impact, of allowing traffic from this application to occur 1 - 5; 
      - (Low, Elevated, Medium, High, and Critical).
    required: false

  entries_session_ttl:
    description:
      - Session TTL (0 = default).
    required: false

  entries_shaper:
    description:
      - Traffic shaper.
    required: false

  entries_shaper_reverse:
    description:
      - Reverse traffic shaper.
    required: false

  entries_sub_category:
    description:
      - Application Sub-category ID list.
    required: false

  entries_technology:
    description:
      - Application technology filter.
    required: false

  entries_vendor:
    description:
      - Application vendor filter.
    required: false

  entries_parameters_value:
    description:
      - Parameter value.
    required: false


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_appctrl:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_Application_Control_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_appctrl:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_Application_Control_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "set"
      entries: [{
                action: "block",
                log: "enable",
                log-packet: "enable",
                protocols: ["1"],
                quarantine: "attacker",
                quarantine-log: "enable",
                },
                {action: "pass",
                category: ["2","3","4"]},
              ]
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


def fmgr_application_list_addsetdelete(fmg, paramgram):
    """
    fmgr_application_list -- Your Description here, bruh
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    # INIT A BASIC OBJECTS
    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/application/list'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/application/list/{name}'.format(adom=adom, name=paramgram["name"])
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
    # pydevd.settrace('10.0.0.122', port=54654, stdoutToServer=True, stderrToServer=True)
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
                module.exit_json(msg="API Called worked, but logout handler has been asked to logout on success",
                                 **results[1])
            else:
                return msg


# FUNCTION/METHOD FOR CONVERTING CIDR TO A NETMASK
# DID NOT USE IP ADDRESS MODULE TO KEEP INCLUDES TO A MINIMUM
def fmgr_cidr_to_netmask(cidr):
    cidr = int(cidr)
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    return (str((0xff000000 & mask) >> 24) + '.' +
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

        unknown_application_log=dict(required=False, type="str", choices=["disable", "enable"]),
        unknown_application_action=dict(required=False, type="str", choices=["pass", "block"]),
        replacemsg_group=dict(required=False, type="str"),
        p2p_black_list=dict(required=False, type="str", choices=["skype", "edonkey", "bittorrent"]),
        other_application_log=dict(required=False, type="str", choices=["disable", "enable"]),
        other_application_action=dict(required=False, type="str", choices=["pass", "block"]),
        options=dict(required=False, type="str",
                     choices=["allow-dns", "allow-icmp", "allow-http", "allow-ssl", "allow-quic"]),
        name=dict(required=False, type="str"),
        extended_log=dict(required=False, type="str", choices=["disable", "enable"]),
        deep_app_inspection=dict(required=False, type="str", choices=["disable", "enable"]),
        comment=dict(required=False, type="str"),
        app_replacemsg=dict(required=False, type="str", choices=["disable", "enable"]),
        entries=dict(required=False, type="list"),
        entries_action=dict(required=False, type="str", choices=["pass", "block", "reset"]),
        entries_application=dict(required=False, type="str"),
        entries_behavior=dict(required=False, type="str"),
        entries_category=dict(required=False, type="str"),
        entries_log=dict(required=False, type="str", choices=["disable", "enable"]),
        entries_log_packet=dict(required=False, type="str", choices=["disable", "enable"]),
        entries_per_ip_shaper=dict(required=False, type="str"),
        entries_popularity=dict(required=False, type="str", choices=["1", "2", "3", "4", "5"]),
        entries_protocols=dict(required=False, type="str"),
        entries_quarantine=dict(required=False, type="str", choices=["none", "attacker"]),
        entries_quarantine_expiry=dict(required=False, type="str"),
        entries_quarantine_log=dict(required=False, type="str", choices=["disable", "enable"]),
        entries_rate_count=dict(required=False, type="int"),
        entries_rate_duration=dict(required=False, type="int"),
        entries_rate_mode=dict(required=False, type="str", choices=["periodical", "continuous"]),
        entries_rate_track=dict(required=False, type="str",
                                choices=["none", "src-ip", "dest-ip", "dhcp-client-mac", "dns-domain"]),
        entries_risk=dict(required=False, type="str"),
        entries_session_ttl=dict(required=False, type="int"),
        entries_shaper=dict(required=False, type="str"),
        entries_shaper_reverse=dict(required=False, type="str"),
        entries_sub_category=dict(required=False, type="str"),
        entries_technology=dict(required=False, type="str"),
        entries_vendor=dict(required=False, type="str"),

        entries_parameters_value=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "unknown-application-log": module.params["unknown_application_log"],
        "unknown-application-action": module.params["unknown_application_action"],
        "replacemsg-group": module.params["replacemsg_group"],
        "p2p-black-list": module.params["p2p_black_list"],
        "other-application-log": module.params["other_application_log"],
        "other-application-action": module.params["other_application_action"],
        "options": module.params["options"],
        "name": module.params["name"],
        "extended-log": module.params["extended_log"],
        "deep-app-inspection": module.params["deep_app_inspection"],
        "comment": module.params["comment"],
        "app-replacemsg": module.params["app_replacemsg"],
        "entries": {
            "action": module.params["entries_action"],
            "application": module.params["entries_application"],
            "behavior": module.params["entries_behavior"],
            "category": module.params["entries_category"],
            "log": module.params["entries_log"],
            "log-packet": module.params["entries_log_packet"],
            "per-ip-shaper": module.params["entries_per_ip_shaper"],
            "popularity": module.params["entries_popularity"],
            "protocols": module.params["entries_protocols"],
            "quarantine": module.params["entries_quarantine"],
            "quarantine-expiry": module.params["entries_quarantine_expiry"],
            "quarantine-log": module.params["entries_quarantine_log"],
            "rate-count": module.params["entries_rate_count"],
            "rate-duration": module.params["entries_rate_duration"],
            "rate-mode": module.params["entries_rate_mode"],
            "rate-track": module.params["entries_rate_track"],
            "risk": module.params["entries_risk"],
            "session-ttl": module.params["entries_session_ttl"],
            "shaper": module.params["entries_shaper"],
            "shaper-reverse": module.params["entries_shaper_reverse"],
            "sub-category": module.params["entries_sub_category"],
            "technology": module.params["entries_technology"],
            "vendor": module.params["entries_vendor"],
            "parameters": {
                "value": module.params["entries_parameters_value"],
            }
        }
    }
    list_overrides = ['entries']
    for list_variable in list_overrides:
        override_data = list()
        try:
            override_data = module.params[list_variable]
        except BaseException:
            pass
        try:
            if override_data:
                del paramgram[list_variable]
                paramgram[list_variable] = override_data
        except BaseException:
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

    results = fmgr_application_list_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
