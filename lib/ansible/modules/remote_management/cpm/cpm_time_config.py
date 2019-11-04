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
# Module to execute WTI time date Parameters on WTI OOB and PDU devices.
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
module: cpm_time_config
version_added: "2.10"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Set Time/Date parameters in WTI OOB and PDU devices
description:
    - "Set Time/Date and NTP parameters parameters in WTI OOB and PDU devices"
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
  date:
    description:
      - Static date in the format of two digit month, two digit day, four digit year separated by a slash symbol.
    required: false
    type: str
  time:
    description:
      - Static time in the format of two digit hour, two digit minute, two digit second separated by a colon symbol.
    required: false
    type: str
  timezone:
    description:
      - This is timezone that is assigned to the WTI device.
    required: false
    type: int
  ntpenable:
    description:
      - This enables or disables the NTP client service.
    required: false
    type: int
    choices: [ 0, 1 ]
  ipv4address:
    description:
      - Comma separated string of up to two addresses for a primary and secondary IPv4 base NTP server.
    required: false
    type: str
  ipv6address:
    description:
      - Comma separated string of up to two addresses for a primary and secondary IPv6 base NTP server.
    required: false
    type: str
  timeout:
    description:
      - Set the network timeout in seconds of contacting the NTP servers, valid options can be from 1-60.
    required: false
    type: int
notes:
  - Use C(groups/cpm) in C(module_defaults) to set common options used between CPM modules.
"""

EXAMPLES = """
# Set a static time/date and timezone of a WTI device
- name: Set known fixed time/date of a WTI device
  cpm_time_config:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    date: "12/12/2019"
    time: "09:23:46"
    timezone: 5

# Enable NTP and set primary and seconday servers of a WTI device
- name: Set NTP primary and seconday servers of a WTI device
  cpm_time_config:
    cpm_url: "nonexist.wti.com"
    cpm_username: "super"
    cpm_password: "super"
    use_https: true
    validate_certs: false
    timezone: 5
    ntpenable: 1
    ipv4address: "129.6.15.28.pool.ntp.org"
    timeout: 15
"""

RETURN = """
data:
  description: The output JSON returned from the commands sent
  returned: always
  type: complex
  contains:
    date:
      description: Current Date of the WTI device after module execution.
      returned: success
      type: str
      sample: "11/14/2019"
    time:
      description: Current Time of the WTI device after module execution.
      returned: success
      type: str
      sample: "12:12:00"
    timezone:
      description: Current Timezone of the WTI device after module execution.
      returned: success
      type: int
      sample: 5
    ntp:
      description: Current k/v pairs of ntp info of the WTI device after module execution.
      returned: always
      type: dict
      sample: {"enable": "0",
              "ietf-ipv4": {"address": [{"primary": "192.168.0.169","secondary": "12.34.56.78"}]},
              "ietf-ipv6": {"address": [{"primary": "","secondary": ""}]},
              "timeout": "4"}
