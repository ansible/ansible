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
    name:
        description:
        - Name of an organization.
        - If C(clone) is specified, C(name) is the name of the new organization.
    state:
        description:
        - Create or modify an organization
        choices: ['present', 'query']
        required: true
    clone:
        description:
        - Organization to clone to a new organization.
    org_name:
        description:
        - Name of organization.
        - Used when C(name) should refer to another object.
    org_id:
        description:
        - ID of organization
author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = '''
- name: Query information about all organizations associated to the user
  meraki_organization:
    auth_key: abc12345
    state: query
  delegate_to: localhost

- name: Query information about a single organization named YourOrg
  meraki_organization:
    auth_key: abc12345
    name: YourOrg
    state: query
  delegate_to: localhost

- name: Create a new organization named YourOrg
  meraki_organization:
    auth_key: abc12345
    name: YourOrg
    state: present
  delegate_to: localhost

- name: Clone an organization named Org to a new one called ClonedOrg
  meraki_organization:
    auth_key: abc12345
    clone: Org
    name: ClonedOrg
    state: present
  delegate_to: localhost
'''

RETURN = '''
response:
    description: Data returned from Meraki dashboard.
    type: dict
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
    argument_spec.update(clone=dict(type='str'),
                         state=dict(type='str', choices=['present', 'query'], required=True),
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
                           supports_check_mode=False,
                           )
    meraki = MerakiModule(module)

    meraki.function = 'organizations'
    meraki.params['follow_redirects'] = 'all'
    meraki.required_if = [['state', 'present', ['name']],
                          ['clone', ['name']],
                          ]

    create_urls = {'organizations': '/organizations',
                   }
    update_urls = {'organizations': '/organizations/replace_org_id',
                   }
    clone_urls = {'organizations': '/organizations/replace_org_id/clone',
                  }

    meraki.url_catalog['create'] = create_urls
    meraki.url_catalog['update'] = update_urls
    meraki.url_catalog['clone'] = clone_urls

    try:
        meraki.params['auth_key'] = os.environ['MERAKI_KEY']
    except KeyError:
        pass

    if meraki.params['auth_key'] is None:
        meraki.fail_json(msg='Meraki Dashboard API key not set')

    payload = None

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return meraki.result

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    if meraki.params['state'] == 'query':
        if meraki.params['name'] is None:  # Query all organizations, no matter what
            orgs = meraki.get_orgs()
            meraki.result['organization'] = orgs
        elif meraki.params['name'] is not None:  # Query by organization name
            module.warn('All matching organizations will be returned, even if there are duplicate named organizations')
            orgs = meraki.get_orgs()
            for o in orgs:
                if o['name'] == meraki.params['name']:
                    meraki.result['organization'] = o
    elif meraki.params['state'] == 'present':
        if meraki.params['clone'] is not None:  # Cloning
            payload = {'name': meraki.params['name']}
            # meraki.fail_json(msg=meraki.construct_path('clone', org_name=meraki.params['clone']))
            meraki.result['response'] = json.loads(
                meraki.request(
                    meraki.construct_path(
                        'clone',
                        org_name=meraki.params['clone']
                    ),
                    payload=json.dumps(payload),
                    method='POST'))
        elif meraki.params['org_id'] is None and meraki.params['name'] is not None:  # Create new organization
            payload = {'name': meraki.params['name']}
            meraki.result['response'] = json.loads(
                meraki.request(
                    meraki.construct_path('create'),
                    payload=json.dumps(payload)))
        elif meraki.params['org_id'] is not None and meraki.params['name'] is not None:  # Update an existing organization
            payload = {'name': meraki.params['name'],
                       'id': meraki.params['org_id'],
                       }
            meraki.result['response'] = json.loads(
                meraki.request(
                    meraki.construct_path(
                        'update',
                        org_id=meraki.params['org_id']
                    ),
                    method='PUT',
                    payload=json.dumps(payload)))

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
