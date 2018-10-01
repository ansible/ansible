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

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
    state:
        description:
        - Create or modify an organization.
        choices: [absent, present, query]
        default: present
    net_name:
        description:
        - Name of a network.
        aliases: [name, network]
    net_id:
        description:
        - ID number of a network.
    org_name:
        description:
        - Name of organization associated to a network.
    org_id:
        description:
        - ID of organization associated to a network.
    server:
        description:
        - Syslog server settings
        suboptions:
            host:
                description:
                - IP address or hostname of Syslog server.
            port:
                description:
                - Port number Syslog server is listening on.
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
- name: Query Syslog configurations on network named MyNet in the YourOrg organization
  meraki_snmp:
    auth_key: abc12345
    status: query
    org_name: YourOrg
    net_name: MyNet
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about the created or manipulated object.
    returned: info
    type: complex
    contains:
      host:
        description: Hostname or IP address of Syslog server.
        returned: success
        type: string
        sample: 192.0.1.1
      port:
        description: Port number for Syslog communication.
        returned: success
        type: int
        sample: 443
      roles:
        description: Organization ID which owns the network.
        returned: success
        type: list
        sample: "Wireless event log", "URLs"
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

def validate_roles(meraki, data):
    ''' Validates whether provided rules are valid '''
    valid_roles = ['WIRELESS EVENT LOG',
                   'APPLIANCE EVENT LOG',
                   'SWITCH EVENT LOG',
                   'AIR MARSHAL EVENTS',
                   'FLOWS',
                   'URLS',
                   'IDS ALERTS',
                   'SECURITY EVENTS']
    for server in data:
        for role in server:
            if role.upper() not in valid_roles:
                meraki.fail_json(msg='{role} is not a valid Syslog role.'.format(role=role))

def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    server_arg_spec = dict(host=dict(type='str'),
                           port=dict(type='int'),
                           roles=dict(type='list'),
                           )

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        servers=dict(type='list', element='dict', options=server_arg_spec)
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
    net_id = meraki.get_netid(net_name=meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        path = meraki.construct_path('query_update', net_id=net_id)
        r = meraki.request(path, METHOD='GET')
        if meraki.status == 200:
            meraki.result['data'] = r
    elif meraki.params['state'] == 'present':
        # Construct payload
        payload = dict()
        payload['servers'] = meraki.params['servers']

        path = meraki.construct_path('query_update', net_id=net_id)
        r = meraki.request(path, METHOD='GET')
        if meraki.status == 200:
            original = r

        validate_roles(meraki, payload)
        if meraki.is_update_required(original, payload):
            path = meraki.construct_path('query_update', net_id=net_id)
            r = meraki.request(path, METHOD='PUT', payload=payload)
            if meraki.status == 200:
                meraki.result['data'] = r
                meraki.result['changed'] = True
    elif meraki.params['state'] == 'absent':
        # Construct payload
        payload = dict()

        path = meraki.construct_path('query_update', net_id=net_id)
        r = meraki.request(path, METHOD='GET')
        if meraki.status == 200:
            original = r

        if meraki.is_update_required(original, payload):
            path = meraki.construct_path('query_update', net_id=net_id)
            r = meraki.request(path, METHOD='PUT', payload=payload)
            if meraki.status == 200:
                meraki.result['data'] = r
                meraki.result['changed'] = True        


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