"""

import base64
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError


def assemble_json(cpmmodule, existing):
    total_change = 0
    json_load = ietfstring = ""

    localdate = localtime = localtimezone = localenable = localtimeout = None

    localprimary = []
    localsecondary = []

    for x in range(0, 2):
        localprimary.insert(x, None)
        localsecondary.insert(x, None)

    if cpmmodule.params["date"] is not None:
        if (existing["date"] != to_native(cpmmodule.params["date"])):
            total_change = (total_change | 1)
            localdate = to_native(cpmmodule.params["date"])
    if cpmmodule.params["time"] is not None:
        if (existing["time"] != to_native(cpmmodule.params["time"])):
            total_change = (total_change | 2)
            localtime = to_native(cpmmodule.params["time"])
    if cpmmodule.params["timezone"] is not None:
        if (existing["timezone"] != to_native(cpmmodule.params["timezone"])):
            total_change = (total_change | 4)
            localtimezone = to_native(cpmmodule.params["timezone"])
    if cpmmodule.params["ntpenable"] is not None:
        if (existing["ntp"]["enable"] != to_native(cpmmodule.params["ntpenable"])):
            total_change = (total_change | 16)
            localenable = to_native(cpmmodule.params["ntpenable"])
    if cpmmodule.params["ipv4address"] is not None:
        loopcounter = 0
        portspassed = cpmmodule.params["ipv4address"].split(",")
        for val in portspassed:
            if (loopcounter == 0):
                if (existing["ntp"]["ietf-ipv4"]["address"][0]["primary"] != to_native(val)):
                    total_change = (total_change | 32)
                    localprimary[0] = to_native(val)
                loopcounter += 1
            else:
                if (existing["ntp"]["ietf-ipv4"]["address"][0]["secondary"] != to_native(val)):
                    total_change = (total_change | 32)
                    localsecondary[0] = to_native(val)
                loopcounter += 1
    if cpmmodule.params["ipv6address"] is not None:
        loopcounter = 0
        portspassed = cpmmodule.params["ipv6address"].split(",")
        for val in portspassed:
            if (loopcounter == 0):
                if (existing["ntp"]["ietf-ipv6"]["address"][0]["primary"] != to_native(val)):
                    total_change = (total_change | 64)
                    localprimary[1] = to_native(val)
                loopcounter += 1
            else:
                if (existing["ntp"]["ietf-ipv6"]["address"][0]["secondary"] != to_native(val)):
                    total_change = (total_change | 64)
                    localsecondary[1] = to_native(val)
                loopcounter += 1
    if cpmmodule.params["timeout"] is not None:
        if (existing["ntp"]["timeout"] != to_native(cpmmodule.params["timeout"])):
            if ((int(to_native(cpmmodule.params["timeout"])) > 0) and (int(to_native(cpmmodule.params["timeout"])) <= 60)):
                total_change = (total_change | 8)
                localtimeout = to_native(cpmmodule.params["timeout"])

    if (total_change > 0):
        protocol = protocolchanged = 0
        ietfstring = ""

        if (localdate is not None):
            ietfstring = '%s"date": "%s"' % (ietfstring, localdate)

        if (localtime is not None):
            if (len(ietfstring) > 0):
                ietfstring = '%s,' % (ietfstring)
            ietfstring = '%s"time": "%s"' % (ietfstring, localtime)

        if (localtimezone is not None):
            if (len(ietfstring) > 0):
                ietfstring = '%s,' % (ietfstring)
            ietfstring = '%s"timezone": "%s"' % (ietfstring, localtimezone)

        if ((localenable is not None) or (localtimeout is not None) or
                (localprimary[0] is not None) or (localsecondary[0] is not None) or
                (localprimary[1] is not None) or (localsecondary[1] is not None)):
            if (len(ietfstring) > 0):
                ietfstring = '%s,' % (ietfstring)
            ietfstring = '%s  "ntp": {' % (ietfstring)

            if (localenable is not None):
                ietfstring = '%s"enable": "%s"' % (ietfstring, localenable)

            if (localtimeout is not None):
                if (len(ietfstring) > 0):
                    ietfstring = '%s,' % (ietfstring)
                ietfstring = '%s"timeout": "%s"' % (ietfstring, localtimeout)

            if ((localprimary[0] is not None) or (localsecondary[0] is not None)):
                if ((localenable is not None) or (localtimeout is not None)):
                    ietfstring = '%s,' % (ietfstring)
                ietfstring = '%s  "ietf-ipv4": { "address": [{' % (ietfstring)

                if (localprimary[0] is not None):
                    ietfstring = '%s  "primary": "%s"' % (ietfstring, localprimary[0])

                if (localsecondary[0] is not None):
                    if (localprimary[0] is not None):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s  "secondary": "%s"' % (ietfstring, localsecondary[0])

                # end ietf-ipv4 block
                ietfstring = '%s  }]}' % (ietfstring)

            if ((localprimary[1] is not None) or (localsecondary[1] is not None)):
                if ((localprimary[0] is not None) or (localsecondary[0] is not None) or
                        (localenable is not None) or (localtimeout is not None)):
                    ietfstring = '%s,' % (ietfstring)

                ietfstring = '%s  "ietf-ipv6": { "address": [{' % (ietfstring)

                if (localprimary[1] is not None):
                    ietfstring = '%s  "primary": "%s"' % (ietfstring, localprimary[1])

                if (localsecondary[1] is not None):
                    if (localprimary[1] is not None):
                        ietfstring = '%s,' % (ietfstring)
                    ietfstring = '%s  "secondary": "%s"' % (ietfstring, localsecondary[1])

                # end ietf-ipv6 block
                ietfstring = '%s  }]}' % (ietfstring)
            # end ntp block
            ietfstring = '%s}' % (ietfstring)

        json_load = "{"
        json_load = '%s%s' % (json_load, ietfstring)
        json_load = '%s}' % (json_load)
    else:
        json_load = None
    return json_load


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cpm_url=dict(type='str', required=True),
        cpm_username=dict(type='str', required=True),
        cpm_password=dict(type='str', required=True, no_log=True),
        date=dict(type='str', required=False, default=None),
        time=dict(type='str', required=False, default=None),
        timezone=dict(type='int', required=False, default=None),
        ntpenable=dict(type='int', required=False, default=None, choices=[0, 1]),
        ipv4address=dict(type='str', required=False, default=None),
        ipv6address=dict(type='str', required=False, default=None),
        timeout=dict(type='int', required=False, default=None),
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

    fullurl = ("%s%s/api/v2/config/timedate" % (protocol, to_native(module.params['cpm_url'])))
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

    result['data'] = response.read()
    payload = assemble_json(module, json.loads(result['data']))

    if module.check_mode:
        if payload is not None:
            result['changed'] = True
    else:
        if payload is not None:
            fullurl = ("%s%s/api/v2/config/timedate" % (protocol, to_native(module.params['cpm_url'])))
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
