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
version_added: "2.9"
description:
- Allows for creation, management, and visibility of NAT rules (1:1, 1:many, port forwarding) within Meraki.

options:
    state:
        description:
        - Create or modify an organization.
        choices: [present, query]
        default: present
        type: str
    net_name:
        description:
        - Name of a network.
        aliases: [name, network]
        type: str
    net_id:
        description:
        - ID number of a network.
        type: str
    org_id:
        description:
        - ID of organization associated to a network.
        type: str
    subset:
        description:
        - Specifies which NAT components to query.
        choices: ['1:1', '1:many', all, port_forwarding]
        default: all
        type: list
    one_to_one:
        description:
        - List of 1:1 NAT rules.
        type: list
        suboptions:
            name:
                description:
                - A descriptive name for the rule.
                type: str
            public_ip:
                description:
                - The IP address that will be used to access the internal resource from the WAN.
                type: str
            lan_ip:
                description:
                - The IP address of the server or device that hosts the internal resource that you wish to make available on the WAN.
                type: str
            uplink:
                description:
                - The physical WAN interface on which the traffic will arrive.
                choices: [both, internet1, internet2]
            allowed_inbound:
                description:
                - The ports this mapping will provide access on, and the remote IPs that will be allowed access to the resource.
                type: list
                suboptions:
                    protocol:
                        description:
                        - Protocol to apply NAT rule to.
                        choices: [any, icmp-ping, tcp, udp]
                        type: str
                        default: any
                    destination_ports:
                        description:
                        - List of ports or port ranges that will be forwarded to the host on the LAN.
                        type: list
                    allowed_ips:
                        description:
                        - ranges of WAN IP addresses that are allowed to make inbound connections on the specified ports or port ranges, or 'any'.
                        type: list
    one_to_many:
        description:
        - List of 1:many NAT rules.
        type: list
        suboptions:
            public_ip:
                description:
                - The IP address that will be used to access the internal resource from the WAN.
                type: str
            uplink:
                description:
                - The physical WAN interface on which the traffic will arrive.
                choices: [both, internet1, internet2]
                type: str
            port_rules:
                description:
                - List of associated port rules.
                type: list
                suboptions:
                    name:
                        description:
                        - A description of the rule.
                        type: str
                    protocol:
                        description:
                        - Protocol to apply NAT rule to.
                        choices: [tcp, udp]
                        type: str
                    public_port:
                        description:
                        - Destination port of the traffic that is arriving on the WAN.
                        type: str
                    local_ip:
                        description:
                        - Local IP address to which traffic will be forwarded.
                        type: str
                    local_port:
                        description:
                        - Destination port of the forwarded traffic that will be sent from the MX to the specified host on the LAN.
                        - If you simply wish to forward the traffic without translating the port, this should be the same as the Public port.
                        type: str
                    allowed_ips:
                        description:
                        - Remote IP addresses or ranges that are permitted to access the internal resource via this port forwarding rule, or 'any'.
                        type: list
    port_forwarding:
        description:
        - List of port forwarding rules.
        type: list
        suboptions:
            name:
                description:
                - A descriptive name for the rule.
                type: str
            lan_ip:
                description:
                - The IP address of the server or device that hosts the internal resource that you wish to make available on the WAN.
                type: str
            uplink:
                description:
                - The physical WAN interface on which the traffic will arrive.
                choices: [both, internet1, internet2]
                type: str
            public_port:
                description:
                - A port or port ranges that will be forwarded to the host on the LAN.
                type: str
            local_port:
                description:
                - A port or port ranges that will receive the forwarded traffic from the WAN.
                type: str
            allowed_ips:
                description:
                - List of ranges of WAN IP addresses that are allowed to make inbound connections on the specified ports or port ranges (or any).
            protocol:
                description:
                - Protocol to forward traffic for.
                choices: [tcp, udp]
                type: str

author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query all NAT rules
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: query
    subset: all
  delegate_to: localhost

- name: Query 1:1 NAT rules
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: query
    subset: '1:1'
  delegate_to: localhost

- name: Create 1:1 rule
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    one_to_one:
      - name: Service behind NAT
        public_ip: 1.2.1.2
        lan_ip: 192.168.128.1
        uplink: internet1
        allowed_inbound:
          - protocol: tcp
            destination_ports:
              - 80
            allowed_ips:
              - 10.10.10.10
  delegate_to: localhost

