#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (C) 2018 Red Hat Inc.
# Copyright (C) 2018 Western Telematic Inc. <kenp@wti.com>
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
# Module to execute WTI Plug Commands on WTI OOB and PDU devices.
# WTI remote_management
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
module: cpm_plugcontrol
version_added: "2.8"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get and Set Plug actions on WTI OOB and PDU power devices
description:
    - "Get and Set Plug actions on WTI OOB and PDU devices"
options:
  cpm_action:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "getplugcontrol", "setplugcontrol" ]
  cpm_url:
    description:
      - This is the URL of the WTI device  to send the module.
    required: true
  cpm_username:
    description:
      - This is the Username of the WTI device to send the module.
  cpm_password:
    description:
      - This is the Password of the WTI device to send the module.
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
  plug_id:
    description:
      - This is the plug number or the plug name that is to be manipulated
        For the plugget command, the plug_id 'all' will return the status of all the plugs the
        user has rights to access.
    required: true
  plug_state:
    description:
      - This is what action to take on the plug.
    required: false
    choices: [ "on", "off", "boot", "default" ]
"""

EXAMPLES = """
# Get Plug status for all ports
- name: Get the Plug status for ALL ports of a WTI device
  cpm_plugcontrol:
    cpm_action: "getplugcontrol"
    cpm_url: "rest.wti.com"
    cpm_username: "restpower"
    cpm_password: "restfulpowerpass12"
    use_https: true
    validate_certs: true
    plug_id: "all"

# Get Plug status for port 2
- name: Get the Plug status for the given port of a WTI device
  cpm_plugcontrol:
    cpm_action: "getplugcontrol"
    cpm_url: "rest.wti.com"
    cpm_username: "restpower"
    cpm_password: "restfulpowerpass12"
    use_https: true
    validate_certs: false
    plug_id: "2"

# Reboot plug 5
- name: Reboot Plug 5 on a given WTI device
  cpm_plugcontrol:
    cpm_action: "setplugcontrol"
    cpm_url: "rest.wti.com"
    cpm_username: "restpower"
    cpm_password: "restfulpowerpass12"
    use_https: true
    plug_id: "5"
    plug_state: "boot"
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


def assemble_json(cpmmodule, cpmresult):
    json_load = ""
    plugspassed = cpmmodule.params["plug_id"].split(",")

    for val in plugspassed:
        if (val.isdigit() is True):
            json_load = '%s{"plug": "%s"' % (json_load, to_native(val))
        else:
            json_load = '%s{"plugname": "%s"' % (json_load, to_native(val))

        if cpmmodule.params["plug_state"] is not None:
            json_load = '%s,"state": "%s"' % (json_load, to_native(cpmmodule.params["plug_state"]))

        json_load = '%s}' % (json_load)

    return json_load


def run_module():

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cpm_action=dict(choices=['getplugcontrol', 'setplugcontrol'], required=True),
        cpm_url=dict(type='str', required=True),
        cpm_username=dict(type='str', required=True),
        cpm_password=dict(type='str', required=True, no_log=True),
        plug_id=dict(type='str', required=True),
        plug_state=dict(choices=['on', 'off', 'boot', 'default'], required=False),
        use_https=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
        use_proxy=dict(type='bool', default=False)
    )

    result = dict(
        changed=False,
        data=''
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        return result

    auth = to_text(base64.b64encode(to_bytes('{0}:{1}'.format(to_native(module.params['cpm_username']), to_native(module.params['cpm_password'])),
                   errors='surrogate_or_strict')))

    if module.params['use_https'] is True:
        protocol = "https://"
    else:
        protocol = "http://"

    Payload = None
    if (module.params['cpm_action'] == 'getplugcontrol'):
        fullurl = ("%s%s/api/v2/config/powerplug" % (protocol, to_native(module.params['cpm_url'])))
        if (module.params['plug_id'].lower() != 'all'):
            fullurl = '%s?plug=%s' % (fullurl, to_native(module.params['plug_id']))
        method = 'GET'
    elif (module.params['cpm_action'] == 'setplugcontrol'):
        Payload = assemble_json(module, result)
        fullurl = ("%s%s/api/v2/config/powerplug" % (protocol, to_native(module.params['cpm_url'])))
        method = 'POST'

    try:
        response = open_url(fullurl, data=Payload, method=method, validate_certs=module.params['validate_certs'], use_proxy=module.params['use_proxy'],
                            headers={'Content-Type': 'application/json', 'Authorization': "Basic %s" % auth})
        if (method != 'GET'):
            result['changed'] = True

    except HTTPError as e:
        fail_json = dict(msg='Received HTTP error for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except URLError as e:
        fail_json = dict(msg='Failed lookup url for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except SSLValidationError as e:
        fail_json = dict(msg='Error validating the server''s certificate for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)
    except ConnectionError as e:
        fail_json = dict(msg='Error connecting to  for {0} : {1}'.format(fullurl, to_native(e)), changed=False)
        module.fail_json(**fail_json)

    result['data'] = json.loads(response.read())

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
