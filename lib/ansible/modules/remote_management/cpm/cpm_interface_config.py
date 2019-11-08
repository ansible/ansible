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
# Module to execute WTI network interface Parameters on WTI OOB and PDU devices.
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
module: cpm_interface_config
version_added: "2.10"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Set network interface parameters in WTI OOB and PDU devices
description:
    - "Set network interface parameters in WTI OOB and PDU devices"
options:
  cpm_url:
    description:
      - This is the URL of the WTI device to send the module.
    required: true
    type: str
  cpm_username:
    description:
      - This is the Username of the WTI device to send the module.
    required: true
    type: str
  cpm_password:
    description:
      - This is the Password of the WTI device to send the module.
    required: true
    type: str
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
  interface:
    description:
      - This is the ethernet port name that is getting configured.
    required: false
    type: str
  negotiation:
    description:
      - This is the speed of the interface port being configured.
      - 0=Auto, 1=10/half, 2=10/full, 3=100/half, 4=100/full, 5=1000/half, 6=1000/full
    required: false
    type: int
    choices: [ 0, 1, 2, 3, 4, 5, 6 ]
  ipv4address:
    description:
      - IPv4 format IP address for the defined interface Port.
    required: false
    type: str
  ipv4netmask:
    description:
      - IPv4 format Netmask for the defined interface Port.
    required: false
    type: str
  ipv4gateway:
    description:
      - IPv4 format Gateway address for the defined interface Port.
    required: false
    type: str
  ipv4dhcpenable:
    description:
      - Enable IPv4 DHCP request call to obtain confufuration information.
    required: false
    type: int
    choices: [ 0, 1 ]
  ipv4dhcphostname:
    description:
      - Define IPv4 DHCP Hostname.
    required: false
    type: str
  ipv4dhcplease:
    description:
      - IPv4 DHCP Lease Time.
    required: false
    type: int
  ipv4dhcpobdns:
    description:
      - IPv6 DHCP Obtain DNS addresses auto.
    required: false
    type: int
    choices: [ 0, 1 ]
  ipv4dhcpupdns:
    description:
      - IPv4 DHCP DNS Server Update.
    required: false
    type: int
    choices: [ 0, 1 ]
  ipv4dhcpdefgateway:
    description:
      - Enable or Disable this ports configuration as the default IPv4 route for the device.
    required: false
    type: int
    choices: [ 0, 1 ]
  ipv6address:
    description:
      - IPv6 format IP address for the defined interface Port.
    required: false
    type: str
  ipv6subnetprefix:
    description:
      - IPv6 format Subnet Prefix for the defined interface Port.
    required: false
    type: str
  ipv6gateway:
    description:
      - IPv6 format Gateway address for the defined interface Port.
    required: false
    type: str
notes:
  - Use C(groups/cpm) in C(module_defaults) to set common options used between CPM modules.
"""

EXAMPLES = """
# Set Network Interface Parameters
- name: Set the Interface Parameters for port eth1 of a WTI device
  cpm_interface_config:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    interface: "eth1"
    ipv4address: "192.168.0.14"
    ipv4netmask: "255.255.255.0"
    ipv4gateway: "192.168.0.1"
    negotiation: 0

# Set Network Interface Parameters
- name: Set the Interface Parameters for port eth1 to DHCP of a WTI device
  cpm_interface_config:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    interface: "eth1"
    negotiation: 0
    ipv4dhcpenable: 1
    ipv4dhcphostname: ""
    ipv4dhcplease: -1
    ipv4dhcpobdns: 0
    ipv4dhcpupdns: 0
    ipv4dhcpdefgateway: 0
"""

RETURN = """
data:
  description: The output JSON returned from the commands sent
  returned: always
  type: complex
  contains:
    totalports:
      description: Total interface ports requested of the WTI device.
      returned: success
      type: int
      sample: 1
    interface:
      description: Current k/v pairs of interface info for the WTI device after module execution.
      returned: always
      type: dict
      sample: {"name": "eth1", "type": "0", "mac_address": "00-09-9b-02-45-db", "is_up": "0", "is_gig": "1", "speed": "10", "negotiation": "0",
              "ietf-ipv4": {"address": [{"ip": "10.10.10.2","netmask": "255.255.255.0","gateway": ""}],
              "dhcpclient": [{"enable": 0, "hostname": "", "lease": -1, "obdns": 1, "updns": 1}]},
              "ietf-ipv6": {"address": [{"ip": "", "netmask": "", "gateway": "" }]}}
