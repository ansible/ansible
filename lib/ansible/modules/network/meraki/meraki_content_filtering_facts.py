#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
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
module: meraki_content_filtering_facts
short_description: View information about Meraki MX content filtering
version_added: '2.9'
description:
- Allows for displaying content filtering categories and policies.

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard.
        - Required if environment variable C(MERAKI_KEY) is not set.
        type: str
    net_name:
        description:
        - Name of a network.
        aliases: [network]
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
    subset:
        description:
        - Display only certain facts.
        choices: [categories, policy]
        type: str

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: List all content filtering information
  meraki_content_filtering_facts:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
  delegate_to: localhost

- name: List content filtering policy information
  meraki_content_filtering_facts:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    subset: policy
  delegate_to: localhost

- name: List all content filtering categories
  meraki_content_filtering_facts:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    subset: categories
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
        type: str
        sample: N_12345
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        net_name=dict(type='str', aliases=['network']),
        subset=dict(type='str', choices=['categories', 'policy'])
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )

    meraki = MerakiModule(module, function='content_filtering_facts')
    module.params['follow_redirects'] = 'all'

    category_urls = {'content_filtering_facts': '/networks/{net_id}/contentFiltering/categories'}
    policy_urls = {'content_filtering_facts': '/networks/{net_id}/contentFiltering'}

    meraki.url_catalog['categories'] = category_urls
    meraki.url_catalog['policy'] = policy_urls

    if meraki.params['net_name'] and meraki.params['net_id']:
        meraki.fail_json(msg='net_name and net_id are mutually exclusive')

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    org_id = meraki.params['org_id']
    if not org_id:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    nets = meraki.get_nets(org_id=org_id)

    # check if network is created
    net_id = meraki.params['net_id']
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(org_id, meraki.params['net_name'], data=nets)

    if meraki.params['subset']:
        if meraki.params['subset'] == 'categories':
            path = meraki.construct_path('categories', net_id=net_id)
            meraki.exit_json(ansible_facts=meraki.request(path, method='GET'))
        elif meraki.params['subset'] == 'policy':
            path = meraki.construct_path('policy', net_id=net_id)
            meraki.exit_json(ansible_facts=meraki.request(path, method='GET'))
    else:
        response_data = {'categories': None,
                         'policy': None,
                         }
        path = meraki.construct_path('categories', net_id=net_id)
        response_data['categories'] = meraki.request(path, method='GET')
        path = meraki.construct_path('policy', net_id=net_id)
        response_data['policy'] = meraki.request(path, method='GET')

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(ansible_facts=response_data)


if __name__ == '__main__':
    main()
