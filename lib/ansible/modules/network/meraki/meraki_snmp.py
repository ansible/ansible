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
module: meraki_snmp
short_description: Manage organizations in the Meraki cloud
version_added: "2.6"
description:
- Allows for management of SNMP settings for Meraki.
notes:
- More information about the Meraki API can be found at U(https://dashboard.meraki.com/api_docs).
- Some of the options are likely only used for developers within Meraki.
options:
    state:
        description:
        - Create or modify an organization.
        choices: ['present', 'query']
        default: present
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
- name: Create a new organization named YourOrg
  meraki_snmp:
    auth_key: abc12345
    org_name: YourOrg
    state: present
  delegate_to: localhost
'''

RETURN = r'''
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

def get_snmp(meraki, org_id):
    path = meraki.construct_path('get_all', org_id=org_id)
    r = meraki.request(path,
                       method='GET',
                       )
    return json.loads(r)

def set_snmp(meraki, org_id):
    payload = {'v2cEnabled': meraki.params['v2cEnabled'],
               'v3Enabled': meraki.params['v3Enabled'],
               'v3AuthMode': meraki.params['v3AuthMode'],
               'v3AuthPass': meraki.params['v3AuthPass'],
               'v3PrivMode': meraki.params['v3PrivMode'],
               'v3PrivPass': meraki.params['v3PrivPass'],
               'peerIps': meraki.params['peerIps'],
               }
    path = meraki.construct_path('create', org_id=org_id)
    snmp = get_snmp(meraki, org_id)
    ignored_parameters = ['v3AuthPass', 'v3PrivPass', 'hostname', 'port']
    if meraki.is_update_required(snmp, payload, ignore=ignored_parameters)
        r = meraki.request(path,
                           method='PUT',
                           payload=payload)
        return json.loads(r)
    return -1

def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    argument_spec = meraki_argument_spec()
    argument_spec.update(clone=dict(type='str'),
                         state=dict(type='str', choices=['present', 'query'], default='present'),
                         org_name=dict(type='str', aliases=['name', 'organization']),
                         org_id=dict(type='int', aliases=['id']),
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
    meraki = MerakiModule(module, function='snmp')

    meraki.params['follow_redirects'] = 'all'

    query_urls = {'snmp': '/organizations/{org_id}/snmp',
                   }


    meraki.url_catalog['get_all'] = query_urls

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
    org_id = None

    if not meraki.params['org_id']:
        org_id = meraki.get_org_id(meraki.params(['org_name'])
    else:
        org_id = meraki.params['org_id']

    if meraki.params['state'] == 'query':
        meraki.result['data'] = get_snmp(meraki, org_id)
    if meraki.params['state'] == 'present':
        meraki.result['data'] = set_snmp(meraki, org_id)


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
