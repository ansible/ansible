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
# Module to execute CPM User Commands on WTI OOB and PDU devices.
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
module: cpm_user
version_added: "2.7"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get various status and parameters from WTI OOB and PDU devices
description:
    - "Get/Add/Edit Delete Users from WTI OOB and PDU devices"
options:
  cpm_action:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "getuser", "adduser", "edituser", "deleteuser" ]
  cpm_url:
    description:
      - This is the URL of the WTI device to send the module.
    required: true
  cpm_username:
    description:
      - This is the Basic Authentication Username of the WTI device to send the module.
    required: true
  cpm_password:
    description:
      - This is the Basic Authentication Password of the WTI device to send the module.
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
  user_name:
    description:
      - This is the User Name that needs to be create/modified/deleted
    required: true
  user_pass:
    description:
      - This is the User Password that needs to be create/modified/deleted
      - If the user is being Created this parameter is required
    required: false
  user_accesslevel:
    description:
      - This is the access level that needs to be create/modified/deleted
      - 0 View, 1 User, 2 SuperUser, 3 Administrator
    required: false
    choices: [ 0, 1, 2, 3 ]
  user_accessssh:
    description:
      - If the user has access to the WTI device via SSH
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessserial:
    description:
      - If the user has access to the WTI device via Serial ports
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessweb:
    description:
      - If the user has access to the WTI device via Web
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessapi:
    description:
      - If the user has access to the WTI device via RESTful APIs
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessmonitor:
    description:
      - If the user has ability to monitor connection sessions
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessoutbound:
    description:
      - If the user has ability to initiate Outbound connection
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_portaccess:
    description:
      - If AccessLevel is lower than Administrator, which ports the user has access
    required: false
  user_plugaccess:
    description:
      - If AccessLevel is lower than Administrator, which plugs the user has access
    required: false
  user_groupaccess:
    description:
      - If AccessLevel is lower than Administrator, which Groups the user has access
    required: false
  user_callbackphone:
    description:
      - This is the Call Back phone number used for POTS modem connections
    required: false
"""

EXAMPLES = """
# Get User Parameters
- name: Get the User Parameters for the given user of a WTI device
  cpm_user:
    cpm_action: "getuser"
    cpm_url: "rest.wti.com"
    cpm_username: "restuser"
    cpm_password: "restfuluserpass12"
    use_https: true
    validate_certs: true
    user_name: "usernumberone"

# Create User
- name: Create a User on a given WTI device
  cpm_user:
    cpm_action: "adduser"
    cpm_url: "rest.wti.com"
    cpm_username: "restuser"
    cpm_password: "restfuluserpass12"
    use_https: true
    validate_certs: false
    user_name: "usernumberone"
    user_pass: "complicatedpassword"
    user_accesslevel: 2
    user_accessssh: 1
    user_accessserial: 1
    user_accessweb: 0
    user_accessapi: 1
    user_accessmonitor: 0
    user_accessoutbound: 0
    user_portaccess: "10011111"
    user_plugaccess: "00000111"
    user_groupaccess: "00000000"

# Edit User
- name: Edit a User on a given WTI device
  cpm_user:
    cpm_action: "edituser"
    cpm_url: "rest.wti.com"
    cpm_username: "restuser"
    cpm_password: "restfuluserpass12"
    use_https: true
    validate_certs: false
    user_name: "usernumberone"
    user_pass: "newpasswordcomplicatedpassword"

# Delete User
- name: Delete a User from a given WTI device
  cpm_user:
    cpm_action: "deleteuser"
    cpm_url: "rest.wti.com"
    cpm_username: "restuser"
    cpm_password: "restfuluserpass12"
    use_https: true
    validate_certs: true
    user_name: "usernumberone"
"""

RETURN = """
data:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

import base64

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError


