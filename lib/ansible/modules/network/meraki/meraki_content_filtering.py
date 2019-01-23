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
module: meraki_content_filtering
short_description: Edit Meraki MX content filtering policies
version_added: "2.8"
description:
- Allows for setting policy on content filtering.

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
    net_name:
        description:
        - Name of a network.
        aliases: [network]
    net_id:
        description:
        - ID number of a network.
    org_name:
        description:
        - Name of organization associated to a network.
    org_id:
        description:
        - ID of organization associated to a network.
    subset:
        description:
        - Display only certain facts
        choices: [categories, policy]

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


def get_category_dict(meraki, full_list, category):
    # meraki.fail_json(msg="Category dictionary builder", category=category, full_list=full_list)
    for i in full_list['categories']:
        # meraki.fail_json(msg="Item", i=i)
        if i['name'] == category:
            # meraki.fail_json(msg="Category found!")
            return i
    meraki.fail_json(msg="{0} is not a valid content filtering category".format(category))

def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    category_spec = dict(
                         )

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        net_name=dict(type='str', aliases=['network']),
        subset=dict(type='str', choices=['categories', 'policy']),
        state=dict(type='str', choices=['present'], default='present'),
        allowed_urls=dict(type='list'),
        blocked_urls=dict(type='list'),
        blocked_categories=dict(type='list'),
        # blocked_categories=dict(type='list', element='dict', default=None, options=category_spec),
        category_list_size=dict(type='str', choices=['top sites', 'full list']),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )

    meraki = MerakiModule(module, function='content_filtering')
    module.params['follow_redirects'] = 'all'

    category_urls = {'content_filtering': '/networks/{net_id}/contentFiltering/categories'}
    policy_urls = {'content_filtering': '/networks/{net_id}/contentFiltering'}

    meraki.url_catalog['categories'] = category_urls
    meraki.url_catalog['policy'] = policy_urls

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

    net_id = None
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(org_id, meraki.params['net_name'], data=nets)

    if module.params['state'] == 'present':
        payload = dict()
        if meraki.params['allowed_urls']:
            payload['allowedUrlPatterns'] = meraki.params['allowed_urls']
        if meraki.params['blocked_urls']:
            payload['blockedUrlPatterns'] = meraki.params['blocked_urls']
        if meraki.params['blocked_categories']:
            if len(meraki.params['blocked_categories']) == 0:  # Corner case for resetting
                payload['blockedUrlCategories'] = []
            else:
                category_path = meraki.construct_path('categories', net_id=net_id)
                categories = meraki.request(category_path, method='GET')
                payload['blockedUrlCategories'] = []
                for category in meraki.params['blocked_categories']:
                    payload['blockedUrlCategories'].append(get_category_dict(meraki,
                                                                             categories,
                                                                             category))
                # meraki.fail_json(msg='Payload', payload=payload)
        if meraki.params['category_list_size']:
            if meraki.params['category_list_size'].lower() == 'top sites':
                payload['urlCategoryListSize'] = "topSites"
            elif meraki.params['category_list_size'].lower() == 'full list':
                payload['urlCategoryListSize'] = "fullList"
        path = meraki.construct_path('policy', net_id=net_id)
        current = meraki.request(path, method='GET')
        if meraki.is_update_required(current, payload):
            response = meraki.request(path, method='PUT', payload=json.dumps(payload))
            meraki.result['data'] = response
            meraki.result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
