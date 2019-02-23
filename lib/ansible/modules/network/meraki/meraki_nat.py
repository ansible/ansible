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
module: meraki_nat
short_description: Manage NAT rules in Meraki cloud
version_added: "2.8"
description:
- Allows for creation, management, and visibility of NAT rules (1:1, 1:many, port forwarding) within Meraki.

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
    state:
        description:
        - Create or modify an organization.
        choices: [absent, present, query]
        default: present
    net_name:
        description:
        - Name of a network.
        aliases: [name, network]
    net_id:
        description:
        - ID number of a network.
    org_name:
        description:
        - Name of organization associated to a network.
    org_id:
        description:
        - ID of organization associated to a network.
    type:
        description:
        - Type of network device network manages.
        - Required when creating a network.
        choices: [appliance, combined, switch, wireless]
        aliases: [net_type]
    tags:
        description:
        - Comma delimited list of tags to assign to network.
    timezone:
        description:
        - Timezone associated to network.
        - See U(https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for a list of valid timezones.
    disable_my_meraki:
        description: >
            - Disables the local device status pages (U[my.meraki.com](my.meraki.com), U[ap.meraki.com](ap.meraki.com), U[switch.meraki.com](switch.meraki.com),
            U[wired.meraki.com](wired.meraki.com))
        type: bool
        version_added: '2.7'

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: List all networks associated to the YourOrg organization
  meraki_network:
    auth_key: abc12345
    state: query
    org_name: YourOrg
  delegate_to: localhost
- name: Query network named MyNet in the YourOrg organization
  meraki_network:
    auth_key: abc12345
    state: query
    org_name: YourOrg
    net_name: MyNet
  delegate_to: localhost
- name: Create network named MyNet in the YourOrg organization
  meraki_network:
    auth_key: abc12345
    state: present
    org_name: YourOrg
    net_name: MyNet
    type: switch
    timezone: America/Chicago
    tags: production, chicago
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about the created or manipulated object.
    returned: info
    type: complex
    contains:
      id:
        description: Identification string of network.
        returned: success
        type: str
        sample: N_12345
      name:
        description: Written name of network.
        returned: success
        type: str
        sample: YourNet
      organizationId:
        description: Organization ID which owns the network.
        returned: success
        type: str
        sample: 0987654321
      tags:
        description: Space delimited tags assigned to network.
        returned: success
        type: str
        sample: " production wireless "
      timeZone:
        description: Timezone where network resides.
        returned: success
        type: str
        sample: America/Chicago
      type:
        description: Functional type of network.
        returned: success
        type: str
        sample: switch
      disableMyMerakiCom:
        description: States whether U(my.meraki.com) and other device portals should be disabled.
        returned: success
        type: bool
        sample: true
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    one_to_one_spec = dict(name=dict(type='str'),
                           public_ip=dict(type='str'),
                           lan_ip=dict(type='str'),
                           uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                           allowed_inbound=dict(type='str'),
                           protocol=dict(type='str', choices=['tcp', 'udp', 'icmp-ping', 'any'], default='any'),
                           destination_ports=dict(type='list'),
                           allowed_ips=dict(type='list'),
                           )

    one_to_many_spec = dict(name=dict(type='str'),
                            public_ip=dict(type='str'),
                            lan_ip=dict(type='str'),
                            uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                            protocol=dict(type='str', choices=['tcp', 'udp']),
                            allowed_ips=dict(type='list'),
                            port_rules=dict(type='list'),
                            public_port=dict(type='int'),
                            local_ip=dict(type='str'),
                            local_port=dict(type='str'),
                            )

    port_forwarding_spec = dict(name=dict(type='str'),
                                lan_ip=dict(type='str'),
                                uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                                protocol=dict(type='str', choices=['tcp', 'udp']),
                                public_port=dict(type='int'),
                                local_port=dict(type='int'),
                                allowed_ips=dict(type='list'),
                                )

    key_map = {'name': 'name',
               'public_ip': 'publicIp',
               'lan_ip': 'lanIp',
               'uplink': 'uplink',
               'allowed_inbound': 'allowedInbound',
               'protocol': 'protocol',
               'destination_ports': 'destinationPorts',
               'allowed_ips': 'allowedIps',
               'port_rules': 'portRules',
               'public_port': 'publicPort',
               'local_ip': 'localIp',
               'local_port': 'localPort',
               }

    argument_spec = meraki_argument_spec()
    argument_spec.update(
        net_id=dict(type='str'),
        net_name=dict(type='str', aliases=['name', 'network']),
        state=dict(type='str', choices=['present', 'query'], default='present'),
        subset=dict(type='list', choices=['1:1', '1:many', 'all', 'port_forwarding'], default='all'),
        one_to_one=dict(type='list', element='dict', options=one_to_one_spec),
        one_to_many=dict(type='list', element='dict', options=one_to_many_spec),
        port_forwarding=dict(type='list', element='dict', options=port_forwarding_spec),
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )

    meraki = MerakiModule(module, function='nat')
    module.params['follow_redirects'] = 'all'

    if meraki.params['state'] == 'present':
        if meraki.params['one_to_one']:
            one_to_one_payload = []
            for rule in meraki.params['one_to_one']:
                rule_set = {}
                for k, v in rule.items():
                    rule_set[key_map[k]] = v
                one_to_one_payload.append(rule_set)
        if meraki.params['one_to_many']:
            one_to_many_payload = []
            for rule in meraki.params['one_to_many']:
                rule_set = {}
                for k, v in rule.items():
                    rule_set[key_map[k]] = v
                one_to_many_payload.append(rule_set)
        if meraki.params['port_forwarding']:
            port_forwarding_payload = []
            for rule in meraki.params['port_forwarding']:
                rule_set = {}
                for k, v in rule.items():
                    rule_set[key_map[k]] = v
                port_forwarding_payload.append(rule_set)

    # meraki.fail_json(msg="Payload", one_to_one=one_to_one_payload)
    # meraki.fail_json(msg="Payload", one_to_many=one_to_many_payload)
    # meraki.fail_json(msg="Payload", port_forwarding=port_forwarding_payload)

    onetomany_urls = {'nat': '/networks/{net_id}/oneToOneNatRules'}
    onetoone_urls = {'nat': '/networks/{net_id}/oneToManyNatRules'}
    port_forwarding_urls = {'nat': '/networks/{net_id}/portForwardingRules'}
    meraki.url_catalog['1:many'] = onetomany_urls
    meraki.url_catalog['1:1'] = onetoone_urls
    meraki.url_catalog['port_forwarding'] = port_forwarding_urls

    if meraki.params['net_name'] and meraki.params['net_id']:
        meraki.fail_json(msg='net_name and net_id are mutually exclusive')

    org_id = meraki.params['org_id']
    if not org_id:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(org_id, meraki.params['net_name'], data=nets)        

    if meraki.params['state'] == 'query':
        # meraki.fail_json(msg="Parameters", params=meraki.params)
        if meraki.params['subset'][0] == 'all':
            path = meraki.construct_path('1:many', net_id=net_id)
            data = {'1:many': meraki.request(path, method='GET')}
            path = meraki.construct_path('1:1', net_id=net_id)
            data['1:1'] = meraki.request(path, method='GET')
            path = meraki.construct_path('port_forwarding', net_id=net_id)
            data['port_forwarding'] = meraki.request(path, method='GET')
            meraki.result['data'] = data
        else:
            for subset in meraki.params['subset']:
                path = meraki.construct_path(subset, net_id=net_id)
                data = {subset: meraki.request(path, method='GET')}
                try:
                    meraki.result['data'][subset] = data
                except KeyError:
                    meraki.result['data'] = {subset: data}

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
