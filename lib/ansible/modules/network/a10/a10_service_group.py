#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Mischa Peters <mpeters@a10networks.com>,
#           Eric Chou <ericc@a10networks.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: a10_service_group
version_added: 1.8
short_description: Manage A10 Networks AX/SoftAX/Thunder/vThunder devices' service groups.
description:
    - Manage SLB (Server Load Balancing) service-group objects on A10 Networks devices via aXAPIv2.
author:
  - Eric Chou (@ericchou)
  - Mischa Peters (@mischapeters)
notes:
    - Requires A10 Networks aXAPI 2.1.
    - When a server doesn't exist and is added to the service-group the server will be created.
extends_documentation_fragment:
  - a10
  - url
options:
  state:
    description:
      - If the specified service group should exists.
    default: present
    choices: ['present', 'absent']
  partition:
    version_added: "2.3"
    description:
      - set active-partition
  service_group:
    description:
      - The SLB (Server Load Balancing) service-group name
    required: true
    aliases: ['service', 'pool', 'group']
  service_group_protocol:
    description:
      - The SLB service-group protocol of TCP or UDP.
    default: tcp
    aliases: ['proto', 'protocol']
    choices: ['tcp', 'udp']
  service_group_method:
    description:
      - The SLB service-group load balancing method, such as round-robin or weighted-rr.
    default: round-robin
    aliases: ['method']
    choices:
        - 'round-robin'
        - 'weighted-rr'
        - 'least-connection'
        - 'weighted-least-connection'
        - 'service-least-connection'
        - 'service-weighted-least-connection'
        - 'fastest-response'
        - 'least-request'
        - 'round-robin-strict'
        - 'src-ip-only-hash'
        - 'src-ip-hash'
  servers:
    description:
      - A list of servers to add to the service group. Each list item should be a
        dictionary which specifies the C(server:) and C(port:), but can also optionally
        specify the C(status:). See the examples below for details.
    aliases: ['server', 'member']
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled devices using self-signed certificates.
    type: bool
    default: 'yes'

'''

EXAMPLES = '''
# Create a new service-group
- a10_service_group:
    host: a10.mydomain.com
    username: myadmin
    password: mypassword
    partition: mypartition
    service_group: sg-80-tcp
    servers:
      - server: foo1.mydomain.com
        port: 8080
      - server: foo2.mydomain.com
        port: 8080
      - server: foo3.mydomain.com
        port: 8080
      - server: foo4.mydomain.com
        port: 8080
        status: disabled

'''

RETURN = '''
content:
  description: the full info regarding the slb_service_group
  returned: success
  type: str
  sample: "mynewservicegroup"
