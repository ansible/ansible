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

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fsm_send_syslog
version_added: "2.8"
author: Luke Weighall (@lweighall)
short_description: Sends a text string to FortiSIEM as a Syslog
description:
  - Used to send events/logs/errors to FortiSIEM for any purpose.
  - Can be used to send alerts from non-connected systems, or from any ansible playbook.

options:
  syslog_host:
    description:
      - The FortiSIEM's FQDN or IP Address.
    required: true
    
  ignore_ssl_errors:
    description:
      - When Enabled this will instruct the HTTP Libraries to ignore any ssl validation errors.
      - Also will ignore any errors when network_protocol = TCP
    required: false
    default: "enable"
    options: ["enable", "disable"]
    
  network_protocol:
    description:
      - Handles how the syslog is transmitted. TCP or UDP, with or without TLS 1.2.
    required: false
    default: "udp"
    options: ["udp", "tcp", "tcp-tls1.2"]
    
  network_port:
    description:
      - Handles which port to send the log on, TCP or UDP. Default 514
    required: false
    default: 514
    
  syslog_message:
    description:
      - The actual message to send.
    required: true

  syslog_header:
    description:
      - If defined, will be used as the syslog header after the priority <##> (we specify that for you)
      - If left empty, we generate a header for you.
    required: false
    
'''


EXAMPLES = '''
- name: SEND UDP/514 SYSLOG WITH AUTO HEADER
  fsm_send_syslog:
    host: "10.0.0.15"
    ignore_ssl_errors: "enable"
    syslog_message: "This is a test syslog from Ansible!"

- name: SEND UDP/514 SYSLOG WITH AUTO HEADER
    fsm_send_syslog:
      syslog_host: "10.7.220.61"
      ignore_ssl_errors: "enable"
      syslog_message: "This is a test syslog from Ansible!"
      
- name: SEND UDP/514 SYSLOG CUSTOM HEADER
  fsm_send_syslog:
    syslog_host: "10.7.220.61"
    ignore_ssl_errors: "enable"
    syslog_message: "This is a test syslog from Ansible!"
    syslog_header: "This is a TEST HEADER :"

- name: SEND TCP/1470 SYSLOG WITH CUSTOM HEADER
  fsm_send_syslog:
    syslog_host: "10.7.220.61"
    ignore_ssl_errors: "enable"
    network_port: 1470
    network_protocol: "tcp"
    syslog_message: "This is a test syslog from Ansible!"
    syslog_header: "This is a TEST HEADER TCP PORT 1470 :"

- name: SEND TCP/6514 TLS SYSLOG WITH CUSTOM HEADER
  fsm_send_syslog:
    syslog_host: "10.7.220.61"
    ignore_ssl_errors: "enable"
    network_port: 6514
    network_protocol: "tcp-tls1.2"
    syslog_message: "This is a test syslog from Ansible!"
    syslog_header: "This is a TEST HEADER TCP TLS PORT 6514 :"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: string
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.fortisiem.common import FSMBaseException
from ansible.module_utils.network.fortisiem.common import DEFAULT_EXIT_MSG
from ansible.module_utils.network.fortisiem.fortisiem import FortiSIEMHandler


def main():
    argument_spec = dict(
        syslog_host=dict(required=True, type="str"),
        ignore_ssl_errors=dict(required=False, type="str", choices=["enable", "disable"], default="enable"),

        network_protocol=dict(required=False, type="str", default="udp",
                              choices=["udp", "tcp", "tcp-tls1.2"]),
        network_port=dict(required=False, type="int", default=0),
        syslog_message=dict(required=False, type="str"),
        syslog_header=dict(required=False, type="str", default=None),

    )
    module = AnsibleModule(argument_spec, supports_check_mode=False)

    paramgram = {
        "syslog_host": module.params["syslog_host"],
        "ignore_ssl_errors": module.params["ignore_ssl_errors"],

        "network_protocol": module.params["network_protocol"],
        "network_port": module.params["network_port"],
        "syslog_message": module.params["syslog_message"],
        "syslog_header": module.params["syslog_header"],
    }

    if paramgram["network_port"] == 0:
        if paramgram["network_protocol"] == "udp":
            paramgram["network_port"] = 514
        if paramgram["network_protocol"] == "tcp":
            paramgram["network_port"] = 1470
        if paramgram["network_protocol"] == "tcp-tls1.2":
            paramgram["network_port"] = 6514
        if paramgram["network_protocol"] == "udp-tls1.2":
            paramgram["network_port"] = 6514

    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fsm = None
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))

    if not paramgram["syslog_header"]:
        paramgram["syslog_header"] = str(fsm.get_current_datetime() + " ansible_module:fsm_send_syslog")
        module.paramgram = paramgram

    # EXECUTE THE MODULE OPERATION
    results = DEFAULT_EXIT_MSG
    try:
        results = fsm.handle_syslog_request()
    except BaseException as err:
        raise FSMBaseException(err)

    return module.exit_json(msg=str(results["message"]), results=str(results["status"]))


if __name__ == "__main__":
    main()
