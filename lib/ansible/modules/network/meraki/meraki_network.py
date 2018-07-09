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
short_description: Manage networks in the Meraki cloud
version_added: "2.6"
description:
- Allows for creation, management, and visibility into networks within Meraki.

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
    type:
        description:
        - Type of network device network manages.
        - Required when creating a network.
        choices: [appliance, combined, switch, wireless]
        aliases: [net_type]
    tags:
        description:
        - Comma delimited list of tags to assign to network.
    timezone:
        description:
        - Timezone associated to network.
        - See U(https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for a list of valid timezones.

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: List all networks associated to the YourOrg organization
  meraki_network:
    auth_key: abc12345
    status: query
    org_name: YourOrg
  delegate_to: localhost
- name: Query network named MyNet in the YourOrg organization
  meraki_network:
    auth_key: abc12345
    status: query
    org_name: YourOrg
    net_name: MyNet
  delegate_to: localhost
- name: Create network named MyNet in the YourOrg organization
  meraki_network:
    auth_key: abc12345
    status: present
    org_name: YourOrg
    net_name: MyNet
    type: switch
    timezone: America/Chicago
    tags: production, chicago
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


def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        type=dict(type='str', choices=['wireless', 'switch', 'appliance', 'combined'], aliases=['net_type']),
        tags=dict(type='str'),
        timezone=dict(type='str'),
        net_name=dict(type='str', aliases=['name', 'network']),
        state=dict(type='str', choices=['present', 'query', 'absent'], default='present'),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )

    meraki = MerakiModule(module, function='network')
    module.params['follow_redirects'] = 'all'
    payload = None

    create_urls = {'network': '/organizations/{org_id}/networks'}
    update_urls = {'network': '/networks/{net_id}'}
    delete_urls = {'network': '/networks/{net_id}'}
    meraki.url_catalog['create'] = create_urls
    meraki.url_catalog['update'] = update_urls
    meraki.url_catalog['delete'] = delete_urls

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

    # Construct payload
    if meraki.params['state'] == 'present':
        payload = {'name': meraki.params['net_name'],
                   'type': meraki.params['type'],
                   }
        if meraki.params['tags']:
            payload['tags'] = construct_tags(meraki.params['tags'])
        if meraki.params['timezone']:
            payload['timeZone'] = meraki.params['timezone']
        if meraki.params['type'] == 'combined':
            payload['type'] = 'switch wireless appliance'

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    if meraki.params['org_name']:
        nets = meraki.get_nets(org_name=meraki.params['org_name'])
    elif meraki.params['org_id']:
        nets = meraki.get_nets(org_id=meraki.params['org_id'])

    if meraki.params['state'] == 'query':
        if not meraki.params['net_name'] and not meraki.params['net_id']:
            meraki.result['data'] = nets
        elif meraki.params['net_name'] or meraki.params['net_id'] is not None:
            meraki.result['data'] = meraki.get_net(meraki.params['org_name'],
                                                   meraki.params['net_name'],
                                                   nets
                                                   )
    elif meraki.params['state'] == 'present':
        if meraki.params['net_name']:  # FIXME: Idempotency check is ugly here, improve
            if is_net_valid(meraki, meraki.params['net_name'], nets) is False:
                if meraki.params['org_name']:  # FIXME: This can be cleaned up...maybe
                    path = meraki.construct_path('create',
                                                 org_name=meraki.params['org_name']
                                                 )
                elif meraki.params['org_id']:
                    path = meraki.construct_path('create',
                                                 org_id=meraki.params['org_id']
                                                 )
                r = meraki.request(path,
                                   method='POST',
                                   payload=json.dumps(payload)
                                   )
                meraki.result['data'] = r
                meraki.result['changed'] = True
            else:
                net = meraki.get_net(meraki.params['org_name'], meraki.params['net_name'], data=nets)
                proposed = payload
                if meraki.params['timezone']:
                    proposed['timeZone'] = meraki.params['timezone']
                else:
                    proposed['timeZone'] = 'America/Los_Angeles'
                if not meraki.params['tags']:
                    proposed['tags'] = None
                if not proposed['type']:
                    proposed['type'] = net['type']

                if meraki.is_update_required(net, payload):
                    path = meraki.construct_path('update',
                                                 net_id=meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)
                                                 )
                    r = meraki.request(path,
                                       method='PUT',
                                       payload=json.dumps(payload))
                    meraki.result['data'] = r
                    meraki.result['changed'] = True
    elif meraki.params['state'] == 'absent':
        if is_net_valid(meraki, meraki.params['net_name'], nets) is True:
            net_id = meraki.get_net_id(org_name=meraki.params['org_name'],
                                       net_name=meraki.params['net_name'],
                                       data=nets)
            path = meraki.construct_path('delete', net_id=net_id)
            r = meraki.request(path, method='DELETE')
            if meraki.status == 204:
                meraki.result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
