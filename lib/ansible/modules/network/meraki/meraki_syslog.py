#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: meraki_syslog
short_description: Manage syslog server settings in the Meraki cloud.
version_added: "2.8"
description:
- Allows for creation and management of Syslog servers within Meraki.
notes:
- Changes to existing syslog servers replaces existing configuration. If you need to add to an
  existing configuration set state to query to gather the existing configuration and then modify or add.
options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
        type: str
    state:
        description:
        - Query or edit syslog servers
        - To delete a syslog server, do not include server in list of servers
        choices: [present, query]
        default: present
        type: str
    net_name:
        description:
        - Name of a network.
        aliases: [name, network]
        type: str
    net_id:
        description:
        - ID number of a network.
        type: str
    org_name:
        description:
        - Name of organization associated to a network.
        type: str
    org_id:
        description:
        - ID of organization associated to a network.
        type: str
    servers:
        description:
        - List of syslog server settings
        suboptions:
            host:
                description:
                - IP address or hostname of Syslog server.
            port:
                description:
                - Port number Syslog server is listening on.
                default: "514"
            roles:
                description:
                - List of applicable Syslog server roles.
                choices: ['Wireless event log',
                          'Appliance event log',
                          'Switch event log',
                          'Air Marshal events',
                          'Flows',
                          'URLs',
                          'IDS alerts',
                          'Security events']

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query syslog configurations on network named MyNet in the YourOrg organization
  meraki_syslog:
    auth_key: abc12345
    status: query
    org_name: YourOrg
    net_name: MyNet
  delegate_to: localhost

- name: Add single syslog server with Appliance event log role
  meraki_syslog:
    auth_key: abc12345
    status: query
    org_name: YourOrg
    net_name: MyNet
    servers:
      - host: 192.0.1.2
        port: 514
        roles:
          - Appliance event log
  delegate_to: localhost

- name: Add multiple syslog servers
  meraki_syslog:
    auth_key: abc12345
    status: query
    org_name: YourOrg
    net_name: MyNet
    servers:
      - host: 192.0.1.2
        port: 514
        roles:
          - Appliance event log
      - host: 192.0.1.3
        port: 514
        roles:
          - Appliance event log
          - Flows
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about the created or manipulated object.
    returned: info
    type: complex
    contains:
      host:
        description: Hostname or IP address of syslog server.
        returned: success
        type: string
        sample: 192.0.1.1
      port:
        description: Port number for syslog communication.
        returned: success
        type: string
        sample: 443
      roles:
        description: List of roles assigned to syslog server.
        returned: success
        type: list
        sample: "Wireless event log, URLs"
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def is_net_valid(meraki, net_name, data):
    for n in data:
        if n['name'] == net_name:
            return True
    return False


def construct_tags(tags):
    ''' Assumes tags are a comma separated list '''
    if tags is not None:
        tags = tags.replace(' ', '')
        tags = tags.split(',')
        tag_list = str()
        for t in tags:
            tag_list = tag_list + " " + t
        tag_list = tag_list + " "
        return tag_list
    return None

# This code was used but relying on API and/or server_arg_spec instead
# def validate_roles(meraki, data):
#     ''' Validates whether provided rules are valid '''
#     valid_roles = ['WIRELESS EVENT LOG',
#                    'APPLIANCE EVENT LOG',
#                    'SWITCH EVENT LOG',
#                    'AIR MARSHAL EVENTS',
#                    'FLOWS',
#                    'URLS',
#                    'IDS ALERTS',
#                    'SECURITY EVENTS']
#     for server in data['servers']:
#         for role in server['roles']:
#             if role.upper() not in valid_roles:
#                 # meraki.fail_json(msg="Heck yes")
#                 meraki.fail_json(msg='{0} is not a valid Syslog role.'.format(role))


def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    server_arg_spec = dict(host=dict(type='str'),
                           port=dict(type='int', default="514"),
                           roles=dict(type='list', choices=['Wireless Event log',
                                                            'Appliance event log',
                                                            'Switch event log',
                                                            'Air Marshal events',
                                                            'Flows',
                                                            'URLs',
                                                            'IDS alerts',
                                                            'Security events',
                                                            ]),
                           )

    argument_spec = meraki_argument_spec()
    argument_spec.update(net_id=dict(type='str'),
                         servers=dict(type='list', element='dict', options=server_arg_spec),
                         state=dict(type='str', choices=['present', 'query'], default='present'),
                         net_name=dict(type='str', aliases=['name', 'network']),
                         )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )

    meraki = MerakiModule(module, function='syslog')
    module.params['follow_redirects'] = 'all'
    payload = None

    syslog_urls = {'syslog': '/networks/{net_id}/syslogServers'}
    meraki.url_catalog['query_update'] = syslog_urls

    if not meraki.params['org_name'] and not meraki.params['org_id']:
        meraki.fail_json(msg='org_name or org_id parameters are required')
    if meraki.params['state'] != 'query':
        if not meraki.params['net_name'] or meraki.params['net_id']:
            meraki.fail_json(msg='net_name or net_id is required for present or absent states')
    if meraki.params['net_name'] and meraki.params['net_id']:
        meraki.fail_json(msg='net_name and net_id are mutually exclusive')

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return meraki.result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    org_id = meraki.params['org_id']
    if not org_id:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    nets = meraki.get_nets(org_id=org_id)
    net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        path = meraki.construct_path('query_update', net_id=net_id)
        r = meraki.request(path, method='GET')
        if meraki.status == 200:
            meraki.result['data'] = r
    elif meraki.params['state'] == 'present':
        # Construct payload
        payload = dict()
        payload['servers'] = meraki.params['servers']

        # Convert port numbers to string for idempotency checks
        for server in payload['servers']:
            if server['port']:
                server['port'] = str(server['port'])

        path = meraki.construct_path('query_update', net_id=net_id)
        r = meraki.request(path, method='GET')
        if meraki.status == 200:
            original = dict()
            original['servers'] = r

        if meraki.is_update_required(original, payload):
            path = meraki.construct_path('query_update', net_id=net_id)
            r = meraki.request(path, method='PUT', payload=json.dumps(payload))
            if meraki.status == 200:
                meraki.result['data'] = r
                meraki.result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
