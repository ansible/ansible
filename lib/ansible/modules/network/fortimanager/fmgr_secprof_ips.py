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
module: fmgr_secprof_ips
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Managing IPS security profiles in FortiManager
description:
  -  Managing IPS security profiles in FortiManager

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

  replacemsg_group:
    description:
      - Replacement message group.
    required: false

  name:
    description:
      - Sensor name.
    required: false

  extended_log:
    description:
      - Enable/disable extended logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  comment:
    description:
      - Comment.
    required: false

  block_malicious_url:
    description:
      - Enable/disable malicious URL blocking.
      - choice | disable | Disable malicious URL blocking.
      - choice | enable | Enable malicious URL blocking.
    required: false
    choices: ["disable", "enable"]

  entries:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED. This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, OMIT THE USE OF THIS PARAMETER AND USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH
        MULTIPLE TASKS
    required: false

  entries_action:
    description:
      - Action taken with traffic in which signatures are detected.
      - choice | pass | Pass or allow matching traffic.
      - choice | block | Block or drop matching traffic.
      - choice | reset | Reset sessions for matching traffic.
      - choice | default | Pass or drop matching traffic, depending on the default action of the signature.
    required: false
    choices: ["pass", "block", "reset", "default"]

  entries_application:
    description:
      - Applications to be protected. set application ? lists available applications. all includes all applications.
        Other includes all unlisted applications.
    required: false

  entries_location:
    description:
      - Protect client or server traffic.
    required: false

  entries_log:
    description:
      - Enable/disable logging of signatures included in filter.
      - choice | disable | Disable logging of selected rules.
      - choice | enable | Enable logging of selected rules.
    required: false
    choices: ["disable", "enable"]

  entries_log_attack_context:
    description:
      - Enable/disable logging of attack context: URL buffer, header buffer, body buffer, packet buffer.
      - choice | disable | Disable logging of detailed attack context.
      - choice | enable | Enable logging of detailed attack context.
    required: false
    choices: ["disable", "enable"]

  entries_log_packet:
    description:
      - Enable/disable packet logging. Enable to save the packet that triggers the filter. You can download the
        packets in pcap format for diagnostic use.
      - choice | disable | Disable packet logging of selected rules.
      - choice | enable | Enable packet logging of selected rules.
    required: false
    choices: ["disable", "enable"]

  entries_os:
    description:
      - Operating systems to be protected.  all includes all operating systems. other includes all unlisted
        operating systems.
    required: false

  entries_protocol:
    description:
      - Protocols to be examined. set protocol ? lists available protocols. all includes all protocols.
        Other includes all unlisted protocols.
    required: false

  entries_quarantine:
    description:
      - Quarantine method.
      - choice | none | Quarantine is disabled.
      - choice | attacker | Block all traffic sent from attacker's IP address. The attacker's IP address is also added
        to the banned user list. The target's address is not affected.
    required: false
    choices: ["none", "attacker"]

  entries_quarantine_expiry:
    description:
      - Duration of quarantine. (Format ###d##h##m, minimum 1m, maximum 364d23h59m, default = 5m).
        Requires quarantine set to attacker.
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

  entries_rule:
    description:
      - Identifies the predefined or custom IPS signatures to add to the sensor.
    required: false

  entries_severity:
    description:
      - Relative severity of the signature, from info to critical. Log messages generated by the signature
        include the severity.
    required: false

  entries_status:
    description:
      - Status of the signatures included in filter. default enables the filter and only use filters with default
        status of enable. Filters with default status of disable will not be used.
      - choice | disable | Disable status of selected rules.
      - choice | enable | Enable status of selected rules.
      - choice | default | Default.
    required: false
    choices: ["disable", "enable", "default"]

  entries_exempt_ip_dst_ip:
    description:
      - Destination IP address and netmask.
    required: false

  entries_exempt_ip_src_ip:
    description:
      - Source IP address and netmask.
    required: false

  filter:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED. This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, OMIT THE USE OF THIS PARAMETER AND USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS
        WITH MULTIPLE TASKS
    required: false

  filter_action:
    description:
      - Action of selected rules.
      - choice | pass | Pass or allow matching traffic.
      - choice | block | Block or drop matching traffic.
      - choice | default | Pass or drop matching traffic, depending on the default action of the signature.
      - choice | reset | Reset sessions for matching traffic.
    required: false
    choices: ["pass", "block", "default", "reset"]

  filter_application:
    description:
      - Vulnerable application filter.
    required: false

  filter_location:
    description:
      - Vulnerability location filter.
    required: false

  filter_log:
    description:
      - Enable/disable logging of selected rules.
      - choice | disable | Disable logging of selected rules.
      - choice | enable | Enable logging of selected rules.
    required: false
    choices: ["disable", "enable"]

  filter_log_packet:
    description:
      - Enable/disable packet logging of selected rules.
      - choice | disable | Disable packet logging of selected rules.
      - choice | enable | Enable packet logging of selected rules.
    required: false
    choices: ["disable", "enable"]

  filter_name:
    description:
      - Filter name.
    required: false

  filter_os:
    description:
      - Vulnerable OS filter.
    required: false

  filter_protocol:
    description:
      - Vulnerable protocol filter.
    required: false

  filter_quarantine:
    description:
      - Quarantine IP or interface.
      - choice | none | Quarantine is disabled.
      - choice | attacker | Block all traffic sent from attacker's IP address. The attacker's IP address is also
        added to the banned user list. The target's address is not affected.
    required: false
    choices: ["none", "attacker"]

  filter_quarantine_expiry:
    description:
      - Duration of quarantine in minute.
    required: false

  filter_quarantine_log:
    description:
      - Enable/disable logging of selected quarantine.
      - choice | disable | Disable logging of selected quarantine.
      - choice | enable | Enable logging of selected quarantine.
    required: false
    choices: ["disable", "enable"]

  filter_severity:
    description:
      - Vulnerability severity filter.
    required: false

  filter_status:
    description:
      - Selected rules status.
      - choice | disable | Disable status of selected rules.
      - choice | enable | Enable status of selected rules.
      - choice | default | Default.
    required: false
    choices: ["disable", "enable", "default"]

  override:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED. This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, OMIT THE USE OF THIS PARAMETER AND USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH
        MULTIPLE TASKS
    required: false

  override_action:
    description:
      - Action of override rule.
      - choice | pass | Pass or allow matching traffic.
      - choice | block | Block or drop matching traffic.
      - choice | reset | Reset sessions for matching traffic.
    required: false
    choices: ["pass", "block", "reset"]

  override_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable logging.
      - choice | enable | Enable logging.
    required: false
    choices: ["disable", "enable"]

  override_log_packet:
    description:
      - Enable/disable packet logging.
      - choice | disable | Disable packet logging.
      - choice | enable | Enable packet logging.
    required: false
    choices: ["disable", "enable"]

  override_quarantine:
    description:
      - Quarantine IP or interface.
      - choice | none | Quarantine is disabled.
      - choice | attacker | Block all traffic sent from attacker's IP address. The attacker's IP address is also
        added to the banned user list. The target's address is not affected.
    required: false
    choices: ["none", "attacker"]

  override_quarantine_expiry:
    description:
      - Duration of quarantine in minute.
    required: false

  override_quarantine_log:
    description:
      - Enable/disable logging of selected quarantine.
      - choice | disable | Disable logging of selected quarantine.
      - choice | enable | Enable logging of selected quarantine.
    required: false
    choices: ["disable", "enable"]

  override_rule_id:
    description:
      - Override rule ID.
    required: false

  override_status:
    description:
      - Enable/disable status of override rule.
      - choice | disable | Disable status of override rule.
      - choice | enable | Enable status of override rule.
    required: false
    choices: ["disable", "enable"]

  override_exempt_ip_dst_ip:
    description:
      - Destination IP address and netmask.
    required: false

  override_exempt_ip_src_ip:
    description:
      - Source IP address and netmask.
    required: false


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_ips:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_IPS_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_ips:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_IPS_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "set"
      block_malicious_url: "enable"
      entries: [{severity: "high", action: "block", log-packet: "enable"}, {severity: "medium", action: "pass"}]
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


def fmgr_ips_sensor_addsetdelete(fmg, paramgram):
    """
    fmgr_ips_sensor -- Your Description here, bruh
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    # INIT A BASIC OBJECTS
    response = (-100000,
                {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/ips/sensor'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/ips/sensor/{name}'.format(
            adom=adom, name=paramgram["name"])
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
def fmgr_logout(
        fmg,
        module,
        msg="NULL",
        results=(),
        good_codes=(
            0,
        ),
        logout_on_fail=True,
        logout_on_success=False):
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
                module.exit_json(
                    msg="API Called worked, but logout handler has been asked to logout on success",
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


# EDITED FUNCTION WITH ADDITIONAL FUNCTION CALL TO CHECK IF IS EMPTY DICT
# OR NOT
def fmgr_del_none(obj):
    if isinstance(obj, dict):
        return type(obj)(
            (fmgr_del_none(k),
             fmgr_del_none(v)) for k,
            v in obj.items() if k is not None and (
                v is not None and not fmgr_is_empty_dict(v)))
    else:
        return obj


# NEW FUNCTION TO INSPECT FOR NESTED EMPTY DICTIONARIES
def fmgr_is_empty_dict(obj):
    # SET RETURN_VAL TO FALSE -- WE MUST PROVE THAT THIS IS EMPTY!
    return_val = False
    # IS IT A DICTIONARY?
    if isinstance(obj, dict):
        # IS IT EMPTY?
        if len(obj) > 0:
            # IF NOT EMPTY, LOOP THROUGH ITS ITEMS
            for k, v in obj.items():
                # IS CHILD ITEM A DICTIONARY?
                if isinstance(v, dict):
                    # IS IT EMPTY?
                    if len(v) == 0:
                        # RETURN TRUE (SO FAR)
                        return_val = True
                    # IF NOT EMPTY -- LOOP THOUGH CHILD ITEMS TO SEE IF THEY
                    # ARE == NONE
                    elif len(v) > 0:
                        for k1, v1 in v.items():
                            # IF CHILD OBJECTS ARE NONE, RETURN TRUE (EMPTY)
                            if v1 is None:
                                return_val = True
                            # IF A CHILD OBJECT IS NOT NONE, RETURN FALSE (NOT
                            # EMPTY) AND EXIT
                            elif v1 is not None:
                                return_val = False
                                return return_val
                # IF IT ISN'T A DICTIONARY, AND IS EMPTY, RETURN TRUE
                elif v is None:
                    return_val = True
                # IF IT ISN'T A DICTIONARY, AND ISN'T EMPTY, RETURN FALSE
                elif v is not None:
                    return_val = False
                    return return_val
        # IF DICTIONARY IS EMPTY RETURN TRUE
        elif len(obj) == 0:
            return_val = True

    return return_val


# utility function: remove keys that are need for the logic but the FMG
# API won't accept them
def fmgr_prepare_dict(obj):
    list_of_elems = ["mode", "adom", "host", "username", "password"]
    if isinstance(obj, dict):
        obj = dict((key, fmgr_prepare_dict(value))
                   for (key, value) in obj.items() if key not in list_of_elems)
    return obj


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(
            fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(
            fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
        mode=dict(choices=["add", "set", "delete", "update"],
                  type="str", default="add"),

        replacemsg_group=dict(required=False, type="str"),
        name=dict(required=False, type="str"),
        extended_log=dict(required=False, type="str",
                          choices=["disable", "enable"]),
        comment=dict(required=False, type="str"),
        block_malicious_url=dict(required=False, type="str", choices=[
                                 "disable", "enable"]),
        entries=dict(required=False, type="list"),
        entries_action=dict(required=False, type="str", choices=[
                            "pass", "block", "reset", "default"]),
        entries_application=dict(required=False, type="str"),
        entries_location=dict(required=False, type="str"),
        entries_log=dict(required=False, type="str",
                         choices=["disable", "enable"]),
        entries_log_attack_context=dict(
            required=False, type="str", choices=["disable", "enable"]),
        entries_log_packet=dict(required=False, type="str", choices=[
                                "disable", "enable"]),
        entries_os=dict(required=False, type="str"),
        entries_protocol=dict(required=False, type="str"),
        entries_quarantine=dict(required=False, type="str", choices=[
                                "none", "attacker"]),
        entries_quarantine_expiry=dict(required=False, type="str"),
        entries_quarantine_log=dict(
            required=False, type="str", choices=["disable", "enable"]),
        entries_rate_count=dict(required=False, type="int"),
        entries_rate_duration=dict(required=False, type="int"),
        entries_rate_mode=dict(required=False, type="str", choices=[
                               "periodical", "continuous"]),
        entries_rate_track=dict(required=False, type="str",
                                choices=["none", "src-ip", "dest-ip", "dhcp-client-mac", "dns-domain"]),
        entries_rule=dict(required=False, type="str"),
        entries_severity=dict(required=False, type="str"),
        entries_status=dict(required=False, type="str", choices=[
                            "disable", "enable", "default"]),

        entries_exempt_ip_dst_ip=dict(required=False, type="str"),
        entries_exempt_ip_src_ip=dict(required=False, type="str"),
        filter=dict(required=False, type="list"),
        filter_action=dict(required=False, type="str", choices=[
                           "pass", "block", "default", "reset"]),
        filter_application=dict(required=False, type="str"),
        filter_location=dict(required=False, type="str"),
        filter_log=dict(required=False, type="str",
                        choices=["disable", "enable"]),
        filter_log_packet=dict(required=False, type="str",
                               choices=["disable", "enable"]),
        filter_name=dict(required=False, type="str"),
        filter_os=dict(required=False, type="str"),
        filter_protocol=dict(required=False, type="str"),
        filter_quarantine=dict(required=False, type="str",
                               choices=["none", "attacker"]),
        filter_quarantine_expiry=dict(required=False, type="int"),
        filter_quarantine_log=dict(required=False, type="str", choices=[
                                   "disable", "enable"]),
        filter_severity=dict(required=False, type="str"),
        filter_status=dict(required=False, type="str", choices=[
                           "disable", "enable", "default"]),
        override=dict(required=False, type="list"),
        override_action=dict(required=False, type="str",
                             choices=["pass", "block", "reset"]),
        override_log=dict(required=False, type="str",
                          choices=["disable", "enable"]),
        override_log_packet=dict(required=False, type="str", choices=[
                                 "disable", "enable"]),
        override_quarantine=dict(required=False, type="str", choices=[
                                 "none", "attacker"]),
        override_quarantine_expiry=dict(required=False, type="int"),
        override_quarantine_log=dict(
            required=False, type="str", choices=["disable", "enable"]),
        override_rule_id=dict(required=False, type="str"),
        override_status=dict(required=False, type="str",
                             choices=["disable", "enable"]),

        override_exempt_ip_dst_ip=dict(required=False, type="str"),
        override_exempt_ip_src_ip=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "replacemsg-group": module.params["replacemsg_group"],
        "name": module.params["name"],
        "extended-log": module.params["extended_log"],
        "comment": module.params["comment"],
        "block-malicious-url": module.params["block_malicious_url"],
        "entries": {
            "action": module.params["entries_action"],
            "application": module.params["entries_application"],
            "location": module.params["entries_location"],
            "log": module.params["entries_log"],
            "log-attack-context": module.params["entries_log_attack_context"],
            "log-packet": module.params["entries_log_packet"],
            "os": module.params["entries_os"],
            "protocol": module.params["entries_protocol"],
            "quarantine": module.params["entries_quarantine"],
            "quarantine-expiry": module.params["entries_quarantine_expiry"],
            "quarantine-log": module.params["entries_quarantine_log"],
            "rate-count": module.params["entries_rate_count"],
            "rate-duration": module.params["entries_rate_duration"],
            "rate-mode": module.params["entries_rate_mode"],
            "rate-track": module.params["entries_rate_track"],
            "rule": module.params["entries_rule"],
            "severity": module.params["entries_severity"],
            "status": module.params["entries_status"],
            "exempt-ip": {
                "dst-ip": module.params["entries_exempt_ip_dst_ip"],
                "src-ip": module.params["entries_exempt_ip_src_ip"],
            },
        },
        "filter": {
            "action": module.params["filter_action"],
            "application": module.params["filter_application"],
            "location": module.params["filter_location"],
            "log": module.params["filter_log"],
            "log-packet": module.params["filter_log_packet"],
            "name": module.params["filter_name"],
            "os": module.params["filter_os"],
            "protocol": module.params["filter_protocol"],
            "quarantine": module.params["filter_quarantine"],
            "quarantine-expiry": module.params["filter_quarantine_expiry"],
            "quarantine-log": module.params["filter_quarantine_log"],
            "severity": module.params["filter_severity"],
            "status": module.params["filter_status"],
        },
        "override": {
            "action": module.params["override_action"],
            "log": module.params["override_log"],
            "log-packet": module.params["override_log_packet"],
            "quarantine": module.params["override_quarantine"],
            "quarantine-expiry": module.params["override_quarantine_expiry"],
            "quarantine-log": module.params["override_quarantine_log"],
            "rule-id": module.params["override_rule_id"],
            "status": module.params["override_status"],
            "exempt-ip": {
                "dst-ip": module.params["override_exempt_ip_dst_ip"],
                "src-ip": module.params["override_exempt_ip_src_ip"],
            }
        }
    }
    list_overrides = ['entries', 'filter', 'override']

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
    fmg = AnsibleFortiManager(
        module,
        module.params["host"],
        module.params["username"],
        module.params["password"])

    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    results = fmgr_ips_sensor_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(
            msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
