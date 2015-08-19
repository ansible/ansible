#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage A10 Networks slb virtual server objects
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
module: a10_virtual_server
version_added: 1.8
short_description: Manage A10 Networks devices' virtual servers
description:
    - Manage slb virtual server objects on A10 Networks devices via aXAPI
author: "Mischa Peters (@mischapeters)"
notes:
    - Requires A10 Networks aXAPI 2.1
requirements: []
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
  virtual_server:
    description:
      - slb virtual server name
    required: true
    default: null
    aliases: ['vip', 'virtual']
    choices: []
  virtual_server_ip:
    description:
      - slb virtual server ip address
    required: false
    default: null
    aliases: ['ip', 'address']
    choices: []
  virtual_server_status:
    description:
      - slb virtual server status
    required: false
    default: enable
    aliases: ['status']
    choices: ['enabled', 'disabled']
  virtual_server_ports:
    description:
      - A list of ports to create for the virtual server. Each list item should be a
        dictionary which specifies the C(port:) and C(type:), but can also optionally
        specify the C(service_group:) as well as the C(status:). See the examples
        below for details. This parameter is required when C(state) is C(present).
    required: false
  write_config:
    description:
      - If C(yes), any changes will cause a write of the running configuration
        to non-volatile memory. This will save I(all) configuration changes,
        including those that may have been made manually or through other modules,
        so care should be taken when specifying C(yes).
    required: false
    default: "no"
    choices: ["yes", "no"]
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled devices using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']

'''

EXAMPLES = '''
# Create a new virtual server
- a10_virtual_server: 
    host: a10.mydomain.com
    username: myadmin
    password: mypassword
    virtual_server: vserver1
    virtual_server_ip: 1.1.1.1
    virtual_server_ports:
      - port: 80
        protocol: TCP
        service_group: sg-80-tcp
      - port: 443
        protocol: HTTPS
        service_group: sg-443-https
      - port: 8080
        protocol: http
        status: disabled

'''

VALID_PORT_FIELDS = ['port', 'protocol', 'service_group', 'status']

def validate_ports(module, ports):
    for item in ports:
        for key in item:
            if key not in VALID_PORT_FIELDS:
                module.fail_json(msg="invalid port field (%s), must be one of: %s" % (key, ','.join(VALID_PORT_FIELDS)))

        # validate the port number is present and an integer
        if 'port' in item:
            try:
                item['port'] = int(item['port'])
            except:
                module.fail_json(msg="port definitions must be integers")
        else:
            module.fail_json(msg="port definitions must define the port field")

        # validate the port protocol is present, and convert it to
        # the internal API integer value (and validate it)
        if 'protocol' in item:
            protocol = axapi_get_vport_protocol(item['protocol'])
            if not protocol:
                module.fail_json(msg="invalid port protocol, must be one of: %s" % ','.join(AXAPI_VPORT_PROTOCOLS))
            else:
                item['protocol'] = protocol
        else:
            module.fail_json(msg="port definitions must define the port protocol (%s)" % ','.join(AXAPI_VPORT_PROTOCOLS))

        # convert the status to the internal API integer value
        if 'status' in item:
            item['status'] = axapi_enabled_disabled(item['status'])
        else:
            item['status'] = 1

        # ensure the service_group field is at least present
        if 'service_group' not in item:
            item['service_group'] = ''

def main():
    argument_spec = a10_argument_spec()
    argument_spec.update(url_argument_spec())
    argument_spec.update(
        dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            virtual_server=dict(type='str', aliases=['vip', 'virtual'], required=True),
            virtual_server_ip=dict(type='str', aliases=['ip', 'address'], required=True),
            virtual_server_status=dict(type='str', default='enabled', aliases=['status'], choices=['enabled', 'disabled']),
            virtual_server_ports=dict(type='list', required=True),
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
    slb_virtual = module.params['virtual_server']
    slb_virtual_ip = module.params['virtual_server_ip']
    slb_virtual_status = module.params['virtual_server_status']
    slb_virtual_ports = module.params['virtual_server_ports']

    if slb_virtual is None:
        module.fail_json(msg='virtual_server is required')

    validate_ports(module, slb_virtual_ports)

    axapi_base_url = 'https://%s/services/rest/V2.1/?format=json' % host
    session_url = axapi_authenticate(module, axapi_base_url, username, password)

    slb_virtual_data = axapi_call(module, session_url + '&method=slb.virtual_server.search', json.dumps({'name': slb_virtual}))
    slb_virtual_exists = not axapi_failure(slb_virtual_data)

    changed = False
    if state == 'present':
        json_post = {
            'virtual_server': {
                'name': slb_virtual,
                'address': slb_virtual_ip,
                'status': axapi_enabled_disabled(slb_virtual_status),
                'vport_list': slb_virtual_ports,
            }
        }

        # before creating/updating we need to validate that any
        # service groups defined in the ports list exist since
        # since the API will still create port definitions for
        # them while indicating a failure occurred
        checked_service_groups = []
        for port in slb_virtual_ports:
            if 'service_group' in port and port['service_group'] not in checked_service_groups:
                # skip blank service group entries
                if port['service_group'] == '':
                    continue
                result = axapi_call(module, session_url + '&method=slb.service_group.search', json.dumps({'name': port['service_group']}))
                if axapi_failure(result):
                    module.fail_json(msg="the service group %s specified in the ports list does not exist" % port['service_group'])
                checked_service_groups.append(port['service_group'])

        if not slb_virtual_exists:
            result = axapi_call(module, session_url + '&method=slb.virtual_server.create', json.dumps(json_post))
            if axapi_failure(result):
                module.fail_json(msg="failed to create the virtual server: %s" % result['response']['err']['msg'])
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
                        if src_port['port'] == dst_port['port']:
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

            defined_ports = slb_virtual_data.get('virtual_server', {}).get('vport_list', [])

            # we check for a needed update both ways, in case ports
            # are missing from either the ones specified by the user
            # or from those on the device
            if needs_update(defined_ports, slb_virtual_ports) or needs_update(slb_virtual_ports, defined_ports):
                result = axapi_call(module, session_url + '&method=slb.virtual_server.update', json.dumps(json_post))
                if axapi_failure(result):
                    module.fail_json(msg="failed to create the virtual server: %s" % result['response']['err']['msg'])
                changed = True

        # if we changed things, get the full info regarding
        # the service group for the return data below
        if changed:
            result = axapi_call(module, session_url + '&method=slb.virtual_server.search', json.dumps({'name': slb_virtual}))
        else:
            result = slb_virtual_data
    elif state == 'absent':
        if slb_virtual_exists:
            result = axapi_call(module, session_url + '&method=slb.virtual_server.delete', json.dumps({'name': slb_virtual}))
            changed = True
        else:
            result = dict(msg="the virtual server was not present")

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
if __name__ == '__main__':
    main()