- name: Create 1:many rule
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    one_to_many:
      - public_ip: 1.1.1.1
        uplink: internet1
        port_rules:
          - name: Test rule
            protocol: tcp
            public_port: 10
            local_ip: 192.168.128.1
            local_port: 11
            allowed_ips:
              - any
  delegate_to: localhost

- name: Create port forwarding rule
  meraki_nat:
    auth_key: abc123
    org_name: YourOrg
    net_name: YourNet
    state: present
    port_forwarding:
      - name: Test map
        lan_ip: 192.168.128.1
        uplink: both
        protocol: tcp
        allowed_ips:
          - 1.1.1.1
        public_port: 10
        local_port: 11
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about the created or manipulated object.
    returned: success
    type: complex
    contains:
        one_to_one:
            description: Information about 1:1 NAT object.
            returned: success, when 1:1 NAT object is in task
            type: complex
            contains:
                rules:
                    description: List of 1:1 NAT rules.
                    returned: success, when 1:1 NAT object is in task
                    type: complex
                    contains:
                        name:
                            description: Name of NAT object.
                            returned: success, when 1:1 NAT object is in task
                            type: str
                            example: Web server behind NAT
                        lanIp:
                            description: Local IP address to be mapped.
                            returned: success, when 1:1 NAT object is in task
                            type: str
                            example: 192.168.128.22
                        publicIp:
                            description: Public IP address to be mapped.
                            returned: success, when 1:1 NAT object is in task
                            type: str
                            example: 148.2.5.100
                        uplink:
                            description: Internet port where rule is applied.
                            returned: success, when 1:1 NAT object is in task
                            type: str
                            example: internet1
                        allowedInbound:
                            description: List of inbound forwarding rules.
                            returned: success, when 1:1 NAT object is in task
                            type: complex
                            contains:
                                protocol:
                                    description: Protocol to apply NAT rule to.
                                    returned: success, when 1:1 NAT object is in task
                                    type: str
                                    example: tcp
                                destinationPorts:
                                    description: Ports to apply NAT rule to.
                                    returned: success, when 1:1 NAT object is in task
                                    type: str
                                    example: 80
                                allowedIps:
                                    description: List of IP addresses to be forwarded.
                                    returned: success, when 1:1 NAT object is in task
                                    type: list
                                    example: 10.80.100.0/24
        one_to_many:
            description: Information about 1:many NAT object.
            returned: success, when 1:many NAT object is in task
            type: complex
            contains:
                rules:
                    description: List of 1:many NAT rules.
                    returned: success, when 1:many NAT object is in task
                    type: complex
                    contains:
                        publicIp:
                            description: Public IP address to be mapped.
                            returned: success, when 1:many NAT object is in task
                            type: str
                            example: 148.2.5.100
                        uplink:
                            description: Internet port where rule is applied.
                            returned: success, when 1:many NAT object is in task
                            type: str
                            example: internet1
                        portRules:
                            description: List of NAT port rules.
                            returned: success, when 1:many NAT object is in task
                            type: complex
                            contains:
                                name:
                                    description: Name of NAT object.
                                    returned: success, when 1:many NAT object is in task
                                    type: str
                                    example: Web server behind NAT
                                protocol:
                                    description: Protocol to apply NAT rule to.
                                    returned: success, when 1:1 NAT object is in task
                                    type: str
                                    example: tcp
                                publicPort:
                                    description: Destination port of the traffic that is arriving on WAN.
                                    returned: success, when 1:1 NAT object is in task
                                    type: int
                                    example: 9443
                                localIp:
                                    description: Local IP address traffic will be forwarded.
                                    returned: success, when 1:1 NAT object is in task
                                    type: str
                                    example: 192.0.2.10
                                localPort:
                                    description: Destination port to be forwarded to.
                                    returned: success, when 1:1 NAT object is in task
                                    type: int
                                    example: 443
                                allowedIps:
                                    description: List of IP addresses to be forwarded.
                                    returned: success, when 1:1 NAT object is in task
                                    type: list
                                    example: 10.80.100.0/24
        port_forwarding:
            description: Information about port forwarding rules.
            returned: success, when port forwarding is in task
            type: complex
            contains:
                rules:
                    description: List of port forwarding rules.
                    returned: success, when port forwarding is in task
                    type: complex
                    contains:
                        lanIp:
                            description: Local IP address to be mapped.
                            returned: success, when port forwarding is in task
                            type: str
                            example: 192.168.128.22
                        allowedIps:
                            description: List of IP addresses to be forwarded.
                            returned: success, when port forwarding is in task
                            type: list
                            example: 10.80.100.0/24
                        name:
                            description: Name of NAT object.
                            returned: success, when port forwarding is in task
                            type: str
                            example: Web server behind NAT
                        protocol:
                            description: Protocol to apply NAT rule to.
                            returned: success, when port forwarding is in task
                            type: str
                            example: tcp
                        publicPort:
                            description: Destination port of the traffic that is arriving on WAN.
                            returned: success, when port forwarding is in task
                            type: int
                            example: 9443
                        localPort:
                            description: Destination port to be forwarded to.
                            returned: success, when port forwarding is in task
                            type: int
                            example: 443
                        uplink:
                            description: Internet port where rule is applied.
                            returned: success, when port forwarding is in task
                            type: str
                            example: internet1
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import recursive_diff
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec

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


