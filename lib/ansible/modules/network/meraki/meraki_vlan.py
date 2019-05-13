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
module: meraki_vlan
short_description: Manage VLANs in the Meraki cloud
version_added: "2.7"
description:
- Create, edit, query, or delete VLANs in a Meraki environment.
notes:
- Meraki's API will return an error if VLANs aren't enabled on a network. VLANs are returned properly if VLANs are enabled on a network.
- Some of the options are likely only used for developers within Meraki.
- Meraki's API defaults to networks having VLAN support disabled and there is no way to enable VLANs support in the API. VLAN support must be enabled manually.
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
    name:
      description:
      - Name of VLAN.
      aliases: [vlan_name]
    subnet:
      description:
      - CIDR notation of network subnet.
    appliance_ip:
      description:
      - IP address of appliance.
      - Address must be within subnet specified in C(subnet) parameter.
    dns_nameservers:
      description:
      - Semi-colon delimited list of DNS IP addresses.
      - Specify one of the following options for preprogrammed DNS entries opendns, google_dns, upstream_dns
    reserved_ip_range:
      description:
      - IP address ranges which should be reserve and not distributed via DHCP.
    vpn_nat_subnet:
      description:
      - The translated VPN subnet if VPN and VPN subnet translation are enabled on the VLAN.
    fixed_ip_assignments:
      description:
      - Static IP address assignements to be distributed via DHCP by MAC address.
author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query all VLANs in a network.
  meraki_vlan:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    state: query
  delegate_to: localhost

- name: Query information about a single VLAN by ID.
  meraki_vlan:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    vlan_id: 2
    state: query
  delegate_to: localhost

- name: Create a VLAN.
  meraki_vlan:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    state: present
    vlan_id: 2
    name: TestVLAN
    subnet: 192.0.1.0/24
    appliance_ip: 192.0.1.1
  delegate_to: localhost

- name: Update a VLAN.
  meraki_vlan:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    state: present
    vlan_id: 2
    name: TestVLAN
    subnet: 192.0.1.0/24
    appliance_ip: 192.168.250.2
    fixed_ip_assignments:
      - mac: "13:37:de:ad:be:ef"
        ip: 192.168.250.10
        name: fixed_ip
    reserved_ip_range:
      - start: 192.168.250.10
        end: 192.168.250.20
        comment: reserved_range
    dns_nameservers: opendns
  delegate_to: localhost

- name: Delete a VLAN.
  meraki_vlan:
    auth_key: abc12345
    org_name: YourOrg
    net_name: YourNet
    state: absent
    vlan_id: 2
  delegate_to: localhost
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
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def fixed_ip_factory(meraki, data):
    fixed_ips = dict()
    for item in data:
        fixed_ips[item['mac']] = {'ip': item['ip'], 'name': item['name']}
    return fixed_ips


def get_vlans(meraki, net_id):
    path = meraki.construct_path('get_all', net_id=net_id)
    return meraki.request(path, method='GET')


# TODO: Allow method to return actual item if True to reduce number of calls needed
def is_vlan_valid(meraki, net_id, vlan_id):
    vlans = get_vlans(meraki, net_id)
    for vlan in vlans:
        if vlan_id == vlan['id']:
            return True
    return False


def format_dns(nameservers):
    return nameservers.replace(';', '\n')


def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    fixed_ip_arg_spec = dict(mac=dict(type='str'),
                             ip=dict(type='str'),
                             name=dict(type='str'),
                             )

    reserved_ip_arg_spec = dict(start=dict(type='str'),
                                end=dict(type='str'),
                                comment=dict(type='str'),
                                )

    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present', 'query'], default='query'),
                         net_name=dict(type='str', aliases=['network']),
                         net_id=dict(type='str'),
                         vlan_id=dict(type='int'),
                         name=dict(type='str', aliases=['vlan_name']),
                         subnet=dict(type='str'),
                         appliance_ip=dict(type='str'),
                         fixed_ip_assignments=dict(type='list', default=None, elements='dict', options=fixed_ip_arg_spec),
                         reserved_ip_range=dict(type='list', default=None, elements='dict', options=reserved_ip_arg_spec),
                         vpn_nat_subnet=dict(type='str'),
                         dns_nameservers=dict(type='str'),
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
    meraki = MerakiModule(module, function='vlan')

    meraki.params['follow_redirects'] = 'all'

    query_urls = {'vlan': '/networks/{net_id}/vlans'}
    query_url = {'vlan': '/networks/{net_id}/vlans/{vlan_id}'}
    create_url = {'vlan': '/networks/{net_id}/vlans'}
    update_url = {'vlan': '/networks/{net_id}/vlans/'}
    delete_url = {'vlan': '/networks/{net_id}/vlans/'}

    meraki.url_catalog['get_all'].update(query_urls)
    meraki.url_catalog['get_one'].update(query_url)
    meraki.url_catalog['create'] = create_url
    meraki.url_catalog['update'] = update_url
    meraki.url_catalog['delete'] = delete_url

    payload = None

    org_id = meraki.params['org_id']
    if org_id is None:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        if not meraki.params['vlan_id']:
            meraki.result['data'] = get_vlans(meraki, net_id)
        else:
            path = meraki.construct_path('get_one', net_id=net_id, custom={'vlan_id': meraki.params['vlan_id']})
            response = meraki.request(path, method='GET')
            meraki.result['data'] = response
    elif meraki.params['state'] == 'present':
        payload = {'id': meraki.params['vlan_id'],
                   'name': meraki.params['name'],
                   'subnet': meraki.params['subnet'],
                   'applianceIp': meraki.params['appliance_ip'],
                   }
        if is_vlan_valid(meraki, net_id, meraki.params['vlan_id']) is False:
            path = meraki.construct_path('create', net_id=net_id)
            response = meraki.request(path, method='POST', payload=json.dumps(payload))
            meraki.result['changed'] = True
            meraki.result['data'] = response
        else:
            path = meraki.construct_path('get_one', net_id=net_id, custom={'vlan_id': meraki.params['vlan_id']})
            original = meraki.request(path, method='GET')
            if meraki.params['dns_nameservers']:
                if meraki.params['dns_nameservers'] not in ('opendns', 'google_dns', 'upstream_dns'):
                    payload['dnsNameservers'] = format_dns(meraki.params['dns_nameservers'])
                else:
                    payload['dnsNameservers'] = meraki.params['dns_nameservers']
            if meraki.params['fixed_ip_assignments']:
                payload['fixedIpAssignments'] = fixed_ip_factory(meraki, meraki.params['fixed_ip_assignments'])
            if meraki.params['reserved_ip_range']:
                payload['reservedIpRanges'] = meraki.params['reserved_ip_range']
            if meraki.params['vpn_nat_subnet']:
                payload['vpnNatSubnet'] = meraki.params['vpn_nat_subnet']
            ignored = ['networkId']
            if meraki.is_update_required(original, payload, optional_ignore=ignored):
                path = meraki.construct_path('update', net_id=net_id) + str(meraki.params['vlan_id'])
                response = meraki.request(path, method='PUT', payload=json.dumps(payload))
                meraki.result['changed'] = True
                meraki.result['data'] = response
    elif meraki.params['state'] == 'absent':
        if is_vlan_valid(meraki, net_id, meraki.params['vlan_id']):
            path = meraki.construct_path('delete', net_id=net_id) + str(meraki.params['vlan_id'])
            response = meraki.request(path, 'DELETE')
            meraki.result['changed'] = True
            meraki.result['data'] = response

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # FIXME: Work with Meraki so they can implement a check mode
    if module.check_mode:
        meraki.exit_json(**meraki.result)

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
