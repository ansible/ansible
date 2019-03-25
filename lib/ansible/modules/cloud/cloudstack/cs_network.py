#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_network
short_description: Manages networks on Apache CloudStack based clouds.
description:
    - Create, update, restart and delete networks.
version_added: '2.0'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name (case sensitive) of the network.
    type: str
    required: true
  display_text:
    description:
      - Display text of the network.
      - If not specified, I(name) will be used as I(display_text).
    type: str
  network_offering:
    description:
      - Name of the offering for the network.
      - Required if I(state=present).
    type: str
  start_ip:
    description:
      - The beginning IPv4 address of the network belongs to.
      - Only considered on create.
    type: str
  end_ip:
    description:
      - The ending IPv4 address of the network belongs to.
      - If not specified, value of I(start_ip) is used.
      - Only considered on create.
    type: str
  gateway:
    description:
      - The gateway of the network.
      - Required for shared networks and isolated networks when it belongs to a VPC.
      - Only considered on create.
    type: str
  netmask:
    description:
      - The netmask of the network.
      - Required for shared networks and isolated networks when it belongs to a VPC.
      - Only considered on create.
    type: str
  start_ipv6:
    description:
      - The beginning IPv6 address of the network belongs to.
      - Only considered on create.
    type: str
  end_ipv6:
    description:
      - The ending IPv6 address of the network belongs to.
      - If not specified, value of I(start_ipv6) is used.
      - Only considered on create.
    type: str
  cidr_ipv6:
    description:
      - CIDR of IPv6 network, must be at least /64.
      - Only considered on create.
    type: str
  gateway_ipv6:
    description:
      - The gateway of the IPv6 network.
      - Required for shared networks.
      - Only considered on create.
  vlan:
    description:
      - The ID or VID of the network.
    type: str
  vpc:
    description:
      - Name of the VPC of the network.
    type: str
  isolated_pvlan:
    description:
      - The isolated private VLAN for this network.
    type: str
  clean_up:
    description:
      - Cleanup old network elements.
      - Only considered on I(state=restarted).
    default: no
    type: bool
  acl_type:
    description:
      - Access control type for the network.
      - If not specified, Cloudstack will default to C(account) for isolated networks
      - and C(domain) for shared networks.
      - Only considered on create.
    type: str
    choices: [ account, domain ]
  acl:
    description:
      - The name of the access control list for the VPC network tier.
    type: str
    version_added: '2.5'
  subdomain_access:
    description:
      - Defines whether to allow subdomains to use networks dedicated to their parent domain(s).
      - Should be used with I(acl_type=domain).
      - Only considered on create.
    type: bool
    version_added: '2.5'
  network_domain:
    description:
      - The network domain.
    type: str
  state:
    description:
      - State of the network.
    type: str
    default: present
    choices: [ present, absent, restarted ]
  zone:
    description:
      - Name of the zone in which the network should be deployed.
      - If not set, default zone is used.
    type: str
  project:
    description:
      - Name of the project the network to be deployed in.
    type: str
  domain:
    description:
      - Domain the network is related to.
    type: str
  account:
    description:
      - Account the network is related to.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a network
  cs_network:
    name: my network
    zone: gva-01
    network_offering: DefaultIsolatedNetworkOfferingWithSourceNatService
    network_domain: example.com
  delegate_to: localhost

- name: Create a VPC tier
  cs_network:
    name: my VPC tier 1
    zone: gva-01
    vpc: my VPC
    network_offering: DefaultIsolatedNetworkOfferingForVpcNetworks
    gateway: 10.43.0.1
    netmask: 255.255.255.0
    acl: my web acl
  delegate_to: localhost

- name: Update a network
  cs_network:
    name: my network
    display_text: network of domain example.local
    network_domain: example.local
  delegate_to: localhost

- name: Restart a network with clean up
  cs_network:
    name: my network
    clean_up: yes
    state: restared
  delegate_to: localhost

- name: Remove a network
  cs_network:
    name: my network
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the network.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the network.
  returned: success
  type: str
  sample: web project
display_text:
  description: Display text of the network.
  returned: success
  type: str
  sample: web project
dns1:
  description: IP address of the 1st nameserver.
  returned: success
  type: str
  sample: 1.2.3.4
dns2:
  description: IP address of the 2nd nameserver.
  returned: success
  type: str
  sample: 1.2.3.4
cidr:
  description: IPv4 network CIDR.
  returned: success
  type: str
  sample: 10.101.64.0/24
gateway:
  description: IPv4 gateway.
  returned: success
  type: str
  sample: 10.101.64.1
netmask:
  description: IPv4 netmask.
  returned: success
  type: str
  sample: 255.255.255.0
cidr_ipv6:
  description: IPv6 network CIDR.
  returned: if available
  type: str
  sample: 2001:db8::/64
gateway_ipv6:
  description: IPv6 gateway.
  returned: if available
  type: str
  sample: 2001:db8::1
