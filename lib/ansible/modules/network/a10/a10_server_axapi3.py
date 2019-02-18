#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Mischa Peters <mpeters@a10networks.com>
# Copyright: (c) 2016, Eric Chou <ericc@a10networks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: a10_server_axapi3
version_added: 2.3
short_description: Manage A10 Networks AX/SoftAX/Thunder/vThunder devices
description:
    - Manage SLB (Server Load Balancer) server objects on A10 Networks devices via aXAPIv3.
author: "Eric Chou (@ericchou) based on previous work by Mischa Peters (@mischapeters)"
extends_documentation_fragment:
  - a10
  - url
options:
  server_name:
    description:
      - The SLB (Server Load Balancer) server name.
    required: true
    aliases: ['server']
  server_ip:
    description:
      - The SLB (Server Load Balancer) server IPv4 address.
    required: true
    aliases: ['ip', 'address']
  server_status:
    description:
      - The SLB (Server Load Balancer) virtual server status.
    default: enable
    aliases: ['action']
    choices: ['enable', 'disable']
  server_ports:
    description:
      - A list of ports to create for the server. Each list item should be a dictionary which specifies the C(port:)
        and C(protocol:).
    aliases: ['port']
  operation:
    description:
      - Create, Update or Remove SLB server. For create and update operation, we use the IP address and server
        name specified in the POST message. For delete operation, we use the server name in the request URI.
    default: create
    choices: ['create', 'update', 'remove']
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled devices using self-signed certificates.
    type: bool
    default: 'yes'

'''

RETURN = '''
#
'''

EXAMPLES = '''
# Create a new server
- a10_server:
    host: a10.mydomain.com
    username: myadmin
    password: mypassword
    server: test
    server_ip: 1.1.1.100
    validate_certs: false
    server_status: enable
    write_config: yes
    operation: create
    server_ports:
      - port-number: 8080
        protocol: tcp
        action: enable
      - port-number: 8443
        protocol: TCP

'''
import json

from ansible.module_utils.network.a10.a10 import axapi_call_v3, a10_argument_spec, axapi_authenticate_v3, axapi_failure
from ansible.module_utils.network.a10.a10 import AXAPI_PORT_PROTOCOLS
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import url_argument_spec


VALID_PORT_FIELDS = ['port-number', 'protocol', 'action']


def validate_ports(module, ports):
    for item in ports:
        for key in item:
            if key not in VALID_PORT_FIELDS:
                module.fail_json(msg="invalid port field (%s), must be one of: %s" % (key, ','.join(VALID_PORT_FIELDS)))

        # validate the port number is present and an integer
        if 'port-number' in item:
            try:
                item['port-number'] = int(item['port-number'])
            except Exception:
                module.fail_json(msg="port-number entries in the port definitions must be integers")
        else:
            module.fail_json(msg="port definitions must define the port-number field")

        # validate the port protocol is present, no need to convert to the internal API integer value in v3
        if 'protocol' in item:
            protocol = item['protocol']
            if not protocol:
                module.fail_json(msg="invalid port protocol, must be one of: %s" % ','.join(AXAPI_PORT_PROTOCOLS))
            else:
                item['protocol'] = protocol
        else:
            module.fail_json(msg="port definitions must define the port protocol (%s)" % ','.join(AXAPI_PORT_PROTOCOLS))

        # 'status' is 'action' in AXAPIv3
        # no need to convert the status, a.k.a action, to the internal API integer value in v3
        # action is either enabled or disabled
        if 'action' in item:
            action = item['action']
            if action not in ['enable', 'disable']:
                module.fail_json(msg="server action must be enable or disable")
        else:
            item['action'] = 'enable'


def main():
    argument_spec = a10_argument_spec()
    argument_spec.update(url_argument_spec())
    argument_spec.update(
        dict(
            operation=dict(type='str', default='create', choices=['create', 'update', 'delete']),
            server_name=dict(type='str', aliases=['server'], required=True),
            server_ip=dict(type='str', aliases=['ip', 'address'], required=True),
            server_status=dict(type='str', default='enable', aliases=['action'], choices=['enable', 'disable']),
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
    operation = module.params['operation']
    write_config = module.params['write_config']
    slb_server = module.params['server_name']
    slb_server_ip = module.params['server_ip']
    slb_server_status = module.params['server_status']
    slb_server_ports = module.params['server_ports']

    axapi_base_url = 'https://{0}/axapi/v3/'.format(host)
    axapi_auth_url = axapi_base_url + 'auth/'
    signature = axapi_authenticate_v3(module, axapi_auth_url, username, password)

    # validate the ports data structure
    validate_ports(module, slb_server_ports)

    json_post = {
        "server-list": [
            {
                "name": slb_server,
                "host": slb_server_ip
            }
        ]
    }

    # add optional module parameters
    if slb_server_ports:
        json_post['server-list'][0]['port-list'] = slb_server_ports

    if slb_server_status:
        json_post['server-list'][0]['action'] = slb_server_status

    slb_server_data = axapi_call_v3(module, axapi_base_url + 'slb/server/', method='GET', body='', signature=signature)

    # for empty slb server list
    if axapi_failure(slb_server_data):
        slb_server_exists = False
    else:
        slb_server_list = [server['name'] for server in slb_server_data['server-list']]
        if slb_server in slb_server_list:
            slb_server_exists = True
        else:
            slb_server_exists = False

    changed = False
    if operation == 'create':
        if slb_server_exists is False:
            result = axapi_call_v3(module, axapi_base_url + 'slb/server/', method='POST', body=json.dumps(json_post), signature=signature)
            if axapi_failure(result):
                module.fail_json(msg="failed to create the server: %s" % result['response']['err']['msg'])
            changed = True
        else:
            module.fail_json(msg="server already exists, use state='update' instead")
            changed = False
        # if we changed things, get the full info regarding result
        if changed:
            result = axapi_call_v3(module, axapi_base_url + 'slb/server/' + slb_server, method='GET', body='', signature=signature)
        else:
            result = slb_server_data
    elif operation == 'delete':
        if slb_server_exists:
            result = axapi_call_v3(module, axapi_base_url + 'slb/server/' + slb_server, method='DELETE', body='', signature=signature)
            if axapi_failure(result):
                module.fail_json(msg="failed to delete server: %s" % result['response']['err']['msg'])
            changed = True
        else:
            result = dict(msg="the server was not present")
    elif operation == 'update':
        if slb_server_exists:
            result = axapi_call_v3(module, axapi_base_url + 'slb/server/', method='PUT', body=json.dumps(json_post), signature=signature)
            if axapi_failure(result):
                module.fail_json(msg="failed to update server: %s" % result['response']['err']['msg'])
            changed = True
        else:
            result = dict(msg="the server was not present")

    # if the config has changed, save the config unless otherwise requested
    if changed and write_config:
        write_result = axapi_call_v3(module, axapi_base_url + 'write/memory/', method='POST', body='', signature=signature)
        if axapi_failure(write_result):
            module.fail_json(msg="failed to save the configuration: %s" % write_result['response']['err']['msg'])

    # log out gracefully and exit
    axapi_call_v3(module, axapi_base_url + 'logoff/', method='POST', body='', signature=signature)
    module.exit_json(changed=changed, content=result)


if __name__ == '__main__':
    main()
