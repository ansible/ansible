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
module: meraki_webhook
short_description: Manage webhooks configured in the Meraki cloud
version_added: "2.9"
description:
- Configure and query information about webhooks within the Meraki cloud.
notes:
- Some of the options are likely only used for developers within Meraki.
options:
    state:
      description:
      - Specifies whether object should be queried, created/modified, or removed.
      choices: [absent, present, query]
      default: query
      type: str
    net_name:
      description:
      - Name of network which configuration is applied to.
      aliases: [network]
      type: str
    net_id:
      description:
      - ID of network which configuration is applied to.
      type: str
    name:
      description:
      - Name of webhook.
      type: str
    shared_secret:
      description:
      - Secret password to use when accessing webhook.
      type: str
    url:
      description:
      - URL to access when calling webhook.
      type: str
    webhook_id:
      description:
      - Unique ID of webhook.
      type: str
    test:
      description:
      - Indicates whether to test or query status.
      type: str
      choices: [test, status]
    test_id:
      description:
      - ID of webhook test query.
      type: str
author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Create webhook
  meraki_webhook:
    auth_key: abc123
    state: present
    org_name: YourOrg
    net_name: YourNet
    name: Test_Hook
    url: https://webhook.url/
    shared_secret: shhhdonttellanyone
  delegate_to: localhost

- name: Query one webhook
  meraki_webhook:
    auth_key: abc123
    state: query
    org_name: YourOrg
    net_name: YourNet
    name: Test_Hook
  delegate_to: localhost

- name: Query all webhooks
  meraki_webhook:
    auth_key: abc123
    state: query
    org_name: YourOrg
    net_name: YourNet
  delegate_to: localhost

- name: Delete webhook
  meraki_webhook:
    auth_key: abc123
    state: absent
    org_name: YourOrg
    net_name: YourNet
    name: Test_Hook
  delegate_to: localhost

- name: Test webhook
  meraki_webhook:
    auth_key: abc123
    state: present
    org_name: YourOrg
    net_name: YourNet
    test: test
    url: https://webhook.url/abc123
  delegate_to: localhost

- name: Get webhook status
  meraki_webhook:
    auth_key: abc123
    state: present
    org_name: YourOrg
    net_name: YourNet
    test: status
    test_id: abc123531234
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: List of administrators.
    returned: success
    type: complex
    contains:
        id:
          description: Unique ID of webhook.
          returned: success
          type: str
          sample: aHR0cHM6Ly93ZWJob22LnvpdGUvOGViNWI3NmYtYjE2Ny00Y2I4LTlmYzQtND32Mj3F5NzIaMjQ0
        name:
          description: Descriptive name of webhook.
          returned: success
          type: str
          sample: Test_Hook
        networkId:
          description: ID of network containing webhook object.
          returned: success
          type: str
          sample: N_12345
        shared_secret:
          description: Password for webhook.
          returned: success
          type: str
          sample: VALUE_SPECIFIED_IN_NO_LOG_PARAMETER
        url:
          description: URL of webhook endpoint.
          returned: success
          type: str
          sample: https://webhook.url/abc123
        status:
          description: Status of webhook test.
          returned: success, when testing webhook
          type: str
          sample: enqueued
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import recursive_diff
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def get_webhook_id(name, webhooks):
    for webhook in webhooks:
        if name == webhook['name']:
            return webhook['id']
    return None


def get_all_webhooks(meraki, net_id):
    path = meraki.construct_path('get_all', net_id=net_id)
    response = meraki.request(path, method='GET')
    if meraki.status == 200:
        return response


