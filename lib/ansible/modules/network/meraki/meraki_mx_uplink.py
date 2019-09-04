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
module: meraki_mx_uplink
short_description: Manage uplinks on Meraki MX appliances
version_added: "2.9"
description:
- Configure and query information about uplinks on Meraki MX appliances.
notes:
- Some of the options are likely only used for developers within Meraki.
options:
    state:
      description:
      - Specifies whether object should be queried, created/modified, or removed.
      choices: [absent, present, query]
      default: query
    org_name:
        description:
        - Name of organization associated to a network.
        type: str
    org_id:
        description:
        - ID of organization associated to a network.
        type: str
    net_name:
      description:
      - Name of network which VLAN is in or should be in.
      aliases: [network]
    net_id:
      description:
      - ID of network which VLAN is in or should be in.
    wan1:
      description:
      - Configuration of WAN1 uplink
      type: dict
      suboptions:
        bandwidth_limits:
          description:
          - Structure for configuring bandwidth limits
          type: dict
          suboptions:
            limit_up:
              description:
              - Maximum upload speed for interface
              type: int
            limit_down:
              description:
              - Maximum download speed for interface
              type: int
    wan2:
      description:
      - Configuration of WAN2 uplink
      type: dict
      suboptions:
        bandwidth_limits:
          description:
          - Structure for configuring bandwidth limits
          type: dict
          suboptions:
            limit_up:
              description:
              - Maximum upload speed for interface
              type: int
            limit_down:
              description:
              - Maximum download speed for interface
              type: int
    cellular:
      description:
      - Configuration of cellular uplink
      type: dict
      suboptions:
        bandwidth_limits:
          description:
          - Structure for configuring bandwidth limits
          type: dict
          suboptions:
            limit_up:
              description:
              - Maximum upload speed for interface
              type: int
            limit_down:
              description:
              - Maximum download speed for interface
              type: int
author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Set MX uplink settings
  meraki_mx_uplink:
    auth_key: '{{auth_key}}'
    state: present
    org_name: '{{test_org_name}}'
    net_name: '{{test_net_name}} - Uplink'
    wan1:
      bandwidth_limits:
        limit_down: 1000000
        limit_up: 1000
    cellular:
      bandwidth_limits:
        limit_down: 0
        limit_up: 0
  delegate_to: localhost

- name: Query MX uplink settings
  meraki_mx_uplink:
    auth_key: '{{auth_key}}'
    state: query
    org_name: '{{test_org_name}}'
    net_name: '{{test_net_name}} - Uplink'
  delegate_to: localhost

'''

RETURN = r'''

data:
  description: Information about the organization which was created or modified
  returned: success
  type: complex
  contains:
    wan1:
      description: WAN1 interface
      returned: success
      type: complex
      contains:
        bandwidth_limits:
          description: Structure for uplink bandwidth limits
          returned: success
          type: complex
          contains:
            limit_up:
              description: Upload bandwidth limit
              returned: success
              type: int
            limit_down:
              description: Download bandwidth limit
              returned: success
              type: int
    wan2:
      description: WAN2 interface
      returned: success
      type: complex
      contains:
        bandwidth_limits:
          description: Structure for uplink bandwidth limits
          returned: success
          type: complex
          contains:
            limit_up:
              description: Upload bandwidth limit
              returned: success
              type: int
            limit_down:
              description: Download bandwidth limit
              returned: success
              type: int
    cellular:
      description: cellular interface
      returned: success
      type: complex
      contains:
        bandwidth_limits:
          description: Structure for uplink bandwidth limits
          returned: success
          type: complex
          contains:
            limit_up:
              description: Upload bandwidth limit
              returned: success
              type: int
            limit_down:
              description: Download bandwidth limit
              returned: success
              type: int
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict, recursive_diff
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec

INT_NAMES = ('wan1', 'wan2', 'cellular')


def clean_custom_format(data):
    for interface in data:
        if data[interface]['bandwidth_limits']['limit_up'] is None:
            data[interface]['bandwidth_limits']['limit_up'] = 0
        if data[interface]['bandwidth_limits']['limit_down'] is None:
            data[interface]['bandwidth_limits']['limit_down'] = 0
    return data