"""

import base64
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError


def assemble_json(cpmmodule, existing_interface):
    total_change = protocol = 0
    json_load = ietfstring = negotiation = None

    address = []
    netmask = []
    gateway = []
    dhcphostname = []
    dhcpenable = []
    dhcplease = []
    dhcpobdns = []
    dhcpupdns = []
    dhcpdefgateway = []

    for x in range(0, 2):
        address.insert(x, None)
        netmask.insert(x, None)
        gateway.insert(x, None)
        dhcpenable.insert(x, None)
        dhcphostname.insert(x, None)
        dhcplease.insert(x, None)
        dhcpobdns.insert(x, None)
        dhcpupdns.insert(x, None)
        dhcpdefgateway.insert(x, None)

    if existing_interface["totalports"] is not None:
        if (existing_interface["totalports"] != 1):
            return None

    # make sure we are working with the correct ethernet port
    if (existing_interface["interface"][0]["name"] != to_native(cpmmodule.params["interface"])):
        return None

    if cpmmodule.params["negotiation"] is not None:
        if (int(existing_interface["interface"][0]["negotiation"]) != cpmmodule.params["negotiation"]):
            total_change = (total_change | 1)
            negotiation = to_native(cpmmodule.params["negotiation"])

    if cpmmodule.params["ipv4address"] is not None:
        if (existing_interface["interface"][0]["ietf-ipv4"]["address"][0]["ip"] != cpmmodule.params["ipv4address"]):
            total_change = (total_change | 2)
            address.insert(protocol, to_native(cpmmodule.params["ipv4address"]))

    if cpmmodule.params["ipv4netmask"] is not None:
        if (existing_interface["interface"][0]["ietf-ipv4"]["address"][0]["netmask"] != cpmmodule.params["ipv4netmask"]):
            total_change = (total_change | 4)
            netmask.insert(protocol, to_native(cpmmodule.params["ipv4netmask"]))

    if cpmmodule.params["ipv4gateway"] is not None:
        if (existing_interface["interface"][0]["ietf-ipv4"]["address"][0]["gateway"] != cpmmodule.params["ipv4gateway"]):
            total_change = (total_change | 8)
            gateway.insert(protocol, to_native(cpmmodule.params["ipv4gateway"]))

    if cpmmodule.params["ipv4dhcpenable"] is not None:
        if (int(existing_interface["interface"][0]["ietf-ipv4"]["dhcpclient"][0]["enable"]) != cpmmodule.params["ipv4dhcpenable"]):
            total_change = (total_change | 16)
            dhcpenable.insert(protocol, to_native(cpmmodule.params["ipv4dhcpenable"]))

    if cpmmodule.params["ipv4dhcphostname"] is not None:
        if (existing_interface["interface"][0]["ietf-ipv4"]["dhcpclient"][0]["hostname"] != cpmmodule.params["ipv4dhcphostname"]):
            total_change = (total_change | 32)
            dhcphostname.insert(protocol, to_native(cpmmodule.params["ipv4dhcphostname"]))

    if cpmmodule.params["ipv4dhcplease"] is not None:
        if (int(existing_interface["interface"][0]["ietf-ipv4"]["dhcpclient"][0]["lease"]) != cpmmodule.params["ipv4dhcplease"]):
            total_change = (total_change | 64)
            dhcplease.insert(protocol, to_native(cpmmodule.params["ipv4dhcplease"]))

    if cpmmodule.params["ipv4dhcpobdns"] is not None:
        if (int(existing_interface["interface"][0]["ietf-ipv4"]["dhcpclient"][0]["obdns"]) != cpmmodule.params["ipv4dhcpobdns"]):
            total_change = (total_change | 128)
            dhcpobdns.insert(protocol, to_native(cpmmodule.params["ipv4dhcpobdns"]))

    if cpmmodule.params["ipv4dhcpupdns"] is not None:
        if (int(existing_interface["interface"][0]["ietf-ipv4"]["dhcpclient"][0]["updns"]) != cpmmodule.params["ipv4dhcpupdns"]):
            total_change = (total_change | 256)
            dhcpupdns.insert(protocol, to_native(cpmmodule.params["ipv4dhcpupdns"]))

    if cpmmodule.params["ipv4dhcpdefgateway"] is not None:
        if (int(existing_interface["interface"][0]["ietf-ipv4"]["address"][0]["defgateway"]) != cpmmodule.params["ipv4dhcpdefgateway"]):
            total_change = (total_change | 512)
            dhcpdefgateway.insert(protocol, to_native(cpmmodule.params["ipv4dhcpdefgateway"]))

    protocol += 1

    if cpmmodule.params["ipv6address"] is not None:
        if (existing_interface["interface"][0]["ietf-ipv6"]["address"][0]["ip"] != cpmmodule.params["ipv6address"]):
            total_change = (total_change | 2)
            address.insert(protocol, to_native(cpmmodule.params["ipv6address"]))

    if cpmmodule.params["ipv6subnetprefix"] is not None:
        if (existing_interface["interface"][0]["ietf-ipv6"]["address"][0]["netmask"] != cpmmodule.params["ipv6subnetprefix"]):
            total_change = (total_change | 4)
            netmask.insert(protocol, to_native(cpmmodule.params["ipv6subnetprefix"]))

    if cpmmodule.params["ipv6gateway"] is not None:
        if (existing_interface["interface"][0]["ietf-ipv6"]["address"][0]["gateway"] != cpmmodule.params["ipv6gateway"]):
            total_change = (total_change | 8)
            gateway.insert(protocol, to_native(cpmmodule.params["ipv6gateway"]))

    if (total_change > 0):
        protocol = protocolchanged = 0
        json_load = '{"interface": [ { "name": "%s"' % (to_native(cpmmodule.params["interface"]))

        if (negotiation is not None):
            json_load = '%s,"negotiation": "%s"' % (json_load, negotiation)

        for protocol in range(0, 2):
            protocolchanged = 0
            if ((address[protocol] is not None) or (netmask[protocol] is not None) or (gateway[protocol] is not None) or
                    (dhcpdefgateway[protocol] is not None)):
                protocolchanged += 1
                ietfstring = ""

                if (address[protocol] is not None):
                    ietfstring = '%s"ip": "%s"' % (ietfstring, address[protocol])

                if (netmask[protocol] is not None):
                    if (len(ietfstring) > 0):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s"netmask": "%s"' % (ietfstring, netmask[protocol])

                if (gateway[protocol] is not None):
                    if (len(ietfstring) > 0):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s"gateway": "%s"' % (ietfstring, gateway[protocol])

                if (dhcpdefgateway[protocol] is not None):
                    if (len(ietfstring) > 0):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s"defgateway": %s' % (ietfstring, dhcpdefgateway[protocol])

                if (protocolchanged > 0):
                    if (protocol == 0):
                        json_load = '%s,"ietf-ipv4": { ' % (json_load)
                    else:
                        json_load = '%s,"ietf-ipv6": { ' % (json_load)

                    json_load = '%s"address": [ {' % (json_load)

                json_load = '%s%s}]' % (json_load, ietfstring)

            if ((dhcphostname[protocol] is not None) or (dhcpenable[protocol] is not None) or (dhcplease[protocol] is not None) or
                    (dhcpobdns[protocol] is not None) or (dhcpupdns[protocol] is not None)):
                if (protocolchanged == 0):
                    if (protocol == 0):
                        json_load = '%s,"ietf-ipv4": { ' % (json_load)
                    else:
                        json_load = '%s,"ietf-ipv6": { ' % (json_load)
                else:
                    json_load = '%s,' % (json_load)

                protocolchanged += 1
                ietfstring = ""
                json_load = '%s"dhcpclient": [ {' % (json_load)

                if (dhcpenable[protocol] is not None):
                    if (len(ietfstring) > 0):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s"enable": %s' % (ietfstring, dhcpenable[protocol])

                if (dhcphostname[protocol] is not None):
                    if (len(ietfstring) > 0):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s"hostname": "%s"' % (ietfstring, dhcphostname[protocol])

                if (dhcplease[protocol] is not None):
                    if (len(ietfstring) > 0):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s"lease": %s' % (ietfstring, dhcplease[protocol])

                if (dhcpobdns[protocol] is not None):
                    if (len(ietfstring) > 0):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s"obdns": %s' % (ietfstring, dhcpobdns[protocol])

                if (dhcpupdns[protocol] is not None):
                    if (len(ietfstring) > 0):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s"updns": %s' % (ietfstring, dhcpupdns[protocol])

                # end of dhcpclient
                json_load = '%s%s}]' % (json_load, ietfstring)

            # end of ietf-ipv4
            if (protocolchanged > 0):
                json_load = '%s}' % (json_load)

        # end of interface
        json_load = '%s}]' % (json_load)
        json_load = '%s}' % (json_load)
    return json_load


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cpm_url=dict(type='str', required=True),
        cpm_username=dict(type='str', required=True),
        cpm_password=dict(type='str', required=True, no_log=True),
        interface=dict(type='str', required=True),
        negotiation=dict(type='int', required=False, default=None, choices=[0, 1, 2, 3, 4, 5, 6]),
        ipv4address=dict(type='str', required=False, default=None),
        ipv4netmask=dict(type='str', required=False, default=None),
        ipv4gateway=dict(type='str', required=False, default=None),
        ipv4dhcpenable=dict(type='int', required=False, default=None, choices=[0, 1]),
        ipv4dhcphostname=dict(type='str', required=False, default=None),
        ipv4dhcplease=dict(type='int', required=False, default=None),
        ipv4dhcpobdns=dict(type='int', required=False, default=None, choices=[0, 1]),
        ipv4dhcpupdns=dict(type='int', required=False, default=None, choices=[0, 1]),
        ipv4dhcpdefgateway=dict(type='int', required=False, default=None, choices=[0, 1]),
        ipv6address=dict(type='str', required=False, default=None),
        ipv6subnetprefix=dict(type='str', required=False, default=None),
        ipv6gateway=dict(type='str', required=False, default=None),
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

    fullurl = ("%s%s/api/v2/config/interface?ports=%s" % (protocol, to_native(module.params['cpm_url']), to_native(module.params['interface'])))
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
            fullurl = ("%s%s/api/v2/config/interface?ports=%s" % (protocol, to_native(module.params['cpm_url']), to_native(module.params['interface'])))
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
