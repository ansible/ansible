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
module: meraki_firewalled_services
short_description: Edit firewall policies for administrative network services
version_added: "2.9"
description:
- Allows for setting policy firewalled services for Meraki network devices.

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
        type: str
    net_name:
        description:
        - Name of a network.
        aliases: [ network ]
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
    state:
        description:
        - States that a policy should be created or modified.
        choices: [present, query]
        default: present
        type: str
    service:
        description:
        - Network service to query or modify.
        choices: [ICMP, SNMP, web]
        type: str
    access:
        description:
        - Network service to query or modify.
        choices: [blocked, restricted, unrestricted]
        type: str
    allowed_ips:
        description:
        - List of IP addresses allowed to access a service.
        - Only used when C(access) is set to restricted.
        type: list

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Set icmp service to blocked
  meraki_firewalled_services:
    auth_key: '{{ auth_key }}'
    state: present
    org_name: '{{test_org_name}}'
    net_name: IntTestNetworkAppliance
    service: ICMP
    access: blocked
  delegate_to: localhost

- name: Set icmp service to restricted
  meraki_firewalled_services:
    auth_key: abc123
    state: present
    org_name: YourOrg
    net_name: YourNet
    service: web
    access: restricted
    allowed_ips:
      - 192.0.1.1
      - 192.0.1.2
  delegate_to: localhost

- name: Query appliance services
  meraki_firewalled_services:
    auth_key: abc123
    state: query
    org_name: YourOrg
    net_name: YourNet
  delegate_to: localhost

- name: Query services
  meraki_firewalled_services:
    auth_key: abc123
    state: query
    org_name: YourOrg
    net_name: YourNet
    service: ICMP
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: List of network services.
    returned: info
    type: complex
    contains:
      access:
        description: Access assigned to a service type.
        returned: success
        type: str
        sample: unrestricted
      service:
        description: Service to apply policy to.
        returned: success
        type: str
        sample: ICMP
      allowed_ips:
        description: List of IP addresses to have access to service.
        returned: success
        type: str
        sample: 192.0.1.0
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import recursive_diff
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        net_name=dict(type='str', aliases=['network']),
        state=dict(type='str', default='present', choices=['query', 'present']),
        service=dict(type='str', default=None, choices=['ICMP', 'SNMP', 'web']),
        access=dict(type='str', choices=['blocked', 'restricted', 'unrestricted']),
        allowed_ips=dict(type='list', element='str'),
    )

    mutually_exclusive = [('net_name', 'net_id')]

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=mutually_exclusive
                           )

    meraki = MerakiModule(module, function='firewalled_services')
    module.params['follow_redirects'] = 'all'

    net_services_urls = {'firewalled_services': '/networks/{net_id}/firewalledServices'}
    services_urls = {'firewalled_services': '/networks/{net_id}/firewalledServices/{service}'}

    meraki.url_catalog['network_services'] = net_services_urls
    meraki.url_catalog['service'] = services_urls

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    org_id = meraki.params['org_id']
    if not org_id:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = None
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(org_id, meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'present':
        if meraki.params['access'] != 'restricted' and meraki.params['allowed_ips'] is not None:
            meraki.fail_json(msg="allowed_ips is only allowed when access is restricted.")
        payload = {'access': meraki.params['access']}
        if meraki.params['access'] == 'restricted':
            payload['allowedIps'] = meraki.params['allowed_ips']

    if meraki.params['state'] == 'query':
        if meraki.params['service'] is None:
            path = meraki.construct_path('network_services', net_id=net_id)
            response = meraki.request(path, method='GET')
            meraki.result['data'] = response
            meraki.exit_json(**meraki.result)
        else:
            path = meraki.construct_path('service', net_id=net_id, custom={'service': meraki.params['service']})
            response = meraki.request(path, method='GET')
            meraki.result['data'] = response
            meraki.exit_json(**meraki.result)
    elif meraki.params['state'] == 'present':
        path = meraki.construct_path('service', net_id=net_id, custom={'service': meraki.params['service']})
        original = meraki.request(path, method='GET')
        if meraki.is_update_required(original, payload, optional_ignore=['service']):
            if meraki.check_mode is True:
                diff_payload = {'service': meraki.params['service']}  # Need to add service as it's not in payload
                diff_payload.update(payload)
                diff = recursive_diff(original, diff_payload)
                original.update(payload)
                meraki.result['diff'] = {'before': diff[0],
                                         'after': diff[1]}
                meraki.result['data'] = original
                meraki.result['changed'] = True
                meraki.exit_json(**meraki.result)
            path = meraki.construct_path('service', net_id=net_id, custom={'service': meraki.params['service']})
            response = meraki.request(path, method='PUT', payload=json.dumps(payload))
            if meraki.status == 200:
                diff = recursive_diff(original, response)
                meraki.result['diff'] = {'before': diff[0],
                                         'after': diff[1]}
                meraki.result['data'] = response
                meraki.result['changed'] = True
        else:
            meraki.result['data'] = original

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