def meraki_struct_to_custom_format(data):
    new_struct = {}
    for interface in INT_NAMES:
        if interface in data['bandwidthLimits']:
            new_struct[interface] = {'bandwidth_limits': {'limit_up': data['bandwidthLimits'][interface]['limitUp'],
                                                          'limit_down': data['bandwidthLimits'][interface]['limitDown'],
                                                          }
                                     }
    # return snake_dict_to_camel_dict(new_struct)
    return new_struct


def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    bandwidth_arg_spec = dict(limit_up=dict(type='int'),
                              limit_down=dict(type='int'),
                              )

    interface_arg_spec = dict(bandwidth_limits=dict(type='dict', default=None, options=bandwidth_arg_spec),
                              )

    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present', 'query'], default='query'),
                         net_name=dict(type='str', aliases=['network']),
                         net_id=dict(type='str'),
                         wan1=dict(type='dict', default=None, options=interface_arg_spec),
                         wan2=dict(type='dict', default=None, options=interface_arg_spec),
                         cellular=dict(type='dict', default=None, options=interface_arg_spec),
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
    meraki = MerakiModule(module, function='mx_uplink')

    meraki.params['follow_redirects'] = 'all'

    query_urls = {'mx_uplink': '/networks/{net_id}/uplinkSettings'}
    update_bw_url = {'mx_uplink': '/networks/{net_id}/uplinkSettings'}

    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['update_bw'] = update_bw_url

    payload = dict()

    org_id = meraki.params['org_id']
    if org_id is None:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        path = meraki.construct_path('get_all', net_id=net_id)
        response = meraki.request(path, method='GET')
        data = clean_custom_format(meraki_struct_to_custom_format(response))
        meraki.result['data'] = data
    elif meraki.params['state'] == 'present':
        path = meraki.construct_path('get_all', net_id=net_id)
        original = meraki.request(path, method='GET')
        payload = {'bandwidthLimits': {}}
        for interface in INT_NAMES:
            if meraki.params[interface] is not None:
                if meraki.params[interface]['bandwidth_limits'] is not None:
                    payload['bandwidthLimits'][interface] = None
                    payload['bandwidthLimits'][interface] = {'limitUp': meraki.params[interface]['bandwidth_limits']['limit_up'],
                                                             'limitDown': meraki.params[interface]['bandwidth_limits']['limit_down'],
                                                             }
                    if payload['bandwidthLimits'][interface]['limitUp'] == 0:
                        payload['bandwidthLimits'][interface]['limitUp'] = None
                    if payload['bandwidthLimits'][interface]['limitDown'] == 0:
                        payload['bandwidthLimits'][interface]['limitDown'] = None
        if meraki.is_update_required(original, payload):
            if meraki.module.check_mode is True:
                diff = recursive_diff(clean_custom_format(meraki_struct_to_custom_format(original)),
                                      clean_custom_format(meraki_struct_to_custom_format(payload)))
                original.update(payload)
                meraki.result['data'] = clean_custom_format(meraki_struct_to_custom_format(original))
                meraki.result['diff'] = {'before': diff[0],
                                         'after': diff[1],
                                         }
                meraki.result['changed'] = True
                meraki.exit_json(**meraki.result)
            path = meraki.construct_path('update_bw', net_id=net_id)
            response = meraki.request(path, method='PUT', payload=json.dumps(payload))
            if meraki.status == 200:
                formatted_original = clean_custom_format(meraki_struct_to_custom_format(original))
                formatted_response = clean_custom_format(meraki_struct_to_custom_format(response))
                diff = recursive_diff(formatted_original, formatted_response)
                meraki.result['diff'] = {'before': diff[0],
                                         'after': diff[1],
                                         }
                meraki.result['data'] = formatted_response
                meraki.result['changed'] = True
        else:
            meraki.result['data'] = clean_custom_format(meraki_struct_to_custom_format(original))

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
