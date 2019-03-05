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
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
  - Luke Weighall (@lweighall)
  - Andrew Welsh (@Ghilli3)
  - Jim Huber (@p4r4n0y1ng)
short_description: Managing IPS security profiles in FortiManager
description:
  - Managing IPS security profiles in FortiManager

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

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
    required: false
    choices:
      - disable
      - enable

  comment:
    description:
      - Comment.
    required: false

  block_malicious_url:
    description:
      - Enable/disable malicious URL blocking.
    required: false
    choices:
      - disable
      - enable

  entries:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  entries_action:
    description:
      - Action taken with traffic in which signatures are detected.
    required: false
    choices:
      - pass
      - block
      - reset
      - default

  entries_application:
    description:
      - Applications to be protected. set application ? lists available applications. all includes
        all applications. other includes all unlisted applications.
    required: false

  entries_location:
    description:
      - Protect client or server traffic.
    required: false

  entries_log:
    description:
      - Enable/disable logging of signatures included in filter.
    required: false
    choices:
      - disable
      - enable

  entries_log_attack_context:
    description:
      - Enable/disable logging of attack context| URL buffer, header buffer, body buffer, packet buffer.
    required: false
    choices:
      - disable
      - enable

  entries_log_packet:
    description:
      - Enable/disable packet logging. Enable to save the packet that triggers the filter. You can
        download the packets in pcap format for diagnostic use.
    required: false
    choices:
      - disable
      - enable

  entries_os:
    description:
      - Operating systems to be protected.  all includes all operating systems. other includes all
        unlisted operating systems.
    required: false

  entries_protocol:
    description:
      - Protocols to be examined. set protocol ? lists available protocols. all includes all protocols.
        other includes all unlisted protocols.
    required: false

  entries_quarantine:
    description:
      - Quarantine method.
    required: false
    choices:
      - none
      - attacker

  entries_quarantine_expiry:
    description:
      - Duration of quarantine.
    required: false

  entries_quarantine_log:
    description:
      - Enable/disable quarantine logging.
    required: false
    choices:
      - disable
      - enable

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
    required: false
    choices:
      - periodical
      - continuous

  entries_rate_track:
    description:
      - Track the packet protocol field.
    required: false
    choices:
      - none
      - src-ip
      - dest-ip
      - dhcp-client-mac
      - dns-domain

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
      - Status of the signatures included in filter. default enables the filter and only use filters
        with default status of enable. Filters with default status of disable will not be used.
    required: false
    choices:
      - disable
      - enable
      - default

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
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  filter_action:
    description:
      - Action of selected rules.
    required: false
    choices:
      - pass
      - block
      - default
      - reset

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
    required: false
    choices:
      - disable
      - enable

  filter_log_packet:
    description:
      - Enable/disable packet logging of selected rules.
    required: false
    choices:
      - disable
      - enable

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
    required: false
    choices:
      - none
      - attacker

  filter_quarantine_expiry:
    description:
      - Duration of quarantine in minute.
    required: false

  filter_quarantine_log:
    description:
      - Enable/disable logging of selected quarantine.
    required: false
    choices:
      - disable
      - enable

  filter_severity:
    description:
      - Vulnerability severity filter.
    required: false

  filter_status:
    description:
      - Selected rules status.
    required: false
    choices:
      - disable
      - enable
      - default

  override:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  override_action:
    description:
      - Action of override rule.
    required: false
    choices:
      - pass
      - block
      - reset

  override_log:
    description:
      - Enable/disable logging.
    required: false
    choices:
      - disable
      - enable

  override_log_packet:
    description:
      - Enable/disable packet logging.
    required: false
    choices:
      - disable
      - enable

  override_quarantine:
    description:
      - Quarantine IP or interface.
    required: false
    choices:
      - none
      - attacker

  override_quarantine_expiry:
    description:
      - Duration of quarantine in minute.
    required: false

  override_quarantine_log:
    description:
      - Enable/disable logging of selected quarantine.
    required: false
    choices:
      - disable
      - enable

  override_rule_id:
    description:
      - Override rule ID.
    required: false

  override_status:
    description:
      - Enable/disable status of override rule.
    required: false
    choices:
      - disable
      - enable

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
      name: "Ansible_IPS_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_ips:
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
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict


###############
# START METHODS
###############


def fmgr_ips_sensor_modify(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/ips/sensor'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/ips/sensor/{name}'.format(
            adom=adom, name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])

    return response


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
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

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
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
    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    list_overrides = ['entries', 'filter', 'override']

    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)

    results = DEFAULT_RESULT_OBJ
    try:
        results = fmgr_ips_sensor_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