zone:
  description: Name of zone.
  returned: success
  type: str
  sample: ch-gva-2
domain:
  description: Domain the network is related to.
  returned: success
  type: str
  sample: ROOT
account:
  description: Account the network is related to.
  returned: success
  type: str
  sample: example account
project:
  description: Name of project.
  returned: success
  type: str
  sample: Production
tags:
  description: List of resource tags associated with the network.
  returned: success
  type: list
  sample: '[ { "key": "foo", "value": "bar" } ]'
acl_type:
  description: Access type of the network (Domain, Account).
  returned: success
  type: str
  sample: Account
acl:
  description: Name of the access control list for the VPC network tier.
  returned: success
  type: str
  sample: My ACL
  version_added: '2.5'
acl_id:
  description: ID of the access control list for the VPC network tier.
  returned: success
  type: str
  sample: dfafcd55-0510-4b8c-b6c5-b8cedb4cfd88
  version_added: '2.5'
broadcast_domain_type:
  description: Broadcast domain type of the network.
  returned: success
  type: str
  sample: Vlan
type:
  description: Type of the network.
  returned: success
  type: str
  sample: Isolated
traffic_type:
  description: Traffic type of the network.
  returned: success
  type: str
  sample: Guest
state:
  description: State of the network (Allocated, Implemented, Setup).
  returned: success
  type: str
  sample: Allocated
is_persistent:
  description: Whether the network is persistent or not.
  returned: success
  type: bool
  sample: false
network_domain:
  description: The network domain
  returned: success
  type: str
  sample: example.local
network_offering:
  description: The network offering name.
  returned: success
  type: str
  sample: DefaultIsolatedNetworkOfferingWithSourceNatService
network_offering_display_text:
  description: The network offering display text.
  returned: success
  type: str
  sample: Offering for Isolated Vpc networks with Source Nat service enabled
  version_added: '2.5'
network_offering_conserve_mode:
  description: Whether the network offering has IP conserve mode enabled or not.
  returned: success
  type: bool
  sample: false
  version_added: '2.5'
network_offering_availability:
  description: The availability of the network offering the network is created from
  returned: success
  type: str
  sample: Optional
  version_added: '2.5'
is_system:
  description: Whether the network is system related or not.
  returned: success
  type: bool
  sample: false
  version_added: '2.5'
