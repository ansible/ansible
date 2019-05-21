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
    net_name:
      description:
      - Name of network which VLAN is in or should be in.
      aliases: [network]
    net_id:
      description:
      - ID of network which VLAN is in or should be in.
    vlan_id:
      description:
      - ID number of VLAN.
      - ID should be between 1-4096.
author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''

'''

RETURN = r'''

response:
  description: Information about the organization which was created or modified
  returned: success
  type: complex
  contains:
    applianceIp:
      description: IP address of Meraki appliance in the VLAN
      returned: success
      type: str
      sample: 192.0.1.1
    dnsnamservers:
      description: IP address or Meraki defined DNS servers which VLAN should use by default
      returned: success
      type: str
      sample: upstream_dns
    fixedIpAssignments:
      description: List of MAC addresses which have IP addresses assigned.
      returned: success
      type: complex
      contains:
        macaddress:
          description: MAC address which has IP address assigned to it. Key value is the actual MAC address.
          returned: success
          type: complex
          contains:
            ip:
              description: IP address which is assigned to the MAC address.
              returned: success
              type: str
              sample: 192.0.1.4
            name:
              description: Descriptive name for binding.
              returned: success
              type: str
              sample: fixed_ip
    reservedIpRanges:
      description: List of IP address ranges which are reserved for static assignment.
      returned: success
      type: complex
      contains:
        comment:
          description: Description for IP address reservation.
          returned: success
          type: str
          sample: reserved_range
        end:
          description: Last IP address in reservation range.
          returned: success
          type: str
          sample: 192.0.1.10
        start:
          description: First IP address in reservation range.
          returned: success
          type: str
          sample: 192.0.1.5
    id:
      description: VLAN ID number.
      returned: success
      type: int
      sample: 2
    name:
      description: Descriptive name of VLAN.
      returned: success
      type: str
      sample: TestVLAN
    networkId:
      description: ID number of Meraki network which VLAN is associated to.
      returned: success
      type: str
      sample: N_12345
    subnet:
      description: CIDR notation IP subnet of VLAN.
      returned: success
      type: str
      sample: "192.0.1.0/24"
    dhcpHandling:
      description: Status of DHCP server on VLAN.
      returned: success
      type: str
      sample: Run a DHCP server
    dhcpLeaseTime:
      description: DHCP lease time when server is active.
      returned: success
      type: str
      sample: 1 day
    dhcpBootOptionsEnabled:
      description: Whether DHCP boot options are enabled.
      returned: success
      type: bool
      sample: no
    dhcpBootNextServer:
      description: DHCP boot option to direct boot clients to the server to load the boot file from.
      returned: success
      type: str
      sample: 192.0.1.2
    dhcpBootFilename:
      description: Filename for boot file.
      returned: success
      type: str
      sample: boot.txt
    dhcpOptions:
      description: DHCP options.
      returned: success
      type: complex
      contains:
        code:
          description:
            - Code for DHCP option.
            - Integer between 2 and 254.
          returned: success
          type: int
          sample: 43
        type:
          description:
            - Type for DHCP option.
            - Choices are C(text), C(ip), C(hex), C(integer).
          returned: success
          type: str
          sample: text
        value:
          description: Value for the DHCP option.
          returned: success
          type: str
          sample: 192.0.1.2
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


def custom_struct_to_meraki_format(data):
    new_struct = {'bandwidthLimits': None}
    for interface in INT_NAMES:
        if interface in data:
            new_struct['bandwidthLimits'][interface] = {'limitUp': data[interface]['bandwidth_limits']['limit_up'],
                                                        'limitDown': data[interface]['bandwidth_limits']['limit_down']}
    return new_struct


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
                diff = recursive_diff(clean_custom_format(meraki_struct_to_custom_format(original)), clean_custom_format(meraki_struct_to_custom_format(payload)))
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
