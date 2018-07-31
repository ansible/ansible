#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (C) 2018 Red Hat Inc.
# Copyright (C) 2018 Western Telematic Inc.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Module to execute WTI Port Commands on WTI OOB and PDU devices.
# WTI Networking
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: wti_ports
version_added: "2.7"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get and Set port parameters in WTI OOB and PDU devices
description:
    - "Get and Set port parameters in WTI OOB and PDU devices"
options:
  wti_action:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "getport", "setport" ]
  wti_url:
    description:
      - This is the URL of the WTI device  to send the module.
    required: true
  wti_username:
    description:
      - This is the Username of the WTI device to send the module.
    required: true
  wti_password:
    description:
      - This is the Password of the WTI device to send the module.
    required: true
  use_https:
    description:
      - Designates to use an https connection or http connection.
    required: false
    default: True
    choices: [ True, False ]
  port:
    description:
      - This is the port number that is getting the action performed on.
    required: true
  portname:
    description:
      - This is the Name of the Port that is displayed.
    required: false
  baud:
    description:
      - This is the baud rate to assign to the port.
      - 0=300, 1=1200, 2=2400, 3=4800, 4=9600, 5=19200, 6=38400, 7=57600, 8=115200, 9=230400, 10=460800
    required: false
    choices: [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ]
  handshake:
    description:
      - This is the handshake to assign to the port, 0=None, 1=XON/XOFF, 2=RTS/CTS, 3=Both.
    required: false
    choices: [ 0, 1, 2, 3 ]
  stopbits:
    description:
      - This is the stop bits to assign to the port, 0=1 Stop Bit, 1=1 Stop Bit.
    required: false
    choices: [ 0, 1 ]
  parity:
    description:
      - This is the parity to assign to the port, 0=7-None, 1=7-Even, 2=7-Odd, 3=8-None, 4=8-Even, 5=8-Odd.
    required: false
    choices: [ 0, 1, 2, 3, 4, 5 ]
  mode:
    description:
      - This is the port mode to assign to the port, 0=Any-to-Any. 1=Passive, 2=Buffer, 3=Modem, 4=ModemPPP.
    required: false
    choices: [ 0, 1, 2, 3, 4 ]
  cmd:
    description:
      - This is the Admin Mode to assign to the port, 0=Deny, 1=Permit.
    required: false
    choices: [ 0, 1 ]
  seq:
    description:
      - This is the type of Sequence Disconnect to assign to the port, 0=Three Characters (before and after), 1=One Character Only, 2=Off
    required: false
    choices: [ 0, 1, 2 ]
  tout:
    description:
      - This is the Port Activity Timeout to assign to the port, 0=Off, 1=5 Min, 2=15 Min, 3=30 Min, 4=90 Min, 5=1 Min.
    required: false
    choices: [ 0, 1, 2, 3, 4, 5 ]
  echo:
    description:
      -This is the command echo parameter to assign to the port, 0=Off, 1=On
    required: false
    choices: [ 0, 1 ]
  break:
    description:
      - This is the how to handle a break character for the port, . 0=No, 1=Yes
    required: false
    choices: [ 0, 1 ]
  logoff:
    description:
      - This is the logout character to assign to the port
      - If preceded by a ^ character, the sequence will be a control character. Used if seq is set to 0 or 1
    required: false
"""

EXAMPLES = """
# Get Port Parameters
- name: Get the Port Parameters for port 2 of a WTI device
  wti_ports:
    wti_action: "getport"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    port: "2"

# Get Port Parameters
- name: Set the Port Parameters for port 2 of a WTI device
  wti_ports:
    wti_action: "setport"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    port: 2,
    portname: "RouterLabel",
    baud: 7,
    handshake: 1,
    stopbits: 0,
    parity: 0,
    mode: 0,
    cmd: 0,
    seq: 1,
    tout: 1,
    echo: 0,
    break: 0,
    logoff: "^H"
"""

RETURN = """
data:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

from ansible.module_utils.network.wti.wti_common import request
from ansible.module_utils.basic import AnsibleModule


