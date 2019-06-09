#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019 Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
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
module: meraki_intrusion_prevention
short_description: Manage intrustion prevention in the Meraki cloud
version_added: "2.9"
description:
- Allows for management of intrusion prevention rules networks within Meraki MX networks.

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
    state:
        description:
        - Create or modify an organization.
        choices: [ absent, present, query ]
        default: present
    net_name:
        description:
        - Name of a network.
        aliases: [ name, network ]
    net_id:
        description:
        - ID number of a network.
    org_name:
        description:
        - Name of organization associated to a network.
    org_id:
        description:
        - ID of organization associated to a network.

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''

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
        type: str
        sample: N_12345
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec

param_map = {'whitelisted_rules': 'whitelistedRules',
             'rule_id': 'ruleId',
             'message': 'message',
             'mode': 'mode',
             'protected_networks': 'protectedNetworks',
             'use_default': 'useDefault',
             'included_cidr': 'includedCidr',
             }

def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    whitelist_arg_spec=dict(rule_id=dict(type='str'),
                            message=dict(type='str'),
                            )

    protected_nets_arg_spec=dict(use_default=dict(type='bool'),
                                 included_cidr=dict(type='list', element='str'),
                                 excluded_cidr=dict(type='list', element='str'),
                                 )

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        net_name=dict(type='str', aliases=['name', 'network']),
        state=dict(type='str', choices=['absent', 'present', 'query'], default='present'),
        whitelisted_rules=dict(type='list', default=None, element='dict', options=whitelist_arg_spec),
        mode=dict(type='str', choices=['detection', 'disabled', 'prevention']),
        ids_rulesets=dict(type='str', choices=['connectivity', 'balanced', 'security']),
        protected_networks=dict(type='dict', default=None, options=protected_nets_arg_spec),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )

    meraki = MerakiModule(module, function='intrusion_prevention')
    module.params['follow_redirects'] = 'all'
    payload = None

    query_org_urls = {'intrusion_prevention': '/organizations/{org_id}/security/intrusionSettings'}
    query_net_urls = {'intrusion_prevention': '/networks/{net_id}/security/intrusionSettings'}
    set_org_urls = {'intrusion_prevention': '/organizations/{org_id}/security/intrusionSettings'}
    set_net_urls = {'intrusion_prevention': '/networks/{net_id}/security/intrusionSettings'}
    meraki.url_catalog['query_org'] = query_org_urls
    meraki.url_catalog['query_net'] = query_net_urls
    meraki.url_catalog['set_org'] = set_org_urls
    meraki.url_catalog['set_net'] = set_net_urls
    
    if not meraki.params['org_name'] and not meraki.params['org_id']:
        meraki.fail_json(msg='org_name or org_id parameters are required')
    if meraki.params['net_name'] and meraki.params['net_id']:
        meraki.fail_json(msg='net_name and net_id are mutually exclusive')
    if meraki.params['net_name'] is None and meraki.params['net_id'] is None:  # Organization param check
        if meraki.params['state'] == 'present':
            if meraki.params['whitelisted_rules'] is None:
                meraki.fail_json(msg='whitelisted_rules is required when state is present and no network is specified.')
    if meraki.params['net_name'] or meraki.params['net_id']:  # Network param check
        if meraki.params['state'] == 'present':
            if meraki.params['protected_networks'] is not None:
                if meraki.params['protected_networks']['use_default'] is False and meraki.params['protected_networks']['included_cidr'] is None:
                    meraki.fail_json(msg="included_cidr is required when use_default is False.")
                if meraki.params['protected_networks']['use_default'] is False and meraki.params['protected_networks']['excluded_cidr'] is None:
                    meraki.fail_json(msg="excluded_cidr is required when use_default is False.")

    org_id = meraki.params['org_id']
    if not org_id:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if net_id is None and meraki.params['net_name']:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)        

    # Assemble payload
    if meraki.params['state'] == 'present':
        if net_id is None:  # Create payload for organization
            rules = []
            for rule in meraki.params['whitelisted_rules']:
                rules.append({'ruleId': rule['rule_id'],
                              'message': rule['message'],
                              })
            payload = {'whitelistedRules': rules}
        else:  # Create payload for network
            payload = dict()
            if meraki.params['mode']:
                payload['mode'] = meraki.params['mode']
            if meraki.params['ids_rulesets']:
                payload['idsRulesets'] = meraki.params['ids_rulesets']
            if meraki.params['protected_networks']:
                payload['protectedNetworks'] = {}
                if meraki.params['protected_networks']['use_default']:
                    payload['protectedNetworks'].update({'useDefault': meraki.params['protected_networks']['use_default']})
                if meraki.params['protected_networks']['included_cidr']:
                    payload['protectedNetworks'].update({'includedCidr': meraki.params['protected_networks']['included_cidr']})
                if meraki.params['protected_networks']['excluded_cidr']:
                    payload['protectedNetworks'].update({'excludedCidr': meraki.params['protected_networks']['excluded_cidr']})
    elif meraki.params['state'] == 'absent':
        if net_id is None:  # Create payload for organization
            payload = {'whitelistedRules': []}

    if meraki.params['state'] == 'query':
        if net_id is None:  # Query settings for organization
            path = meraki.construct_path('query_org', org_id=org_id)
            data = meraki.request(path, method='GET')
            if meraki.status == 200:
                meraki.result['data'] = data
        else:  # Query settings for network
            path = meraki.construct_path('query_net', net_id=net_id)
            data = meraki.request(path, method='GET')
    elif meraki.params['state'] == 'present':
        path = meraki.construct_path('query_org', org_id=org_id)
        original = meraki.request(path, method='GET')
        if net_id is None:  # Set configuration for organization
            if meraki.is_update_required(original, payload, optional_ignore=['message']):
                if meraki.module.check_mode is True:
                    original.update(payload)
                    meraki.result['data'] = original
                    meraki.result['changed'] = True
                    meraki.exit_json(**meraki.result)
                path = meraki.construct_path('set_org', org_id=org_id)
                data = meraki.request(path, method='PUT', payload=json.dumps(payload))
                if meraki.status == 200:
                    meraki.result['data'] = data
                    meraki.result['changed'] = True
            else:
                meraki.result['data'] = original
                meraki.result['changed'] = False
        else:  # Set configuration for network
            path = meraki.construct_path('query_net', net_id=net_id)
            original = meraki.request(path, method='GET')
            if meraki.is_update_required(original, payload):
                if meraki.module.check_mode is True:
                    payload.update(original)
                    meraki.result['data'] = payload
                    meraki.result['changed'] = True
                    meraki.exit_json(**meraki.result)
                path = meraki.construct_path('set_net', net_id=net_id)
                data = meraki.request(path, method='PUT', payload=json.dumps(payload))
                if meraki.status == 200:
                    meraki.result['data'] = data
                    meraki.result['changed'] = True
            else:
                meraki.result['data'] = original
                meraki.result['changed'] = False
    elif meraki.params['state'] == 'absent':
        if net_id is None:
            path = meraki.construct_path('query_org', org_id=org_id)
            original = meraki.request(path, method='GET')
        if meraki.is_update_required(original, payload):
            if meraki.module.check_mode is True:
                payload.update(original)
                meraki.result['data'] = payload
                meraki.result['changed'] = True
                meraki.exit_json(**meraki.result)
            path = meraki.construct_path('set_org', org_id=org_id)
            data = meraki.request(path, method='PUT', payload=json.dumps(payload))
            if meraki.status == 200:
                meraki.result['data'] = data
                meraki.result['changed'] = True
        else:
            meraki.result['data'] = original
            meraki.result['changed'] = False


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