def construct_payload(params):
    if isinstance(params, list):
        items = []
        for item in params:
            items.append(construct_payload(item))
        return items
    elif isinstance(params, dict):
        info = {}
        for param in params:
            info[key_map[param]] = construct_payload(params[param])
        return info
    elif isinstance(params, str) or isinstance(params, int):
        return params


def list_int_to_str(data):
    return [str(item) for item in data]


def main():

    # define the available arguments/parameters that a user can pass to
    # the module

    one_to_one_allowed_inbound_spec = dict(protocol=dict(type='str', choices=['tcp', 'udp', 'icmp-ping', 'any'], default='any'),
                                           destination_ports=dict(type='list', element='str'),
                                           allowed_ips=dict(type='list'),
                                           )

    one_to_many_port_inbound_spec = dict(protocol=dict(type='str', choices=['tcp', 'udp']),
                                         name=dict(type='str'),
                                         local_ip=dict(type='str'),
                                         local_port=dict(type='str'),
                                         allowed_ips=dict(type='list'),
                                         public_port=dict(type='str'),
                                         )

    one_to_one_spec = dict(name=dict(type='str'),
                           public_ip=dict(type='str'),
                           lan_ip=dict(type='str'),
                           uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                           allowed_inbound=dict(type='list', element='dict', options=one_to_one_allowed_inbound_spec),
                           )

    one_to_many_spec = dict(public_ip=dict(type='str'),
                            uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                            port_rules=dict(type='list', element='dict', options=one_to_many_port_inbound_spec),
                            )

    port_forwarding_spec = dict(name=dict(type='str'),
                                lan_ip=dict(type='str'),
                                uplink=dict(type='str', choices=['internet1', 'internet2', 'both']),
                                protocol=dict(type='str', choices=['tcp', 'udp']),
                                public_port=dict(type='int'),
                                local_port=dict(type='int'),
                                allowed_ips=dict(type='list'),
                                )

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
                           supports_check_mode=True,
                           )

    meraki = MerakiModule(module, function='nat')
    module.params['follow_redirects'] = 'all'

    one_to_one_payload = None
    one_to_many_payload = None
    port_forwarding_payload = None
    if meraki.params['state'] == 'present':
        if meraki.params['one_to_one'] is not None:
            rules = []
            for i in meraki.params['one_to_one']:
                data = {'name': i['name'],
                        'publicIp': i['public_ip'],
                        'uplink': i['uplink'],
                        'lanIp': i['lan_ip'],
                        'allowedInbound': construct_payload(i['allowed_inbound'])
                        }
                for inbound in data['allowedInbound']:
                    inbound['destinationPorts'] = list_int_to_str(inbound['destinationPorts'])
                rules.append(data)
            one_to_one_payload = {'rules': rules}
        if meraki.params['one_to_many'] is not None:
            rules = []
            for i in meraki.params['one_to_many']:
                data = {'publicIp': i['public_ip'],
                        'uplink': i['uplink'],
                        }
                port_rules = []
                for port_rule in i['port_rules']:
                    rule = {'name': port_rule['name'],
                            'protocol': port_rule['protocol'],
                            'publicPort': str(port_rule['public_port']),
                            'localIp': port_rule['local_ip'],
                            'localPort': str(port_rule['local_port']),
                            'allowedIps': port_rule['allowed_ips'],
                            }
                    port_rules.append(rule)
                data['portRules'] = port_rules
                rules.append(data)
            one_to_many_payload = {'rules': rules}
        if meraki.params['port_forwarding'] is not None:
            port_forwarding_payload = {'rules': construct_payload(meraki.params['port_forwarding'])}
            for rule in port_forwarding_payload['rules']:
                rule['localPort'] = str(rule['localPort'])
                rule['publicPort'] = str(rule['publicPort'])

    onetomany_urls = {'nat': '/networks/{net_id}/oneToManyNatRules'}
    onetoone_urls = {'nat': '/networks/{net_id}/oneToOneNatRules'}
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
    elif meraki.params['state'] == 'present':
        meraki.result['data'] = dict()
        if one_to_one_payload is not None:
            path = meraki.construct_path('1:1', net_id=net_id)
            current = meraki.request(path, method='GET')
            if meraki.is_update_required(current, one_to_one_payload):
                if meraki.module.check_mode is True:
                    diff = recursive_diff(current, one_to_one_payload)
                    current.update(one_to_one_payload)
                    if 'diff' not in meraki.result:
                        meraki.result['diff'] = {'before': {}, 'after': {}}
                    meraki.result['diff']['before'].update({'one_to_one': diff[0]})
                    meraki.result['diff']['after'].update({'one_to_one': diff[1]})
                    meraki.result['data'] = {'one_to_one': current}
                    meraki.result['changed'] = True
                else:
                    r = meraki.request(path, method='PUT', payload=json.dumps(one_to_one_payload))
                    if meraki.status == 200:
                        diff = recursive_diff(current, one_to_one_payload)
                        if 'diff' not in meraki.result:
                            meraki.result['diff'] = {'before': {}, 'after': {}}
                        meraki.result['diff']['before'].update({'one_to_one': diff[0]})
                        meraki.result['diff']['after'].update({'one_to_one': diff[1]})
                        meraki.result['data'] = {'one_to_one': r}
                        meraki.result['changed'] = True
            else:
                meraki.result['data']['one_to_one'] = current
        if one_to_many_payload is not None:
            path = meraki.construct_path('1:many', net_id=net_id)
            current = meraki.request(path, method='GET')
            if meraki.is_update_required(current, one_to_many_payload):
                if meraki.module.check_mode is True:
                    diff = recursive_diff(current, one_to_many_payload)
                    current.update(one_to_many_payload)
                    if 'diff' not in meraki.result:
                        meraki.result['diff'] = {'before': {}, 'after': {}}
                    meraki.result['diff']['before'].update({'one_to_many': diff[0]})
                    meraki.result['diff']['after'].update({'one_to_many': diff[1]})
                    meraki.result['data']['one_to_many'] = current
                    meraki.result['changed'] = True
                else:
                    r = meraki.request(path, method='PUT', payload=json.dumps(one_to_many_payload))
                    if meraki.status == 200:
                        diff = recursive_diff(current, one_to_many_payload)
                        if 'diff' not in meraki.result:
                            meraki.result['diff'] = {'before': {}, 'after': {}}
                        meraki.result['diff']['before'].update({'one_to_many': diff[0]})
                        meraki.result['diff']['after'].update({'one_to_many': diff[1]})
                        meraki.result['data'].update({'one_to_many': r})
                        meraki.result['changed'] = True
            else:
                meraki.result['data']['one_to_many'] = current
        if port_forwarding_payload is not None:
            path = meraki.construct_path('port_forwarding', net_id=net_id)
            current = meraki.request(path, method='GET')
            if meraki.is_update_required(current, port_forwarding_payload):
                if meraki.module.check_mode is True:
                    diff = recursive_diff(current, port_forwarding_payload)
                    current.update(port_forwarding_payload)
                    if 'diff' not in meraki.result:
                        meraki.result['diff'] = {'before': {}, 'after': {}}
                    meraki.result['diff']['before'].update({'port_forwarding': diff[0]})
                    meraki.result['diff']['after'].update({'port_forwarding': diff[1]})
                    meraki.result['data']['port_forwarding'] = current
                    meraki.result['changed'] = True
                else:
                    r = meraki.request(path, method='PUT', payload=json.dumps(port_forwarding_payload))
                    if meraki.status == 200:
                        if 'diff' not in meraki.result:
                            meraki.result['diff'] = {'before': {}, 'after': {}}
                        diff = recursive_diff(current, port_forwarding_payload)
                        meraki.result['diff']['before'].update({'port_forwarding': diff[0]})
                        meraki.result['diff']['after'].update({'port_forwarding': diff[1]})
                        meraki.result['data'].update({'port_forwarding': r})
                        meraki.result['changed'] = True
            else:
                meraki.result['data']['port_forwarding'] = current

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
