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
module: meraki_switchport
short_description: Manage switchports on a switch in the Meraki cloud
version_added: "2.7"
description:
- Allows for management of switchports settings for Meraki MS switches.
options:
    state:
        description:
        - Specifies whether a switchport should be queried or modified.
        choices: [query, present]
        default: query
    access_policy_number:
        description:
        - Number of the access policy to apply.
        - Only applicable to access port types.
    allowed_vlans:
        description:
        - List of VLAN numbers to be allowed on switchport.
        default: all
    enabled:
        description:
        - Whether a switchport should be enabled or disabled.
        type: bool
        default: yes
    isolation_enabled:
        description:
        - Isolation status of switchport.
        default: no
        type: bool
    link_negotiation:
        description:
        - Link speed for the switchport.
        default: Auto negotiate
        choices: [Auto negotiate, 100Megabit (auto), 100 Megabit full duplex (forced)]
    name:
        description:
        - Switchport description.
        aliases: [description]
    number:
        description:
        - Port number.
    poe_enabled:
        description:
        - Enable or disable Power Over Ethernet on a port.
        type: bool
        default: true
    rstp_enabled:
        description:
        - Enable or disable Rapid Spanning Tree Protocol on a port.
        type: bool
        default: true
    serial:
        description:
        - Serial nubmer of the switch.
    stp_guard:
        description:
        - Set state of STP guard.
        choices: [disabled, root guard, bpdu guard, loop guard]
        default: disabled
    tags:
        description:
        - Space delimited list of tags to assign to a port.
    type:
        description:
        - Set port type.
        choices: [access, trunk]
        default: access
    vlan:
        description:
        - VLAN number assigned to port.
        - If a port is of type trunk, the specified VLAN is the native VLAN.
    voice_vlan:
        description:
        - VLAN number assigned to a port for voice traffic.
        - Only applicable to access port type.

author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query information about all switchports on a switch
  meraki_switchport:
    auth_key: abc12345
    state: query
    serial: ABC-123
  delegate_to: localhost

- name: Query information about all switchports on a switch
  meraki_switchport:
    auth_key: abc12345
    state: query
    serial: ABC-123
    number: 2
  delegate_to: localhost

- name: Name switchport
  meraki_switchport:
    auth_key: abc12345
    state: present
    serial: ABC-123
    number: 7
    name: Test Port
  delegate_to: localhost

- name: Configure access port with voice VLAN
  meraki_switchport:
    auth_key: abc12345
    state: present
    serial: ABC-123
    number: 7
    enabled: true
    name: Test Port
    tags: desktop
    type: access
    vlan: 10
    voice_vlan: 11
  delegate_to: localhost

- name: Check access port for idempotenty
  meraki_switchport:
    auth_key: abc12345
    state: present
    serial: ABC-123
    number: 7
    enabled: true
    name: Test Port
    tags: desktop
    type: access
    vlan: 10
    voice_vlan: 11
  delegate_to: localhost

- name: Configure trunk port with specific VLANs
  meraki_switchport:
    auth_key: abc12345
    state: present
    serial: ABC-123
    number: 7
    enabled: true
    name: Server port
    tags: server
    type: trunk
    allowed_vlans:
      - 10
      - 15
      - 20
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about queried or updated object.
    type: list
    returned: info
    sample:
      "data": {
          "hostname": "n110.meraki.com",
          "peer_ips": null,
          "port": 16100,
          "v2c_enabled": false,
          "v3_auth_mode": null,
          "v3_enabled": false,
          "v3_priv_mode": null
      }
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec

# param_map isn't used but leaving in as it is a more efficient method for implementation later
param_map = {'accessPolicyNumber': 'access_policy_number',
             'allowedVlans': 'allowed_vlans',
             'enabled': 'enabled',
             'isolationEnabled': 'isolation_enabled',
             'linkNegotiation': 'link_negotiation',
             'name': 'name',
             'number': 'number',
             'poeEnabled': 'poe_enabled',
             'rstpEnabled': 'rstp_enabled',
             'stpGuard': 'stp_guard',
             'tags': 'tags',
             'type': 'type',
             'vlan': 'vlan',
             'voiceVlan': 'voice_vlan',
             }


def list_to_csv(items):
    csv = ''
    count = 0
    for item in items:
        if count == len(items) - 1:
            csv = csv + str(item)
        else:
            csv = csv + str(item) + ','
        count += 1
    return csv


