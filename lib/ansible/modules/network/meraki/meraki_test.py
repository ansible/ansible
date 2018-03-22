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

DOCUMENTATION = '''
---
module: meraki_organization
short_description: Manage organizations in the Meraki cloud
version_added: "2.6"
description:
- Allows for creation, management, and visibility into organizations within Meraki

notes:
- More information about the Meraki API can be found at U(https://dashboard.meraki.com/api_docs).
- Some of the options are likely only used for developers within Meraki

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
    name:
        description:
        - Organization ID of an organization
    host:
        description:
        - Hostname for Meraki dashboard
        - Only useful for internal Meraki developers
        type: string
        default: 'api.meraki.com'
    use_proxy:
        description:
        - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
        type: bool
    use_ssl:
        description:
        - If C(no), it will use HTTP. Otherwise it will use HTTPS.
        - Only useful for internal Meraki developers
        type: bool
        default: 'yes'
    output_level:
        description:
        - Set amount of debug output during module execution
        choices: ['normal', 'debug']

author:
    - Kevin Breit (@kbreit)
'''

EXAMPLES = '''
- name: Query information about all organizations
  meraki_organization:
    auth_key: abc12345
    status: query
  delegate_to: localhost

- name: Query information about a single organization named YourOrg
  meraki_organization:
    auth_key: abc12345
    name: YourOrg
    status: query
  delegate_to: localhost

- name: Create a new organization named YourOrg
  meraki_organization:
    auth_key: abc12345
    name: YourOrg
    status: present
  delegate_to: localhost
'''

RETURN = '''
response:
    description: Data returned from Meraki dashboard.
    type: dict
    state: query
    returned: info
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
        username=dict(type='str'),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )

    meraki = MerakiModule(module)

    module.params['follow_redirects'] = 'all'

    payload = None

    create_urls = {'organizations', '/organizations'}
    meraki.url_catalog['create'] = create_urls

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    meraki.function = 'organizations'

    if meraki.params['state'] == 'query':
        meraki.result['response'] = meraki.get_orgs()
    elif meraki.params['state'] == 'present':
        if meraki.params['org_name']:
            meraki.original = meraki.create_object(meraki.params['org_name'])
    elif meraki.params['state'] == 'absent':
        mearki.original = meraki.delete_object('organizations')

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
