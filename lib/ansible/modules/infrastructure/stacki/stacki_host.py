#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Hugh Ma <Hugh.Ma@flextronics.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: stacki_host
short_description: Add or remove host to stacki front-end
description:
 - Use this module to add or remove hosts to a stacki front-end via API
 - https://github.com/StackIQ/stacki
version_added: "2.3"
options:
  chdir:
    description:
     - change working directory
    required: false
    default: null
  cpu:
    description:
     - number of cpus to stress
    required: true
  delay:
    description:
     - piggybacks off the at module as a action plugin to run benchmark at a schedule time
    required: false
  executable:
    description:
     - path to stress executable if running from source
    required: false
  dest:
    description:
     - absolute path of file to write stdout to
    required: false
  timeout:
    description:
     - Total time to run stress for.
    required: True
requirements:
 - requests
author: "Hugh Ma <Hugh.Ma@flextronics.com>"
'''

EXAMPLES = '''
# Add a host named test-1
- stacki_host: name=test-1 stacki_user=usr stacki_password=pwd stacki_endpoint=url \
               prim_intf_mac=mac_addr prim_intf_ip=x.x.x.x prim_intf=eth0

-
# Remove a host named test-1
- stacki_host: name=test-1 stacki_user=usr stacki_password=pwd stacki_endpoint=url state=absent
'''

RETURN = '''
changed:
  description: response to whether or not the api call completed successfully
  returned: always
  type: boolean
  sample: true

stdout:
  description: the set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: the value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]