vpc:
  description: Name of the VPC.
  returned: if available
  type: str
  sample: My VPC
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackNetwork(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackNetwork, self).__init__(module)
        self.returns = {
            'networkdomain': 'network_domain',
            'networkofferingname': 'network_offering',
            'networkofferingdisplaytext': 'network_offering_display_text',
            'networkofferingconservemode': 'network_offering_conserve_mode',
            'networkofferingavailability': 'network_offering_availability',
            'aclid': 'acl_id',
            'issystem': 'is_system',
            'ispersistent': 'is_persistent',
            'acltype': 'acl_type',
            'type': 'type',
            'traffictype': 'traffic_type',
            'ip6gateway': 'gateway_ipv6',
            'ip6cidr': 'cidr_ipv6',
            'gateway': 'gateway',
            'cidr': 'cidr',
            'netmask': 'netmask',
            'broadcastdomaintype': 'broadcast_domain_type',
            'dns1': 'dns1',
            'dns2': 'dns2',
        }
        self.network = None

    def get_network_acl(self, key=None, acl_id=None):
        if acl_id is not None:
            args = {
                'id': acl_id,
                'vpcid': self.get_vpc(key='id'),
            }
        else:
            acl_name = self.module.params.get('acl')
            if not acl_name:
                return

            args = {
                'name': acl_name,
                'vpcid': self.get_vpc(key='id'),
            }
        network_acls = self.query_api('listNetworkACLLists', **args)
        if network_acls:
            acl = network_acls['networkacllist'][0]
            return self._get_by_key(key, acl)

    def get_network_offering(self, key=None):
        network_offering = self.module.params.get('network_offering')
        if not network_offering:
            self.module.fail_json(msg="missing required arguments: network_offering")

        args = {
            'zoneid': self.get_zone(key='id'),
            'fetch_list': True,
        }

        network_offerings = self.query_api('listNetworkOfferings', **args)
        if network_offerings:
            for no in network_offerings:
                if network_offering in [no['name'], no['displaytext'], no['id']]:
                    return self._get_by_key(key, no)
        self.module.fail_json(msg="Network offering '%s' not found" % network_offering)

    def _get_args(self):
        args = {
            'name': self.module.params.get('name'),
            'displaytext': self.get_or_fallback('display_text', 'name'),
            'networkdomain': self.module.params.get('network_domain'),
            'networkofferingid': self.get_network_offering(key='id')
        }
        return args

    def get_network(self, refresh=False):
        if not self.network or refresh:
            network = self.module.params.get('name')
            args = {
                'zoneid': self.get_zone(key='id'),
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'vpcid': self.get_vpc(key='id'),
                'fetch_list': True,
            }
            networks = self.query_api('listNetworks', **args)
            if networks:
                for n in networks:
                    if network in [n['name'], n['displaytext'], n['id']]:
                        self.network = n
                        self.network['acl'] = self.get_network_acl(key='name', acl_id=n.get('aclid'))
                        break
        return self.network

    def present_network(self):
        if self.module.params.get('acl') is not None and self.module.params.get('vpc') is None:
            self.module.fail_json(msg="Missing required params: vpc")

        network = self.get_network()
        if not network:
            network = self.create_network(network)
        else:
            network = self.update_network(network)
        return network

    def update_network(self, network):
        args = self._get_args()
        args['id'] = network['id']

        if self.has_changed(args, network):
            self.result['changed'] = True
            if not self.module.check_mode:
                network = self.query_api('updateNetwork', **args)

                poll_async = self.module.params.get('poll_async')
                if network and poll_async:
                    network = self.poll_job(network, 'network')

        # Skip ACL check if the network is not a VPC tier
        if network.get('aclid') != self.get_network_acl(key='id'):
            self.result['changed'] = True
            if not self.module.check_mode:
                args = {
                    'aclid': self.get_network_acl(key='id'),
                    'networkid': network['id'],
                }
                network = self.query_api('replaceNetworkACLList', **args)
                if self.module.params.get('poll_async'):
                    self.poll_job(network, 'networkacllist')
                    network = self.get_network(refresh=True)
        return network

    def create_network(self, network):
        self.result['changed'] = True

        args = self._get_args()
        args.update({
            'acltype': self.module.params.get('acl_type'),
            'aclid': self.get_network_acl(key='id'),
            'zoneid': self.get_zone(key='id'),
            'projectid': self.get_project(key='id'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'startip': self.module.params.get('start_ip'),
            'endip': self.get_or_fallback('end_ip', 'start_ip'),
            'netmask': self.module.params.get('netmask'),
            'gateway': self.module.params.get('gateway'),
            'startipv6': self.module.params.get('start_ipv6'),
            'endipv6': self.get_or_fallback('end_ipv6', 'start_ipv6'),
            'ip6cidr': self.module.params.get('cidr_ipv6'),
            'ip6gateway': self.module.params.get('gateway_ipv6'),
            'vlan': self.module.params.get('vlan'),
            'isolatedpvlan': self.module.params.get('isolated_pvlan'),
            'subdomainaccess': self.module.params.get('subdomain_access'),
            'vpcid': self.get_vpc(key='id')
        })

        if not self.module.check_mode:
            res = self.query_api('createNetwork', **args)

            network = res['network']
        return network

    def restart_network(self):
        network = self.get_network()

        if not network:
            self.module.fail_json(msg="No network named '%s' found." % self.module.params('name'))

        # Restarting only available for these states
        if network['state'].lower() in ['implemented', 'setup']:
            self.result['changed'] = True

            args = {
                'id': network['id'],
                'cleanup': self.module.params.get('clean_up')
            }

            if not self.module.check_mode:
                network = self.query_api('restartNetwork', **args)

                poll_async = self.module.params.get('poll_async')
                if network and poll_async:
                    network = self.poll_job(network, 'network')
        return network

    def absent_network(self):
        network = self.get_network()
        if network:
            self.result['changed'] = True

            args = {
                'id': network['id']
            }

            if not self.module.check_mode:
                res = self.query_api('deleteNetwork', **args)

                poll_async = self.module.params.get('poll_async')
                if res and poll_async:
                    self.poll_job(res, 'network')
            return network

    def get_result(self, network):
        super(AnsibleCloudStackNetwork, self).get_result(network)
        if network:
            self.result['acl'] = self.get_network_acl(key='name', acl_id=network.get('aclid'))
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        display_text=dict(),
        network_offering=dict(),
        zone=dict(),
        start_ip=dict(),
        end_ip=dict(),
        gateway=dict(),
        netmask=dict(),
        start_ipv6=dict(),
        end_ipv6=dict(),
        cidr_ipv6=dict(),
        gateway_ipv6=dict(),
        vlan=dict(),
        vpc=dict(),
        isolated_pvlan=dict(),
        clean_up=dict(type='bool', default=False),
        network_domain=dict(),
        subdomain_access=dict(type='bool'),
        state=dict(choices=['present', 'absent', 'restarted'], default='present'),
        acl=dict(),
        acl_type=dict(choices=['account', 'domain']),
        project=dict(),
        domain=dict(),
        account=dict(),
        poll_async=dict(type='bool', default=True),
    ))
    required_together = cs_required_together()
    required_together.extend([
        ['netmask', 'gateway'],
    ])

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        supports_check_mode=True
    )

    acs_network = AnsibleCloudStackNetwork(module)

    state = module.params.get('state')
    if state == 'absent':
        network = acs_network.absent_network()

    elif state == 'restarted':
        network = acs_network.restart_network()

    else:
        network = acs_network.present_network()

    result = acs_network.get_result(network)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
