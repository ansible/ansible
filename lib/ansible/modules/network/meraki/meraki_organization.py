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
    state:
        description:
        - Create or query organizations
        choices: ['query', 'present']
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
        - Set amount of debug output during module execution.
        choices: ['normal', 'debug']
    clone:
        description:
        - Organization to clone to a new organization.
        type: string

author:
    - Kevin Breit (@kbreit)
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

# def find_org_id(data, name):
#     ''' Find an organization's ID based on the provided name '''
#     for i in data:
#         if i['name'] == name:
#             return i['id']

# def meraki_request(module, result, url, method, headers, payload):
#     try:
#         resp, info = fetch_url(module, url,
#                                data=json.dumps(payload),
#                                headers=headers,
#                                method=method,
#                                use_proxy=meraki.params['use_proxy'],
#                                force=False,
#                                )
#     except Exception as e:
#         module.fail_json(msg=str(e), **debug_result)

#     # module.fail_json(msg=info['status'])
#     data = resp.read()
#     if meraki.params['output_level'] == 'debug':
#         debug_result['status'] = info['status']
#         debug_result['resp_headers'] = resp.headers
#         debug_result['response'] = data
#     response = json.loads(to_native(data))

#     if info['status'] >= 200 and info['status'] <= 299:
#         try:
#             result['message'] = response
#             if method == 'POST' or method == 'PUT':
#                 if info['status'] == 201:
#                     result['changed'] = True
#         except:
#             module.fail_json(msg="Meraki dashboard didn't return JSON compatible data")
#     else:
#         module.fail_json(msg='{0}: {1} '.format(info['status'], info['body']), **result)
#     return response

def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    argument_spec = meraki_argument_spec()
    # argument_spec.update(
    #                     )
    #                    clone=dict(type='str'),
    #                    claim=dict(type='str'),
    #                    claim_mode=dict(type='str'),
    #                    inventory=dict(type='bool'),
    #                    snmp_v2c=dict(type='bool'),
    #                    snmp_v3=dict(type='bool'),
    #                    snmp_v3AuthMode=dict(type='str', choices=['md5', 'sha']),
    #                    snmp_v3AuthPass=dict(type='str', no_log=True),
    #                    snmp_v3PrivMode=dict(type='str', choices=['des', 'aes128']),
    #                    snmp_v3PrivPass=dict(type='str', no_log=True),
    #                    snmp_PeerIP=dict(type='str'),
    #                    vpn_PublicIP=dict(type='str'),
    #                    vpn_PrivateSubnets=dict(type='str'),
    #                    vpn_secret=dict(type='str', no_log=True),

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
    meraki.required_if=[
                           ['state', 'present', ['name']],
                           # ['clone', ['name']],
                           # ['vpn_PublicIP', ['name']],
                       ]

    create_urls = {'organizations': '/organizations',
                   }

    update_urls = {'organizations': '/organizations/replace_org_id',
                   }

    meraki.url_catalog['create'] = create_urls
    meraki.url_catalog['update'] = update_urls

    try:
        meraki.params['auth_key'] = os.environ['MERAKI_KEY']
    except KeyError:
        pass

    if meraki.params['auth_key'] is None:
        module.fail_json(msg='Meraki Dashboard API key not set')

    payload = None

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    protocol = 'https'
    if meraki.params['use_ssl'] is not None and meraki.params['use_ssl'] is False:
        protocol = 'http'
    host = 'api.meraki.com'

    url = '{0}://api.meraki.com/api/v0/organizations'.format(protocol)
    headers = {'Content-Type': 'application/json',
               'X-Cisco-Meraki-API-Key': meraki.params['auth_key'],
               }
    method = None

    if meraki.params['output_level'] == 'debug':
      debug_result=dict(url=url,
                        method=method,
                        headers=headers,
                        payload=payload,
                        )
      if meraki.params['state']:
          debug_result['state'] = meraki.params['state']

    org_id = None

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
      if meraki.params['org_id'] is None and meraki.params['name'] is not None:  # Create new organization
        payload = {'name': meraki.params['name']}
        meraki.result['response'] = json.loads(meraki.request(meraki.construct_path('create'), payload=json.dumps(payload)))
      elif meraki.params['org_id'] is not None and meraki.params['name'] is not None:  # Update an existing organization
        # meraki.fail_json(msg='update code triggered')
        payload = {'name': meraki.params['name'],
                   'id': meraki.params['org_id'],
                   }
        # meraki.fail_json(msg=meraki.construct_path('update', org_id=meraki.params['org_id']), payload=payload)
        meraki.result['response'] = json.loads(meraki.request(meraki.construct_path('update', org_id=meraki.params['org_id']), payload=json.dumps(payload), method='PUT'))
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**result)


if __name__ == '__main__':
    main()
