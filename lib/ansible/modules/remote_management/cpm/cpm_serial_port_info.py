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
# Module to retrieve WTI Serial Port Parameters from WTI OOB and PDU devices.
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
module: cpm_serial_port_info
version_added: "2.9"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get Serial port parameters in WTI OOB and PDU devices
description:
    - "Get Serial port parameters from WTI OOB and PDU devices"
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
      - This is the serial port number that is getting retrieved. It can include a single port
        number, multiple port numbers separated by commas, a list of port numbers, or an '*' character for all ports.
    required: true
    type: list
    default: ['*']
notes:
  - Use C(groups/cpm) in C(module_defaults) to set common options used between CPM modules.)
"""

EXAMPLES = """
- name: Get the Serial Port Parameters for port 2 of a WTI device
  cpm_serial_port_info:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    port: 2

- name: Get the Serial Port Parameters for ports 2 and 4 of a WTI device
  cpm_serial_port_info:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    port: 2,4

- name: Get the Serial Port Parameters for all ports of a WTI device
  cpm_serial_port_info:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    port: "*"
"""

RETURN = """
data:
  description: The output JSON returned from the commands sent
  returned: always
  type: complex
  contains:
    serialports:
      description: List of data for each serial port
      returned: success
      type: list
      sample:
        - baud: 4
          break: 1
          cmd: 1
          connstatus: Free
          echo: 1
          handshake: 2
          logoff: '^X'
          mode: 1
          parity: 3
          port: 2
          portname: switch
          seq: 2
          stopbits: 1
          tout: 0

        - baud: 3
          break: 1
          cmd: 1
          connstatus: Free
          echo: 1
          handshake: 2
          logoff: '^X'
          mode: 1
          parity: 1
          port: 4
          portname: router
          seq: 2
          stopbits: 1
          tout: 1
"""

import base64
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cpm_url=dict(type='str', required=True),
        cpm_username=dict(type='str', required=True),
        cpm_password=dict(type='str', required=True, no_log=True),
        port=dict(type='list', default=['*']),
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

    ports = module.params['port']
    if isinstance(ports, list):
        ports = ','.join(to_native(x) for x in ports)
    fullurl = ("%s%s/api/v2/config/serialports?ports=%s" % (protocol, to_native(module.params['cpm_url']), ports))

    try:
        response = open_url(fullurl, data=None, method='GET', validate_certs=module.params['validate_certs'], use_proxy=module.params['use_proxy'],
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

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
