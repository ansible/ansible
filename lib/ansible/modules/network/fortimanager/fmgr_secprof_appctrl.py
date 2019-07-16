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
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
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
      name: "Ansible_Application_Control_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_appctrl:
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


def fmgr_application_list_modify(fmgr, paramgram):
    """
    fmgr_application_list -- Modifies Application Control Profiles on FortiManager

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if paramgram["mode"] in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/application/list'.format(adom=paramgram["adom"])
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif paramgram["mode"] == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/application/list/{name}'.format(adom=paramgram["adom"],
                                                                          name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
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
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
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
    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    list_overrides = ['entries']
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)

    results = DEFAULT_RESULT_OBJ
    try:
        results = fmgr_application_list_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
