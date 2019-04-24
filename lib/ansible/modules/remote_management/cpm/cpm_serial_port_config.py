#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (C) 2019 Red Hat Inc.
# Copyright (C) 2019 Western Telematic Inc.
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
# Module to execute WTI Serial Port Parameters on WTI OOB and PDU devices.
# CPM remote_management
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
module: cpm_serial_port_config
version_added: "2.9"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Set Serial port parameters in WTI OOB and PDU devices
description:
    - "Set Serial port parameters in WTI OOB and PDU devices"
options:
  cpm_url:
    description:
      - This is the URL of the WTI device to send the module.
    required: true
  cpm_username:
    description:
      - This is the Username of the WTI device to send the module.
    required: true
  cpm_password:
    description:
      - This is the Password of the WTI device to send the module.
    required: true
  use_https:
    description:
      - Designates to use an https connection or http connection.
    required: false
    type: bool
    default: true
  validate_certs:
    description:
      - If false, SSL certificates will not be validated. This should only be used
      - on personally controlled sites using self-signed certificates.
    required: false
    type: bool
    default: true
  use_proxy:
    description: Flag to control if the lookup will observe HTTP proxy environment variables when present.
    required: false
    type: bool
    default: false
  port:
    description:
      - This is the port number that is getting the action performed on.
    required: true
    type: int
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
      - This is the stop bits to assign to the port, 0=1 Stop Bit, 1=2 Stop Bit.
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
    choices: [ 1, 2, 3 ]
  tout:
    description:
      - This is the Port Activity Timeout to assign to the port, 0=Off, 1=5 Min, 2=15 Min, 3=30 Min, 4=90 Min, 5=1 Min.
    required: false
    choices: [ 0, 1, 2, 3, 4, 5 ]
  echo:
    description:
      -This is the command echo parameter to assign to the port, 0=Off, 1=On
    required: false
  break_allow:
    description:
      - This is if the break character is allowed to be passed through the port, 0=Off, 1=On
    required: false
  logoff:
    description:
      - This is the logout character to assign to the port
      - If preceded by a ^ character, the sequence will be a control character. Used if seq is set to 0 or 1
    required: false
notes:
  - Use C(groups/cpm) in C(module_defaults) to set common options used between CPM modules.
"""

EXAMPLES = """
# Set Serial Port Parameters
- name: Set the Port Parameters for port 2 of a WTI device
  cpm_serial_port_config:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    port: "2"
    portname: "RouterLabel"
    baud: "7"
    handshake: "1"
    stopbits: "0"
    parity: "0"
    mode: "0"
    cmd: "0"
    seq: "1"
    tout: "1"
    echo: "0"
    break_allow: "0"
    logoff: "^H"

# Set Serial Port Port Name and Baud Rate Parameters
- name: Set New port name and baud rate (115k) for port 4 of a WTI device
  cpm_serial_port_config:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    port: "4"
    portname: "NewPortName1"
    baud: "8"
"""

RETURN = """
data:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

import base64
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError


def assemble_json(cpmmodule, existing_serial):
    total_change = 0

    json_load = '{"serialports":{"port": "%s"' % to_native(cpmmodule.params["port"])

    if cpmmodule.params["portname"] is not None:
        if (existing_serial["serialports"][0]["portname"] != to_native(cpmmodule.params["portname"])):
            total_change = (total_change | 1)
            json_load = '%s,"portname": "%s"' % (json_load, to_native(cpmmodule.params["portname"]))
    if cpmmodule.params["baud"] is not None:
        if (existing_serial["serialports"][0]["baud"] != to_native(cpmmodule.params["baud"])):
            total_change = (total_change | 2)
            json_load = '%s,"baud": %s' % (json_load, to_native(cpmmodule.params["baud"]))
    if cpmmodule.params["handshake"] is not None:
        if (existing_serial["serialports"][0]["handshake"] != to_native(cpmmodule.params["handshake"])):
            total_change = (total_change | 4)
            json_load = '%s,"handshake": %s' % (json_load, to_native(cpmmodule.params["handshake"]))
    if cpmmodule.params["stopbits"] is not None:
        if (existing_serial["serialports"][0]["stopbits"] != to_native(cpmmodule.params["stopbits"])):
            total_change = (total_change | 8)
            json_load = '%s,"stopbits": %s' % (json_load, to_native(cpmmodule.params["stopbits"]))
    if cpmmodule.params["parity"] is not None:
        if (existing_serial["serialports"][0]["parity"] != to_native(cpmmodule.params["parity"])):
            total_change = (total_change | 16)
            json_load = '%s,"parity": %s' % (json_load, to_native(cpmmodule.params["parity"]))
    if cpmmodule.params["mode"] is not None:
        if (existing_serial["serialports"][0]["mode"] != to_native(cpmmodule.params["mode"])):
            total_change = (total_change | 32)
            json_load = '%s,"mode": %s' % (json_load, to_native(cpmmodule.params["mode"]))
    if cpmmodule.params["cmd"] is not None:
        if (existing_serial["serialports"][0]["cmd"] != to_native(cpmmodule.params["cmd"])):
            total_change = (total_change | 64)
            json_load = '%s,"cmd": %s' % (json_load, to_native(cpmmodule.params["cmd"]))
    if cpmmodule.params["seq"] is not None:
        if (existing_serial["serialports"][0]["seq"] != to_native(cpmmodule.params["seq"])):
            total_change = (total_change | 128)
            json_load = '%s,"seq": %s' % (json_load, to_native(cpmmodule.params["seq"]))
    if cpmmodule.params["tout"] is not None:
        if (existing_serial["serialports"][0]["tout"] != to_native(cpmmodule.params["tout"])):
            total_change = (total_change | 256)
            json_load = '%s,"tout": %s' % (json_load, to_native(cpmmodule.params["tout"]))
    if cpmmodule.params["echo"] is not None:
        if (int(existing_serial["serialports"][0]["echo"]) != int(cpmmodule.params["echo"])):
            total_change = (total_change | 512)
            json_load = '%s,"echo": %d' % (json_load, int(cpmmodule.params["echo"]))
    if cpmmodule.params["break_allow"] is not None:
        if (int(existing_serial["serialports"][0]["break"]) != int(cpmmodule.params["break_allow"])):
            total_change = (total_change | 1024)
            json_load = '%s,"break": %d' % (json_load, int(cpmmodule.params["break_allow"]))
    if cpmmodule.params["logoff"] is not None and (len(cpmmodule.params["logoff"]) > 0):
        if (existing_serial["serialports"][0]["logoff"] != to_native(cpmmodule.params["logoff"])):
            total_change = (total_change | 2048)
            json_load = '%s,"logoff": "%s"' % (json_load, to_native(cpmmodule.params["logoff"]))

    json_load = '%s}}' % (json_load)

    if (total_change == 0):
        json_load = None
    return json_load


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cpm_url=dict(type='str', required=True),
        cpm_username=dict(type='str', required=True),
        cpm_password=dict(type='str', required=True, no_log=True),
        port=dict(type='int', required=True),
        portname=dict(type='str', required=False, default=None),
        baud=dict(type='int', required=False, default=None, choices=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        handshake=dict(type='int', required=False, default=None, choices=[0, 1, 2, 3]),
        stopbits=dict(type='int', required=False, default=None, choices=[0, 1]),
        parity=dict(type='int', required=False, default=None, choices=[0, 1, 2, 3, 4, 5]),
        mode=dict(type='int', required=False, default=None, choices=[0, 1, 2, 3, 4]),
        cmd=dict(type='int', required=False, default=None, choices=[0, 1]),
        seq=dict(type='int', required=False, default=None, choices=[1, 2, 3]),
        tout=dict(type='int', required=False, default=None, choices=[0, 1, 2, 3, 4, 5]),
        echo=dict(type='bool', required=False, default=None),
        break_allow=dict(type='bool', required=False),
        logoff=dict(type='str', required=False, default=None),
        use_https=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
        use_proxy=dict(type='bool', default=False)
    )

    result = dict(
        changed=False,
        data=''
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    auth = to_text(base64.b64encode(to_bytes('{0}:{1}'.format(to_native(module.params['cpm_username']), to_native(module.params['cpm_password'])),
                   errors='surrogate_or_strict')))

    if module.params['use_https'] is True:
        protocol = "https://"
    else:
        protocol = "http://"

    fullurl = ("%s%s/api/v2/config/serialports?ports=%s" % (protocol, to_native(module.params['cpm_url']), to_native(module.params['port'])))
    method = 'GET'
    try:
        response = open_url(fullurl, data=None, method=method, validate_certs=module.params['validate_certs'], use_proxy=module.params['use_proxy'],
                            headers={'Content-Type': 'application/json', 'Authorization': "Basic %s" % auth})

    except HTTPError as e:
        fail_json = dict(msg='GET: Received HTTP error for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except URLError as e:
        fail_json = dict(msg='GET: Failed lookup url for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except SSLValidationError as e:
        fail_json = dict(msg='GET: Error validating the server''s certificate for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except ConnectionError as e:
        fail_json = dict(msg='GET: Error connecting to {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)

    result['data'] = json.loads(response.read())
    payload = assemble_json(module, result['data'])

    if module.check_mode:
        if payload is not None:
            result['changed'] = True
    else:
        if payload is not None:
            fullurl = ("%s%s/api/v2/config/serialports" % (protocol, to_native(module.params['cpm_url'])))
            method = 'POST'

            try:
                response = open_url(fullurl, data=payload, method=method, validate_certs=module.params['validate_certs'], use_proxy=module.params['use_proxy'],
                                    headers={'Content-Type': 'application/json', 'Authorization': "Basic %s" % auth})

            except HTTPError as e:
                fail_json = dict(msg='POST: Received HTTP error for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
                module.fail_json(**fail_json)
            except URLError as e:
                fail_json = dict(msg='POST: Failed lookup url for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
                module.fail_json(**fail_json)
            except SSLValidationError as e:
                fail_json = dict(msg='POST: Error validating the server''s certificate for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
                module.fail_json(**fail_json)
            except ConnectionError as e:
                fail_json = dict(msg='POST: Error connecting to {0} : {1}'.format(fullurl, to_native(e)), changed=False)
                module.fail_json(**fail_json)

            result['changed'] = True
            result['data'] = json.loads(response.read())

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