def main():
    # define the available arguments/parameters that a user can pass to
    # the module
    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['present', 'query'], default='query'),
                         serial=dict(type='str', required=True),
                         number=dict(type='str'),
                         name=dict(type='str', aliases=['description']),
                         tags=dict(type='str'),
                         enabled=dict(type='bool', default=True),
                         type=dict(type='str', choices=['access', 'trunk'], default='access'),
                         vlan=dict(type='int'),
                         voice_vlan=dict(type='int'),
                         allowed_vlans=dict(type='list', default='all'),
                         poe_enabled=dict(type='bool', default=True),
                         isolation_enabled=dict(type='bool', default=False),
                         rstp_enabled=dict(type='bool', default=True),
                         stp_guard=dict(type='str', choices=['disabled', 'root guard', 'bpdu guard', 'loop guard'], default='disabled'),
                         access_policy_number=dict(type='str'),
                         link_negotiation=dict(type='str',
                                               choices=['Auto negotiate', '100Megabit (auto)', '100 Megabit full duplex (forced)'],
                                               default='Auto negotiate'),
                         )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    meraki = MerakiModule(module, function='switchport')
    meraki.params['follow_redirects'] = 'all'

    # argument checks
    # if meraki.params['type'] == 'access':
    #     if meraki.params['allowed_vlans']:
    #         meraki.fail_json(msg='allowed_vlans is not allowed on access ports')
    if meraki.params['type'] == 'trunk':
        if not meraki.params['allowed_vlans']:
            meraki.params['allowed_vlans'] = ['all']  # Backdoor way to set default without conflicting on access

    # TODO: Add support for serial in the construct_path() method
    query_urls = {'switchport': '/devices/serial/switchPorts'}
    query_url = {'switchport': '/devices/serial/switchPorts/'}
    update_url = {'switchport': '/devices/serial/switchPorts/'}

    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['get_one'].update(query_url)
    meraki.url_catalog['update'] = update_url

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
    if meraki.params['state'] == 'query':
        if meraki.params['number']:
            path = meraki.construct_path('get_one') + meraki.params['number']
            path = path.replace('serial', meraki.params['serial'])
            response = meraki.request(path, method='GET')
            meraki.result['data'] = response
        else:
            path = meraki.construct_path('get_all')
            path = path.replace('serial', meraki.params['serial'])
            response = meraki.request(path, method='GET')
            meraki.result['data'] = response
    elif meraki.params['state'] == 'present':
        payload = dict()
        proposed = dict()

        # if meraki.params['type'] == 'access':
        payload['name'] = meraki.params['name']
        payload['tags'] = meraki.params['tags']
        payload['enabled'] = meraki.params['enabled']
        payload['poeEnabled'] = meraki.params['poe_enabled']
        payload['type'] = meraki.params['type']
        payload['vlan'] = meraki.params['vlan']
        payload['voiceVlan'] = meraki.params['voice_vlan']
        payload['isolationEnabled'] = meraki.params['isolation_enabled']
        payload['rstpEnabled'] = meraki.params['rstp_enabled']
        payload['stpGuard'] = meraki.params['stp_guard']
        payload['accessPolicyNumber'] = meraki.params['access_policy_number']
        payload['linkNegotiation'] = meraki.params['link_negotiation']
        payload['allowedVlans'] = list_to_csv(meraki.params['allowed_vlans'])
        proposed['name'] = meraki.params['name']
        proposed['tags'] = meraki.params['tags']
        proposed['enabled'] = meraki.params['enabled']
        proposed['poeEnabled'] = meraki.params['poe_enabled']
        proposed['type'] = meraki.params['type']
        proposed['vlan'] = meraki.params['vlan']
        proposed['voiceVlan'] = meraki.params['voice_vlan']
        proposed['isolationEnabled'] = meraki.params['isolation_enabled']
        proposed['rstpEnabled'] = meraki.params['rstp_enabled']
        proposed['stpGuard'] = meraki.params['stp_guard']
        proposed['accessPolicyNumber'] = meraki.params['access_policy_number']
        proposed['linkNegotiation'] = meraki.params['link_negotiation']
        proposed['allowedVlans'] = list_to_csv(meraki.params['allowed_vlans'])

        # Exceptions need to be made for idempotency check based on how Meraki returns
        if meraki.params['type'] == 'trunk':
            if meraki.params['vlan'] and meraki.params['allowed_vlans'] != 'all':
                proposed['allowedVlans'] = str(meraki.params['vlan']) + ',' + proposed['allowedVlans']
        else:
            if not meraki.params['vlan']:  # VLAN needs to be specified in access ports, but can't default to it
                payload['vlan'] = 1
                proposed['vlan'] = 1

        query_path = meraki.construct_path('get_one') + meraki.params['number']
        query_path = query_path.replace('serial', meraki.params['serial'])
        original = meraki.request(query_path, method='GET')
        if meraki.params['type'] == 'trunk':
            proposed['voiceVlan'] = original['voiceVlan']  # API shouldn't include voice VLAN on a trunk port
        if meraki.is_update_required(original, proposed, optional_ignore=('number')):
            path = meraki.construct_path('update') + meraki.params['number']
            path = path.replace('serial', meraki.params['serial'])
            response = meraki.request(path, method='PUT', payload=json.dumps(payload))
            meraki.result['data'] = response
            meraki.result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
