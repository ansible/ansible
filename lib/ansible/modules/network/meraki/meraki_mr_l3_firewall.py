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
module: meraki_organization
short_description: Manage MR access point layer 3 firewalls in the Meraki cloud
version_added: "2.7"
description:
- Allows for creation, management, and visibility into layer 3 firewalls implemented on Meraki MR access points.
options:
    state:
        description:
        - Create or modify an organization.
        choices: ['present', 'query']
        default: present
    clone:
        description:
        - Organization to clone to a new organization.
    org_name:
        description:
        - Name of organization.
        - If C(clone) is specified, C(org_name) is the name of the new organization.
        aliases: [ name, organization ]
    org_id:
        description:
        - ID of organization.
        aliases: [ id ]
author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
'''

RETURN = r'''
data:
  description: Information about the organization which was created or modified
  returned: success
  type: complex
  contains:
    id:
      description: Unique identification number of organization
      returned: success
      type: int
      sample: 2930418
    name:
      description: Name of organization
      returned: success
      type: string
      sample: YourOrg

'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def assemble_payload(meraki):
    params_map = {'policy': 'policy',
                  'protocol': 'protocol',
                  'dest_port': 'destPort',
                  'dest_cidr': 'destCidr',
                  'comment': 'comment', 
                  }
    rules = []
    for rule in meraki.params['rules']:
        proposed_rule = dict()
        for k, v in rule.items():
            proposed_rule[params_map[k]] = v
        rules.append(proposed_rule)
    payload = {'rules': rules}
    return payload


def get_rules(meraki, net_id):
        path = meraki.construct_path('get_all', net_id=net_id)
        path = path + meraki.params['number'] + '/l3FirewallRules'
        response = meraki.request(path, method='GET')
        if meraki.status == 200:
            return response

def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    fw_rules=dict(policy=dict(type='str', choices=['allow', 'deny']),
                  protocol=dict(type='str', choices=['tcp', 'udp', 'icmp', 'any']),
                  dest_port=dict(type='str'),
                  dest_cidr=dict(type='str'),
                  comment=dict(type='str'),
                  )

    argument_spec = meraki_argument_spec()
    argument_spec.update(clone=dict(type='str'),
                         state=dict(type='str', choices=['present', 'query'], default='present'),
                         net_name=dict(type='str'),
                         net_id=dict(type='str'),
                         number=dict(type='str', aliases=['ssid_number']),
                         rules=dict(type='list', default=None, elements='dict', options=fw_rules),
                         allow_lan_access=dict(type='bool', default=True),
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )
    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    meraki = MerakiModule(module, function='mr_l3_firewall')

    meraki.params['follow_redirects'] = 'all'

    query_urls = {'mr_l3_firewall': '/networks/{net_id}/ssids/'}
    update_urls = {'mr_l3_firewall': '/networks/{net_id}/ssids/'}

    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['update'] = update_urls

    payload = None

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # FIXME: Work with Meraki so they can implement a check mode
    if module.check_mode:
        meraki.exit_json(**meraki.result)

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    org_id = meraki.params['org_id']
    orgs = None
    if org_id is None:
        orgs = meraki.get_orgs()
        for org in orgs:
            if org['name'] == meraki.params['org_name']:
                org_id = org['id']
    net_id = meraki.params['net_id']
    if net_id is None:
        if orgs is None:
            orgs = meraki.get_orgs()
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'],
                                   data=meraki.get_nets(org_id=org_id))

    if meraki.params['state'] == 'query':
        meraki.result['data'] = get_rules(meraki, net_id)

    elif meraki.params['state'] == 'present':
        rules = get_rules(meraki, net_id)
        path = meraki.construct_path('get_all', net_id=net_id)
        path = path + meraki.params['number'] + '/l3FirewallRules'
        if meraki.params['rules']:
            payload = assemble_payload(meraki)
        else:
            payload = dict()
        update = False
        try:
            if len(rules) != len(payload['rules']):  # Quick and simple check to avoid more processing
                update = True
            if update is False:
                for r in range(len(rules)-2):
                    if meraki.is_update_required(rules[r], payload[r]) is True:
                        update = True
        except KeyError:
            pass
        if rules[len(rules)-2] != meraki.params['allow_lan_access']:
            update = True
        if update is True:
            payload['allowLanAccess'] = meraki.params['allow_lan_access']
            response = meraki.request(path, method='PUT', payload=json.dumps(payload))
            if meraki.status == 200:
                meraki.result['data'] = response
                meraki.result['changed'] = True


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
