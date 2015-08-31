#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_network
short_description: Manages networks on Apache CloudStack based clouds.
description:
    - Create, update, restart and delete networks.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name (case sensitive) of the network.
    required: true
  display_text:
    description:
      - Display text of the network.
      - If not specified, C(name) will be used as C(display_text).
    required: false
    default: null
  network_offering:
    description:
      - Name of the offering for the network.
      - Required if C(state=present).
    required: false
    default: null
  start_ip:
    description:
      - The beginning IPv4 address of the network belongs to.
      - Only considered on create.
    required: false
    default: null
  end_ip:
    description:
      - The ending IPv4 address of the network belongs to.
      - If not specified, value of C(start_ip) is used.
      - Only considered on create.
    required: false
    default: null
  gateway:
    description:
      - The gateway of the network.
      - Required for shared networks and isolated networks when it belongs to VPC.
      - Only considered on create.
    required: false
    default: null
  netmask:
    description:
      - The netmask of the network.
      - Required for shared networks and isolated networks when it belongs to VPC.
      - Only considered on create.
    required: false
    default: null
  start_ipv6:
    description:
      - The beginning IPv6 address of the network belongs to.
      - Only considered on create.
    required: false
    default: null
  end_ipv6:
    description:
      - The ending IPv6 address of the network belongs to.
      - If not specified, value of C(start_ipv6) is used.
      - Only considered on create.
    required: false
    default: null
  cidr_ipv6:
    description:
      - CIDR of IPv6 network, must be at least /64.
      - Only considered on create.
    required: false
    default: null
  gateway_ipv6:
    description:
      - The gateway of the IPv6 network. 
      - Required for shared networks.
      - Only considered on create.
    required: false
    default: null
  vlan:
    description:
      - The ID or VID of the network.
    required: false
    default: null
  vpc:
    description:
      - The ID or VID of the network.
    required: false
    default: null
  isolated_pvlan:
    description:
      - The isolated private vlan for this network.
    required: false
    default: null
  clean_up:
    description:
      - Cleanup old network elements.
      - Only considered on C(state=restarted).
    required: false
    default: false
  acl_type:
    description:
      - Access control type.
      - Only considered on create.
    required: false
    default: account
    choices: [ 'account', 'domain' ]
  network_domain:
    description:
      - The network domain.
    required: false
    default: null
  state:
    description:
      - State of the network.
    required: false
    default: present
    choices: [ 'present', 'absent', 'restarted' ]
  zone:
    description:
      - Name of the zone in which the network should be deployed.
      - If not set, default zone is used.
    required: false
    default: null
  project:
    description:
      - Name of the project the network to be deployed in.
    required: false
    default: null
  domain:
    description:
      - Domain the network is related to.
    required: false
    default: null
  account:
    description:
      - Account the network is related to.
    required: false
    default: null
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# create a network
- local_action:
    module: cs_network
    name: my network
    zone: gva-01
    network_offering: DefaultIsolatedNetworkOfferingWithSourceNatService
    network_domain: example.com

# update a network
- local_action:
    module: cs_network
    name: my network
    display_text: network of domain example.local
    network_domain: example.local

# restart a network with clean up
- local_action:
    module: cs_network
    name: my network
    clean_up: yes
    state: restared

# remove a network
- local_action:
    module: cs_network
    name: my network
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the network.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the network.
  returned: success
  type: string
  sample: web project
display_text:
  description: Display text of the network.
  returned: success
  type: string
  sample: web project
dns1:
  description: IP address of the 1st nameserver.
  returned: success
  type: string
  sample: 1.2.3.4
dns2:
  description: IP address of the 2nd nameserver.
  returned: success
  type: string
  sample: 1.2.3.4
cidr:
  description: IPv4 network CIDR.
  returned: success
  type: string
  sample: 10.101.64.0/24
gateway:
  description: IPv4 gateway.
  returned: success
  type: string
  sample: 10.101.64.1
netmask:
  description: IPv4 netmask.
  returned: success
  type: string
  sample: 255.255.255.0
cidr_ipv6:
  description: IPv6 network CIDR.
  returned: success
  type: string
  sample: 2001:db8::/64
gateway_ipv6:
  description: IPv6 gateway.
  returned: success
  type: string
  sample: 2001:db8::1
state:
  description: State of the network.
  returned: success
  type: string
  sample: Implemented
