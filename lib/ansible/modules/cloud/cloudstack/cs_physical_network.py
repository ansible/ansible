#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Netservers Ltd. <support@netservers.co.uk>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_physical_network
short_description: Manages physical networks on Apache CloudStack based clouds.
description:
    - Create, update and remove networks.
    - Enabled and disabled Network Service Providers
    - Enables Internal LoadBalancer and VPC/VirtualRouter elements as required
version_added: "2.4"
author: "Netservers Ltd. (@netservers)"
options:
  name:
    description:
      - name of the network.
    required: true
  zone:
    description:
      - Name of the zone in which the network belongs.
      - If not set, default zone is used.
    required: true
    default: null
  broadcastdomainrange:
    description:
      - broadcast domain range for the physical network[Pod or Zone].
    required: false
    default: none
    choices: [ 'POD', 'ZONE' ]
  domain:
    description:
      - Domain the network is owned by.
    required: false
    default: null
  isolation_method:
    description:
      - Isolation method for the physical network.
    required: false
    default: none
    choices: [ 'VLAN', 'GRE', 'L3' ]
  network_speed:
    description:
      - the speed for the physical network[1G/10G]
    required: false
    default: null
  tags:
    description:
      - "A tag to identify this network"
      - "Physical networks support only one tag"
      - "To remove an existing tag pass an empty string"
    required: false
    default: null
    aliases:
      - tag
  vlan:
    description:
      - The VLAN/VNI Ranges of the physical network.
    required: false
    default: null
  nsps_enabled:
    description:
      - List of Network Service Providers to enable
    required: false
    default: null
  nsps_disabled:
    description:
      - List of Network Service Providers to disable
    required: false
    default: null
  url:
    description:
      - URL for the cluster
    required: false
    default: null
  username:
    description:
      - Username for the cluster.
    required: false
    default: null
  password:
    description:
      - Password for the cluster.
    required: false
    default: null
  state:
    description:
      - State of the cluster.
    required: false
    default: 'present'
    choices: [ 'present', 'absent', 'disabled', 'enabled' ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a network is present
- local_action:
    module: cs_phsyical_network
    name: net01
    zone: zone01
    isolation_method: VLAN
    broadcast_domain_range: ZONE

# Set a tag on a network
- local_action:
    module: cs_phsyical_network
    name: net01
    tag: overlay

# Remove tag on a network
- local_action:
    module: cs_phsyical_network
    name: net01
    tag: ""

# Ensure a network is enabled with specific nsps enabled
- local_action:
    module: cs_phsyical_network
    name: net01
    zone: zone01
    isolation_method: VLAN
    vlan: 100-200,300-400
    broadcast_domain_range: ZONE
    state: enabled
    nsps_enabled:
      - Ovs
      - VirtualRouter
      - InternalLbVm
      - VpcVirtualRouter

# Ensure a network is disabled
- local_action:
    module: cs_phsyical_network
    name: net01
    zone: zone01
    state: disabled

# Ensure a network is enabled
- local_action:
    module: cs_phsyical_network
    name: net01
    zone: zone01
    state: enabled

# Ensure a network is absent
- local_action:
    module: cs_phsyical_network
    name: net01
    zone: zone01
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the network.
  returned: success
  type: string
  sample: 3f8f25cd-c498-443f-9058-438cfbcbff50
name:
  description: Name of the network.
  returned: success
  type: string
  sample: net01
state:
  description: State of the network [Enabled/Disabled].
  returned: success
  type: string
  sample: Enabled
broadcast_domain_range:
  description: broadcastdomainrange of the network [POD / ZONE].
  returned: success
  type: string
  sample: ZONE
isolation_method:
  description: isolationmethod of the network [VLAN/GRE/L3].
  returned: success
  type: string
  sample: VLAN
network_speed:
  description: networkspeed of the network [1G/10G].
  returned: success
  type: string
  sample: 1G
zone:
  description: Name of zone the cluster is in.
  returned: success
  type: string
  sample: ch-gva-2
domain:
  description: Name of domain the network is in.
  returned: success
  type: string
  sample: domain1
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    CloudStackException,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackCluster(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackCluster, self).__init__(module)
        self.returns = {
            'isolationmethods': 'isolation_method',
            'broadcastdomainrange': 'broadcast_domain_range',
            'networkspeed': 'network_speed',
            'vlan': 'vlan',
            'tags': 'tags',
        }
        self.network = None
        self.nsps = []
        self.vrouters = None
        self.loadbalancers = None

    def _get_common_args(self):
        args = {
            'name': self.module.params.get('name'),
            'isolationmethods': self.module.params.get('isolation_method'),
            'broadcastdomainrange': self.module.params.get('broadcast_domain_range'),
            'networkspeed': self.module.params.get('network_speed'),
            'tags': self.module.params.get('tags'),
            'vlan': self.module.params.get('vlan'),
        }
        if args['tags'] and len(args['tags']) > 1:
            self.module.fail_json(msg="Failed: Physical networks can only have one tag")

        state = self.module.params.get('state')
        if state in ['enabled', 'disabled']:
            args['state'] = state.capitalize()
        return args

    def get_network(self, key=None):
        if self.network:
            return self.network
        args = {
            'zoneid': self.get_zone(key='id'),
            'name': self.module.params.get('name'),
        }
        nets = self.cs.listPhysicalNetworks(**args)
        if nets:
            self.network = nets['physicalnetwork'][0]
        return self.network

    def get_nsp(self, name=None):
        if not self.nsps:
            network = self.get_network()
            args = {
                'physicalnetworkid': network['id']
            }
            res = self.cs.listNetworkServiceProviders(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            self.nsps = res['networkserviceprovider']

        names = []
        for nsp in self.nsps:
            names.append(nsp['name'])
            if nsp['name'] == name:
                return nsp

        self.module.fail_json(msg="Failed: '{}' not in network service providers list '[{}]'".format(name, names))

    def _update_nsp(self, name=None, state=None, service_list=None):
        nsp = self.get_nsp(name)
        if not service_list and nsp['state'] == state:
            return nsp

        args = {
            'id': nsp['id'],
            'servicelist': service_list,
            'state': state
        }
        res = self.cs.updateNetworkServiceProvider(**args)
        if 'errortext' in res:
            self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

        self.result['changed'] = True
        return res

    def get_vrouter_element(self, nsp_name='VirtualRouter'):
        nsp = self.get_nsp(nsp_name)
        nspid = nsp['id']
        if self.vrouters is None:
            self.vrouters = dict()
            res = self.cs.listVirtualRouterElements()
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            for vrouter in res['virtualrouterelement']:
                self.vrouters[vrouter['nspid']] = vrouter

        if nspid not in self.vrouters:
            self.module.fail_json(msg="Failed: No VirtualRouterElement founf for nsp '%s'" % nsp_name)

        return self.vrouters[nspid]

    def get_loadbalancer_element(self, nsp_name='InternalLbVm'):
        nsp = self.get_nsp(nsp_name)
        nspid = nsp['id']
        if self.loadbalancers is None:
            self.loadbalancers = dict()
            res = self.cs.listInternalLoadBalancerElements()
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            for loadbalancer in res['internalloadbalancerelement']:
                self.loadbalancers[loadbalancer['nspid']] = loadbalancer

            if nspid not in self.loadbalancers:
                self.module.fail_json(msg="Failed: No Loadbalancer found for nsp '%s'" % nsp_name)

        return self.loadbalancers[nspid]

    def set_vrouter_element_state(self, enabled, nsp_name='VirtualRouter'):
        vrouter = self.get_vrouter_element(nsp_name)
        if vrouter['enabled'] == enabled:
            return vrouter

        args = {
            'id': vrouter['id'],
            'enabled': enabled
        }
        res = self.cs.configureVirtualRouterElement(**args)
        if 'errortext' in res:
            self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

        self.result['changed'] = True
        return res

    def set_loadbalancer_element_state(self, enabled, nsp_name='InternalLbVm'):
        loadbalancer = self.get_loadbalancer_element(nsp_name=nsp_name)
        if loadbalancer['enabled'] == enabled:
            return loadbalancer

        args = {
            'id': loadbalancer['id'],
            'enabled': enabled
        }
        res = self.cs.configureInternalLoadBalancerElement(**args)
        if 'errortext' in res:
            self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

        self.result['changed'] = True
        return res

    def present_network(self):
        network = self.get_network()
        if network:
            network = self._update_network()
        else:
            network = self._create_network()
        return network

    def _create_network(self):
        required_params = [
            'name',
            'zone',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        args = self._get_common_args()
        args['zoneid'] = self.get_zone(key='id')
        args['domainid'] = self.get_domain(key='id')
        args['url'] = self.module.params.get('url')
        args['username'] = self.module.params.get('username')
        args['password'] = self.module.params.get('password')

        self.result['changed'] = True

        id = None
        if not self.module.check_mode:
            res = self.cs.createPhysicalNetwork(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            id = res['id']
        return id

    def _update_network(self):
        network = self.get_network()

        args = self._get_common_args()
        args['id'] = network['id']

        if self.has_changed(args, network):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.cs.updatePhysicalNetwork(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return network

    def absent_network(self):
        network = self.get_network()
        if network:
            self.result['changed'] = True

            args = {
                'id': network['id'],
            }
            if not self.module.check_mode:
                res = self.cs.deletePhysicalNetwork(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return network


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        zone=dict(default=None),
        domain=dict(default=None),
        vlan=dict(default=None),
        nsps_disabled=dict(default=None, type='list'),
        nsps_enabled=dict(default=None, type='list'),
        network_speed=dict(choices=['1G', '10G'], default=None),
        broadcast_domain_range=dict(choices=['POD', 'ZONE'], default=None),
        isolation_method=dict(choices=['VLAN', 'GRE', 'L3'], default=None),
        state=dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
        url=dict(default=None),
        username=dict(default=None),
        password=dict(default=None, no_log=True),
        tags=dict(type='list', aliases=['tag'], default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    try:
        acs_network = AnsibleCloudStackCluster(module)

        state = module.params.get('state')
        nsps_disabled = module.params.get('nsps_disabled', [])
        nsps_enabled = module.params.get('nsps_enabled', [])

        if state in ['absent']:
            network = acs_network.absent_network()
        else:
            network = acs_network.present_network()

        if nsps_disabled is not None:
            for name in nsps_disabled:
                acs_network._update_nsp(name=name, state='Disabled')

        if nsps_enabled is not None:
            for nsp_name in nsps_enabled:
                if nsp_name in ['VirtualRouter', 'VpcVirtualRouter']:
                    acs_network.set_vrouter_element_state(enabled=True, nsp_name=nsp_name)
                elif nsp_name == 'InternalLbVm':
                    acs_network.set_loadbalancer_element_state(enabled=True, nsp_name=nsp_name)

                acs_network._update_nsp(name=nsp_name, state='Enabled')

        result = acs_network.get_result(network)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