def assemble_json(cpmmodule):
    json_load = '{"users":{"username": "%s"' % to_native((cpmmodule.params["user_name"]))

    # for Adding there must be a password present
    if cpmmodule.params["user_pass"] is not None and (len(cpmmodule.params["user_pass"]) > 0):
        json_load = '%s,"newpasswd": "%s"' % (json_load, to_native(cpmmodule.params["user_pass"]))
    if cpmmodule.params["user_accesslevel"] is not None:
        json_load = '%s,"accesslevel": %s' % (json_load, to_native(cpmmodule.params["user_accesslevel"]))
    if cpmmodule.params["user_portaccess"] is not None:
        json_load = '%s,"portaccess": %s' % (json_load, to_native(cpmmodule.params["user_portaccess"]))
    if cpmmodule.params["user_plugaccess"] is not None:
        json_load = '%s,"plugaccess": %s' % (json_load, to_native(cpmmodule.params["user_plugaccess"]))
    if cpmmodule.params["user_groupaccess"] is not None:
        json_load = '%s,"groupaccess": %s' % (json_load, to_native(cpmmodule.params["user_groupaccess"]))
    if cpmmodule.params["user_accessserial"] is not None:
        json_load = '%s,"accessserial": %s' % (json_load, to_native(cpmmodule.params["user_accessserial"]))
    if cpmmodule.params["user_accessssh"] is not None:
        json_load = '%s,"accessssh": %s' % (json_load, to_native(cpmmodule.params["user_accessssh"]))
    if cpmmodule.params["user_accessweb"] is not None:
        json_load = '%s,"accessweb": %s' % (json_load, to_native(cpmmodule.params["user_accessweb"]))
    if cpmmodule.params["user_accessoutbound"] is not None:
        json_load = '%s,"accessoutbound": %s' % (json_load, to_native(cpmmodule.params["user_accessoutbound"]))
    if cpmmodule.params["user_accessapi"] is not None:
        json_load = '%s,"accessapi": %s' % (json_load, to_native(cpmmodule.params["user_accessapi"]))
    if cpmmodule.params["user_accessmonitor"] is not None:
        json_load = '%s,"accessmonitor": %s' % (json_load, to_native(cpmmodule.params["user_accessmonitor"]))
    if cpmmodule.params["user_callbackphone"] is not None:
        json_load = '%s,"callbackphone": "%s"' % (json_load, to_native(cpmmodule.params["user_callbackphone"]))

    json_load = '%s}}' % (json_load)

    return json_load


def run_module():

    module_args = dict(
        cpm_action=dict(choices=['getuser', 'adduser', 'edituser', 'deleteuser'], required=True),
        cpm_url=dict(type='str', required=True),
        cpm_username=dict(type='str', required=True),
        cpm_password=dict(type='str', required=True, no_log=True),
        user_name=dict(type='str', required=True),
        user_pass=dict(type='str', required=False, default=None, no_log=True),
        user_accesslevel=dict(type='int', required=False, default=None, choices=[0, 1, 2, 3]),
        user_accessssh=dict(type='int', required=False, default=None, choices=[0, 1]),
        user_accessserial=dict(type='int', required=False, default=None, choices=[0, 1]),
        user_accessweb=dict(type='int', required=False, default=None, choices=[0, 1]),
        user_accessapi=dict(type='int', required=False, default=None, choices=[0, 1]),
        user_accessmonitor=dict(type='int', required=False, default=None, choices=[0, 1]),
        user_accessoutbound=dict(type='int', required=False, default=None, choices=[0, 1]),
        user_portaccess=dict(type='str', required=False, default=None),
        user_plugaccess=dict(type='str', required=False, default=None),
        user_groupaccess=dict(type='str', required=False, default=None),
        user_callbackphone=dict(type='str', required=False, default=None),
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

    payload = None
    if (module.params['cpm_action'] == 'getuser'):
        fullurl = ("%s%s/api/v2/config/users?username=%s" % (protocol, to_native(module.params['cpm_url']), to_native(module.params['user_name'])))
        method = 'GET'
    elif (module.params['cpm_action'] == 'adduser'):
        if module.params["user_pass"] is None or (len(module.params["user_pass"]) == 0):
            module.fail_json(msg='user_pass not defined.', **result)

        payload = assemble_json(module)
        fullurl = ("%s%s/api/v2/config/users" % (protocol, to_native(module.params['cpm_url'])))
        method = 'POST'
    elif (module.params['cpm_action'] == 'edituser'):
        payload = assemble_json(module)
        fullurl = ("%s%s/api/v2/config/users" % (protocol, to_native(module.params['cpm_url'])))
        method = 'PUT'
    elif (module.params['cpm_action'] == 'deleteuser'):
        fullurl = ("%s%s/api/v2/config/users?username=%s" % (protocol, to_native(module.params['cpm_url']), to_native(module.params['user_name'])))
        method = 'DELETE'

    try:
        response = open_url(fullurl, data=payload, method=method, validate_certs=module.params['validate_certs'], use_proxy=module.params['use_proxy'],
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

    result['data'] = to_text(response.read())
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