zone:
  description: Name of zone.
  returned: success
  type: string
  sample: ch-gva-2
domain:
  description: Domain the network is related to.
  returned: success
  type: string
  sample: ROOT
account:
  description: Account the network is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Name of project.
  returned: success
  type: string
  sample: Production
tags:
  description: List of resource tags associated with the network.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
acl_type:
  description: Access type of the network (Domain, Account).
  returned: success
  type: string
  sample: Account
broadcast_domain_type:
  description: Broadcast domain type of the network.
  returned: success
  type: string
  sample: Vlan
type:
  description: Type of the network.
  returned: success
  type: string
  sample: Isolated
traffic_type:
  description: Traffic type of the network.
  returned: success
  type: string
  sample: Guest
state:
  description: State of the network (Allocated, Implemented, Setup).
  returned: success
  type: string
  sample: Allocated
is_persistent:
  description: Whether the network is persistent or not.
  returned: success
  type: boolean
  sample: false
network_domain:
  description: The network domain
  returned: success
  type: string
  sample: example.local
network_offering:
  description: The network offering name.
  returned: success
  type: string
  sample: DefaultIsolatedNetworkOfferingWithSourceNatService
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackNetwork(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackNetwork, self).__init__(module)
        self.returns = {
            'networkdomain':        'network domain',
            'networkofferingname':  'network_offering',
            'ispersistent':         'is_persistent',
            'acltype':              'acl_type',
            'type':                 'type',
            'traffictype':          'traffic_type',
            'ip6gateway':           'gateway_ipv6',
            'ip6cidr':              'cidr_ipv6',
            'gateway':              'gateway',
            'cidr':                 'cidr',
            'netmask':              'netmask',
            'broadcastdomaintype':  'broadcast_domain_type',
            'dns1':                 'dns1',
            'dns2':                 'dns2',
        }

        self.network = None


    def get_vpc(self, key=None):
        vpc = self.module.params.get('vpc')
        if not vpc:
            return None

        args                = {}
        args['account']     = self.get_account(key='name')
        args['domainid']    = self.get_domain(key='id')
        args['projectid']   = self.get_project(key='id')
        args['zoneid']      = self.get_zone(key='id')

        vpcs = self.cs.listVPCs(**args)
        if vpcs:
            for v in vpcs['vpc']:
                if vpc in [ v['name'], v['displaytext'], v['id'] ]:
                    return self._get_by_key(key, v)
        self.module.fail_json(msg="VPC '%s' not found" % vpc)


    def get_network_offering(self, key=None):
        network_offering = self.module.params.get('network_offering')
        if not network_offering:
            self.module.fail_json(msg="missing required arguments: network_offering")

        args            = {}
        args['zoneid']  = self.get_zone(key='id')

        network_offerings = self.cs.listNetworkOfferings(**args)
        if network_offerings:
            for no in network_offerings['networkoffering']:
                if network_offering in [ no['name'], no['displaytext'], no['id'] ]:
                    return self._get_by_key(key, no)
        self.module.fail_json(msg="Network offering '%s' not found" % network_offering)


    def _get_args(self):
        args                        = {}
        args['name']                = self.module.params.get('name')
        args['displaytext']         = self.get_or_fallback('display_text', 'name')
        args['networkdomain']       = self.module.params.get('network_domain')
        args['networkofferingid']   = self.get_network_offering(key='id')
        return args


    def get_network(self):
        if not self.network:
            network = self.module.params.get('name')

            args                = {}
            args['zoneid']      = self.get_zone(key='id')
            args['projectid']   = self.get_project(key='id')
            args['account']     = self.get_account(key='name')
            args['domainid']    = self.get_domain(key='id')

            networks = self.cs.listNetworks(**args)
            if networks:
                for n in networks['network']:
                    if network in [ n['name'], n['displaytext'], n['id']]:
                        self.network = n
                        break
        return self.network


    def present_network(self):
        network = self.get_network()
        if not network:
            network = self.create_network(network)
        else:
            network = self.update_network(network)
        return network


    def update_network(self, network):
        args        = self._get_args()
        args['id']  = network['id']

        if self._has_changed(args, network):
            self.result['changed'] = True
            if not self.module.check_mode:
                network = self.cs.updateNetwork(**args)

                if 'errortext' in network:
                    self.module.fail_json(msg="Failed: '%s'" % network['errortext'])

                poll_async = self.module.params.get('poll_async')
                if network and poll_async:
                    network = self._poll_job(network, 'network')
        return network


    def create_network(self, network):
        self.result['changed'] = True

        args                    = self._get_args()
        args['acltype']         = self.module.params.get('acl_type')
        args['zoneid']          = self.get_zone(key='id')
        args['projectid']       = self.get_project(key='id')
        args['account']         = self.get_account(key='name')
        args['domainid']        = self.get_domain(key='id')
        args['startip']         = self.module.params.get('start_ip')
        args['endip']           = self.get_or_fallback('end_ip', 'start_ip')
        args['netmask']         = self.module.params.get('netmask')
        args['gateway']         = self.module.params.get('gateway')
        args['startipv6']       = self.module.params.get('start_ipv6')
        args['endipv6']         = self.get_or_fallback('end_ipv6', 'start_ipv6')
        args['ip6cidr']         = self.module.params.get('cidr_ipv6')
        args['ip6gateway']      = self.module.params.get('gateway_ipv6')
        args['vlan']            = self.module.params.get('vlan')
        args['isolatedpvlan']   = self.module.params.get('isolated_pvlan')
        args['subdomainaccess'] = self.module.params.get('subdomain_access')
        args['vpcid']           = self.get_vpc(key='id')

        if not self.module.check_mode:
            res = self.cs.createNetwork(**args)

            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

            network = res['network']
        return network


    def restart_network(self):
        network = self.get_network()

        if not network:
            self.module.fail_json(msg="No network named '%s' found." % self.module.params('name'))

        # Restarting only available for these states
        if network['state'].lower() in [ 'implemented', 'setup' ]:
            self.result['changed'] = True

            args            = {}
            args['id']      = network['id']
            args['cleanup'] = self.module.params.get('clean_up')

            if not self.module.check_mode:
                network = self.cs.restartNetwork(**args)

                if 'errortext' in network:
                    self.module.fail_json(msg="Failed: '%s'" % network['errortext'])

                poll_async = self.module.params.get('poll_async')
                if network and poll_async:
                    network = self._poll_job(network, 'network')
        return network


    def absent_network(self):
        network = self.get_network()
        if network:
            self.result['changed'] = True

            args        = {}
            args['id']  = network['id']

            if not self.module.check_mode:
                res = self.cs.deleteNetwork(**args)

                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if res and poll_async:
                    res = self._poll_job(res, 'network')
            return network



