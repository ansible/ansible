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
module: meraki_mx_l3_firewall
short_description: Manage MX appliance layer 3 firewalls in the Meraki cloud
version_added: "2.7"
description:
- Allows for creation, management, and visibility into layer 3 firewalls implemented on Meraki MX firewalls.
notes:
- Module assumes a complete list of firewall rules are passed as a parameter.
- If there is interest in this module allowing manipulation of a single firewall rule, please submit an issue against this module.
options:
    state:
        description:
        - Create or modify an organization.
        choices: ['present', 'query']
        default: present
    net_name:
        description:
        - Name of network which MX firewall is in.
    net_id:
        description:
        - ID of network which MX firewall is in.
    rules:
        description:
        - List of firewall rules.
        suboptions:
            policy:
                description:
                - Policy to apply if rule is hit.
                choices: [allow, deny]
            protocol:
                description:
                - Protocol to match against.
                choices: [any, icmp, tcp, udp]
            dest_port:
                description:
                - Comma separated list of destination port numbers to match against.
            dest_cidr:
                description:
                - Comma separated list of CIDR notation destination networks.
            src_port:
                description:
                - Comma separated list of source port numbers to match against.
            src_cidr:
                description:
                - Comma separated list of CIDR notation source networks.
            comment:
                description:
                - Optional comment to describe the firewall rule.
            syslog_enabled:
                description:
                - Whether to log hints against the firewall rule.
                - Only applicable if a syslog server is specified against the network.

    syslog_default_rule:
        description:
        - Whether to log hits against the default firewall rule.
        - Only applicable if a syslog server is specified against the network.
        - This is not shown in response from Meraki. Instead, refer to the C(syslog_enabled) value in the default rule.
        type: bool
        default: no
author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query firewall rules
  meraki_mx_l3_firewall:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: query
  delegate_to: localhost

- name: Set two firewall rules
  meraki_mx_l3_firewall:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    rules:
      - comment: Block traffic to server
        src_cidr: 192.0.1.0/24
        src_port: any
        dest_cidr: 192.0.2.2/32
        dest_port: any
        protocol: any
        policy: deny
      - comment: Allow traffic to group of servers
        src_cidr: 192.0.1.0/24
        src_port: any
        dest_cidr: 192.0.2.0/24
        dest_port: any
        protocol: any
        policy: permit
  delegate_to: localhost

- name: Set one firewall rule and enable logging of the default rule
  meraki_mx_l3_firewall:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    rules:
      - comment: Block traffic to server
        src_cidr: 192.0.1.0/24
        src_port: any
        dest_cidr: 192.0.2.2/32
        dest_port: any
        protocol: any
        policy: deny
    syslog_default_rule: yes
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Firewall rules associated to network.
    returned: success
    type: complex
    contains:
        comment:
            description: Comment to describe the firewall rule.
            returned: always
            type: str
            sample: Block traffic to server
        src_cidr:
            description: Comma separated list of CIDR notation source networks.
            returned: always
            type: str
            sample: 192.0.1.1/32,192.0.1.2/32
        src_port:
            description: Comma separated list of source ports.
            returned: always
            type: str
            sample: 80,443
        dest_cidr:
            description: Comma separated list of CIDR notation destination networks.
            returned: always
            type: str
            sample: 192.0.1.1/32,192.0.1.2/32
        dest_port:
            description: Comma separated list of destination ports.
            returned: always
            type: str
            sample: 80,443
        protocol:
            description: Network protocol for which to match against.
            returned: always
            type: str
            sample: tcp
        policy:
            description: Action to take when rule is matched.
            returned: always
            type: str
        syslog_enabled:
            description: Whether to log to syslog when rule is matched.
            returned: always
            type: bool
            sample: true
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def assemble_payload(meraki):
    params_map = {'policy': 'policy',
                  'protocol': 'protocol',
                  'dest_port': 'destPort',
                  'dest_cidr': 'destCidr',
                  'src_port': 'srcPort',
                  'src_cidr': 'srcCidr',
                  'syslog_enabled': 'syslogEnabled',
                  'comment': 'comment',
                  }
    rules = []
    for rule in meraki.params['rules']:
        proposed_rule = dict()
        for k, v in rule.items():
            proposed_rule[params_map[k]] = v
        rules.append(proposed_rule)
    payload = {'rules': rules}
    return payload


def get_rules(meraki, net_id):
    path = meraki.construct_path('get_all', net_id=net_id)
    response = meraki.request(path, method='GET')
    if meraki.status == 200:
        return response


def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    fw_rules = dict(policy=dict(type='str', choices=['allow', 'deny']),
                    protocol=dict(type='str', choices=['tcp', 'udp', 'icmp', 'any']),
                    dest_port=dict(type='str'),
                    dest_cidr=dict(type='str'),
                    src_port=dict(type='str'),
                    src_cidr=dict(type='str'),
                    comment=dict(type='str'),
                    syslog_enabled=dict(type='bool', default=False),
                    )

    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['present', 'query'], default='present'),
                         net_name=dict(type='str'),
                         net_id=dict(type='str'),
                         rules=dict(type='list', default=None, elements='dict', options=fw_rules),
                         syslog_default_rule=dict(type='bool'),
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
    meraki = MerakiModule(module, function='mx_l3_firewall')

    meraki.params['follow_redirects'] = 'all'

    query_urls = {'mx_l3_firewall': '/networks/{net_id}/l3FirewallRules/'}
    update_urls = {'mx_l3_firewall': '/networks/{net_id}/l3FirewallRules/'}

    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['update'] = update_urls

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
    org_id = meraki.params['org_id']
    orgs = None
    if org_id is None:
        orgs = meraki.get_orgs()
        for org in orgs:
            if org['name'] == meraki.params['org_name']:
                org_id = org['id']
    net_id = meraki.params['net_id']
    if net_id is None:
        if orgs is None:
            orgs = meraki.get_orgs()
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'],
                                   data=meraki.get_nets(org_id=org_id))

    if meraki.params['state'] == 'query':
        meraki.result['data'] = get_rules(meraki, net_id)
    elif meraki.params['state'] == 'present':
        rules = get_rules(meraki, net_id)
        path = meraki.construct_path('get_all', net_id=net_id)
        if meraki.params['rules']:
            payload = assemble_payload(meraki)
        else:
            payload = dict()
        update = False
        if meraki.params['syslog_default_rule'] is not None:
            payload['syslogDefaultRule'] = meraki.params['syslog_default_rule']
        try:
            if len(rules) - 1 != len(payload['rules']):  # Quick and simple check to avoid more processing
                update = True
            if meraki.params['syslog_default_rule'] is not None:
                if rules[len(rules) - 1]['syslogEnabled'] != meraki.params['syslog_default_rule']:
                    update = True
            if update is False:
                default_rule = rules[len(rules) - 1].copy()
                del rules[len(rules) - 1]  # Remove default rule for comparison
                for r in range(len(rules) - 1):
                    if meraki.is_update_required(rules[r], payload['rules'][r]) is True:
                        update = True
                rules.append(default_rule)
        except KeyError:
            pass
        if update is True:
            response = meraki.request(path, method='PUT', payload=json.dumps(payload))
            if meraki.status == 200:
                meraki.result['data'] = response
                meraki.result['changed'] = True
        else:
            meraki.result['data'] = rules

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