def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present', 'query'], default='query'),
                         net_name=dict(type='str', aliases=['network']),
                         net_id=dict(type='str'),
                         name=dict(type='str'),
                         url=dict(type='str'),
                         shared_secret=dict(type='str', no_log=True),
                         webhook_id=dict(type='str'),
                         test=dict(type='str', choices=['test', 'status']),
                         test_id=dict(type='str'),
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
    meraki = MerakiModule(module, function='webhooks')

    meraki.params['follow_redirects'] = 'all'

    query_url = {'webhooks': '/networks/{net_id}/httpServers'}
    query_one_url = {'webhooks': '/networks/{net_id}/httpServers/{hookid}'}
    create_url = {'webhooks': '/networks/{net_id}/httpServers'}
    update_url = {'webhooks': '/networks/{net_id}/httpServers/{hookid}'}
    delete_url = {'webhooks': '/networks/{net_id}/httpServers/{hookid}'}
    test_url = {'webhooks': '/networks/{net_id}/httpServers/webhookTests'}
    test_status_url = {'webhooks': '/networks/{net_id}/httpServers/webhookTests/{testid}'}

    meraki.url_catalog['get_all'].update(query_url)
    meraki.url_catalog['get_one'].update(query_one_url)
    meraki.url_catalog['create'] = create_url
    meraki.url_catalog['update'] = update_url
    meraki.url_catalog['delete'] = delete_url
    meraki.url_catalog['test'] = test_url
    meraki.url_catalog['test_status'] = test_status_url

    org_id = meraki.params['org_id']
    if org_id is None:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)
    webhook_id = meraki.params['webhook_id']
    if webhook_id is None and meraki.params['name']:
        webhooks = get_all_webhooks(meraki, net_id)
        webhook_id = get_webhook_id(meraki.params['name'], webhooks)

    if meraki.params['state'] == 'present' and meraki.params['test'] is None:
        payload = {'name': meraki.params['name'],
                   'url': meraki.params['url'],
                   'sharedSecret': meraki.params['shared_secret']}

    if meraki.params['state'] == 'query':
        if webhook_id is not None:  # Query a single webhook
            path = meraki.construct_path('get_one', net_id=net_id, custom={'hookid': webhook_id})
            response = meraki.request(path, method='GET')
            if meraki.status == 200:
                meraki.result['data'] = response
        else:
            path = meraki.construct_path('get_all', net_id=net_id)
            response = meraki.request(path, method='GET')
            if meraki.status == 200:
                meraki.result['data'] = response
    elif meraki.params['state'] == 'present':
        if meraki.params['test'] == 'test':
            payload = {'url': meraki.params['url']}
            path = meraki.construct_path('test', net_id=net_id)
            response = meraki.request(path, method='POST', payload=json.dumps(payload))
            if meraki.status == 200:
                meraki.result['data'] = response
                meraki.exit_json(**meraki.result)
        elif meraki.params['test'] == 'status':
            if meraki.params['test_id'] is None:
                meraki.fail_json("test_id is required when querying test status.")
            path = meraki.construct_path('test_status', net_id=net_id, custom={'testid': meraki.params['test_id']})
            response = meraki.request(path, method='GET')
            if meraki.status == 200:
                meraki.result['data'] = response
                meraki.exit_json(**meraki.result)
        if webhook_id is None:  # Make sure it is downloaded
            if webhooks is None:
                webhooks = get_all_webhooks(meraki, net_id)
            webhook_id = get_webhook_id(meraki.params['name'], webhooks)
        if webhook_id is None:  # Test to see if it needs to be created
            if meraki.check_mode is True:
                meraki.result['data'] = payload
                meraki.result['data']['networkId'] = net_id
                meraki.result['changed'] = True
                meraki.exit_json(**meraki.result)
            path = meraki.construct_path('create', net_id=net_id)
            response = meraki.request(path, method='POST', payload=json.dumps(payload))
            if meraki.status == 201:
                meraki.result['data'] = response
                meraki.result['changed'] = True
        else:  # Need to update
            path = meraki.construct_path('get_one', net_id=net_id, custom={'hookid': webhook_id})
            original = meraki.request(path, method='GET')
            if meraki.is_update_required(original, payload):
                if meraki.check_mode is True:
                    diff = recursive_diff(original, payload)
                    original.update(payload)
                    meraki.result['diff'] = {'before': diff[0],
                                             'after': diff[1]}
                    meraki.result['data'] = original
                    meraki.result['changed'] = True
                    meraki.exit_json(**meraki.result)
                path = meraki.construct_path('update', net_id=net_id, custom={'hookid': webhook_id})
                response = meraki.request(path, method='PUT', payload=json.dumps(payload))
                if meraki.status == 200:
                    meraki.result['data'] = response
                    meraki.result['changed'] = True
            else:
                meraki.result['data'] = original
    elif meraki.params['state'] == 'absent':
        if webhook_id is None:  # Make sure it is downloaded
            if webhooks is None:
                webhooks = get_all_webhooks(meraki, net_id)
            webhook_id = get_webhook_id(meraki.params['name'], webhooks)
            if webhook_id is None:
                meraki.fail_json(msg="There is no webhook with the name {0}".format(meraki.params['name']))
        if webhook_id:  # Test to see if it exists
            if meraki.module.check_mode is True:
                meraki.result['data'] = None
                meraki.result['changed'] = True
                meraki.exit_json(**meraki.result)
            path = meraki.construct_path('delete', net_id=net_id, custom={'hookid': webhook_id})
            response = meraki.request(path, method='DELETE')
            if meraki.status == 204:
                meraki.result['data'] = response
                meraki.result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