def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            display_text = dict(default=None),
            network_offering = dict(default=None),
            zone = dict(default=None),
            start_ip = dict(default=None),
            end_ip = dict(default=None),
            gateway = dict(default=None),
            netmask = dict(default=None),
            start_ipv6 = dict(default=None),
            end_ipv6 = dict(default=None),
            cidr_ipv6 = dict(default=None),
            gateway_ipv6 = dict(default=None),
            vlan = dict(default=None),
            vpc = dict(default=None),
            isolated_pvlan = dict(default=None),
            clean_up = dict(type='bool', choices=BOOLEANS, default=False),
            network_domain = dict(default=None),
            state = dict(choices=['present', 'absent', 'restarted' ], default='present'),
            acl_type = dict(choices=['account', 'domain'], default='account'),
            project = dict(default=None),
            domain = dict(default=None),
            account = dict(default=None),
            poll_async = dict(type='bool', choices=BOOLEANS, default=True),
            api_key = dict(default=None),
            api_secret = dict(default=None, no_log=True),
            api_url = dict(default=None),
            api_http_method = dict(choices=['get', 'post'], default='get'),
            api_timeout = dict(type='int', default=10),
            api_region = dict(default='cloudstack'),
        ),
        required_together = (
            ['api_key', 'api_secret', 'api_url'],
            ['start_ip', 'netmask', 'gateway'],
            ['start_ipv6', 'cidr_ipv6', 'gateway_ipv6'],
        ),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_network = AnsibleCloudStackNetwork(module)

        state = module.params.get('state')
        if state in ['absent']:
            network = acs_network.absent_network()

        elif state in ['restarted']:
            network = acs_network.restart_network()

        else:
            network = acs_network.present_network()

        result = acs_network.get_result(network)

    except CloudStackException, e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