def assemble_json(wtimodule):

    if wtimodule.params["serial_port"] is not None and (len(wtimodule.params["serial_port"]) > 0):
        json_load = '{"serialports":'

        json_load = json_load + '{"port": "'+wtimodule.params["serial_port"]+'"'

        if wtimodule.params["serial_portname"] is not None:
                json_load = json_load + ',"portname": "'+str(wtimodule.params["serial_portname"])+'"'
        if wtimodule.params["serial_baud"] is not None:
            if 0 <= wtimodule.params["serial_baud"] <= 9:
                json_load = json_load + ',"baud": '+str(wtimodule.params["serial_baud"])+''
        if wtimodule.params["serial_handshake"] is not None:
            if 0 <= wtimodule.params["serial_handshake"] <= 1:
                json_load = json_load + ',"handshake": '+str(wtimodule.params["serial_handshake"])+''
        if wtimodule.params["serial_stopbits"] is not None:
            if 0 <= wtimodule.params["serial_stopbits"] <= 1:
                json_load = json_load + ',"stopbits": '+str(wtimodule.params["serial_stopbits"])+''
        if wtimodule.params["serial_parity"] is not None:
            if 0 <= wtimodule.params["serial_parity"] <= 1:
                json_load = json_load + ',"parity": '+str(wtimodule.params["serial_parity"])+''
        if wtimodule.params["serial_mode"] is not None:
            if 0 <= wtimodule.params["serial_mode"] <= 1:
                json_load = json_load + ',"mode": '+str(wtimodule.params["serial_mode"])+''
        if wtimodule.params["serial_cmd"] is not None:
            if 0 <= wtimodule.params["serial_cmd"] <= 1:
                json_load = json_load + ',"cmd": '+str(wtimodule.params["serial_cmd"])+''
        if wtimodule.params["serial_seq"] is not None:
            if 1 <= wtimodule.params["serial_seq"] <= 3:
                json_load = json_load + ',"seq": '+str(wtimodule.params["serial_seq"])+''
        if wtimodule.params["serial_tout"] is not None:
            if 0 <= wtimodule.params["serial_tout"] <= 1:
                json_load = json_load + ',"tout": '+str(wtimodule.params["serial_tout"])+''
        if wtimodule.params["serial_echo"] is not None:
            if 0 <= wtimodule.params["serial_echo"] <= 1:
                json_load = json_load + ',"echo": '+str(wtimodule.params["serial_echo"])+''
        if wtimodule.params["serial_break"] is not None:
            if 0 <= wtimodule.params["serial_break"] <= 1:
                json_load = json_load + ',"break": '+str(wtimodule.params["serial_break"])+''

        if wtimodule.params["serial_logoff"] is not None and (len(wtimodule.params["serial_logoff"]) > 0):
            json_load = json_load + ',"logoff": "'+str(wtimodule.params["serial_logoff"])+'"'

        json_load = json_load + '}'
        json_load = json_load + '}'
        return json_load
    else:
        wtimodule.fail_json(msg='serial_port not defined.', **result)

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        name=dict(type='str', required=False),
        wti_action=dict(choices=['getport', 'setport'], required=True),
        wti_url=dict(type='str', required=True),
        wti_username=dict(type='str', required=True),
        wti_password=dict(type='str', required=True, no_log=True),
        serial_port=dict(type='str', required=True, default=None),
        serial_portname=dict(type='str', required=False, default=None),
        serial_baud=dict(type='int', required=False, default=None),
        serial_handshake=dict(type='int', required=False, default=None),
        serial_stopbits=dict(type='int', required=False, default=None),
        serial_parity=dict(type='int', required=False, default=None),
        serial_mode=dict(type='int', required=False, default=None),
        serial_cmd=dict(type='int', required=False, default=None),
        serial_seq=dict(type='int', required=False, default=None),
        serial_tout=dict(type='int', required=False, default=None),
        serial_echo=dict(type='int', required=False, default=None),
        serial_break=dict(type='int', required=False, default=None),
        serial_logoff=dict(type='str', required=False, default=None),
        use_https=dict(type='bool', default=True)
    )


    result = dict(
        changed=False,
        data=''
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        return result

    if module.params['use_https'] is True:
        protocol = "https://"
    else:
        protocol = "http://"

    if (module.params['wti_action'] == 'getport'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/serialports?ports="+str(module.params['serial_port']), module.params['wti_username'], module.params['wti_password'], 8)
    elif (module.params['wti_action'] == 'setport'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/serialports", module.params['wti_username'], module.params['wti_password'], 8, assemble_json(module), 'POST')
        result['changed'] = True
    else:
        module.fail_json(msg='Command not recognized.', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
