#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage A10 Networks slb server objects
(c) 2014, Mischa Peters <mpeters@a10networks.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: a10_server
version_added: 1.8
short_description: Manage A10 Networks AX/SoftAX/Thunder/vThunder devices
description:
    - Manage slb server objects on A10 Networks devices via aXAPI
author: Mischa Peters
notes:
    - Requires A10 Networks aXAPI 2.1
options:
  host:
    description:
      - hostname or ip of your A10 Networks device
    required: true
    default: null
    aliases: []
    choices: []
  username:
    description:
      - admin account of your A10 Networks device
    required: true
    default: null
    aliases: ['user', 'admin']
    choices: []
  password:
    description:
      - admin password of your A10 Networks device
    required: true
    default: null
    aliases: ['pass', 'pwd']
    choices: []
  server_name:
    description:
      - slb server name
    required: true
    default: null
    aliases: ['server']
    choices: []
  server_ip:
    description:
      - slb server IP address
    required: false
    default: null
    aliases: ['ip', 'address']
    choices: []
  server_status:
    description:
      - slb virtual server status
    required: false
    default: enable
    aliases: ['status']
    choices: ['enabled', 'disabled']
  server_ports:
    description:
      - A list of ports to create for the server. Each list item should be a
        dictionary which specifies the C(port:) and C(protocol:), but can also optionally
        specify the C(status:). See the examples below for details. This parameter is
        required when C(state) is C(present).
    required: false
    default: null
    aliases: []
    choices: []
  state:
    description:
      - create, update or remove slb server
    required: false
    default: present
    aliases: []
    choices: ['present', 'absent']
'''

EXAMPLES = '''
# Create a new server
- a10_server: 
    host: a10.mydomain.com
    username: myadmin
    password: mypassword
    server: test
    server_ip: 1.1.1.100
    server_ports:
      - port_num: 8080
        protocol: tcp
      - port_num: 8443
        protocol: TCP

'''

VALID_PORT_FIELDS = ['port_num', 'protocol', 'status']

def validate_ports(module, ports):
    for item in ports:
        for key in item:
            if key not in VALID_PORT_FIELDS:
                module.fail_json(msg="invalid port field (%s), must be one of: %s" % (key, ','.join(VALID_PORT_FIELDS)))

        # validate the port number is present and an integer
        if 'port_num' in item:
            try:
                item['port_num'] = int(item['port_num'])
            except:
                module.fail_json(msg="port_num entries in the port definitions must be integers")
        else:
            module.fail_json(msg="port definitions must define the port_num field")

        # validate the port protocol is present, and convert it to
        # the internal API integer value (and validate it)
        if 'protocol' in item:
            protocol = axapi_get_port_protocol(item['protocol'])
            if not protocol:
                module.fail_json(msg="invalid port protocol, must be one of: %s" % ','.join(AXAPI_PORT_PROTOCOLS))
            else:
                item['protocol'] = protocol
        else:
            module.fail_json(msg="port definitions must define the port protocol (%s)" % ','.join(AXAPI_PORT_PROTOCOLS))

        # convert the status to the internal API integer value
        if 'status' in item:
            item['status'] = axapi_enabled_disabled(item['status'])
        else:
            item['status'] = 1


def main():
    argument_spec = a10_argument_spec()
    argument_spec.update(url_argument_spec())
    argument_spec.update(
        dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            server_name=dict(type='str', aliases=['server'], required=True),
            server_ip=dict(type='str', aliases=['ip', 'address']),
            server_status=dict(type='str', default='enabled', aliases=['status'], choices=['enabled', 'disabled']),
            server_ports=dict(type='list', aliases=['port'], default=[]),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    host = module.params['host']
    username = module.params['username']
    password = module.params['password']
    state = module.params['state']
    write_config = module.params['write_config']
    slb_server = module.params['server_name']
    slb_server_ip = module.params['server_ip']
    slb_server_status = module.params['server_status']
    slb_server_ports = module.params['server_ports']

    if slb_server is None:
        module.fail_json(msg='server_name is required')

    axapi_base_url = 'https://%s/services/rest/V2.1/?format=json' % host
    session_url = axapi_authenticate(module, axapi_base_url, username, password)

    # validate the ports data structure
    validate_ports(module, slb_server_ports)

    json_post = {
        'server': {
            'name': slb_server, 
            'host': slb_server_ip, 
            'status': axapi_enabled_disabled(slb_server_status),
            'port_list': slb_server_ports,
        }
    }

    slb_server_data = axapi_call(module, session_url + '&method=slb.server.search', json.dumps({'name': slb_server}))
    slb_server_exists = not axapi_failure(slb_server_data)

    changed = False
    if state == 'present':
        if not slb_server_ip:
            module.fail_json(msg='you must specify an IP address when creating a server')

        if not slb_server_exists:
            result = axapi_call(module, session_url + '&method=slb.server.create', json.dumps(json_post))
            if axapi_failure(result):
                module.fail_json(msg="failed to create the server: %s" % result['response']['err']['msg'])
            changed = True
        else:
            def needs_update(src_ports, dst_ports):
                '''
                Checks to determine if the port definitions of the src_ports
                array are in or different from those in dst_ports. If there is
                a difference, this function returns true, otherwise false.
                '''
                for src_port in src_ports:
                    found = False
                    different = False
                    for dst_port in dst_ports:
                        if src_port['port_num'] == dst_port['port_num']:
                            found = True
                            for valid_field in VALID_PORT_FIELDS:
                                if src_port[valid_field] != dst_port[valid_field]:
                                    different = True
                                    break
                            if found or different:
                                break
                    if not found or different:
                        return True
                # every port from the src exists in the dst, and none of them were different
                return False

            defined_ports = slb_server_data.get('server', {}).get('port_list', [])

            # we check for a needed update both ways, in case ports
            # are missing from either the ones specified by the user
            # or from those on the device
            if needs_update(defined_ports, slb_server_ports) or needs_update(slb_server_ports, defined_ports):
                result = axapi_call(module, session_url + '&method=slb.server.update', json.dumps(json_post))
                if axapi_failure(result):
                    module.fail_json(msg="failed to update the server: %s" % result['response']['err']['msg'])
                changed = True

        # if we changed things, get the full info regarding
        # the service group for the return data below
        if changed:
            result = axapi_call(module, session_url + '&method=slb.server.search', json.dumps({'name': slb_server}))
        else:
            result = slb_server_data
    elif state == 'absent':
        if slb_server_exists:
            result = axapi_call(module, session_url + '&method=slb.server.delete', json.dumps({'name': slb_server}))
            changed = True
        else:
            result = dict(msg="the  server was not present")

    # if the config has changed, save the config unless otherwise requested
    if changed and write_config:
        write_result = axapi_call(module, session_url + '&method=system.action.write_memory')
        if axapi_failure(write_result):
            module.fail_json(msg="failed to save the configuration: %s" % write_result['response']['err']['msg'])

    # log out of the session nicely and exit
    axapi_call(module, session_url + '&method=session.close')
    module.exit_json(changed=changed, content=result)

# standard ansible module imports
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.a10 import *

main()
