#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Mischa Peters <mpeters@a10networks.com>,
# (c) 2016, Eric Chou <ericc@a10networks.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: a10_server
version_added: 1.8
short_description: Manage A10 Networks AX/SoftAX/Thunder/vThunder devices' server object.
description:
    - Manage SLB (Server Load Balancer) server objects on A10 Networks devices via aXAPIv2.
author: "Eric Chou (@ericchou) 2016, Mischa Peters (@mischapeters) 2014"
notes:
    - Requires A10 Networks aXAPI 2.1.
extends_documentation_fragment:
  - a10
  - url
options:
  partition:
    version_added: "2.3"
    description:
      - set active-partition
  server_name:
    description:
      - The SLB (Server Load Balancer) server name.
    required: true
    aliases: ['server']
  server_ip:
    description:
      - The SLB server IPv4 address.
    aliases: ['ip', 'address']
  server_status:
    description:
      - The SLB virtual server status.
    default: enabled
    aliases: ['status']
    choices: ['enabled', 'disabled']
  server_ports:
    description:
      - A list of ports to create for the server. Each list item should be a
        dictionary which specifies the C(port:) and C(protocol:), but can also optionally
        specify the C(status:). See the examples below for details. This parameter is
        required when C(state) is C(present).
    aliases: ['port']
  state:
    description:
      - This is to specify the operation to create, update or remove SLB server.
    default: present
    choices: ['present', 'absent']
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled devices using self-signed certificates.
    version_added: 2.3
    type: bool
    default: 'yes'

'''

EXAMPLES = '''
# Create a new server
- a10_server:
    host: a10.mydomain.com
    username: myadmin
    password: mypassword
    partition: mypartition
    server: test
    server_ip: 1.1.1.100
    server_ports:
      - port_num: 8080
        protocol: tcp
      - port_num: 8443
        protocol: TCP

'''

RETURN = '''
content:
  description: the full info regarding the slb_server
  returned: success
  type: string
  sample: "mynewserver"
'''
import json

from ansible.module_utils.network.a10.a10 import (axapi_call, a10_argument_spec, axapi_authenticate, axapi_failure, axapi_get_port_protocol,
                                                  axapi_enabled_disabled, AXAPI_PORT_PROTOCOLS)
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import url_argument_spec


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
            partition=dict(type='str', default=[]),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    host = module.params['host']
    partition = module.params['partition']
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
        }
    }

    # add optional module parameters
    if slb_server_ip:
        json_post['server']['host'] = slb_server_ip

    if slb_server_ports:
        json_post['server']['port_list'] = slb_server_ports

    if slb_server_status:
        json_post['server']['status'] = axapi_enabled_disabled(slb_server_status)

    axapi_call(module, session_url + '&method=system.partition.active', json.dumps({'name': partition}))

    slb_server_data = axapi_call(module, session_url + '&method=slb.server.search', json.dumps({'name': slb_server}))
    slb_server_exists = not axapi_failure(slb_server_data)

    changed = False
    if state == 'present':
        if not slb_server_exists:
            if not slb_server_ip:
                module.fail_json(msg='you must specify an IP address when creating a server')

            result = axapi_call(module, session_url + '&method=slb.server.create', json.dumps(json_post))
            if axapi_failure(result):
                module.fail_json(msg="failed to create the server: %s" % result['response']['err']['msg'])
            changed = True
        else:
            def port_needs_update(src_ports, dst_ports):
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

            def status_needs_update(current_status, new_status):
                '''
                Check to determine if we want to change the status of a server.
                If there is a difference between the current status of the server and
                the desired status, return true, otherwise false.
                '''
                if current_status != new_status:
                    return True
                return False

            defined_ports = slb_server_data.get('server', {}).get('port_list', [])
            current_status = slb_server_data.get('server', {}).get('status')

            # we check for a needed update several ways
            # - in case ports are missing from the ones specified by the user
            # - in case ports are missing from those on the device
            # - in case we are change the status of a server
            if (port_needs_update(defined_ports, slb_server_ports) or
                    port_needs_update(slb_server_ports, defined_ports) or
                    status_needs_update(current_status, axapi_enabled_disabled(slb_server_status))):
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
            result = dict(msg="the server was not present")

    # if the config has changed, save the config unless otherwise requested
    if changed and write_config:
        write_result = axapi_call(module, session_url + '&method=system.action.write_memory')
        if axapi_failure(write_result):
            module.fail_json(msg="failed to save the configuration: %s" % write_result['response']['err']['msg'])

    # log out of the session nicely and exit
    axapi_call(module, session_url + '&method=session.close')
    module.exit_json(changed=changed, content=result)


if __name__ == '__main__':
    main()
