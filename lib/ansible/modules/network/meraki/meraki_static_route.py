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
module: meraki_network
short_description: Manage static routes in the Meraki cloud
version_added: "2.6"
description:
- Allows for creation, management, and visibility into static routes within Meraki.

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
    name:
        description:
        - Descriptive name of the static route.
    subnet:
        description:
        - CIDR notation based subnet for static route.
    gateway_ip:
        description:
        - IP address of the gateway for the subnet.

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: List all networks associated to the YourOrg organization
  meraki_network:
    auth_key: abc12345
    state: query
    org_name: YourOrg
  delegate_to: localhost
- name: Query network named MyNet in the YourOrg organization
  meraki_network:
    auth_key: abc12345
    state: query
    org_name: YourOrg
    net_name: MyNet
  delegate_to: localhost
- name: Create network named MyNet in the YourOrg organization
  meraki_network:
    auth_key: abc12345
    state: present
    org_name: YourOrg
    net_name: MyNet
    type: switch
    timezone: America/Chicago
    tags: production, chicago
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about the created or manipulated object.
    returned: info
    type: complex
    contains:
      id:
        description: Identification string of network.
        returned: success
        type: string
        sample: N_12345
      name:
        description: Written name of network.
        returned: success
        type: string
        sample: YourNet
      organizationId:
        description: Organization ID which owns the network.
        returned: success
        type: string
        sample: 0987654321
      tags:
        description: Space delimited tags assigned to network.
        returned: success
        type: string
        sample: " production wireless "
      timeZone:
        description: Timezone where network resides.
        returned: success
        type: string
        sample: America/Chicago
      type:
        description: Functional type of network.
        returned: success
        type: string
        sample: switch
      disableMyMerakiCom:
        description: States whether U(my.meraki.com) and other device portals should be disabled.
        returned: success
        type: bool
        sample: true
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def get_static_routes(meraki, net_id):
    path = meraki.construct_path('get_all', net_id=net_id)
    r = meraki.request(path, method='GET')
    return r


def get_static_route(meraki, net_id, route_id):
    path = meraki.construct_path('get_one', net_id=net_id, custom={'route_id': meraki.params['route_id']})
    r = meraki.request(path, method='GET')
    return r


def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        net_name=dict(type='str'),
        name=dict(type='str'),
        subnet=dict(type='str'),
        gateway_ip=dict(type='str'),
        state=dict(type='str', choices=['absent', 'query', 'present']),
        fixed_ip_assignments=dict(type='list'),
        reserved_ip_ranges=dict(type='list'),
        route_id=dict(type='str'),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )

    meraki = MerakiModule(module, function='static_route')
    module.params['follow_redirects'] = 'all'
    payload = None

    query_urls = {'static_route': '/networks/{net_id}/staticRoutes'}
    query_one_urls = {'static_route': '/networks/{net_id}/staticRoutes/{route_id}'}
    create_urls = {'static_route': '/networks/{net_id}/staticRoutes/'}
    update_urls = {'static_route': '/networks/{net_id}/staticRoutes/{route_id}'}
    delete_urls = {'static_route': '/networks/{net_id}/staticRoutes/{route_id}'}
    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['get_one'].update(query_one_urls)
    meraki.url_catalog['create'] = create_urls
    meraki.url_catalog['update'] = update_urls
    meraki.url_catalog['delete'] = delete_urls

    if not meraki.params['org_name'] and not meraki.params['org_id']:
        meraki.fail_json(msg='org_name or org_id parameters are required')
    if not meraki.params['net_name'] and not meraki.params['net_id']:
        meraki.fail_json(msg='net_name or net_id parameters are required')
    if meraki.params['net_name'] and meraki.params['net_id']:
        meraki.fail_json(msg='net_name and net_id are mutually exclusive')

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return meraki.result

    # Construct payload
    if meraki.params['state'] == 'present':
        payload = dict()
        if meraki.params['net_name']:
            payload['name'] = meraki.params['net_name']


    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    org_id = meraki.params['org_id']
    if not org_id:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    nets = meraki.get_nets(org_id=org_id)
    net_id = meraki.params['net_id']
    if net_id is None:
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        if meraki.params['route_id'] is not None:
            meraki.result['data'] = get_static_route(meraki, net_id, meraki.params['route_id'])
        else:
            meraki.result['data'] = get_static_routes(meraki, net_id)
    elif meraki.params['state'] == 'present':
        payload = dict()
        payload['name'] = meraki.params['name']
        payload['subnet'] = meraki.params['subnet']
        payload['gatewayIp'] = meraki.params['gateway_ip']
        if meraki.params['fixed_ip_assignments'] is not None:
            payload['fixedIpAssignments'] = meraki.params['fixed_ip_assignments']
        if meraki.params['reserved_ip_ranges'] is not None:
            payload['reserved_ip_ranges'] = meraki.params['reserved_ip_ranges']
        if meraki.params['route_id']:
            existing_route = get_static_route(meraki, net_id, meraki.params['route_id'])
            if meraki.is_update_required(existing_route, payload, optional_ignore=['id']):
                path = meraki.construct_path('update', net_id=net_id, custom={'route_id': meraki.params['route_id']})
                meraki.result['data'] = meraki.request(path, method="PUT", payload=json.dumps(payload))
                meraki.result['changed'] = True
        else:
                path = meraki.construct_path('create', net_id=net_id)
                meraki.result['data'] = meraki.request(path, method="POST", payload=json.dumps(payload))
                meraki.result['changed'] = True
    elif meraki.params['state'] == 'absent':
        path = meraki.construct_path('delete', net_id=net_id, custom={'route_id': meraki.params['route_id']})
        meraki.result['data'] = meraki.request(path, method='DELETE')
        meraki.result['changed'] = True


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