'''

import os
import re
import tempfile

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def stack_auth(module, result, params):

    endpoint    = params['stacki_endpoint']
    auth_creds  = {'USERNAME': params['stacki_user'],
                   'PASSWORD': params['stacki_password']}

    client = requests.session()
    client.get(endpoint)

    init_csrf = client.cookies['csrftoken']

    header = {'csrftoken': init_csrf, 'X-CSRFToken': init_csrf,
              'Content-type': 'application/x-www-form-urlencoded'}

    login_endpoint = endpoint + "/login"

    login_req = client.post(login_endpoint, data=auth_creds, headers=header)

    csrftoken = login_req.cookies['csrftoken']
    sessionid = login_req.cookies['sessionid']

    auth_creds.update(CSRFTOKEN=csrftoken, SESSIONID=sessionid)

    return client, auth_creds


def stack_build_header(auth_creds):
    header = {'csrftoken': auth_creds['CSRFTOKEN'],
              'X-CSRFToken': auth_creds['CSRFTOKEN'],
              'sessionid': auth_creds['SESSIONID'],
              'Content-type': 'application/json'}

    return header


def stack_check_host(params, header, client):

    hostname    = params['name']
    endpoint    = params['stacki_endpoint']

    stack_r = client.post(endpoint, data=json.dumps({"cmd": "list host"}),
                          headers=header)
    if hostname in stack_r.text:
        return True
    else:
        return False


def stack_sync(endpoint, header, client):

    stack_r = client.post(endpoint, data=json.dumps({ "cmd": "sync config"}),
                          headers=header)
        
    stack_r = client.post(endpoint, data=json.dumps({"cmd": "sync host config"}),
                          headers=header)

    rc = stack_r.status_code

    if rc == 200:
        rc = 0

    return rc, stack_r.text


def stack_force_install(result, params, header, client):

    hostname = params['name']
    endpoint = params['stacki_endpoint']
    data = dict()
    rc = None
    changed = False

    data['cmd'] = "set host boot {} action=install" \
        .format(hostname)
    stack_r = client.post(endpoint, data=json.dumps(data), headers=header)
    rc = stack_r.status_code if stack_r.status_code != 200 else stack_r.status_code
    out = stack_r.text
    changed = True

    rc, out = stack_sync(endpoint, header, client)

    result['changed'] = changed
    result['stdout'] = "api call successful".rstrip("\r\n")
    result['stderr'] = out.rstrip("\r\n")
    result['rc'] = rc


def stack_add(result, params, header, client):

    hostname        = params['name']
    rack            = params['rack']
    rank            = params['rank']
    appliance       = params['appliance']
    prim_intf       = params['prim_intf']
    prim_intf_ip    = params['prim_intf_ip']
    network         = params['network']
    prim_intf_mac   = params['prim_intf_mac']
    endpoint        = params['stacki_endpoint']
    data            = dict()
    rc              = None
    changed         = False

    data['cmd'] = "add host {} rack={} rank={} appliance={}"\
        .format(hostname, rack, rank, appliance)
    stack_r = client.post(endpoint, data=json.dumps(data), headers=header)
    rc = stack_r.status_code
    out = stack_r.text

    data['cmd'] = "add host interface {} interface={} ip={} network={} mac={} default=true"\
        .format(hostname, prim_intf, prim_intf_ip, network, prim_intf_mac)
    stack_r = client.post(endpoint, data=json.dumps(data), headers=header)
    rc = stack_r.status_code if stack_r.status_code != 200 else stack_r.status_code
    out = stack_r.text
    changed = True

    rc, out = stack_sync(endpoint, header, client)

    result['changed'] = changed
    result['stdout'] = "api call successful".rstrip("\r\n")
    result['stderr'] = out.rstrip("\r\n")
    result['rc'] = rc


def stack_remove(result, params, header, client):

    hostname        = params['name']
    endpoint        = params['stacki_endpoint']
    data            = dict()
    rc              = None

    data['cmd'] = "remove host {}"\
        .format(hostname)
    stack_r = client.post(endpoint, data=json.dumps(data), headers=header)
    rc = stack_r.status_code
    out = stack_r.text

    rc, out = stack_sync(endpoint, header, client)

    result['changed'] = True
    result['stdout'] = "api call successful".rstrip("\r\n")
    result['stderr'] = out.rstrip("\r\n")
    result['rc'] = rc


def main():

    module = AnsibleModule(
        argument_spec = dict(
            state=dict(type='str',
                       default='present',
                       choices=['present', 'absent']),
            name=dict(required=True,
                      type='str'),
            rack=dict(required=False,
                      type='int',
                      default=0),
            rank=dict(required=False,
                      type='int',
                      default=0),
            appliance=dict(required=False,
                           type='str',
                           default='backend'),
            prim_intf=dict(required=False,
                           type='str',
                           default=None),
            prim_intf_ip=dict(required=False,
                              type='str',
                              default=None),
            network=dict(required=False,
                         type='str',
                         default='private'),
            prim_intf_mac=dict(required=False,
                               type='str',
                               default=None),
            stacki_user=dict(required=True,
                             type='str',
                             default=os.environ.get('stacki_user')),
            stacki_password=dict(required=True,
                                 type='str',
                                 default=os.environ.get('stacki_password')),
            stacki_endpoint=dict(required=True,
                                 type='str',
                                 default=os.environ.get('stacki_endpoint')),
            force_install=dict(required=False,
                               type='bool',
                               default=False)
        ),
        supports_check_mode=False
    )

    if not HAS_REQUESTS:
        module.fail_json(msg='requests is required for this module')

    result = {'changed': False}
    missing_params = list()

    client, auth = stack_auth(module, result, module.params)
    header = stack_build_header(auth)
    host_exists = stack_check_host(module.params, header, client)

    # If state is present, but host exists, need force_install flag to put host back into install state
    if module.params['state'] == 'present' and host_exists and module.params['force_install']:
        stack_force_install(result, module.params, header, client)
    # If state is present, but host exists, and force_install and false, do nothing
    elif module.params['state'] == 'present' and host_exists and not module.params['force_install']:
        result['stdout'] = "{} already exists. Set 'force_install' to true to bootstrap"\
            .format(module.params['name'])
    # Otherwise, state is present, but host doesn't exists, require more params to add host
    elif module.params['state'] == 'present' and not host_exists:
        for param in ['appliance', 'prim_intf',
                      'prim_intf_ip', 'network', 'prim_intf_mac']:
            if not module.params[param]:
                missing_params.append(param)
        if len(missing_params) > 0:
            module.fail_json(msg="missing required arguments: {}".format(missing_params))

        stack_add(result, module.params, header, client)
    # If state is absent, and host exists, lets remove it.
    elif module.params['state'] == 'absent' and host_exists:
        stack_remove(result, module.params, header, client)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