'''
import json

from ansible.module_utils.network.a10.a10 import (axapi_call, a10_argument_spec, axapi_authenticate, axapi_failure, axapi_enabled_disabled)
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import url_argument_spec


VALID_SERVICE_GROUP_FIELDS = ['name', 'protocol', 'lb_method']
VALID_SERVER_FIELDS = ['server', 'port', 'status']


def validate_servers(module, servers):
    for item in servers:
        for key in item:
            if key not in VALID_SERVER_FIELDS:
                module.fail_json(msg="invalid server field (%s), must be one of: %s" % (key, ','.join(VALID_SERVER_FIELDS)))

        # validate the server name is present
        if 'server' not in item:
            module.fail_json(msg="server definitions must define the server field")

        # validate the port number is present and an integer
        if 'port' in item:
            try:
                item['port'] = int(item['port'])
            except Exception:
                module.fail_json(msg="server port definitions must be integers")
        else:
            module.fail_json(msg="server definitions must define the port field")

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
            service_group=dict(type='str', aliases=['service', 'pool', 'group'], required=True),
            service_group_protocol=dict(type='str', default='tcp', aliases=['proto', 'protocol'], choices=['tcp', 'udp']),
            service_group_method=dict(type='str', default='round-robin',
                                      aliases=['method'],
                                      choices=['round-robin',
                                               'weighted-rr',
                                               'least-connection',
                                               'weighted-least-connection',
                                               'service-least-connection',
                                               'service-weighted-least-connection',
                                               'fastest-response',
                                               'least-request',
                                               'round-robin-strict',
                                               'src-ip-only-hash',
                                               'src-ip-hash']),
            servers=dict(type='list', aliases=['server', 'member'], default=[]),
            partition=dict(type='str', default=[]),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    host = module.params['host']
    username = module.params['username']
    password = module.params['password']
    partition = module.params['partition']
    state = module.params['state']
    write_config = module.params['write_config']
    slb_service_group = module.params['service_group']
    slb_service_group_proto = module.params['service_group_protocol']
    slb_service_group_method = module.params['service_group_method']
    slb_servers = module.params['servers']

    if slb_service_group is None:
        module.fail_json(msg='service_group is required')

    axapi_base_url = 'https://' + host + '/services/rest/V2.1/?format=json'
    load_balancing_methods = {'round-robin': 0,
                              'weighted-rr': 1,
                              'least-connection': 2,
                              'weighted-least-connection': 3,
                              'service-least-connection': 4,
                              'service-weighted-least-connection': 5,
                              'fastest-response': 6,
                              'least-request': 7,
                              'round-robin-strict': 8,
                              'src-ip-only-hash': 14,
                              'src-ip-hash': 15}

    if not slb_service_group_proto or slb_service_group_proto.lower() == 'tcp':
        protocol = 2
    else:
        protocol = 3

    # validate the server data list structure
    validate_servers(module, slb_servers)

    json_post = {
        'service_group': {
            'name': slb_service_group,
            'protocol': protocol,
            'lb_method': load_balancing_methods[slb_service_group_method],
        }
    }

    # first we authenticate to get a session id
    session_url = axapi_authenticate(module, axapi_base_url, username, password)
    # then we select the active-partition
    axapi_call(module, session_url + '&method=system.partition.active', json.dumps({'name': partition}))
    # then we check to see if the specified group exists
    slb_result = axapi_call(module, session_url + '&method=slb.service_group.search', json.dumps({'name': slb_service_group}))
    slb_service_group_exist = not axapi_failure(slb_result)

    changed = False
    if state == 'present':
        # before creating/updating we need to validate that servers
        # defined in the servers list exist to prevent errors
        checked_servers = []
        for server in slb_servers:
            result = axapi_call(module, session_url + '&method=slb.server.search', json.dumps({'name': server['server']}))
            if axapi_failure(result):
                module.fail_json(msg="the server %s specified in the servers list does not exist" % server['server'])
            checked_servers.append(server['server'])

        if not slb_service_group_exist:
            result = axapi_call(module, session_url + '&method=slb.service_group.create', json.dumps(json_post))
            if axapi_failure(result):
                module.fail_json(msg=result['response']['err']['msg'])
            changed = True
        else:
            # check to see if the service group definition without the
            # server members is different, and update that individually
            # if it needs it
            do_update = False
            for field in VALID_SERVICE_GROUP_FIELDS:
                if json_post['service_group'][field] != slb_result['service_group'][field]:
                    do_update = True
                    break

            if do_update:
                result = axapi_call(module, session_url + '&method=slb.service_group.update', json.dumps(json_post))
                if axapi_failure(result):
                    module.fail_json(msg=result['response']['err']['msg'])
                changed = True

        # next we pull the defined list of servers out of the returned
        # results to make it a bit easier to iterate over
        defined_servers = slb_result.get('service_group', {}).get('member_list', [])

        # next we add/update new member servers from the user-specified
        # list if they're different or not on the target device
        for server in slb_servers:
            found = False
            different = False
            for def_server in defined_servers:
                if server['server'] == def_server['server']:
                    found = True
                    for valid_field in VALID_SERVER_FIELDS:
                        if server[valid_field] != def_server[valid_field]:
                            different = True
                            break
                    if found or different:
                        break
            # add or update as required
            server_data = {
                "name": slb_service_group,
                "member": server,
            }
            if not found:
                result = axapi_call(module, session_url + '&method=slb.service_group.member.create', json.dumps(server_data))
                changed = True
            elif different:
                result = axapi_call(module, session_url + '&method=slb.service_group.member.update', json.dumps(server_data))
                changed = True

        # finally, remove any servers that are on the target
        # device but were not specified in the list given
        for server in defined_servers:
            found = False
            for slb_server in slb_servers:
                if server['server'] == slb_server['server']:
                    found = True
                    break
            # remove if not found
            server_data = {
                "name": slb_service_group,
                "member": server,
            }
            if not found:
                result = axapi_call(module, session_url + '&method=slb.service_group.member.delete', json.dumps(server_data))
                changed = True

        # if we changed things, get the full info regarding
        # the service group for the return data below
        if changed:
            result = axapi_call(module, session_url + '&method=slb.service_group.search', json.dumps({'name': slb_service_group}))
        else:
            result = slb_result
    elif state == 'absent':
        if slb_service_group_exist:
            result = axapi_call(module, session_url + '&method=slb.service_group.delete', json.dumps({'name': slb_service_group}))
            changed = True
        else:
            result = dict(msg="the service group was not present")

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
