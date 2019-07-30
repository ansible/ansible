#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Netservers Ltd. <support@netservers.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
version_added: "2.8"
author:
 - Netservers Ltd. (@netservers)
 - Patryk Cichy (@PatTheSilent)
options:
  name:
    description:
      - Name of the physical network.
    required: true
    aliases:
      - physical_network
    type: str
  zone:
    description:
      - Name of the zone in which the network belongs.
      - If not set, default zone is used.
    type: str
  broadcast_domain_range:
    description:
      - broadcast domain range for the physical network[Pod or Zone].
    choices: [ POD, ZONE ]
    type: str
  domain:
    description:
      - Domain the network is owned by.
    type: str
  isolation_method:
    description:
      - Isolation method for the physical network.
    choices: [ VLAN, GRE, L3 ]
    type: str
  network_speed:
    description:
      - The speed for the physical network.
    choices: [1G, 10G]
    type: str
  tags:
    description:
      - A tag to identify this network.
      - Physical networks support only one tag.
      - To remove an existing tag pass an empty string.
    aliases:
      - tag
    type: str
  vlan:
    description:
      - The VLAN/VNI Ranges of the physical network.
    type: str
  nsps_enabled:
    description:
      - List of Network Service Providers to enable.
    type: list
  nsps_disabled:
    description:
      - List of Network Service Providers to disable.
    type: list
  state:
    description:
      - State of the physical network.
    default: present
    type: str
    choices: [ present, absent, disabled, enabled ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Ensure a network is present
  cs_physical_network:
    name: net01
    zone: zone01
    isolation_method: VLAN
    broadcast_domain_range: ZONE
  delegate_to: localhost

- name: Set a tag on a network
  cs_physical_network:
    name: net01
    tag: overlay
  delegate_to: localhost

- name: Remove tag on a network
  cs_physical_network:
    name: net01
    tag: ""
  delegate_to: localhost

- name: Ensure a network is enabled with specific nsps enabled
  cs_physical_network:
    name: net01
    zone: zone01
    isolation_method: VLAN
    vlan: 100-200,300-400
    broadcast_domain_range: ZONE
    state: enabled
    nsps_enabled:
      - virtualrouter
      - internallbvm
      - vpcvirtualrouter
  delegate_to: localhost

- name: Ensure a network is disabled
  cs_physical_network:
    name: net01
    zone: zone01
    state: disabled
  delegate_to: localhost

- name: Ensure a network is enabled
  cs_physical_network:
    name: net01
    zone: zone01
    state: enabled
  delegate_to: localhost

- name: Ensure a network is absent
  cs_physical_network:
    name: net01
    zone: zone01
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the network.
  returned: success
  type: str
  sample: 3f8f25cd-c498-443f-9058-438cfbcbff50
name:
  description: Name of the network.
  returned: success
  type: str
  sample: net01
state:
  description: State of the network [Enabled/Disabled].
  returned: success
  type: str
  sample: Enabled
broadcast_domain_range:
  description: broadcastdomainrange of the network [POD / ZONE].
  returned: success
  type: str
  sample: ZONE
isolation_method:
  description: isolationmethod of the network [VLAN/GRE/L3].
  returned: success
  type: str
  sample: VLAN
network_speed:
  description: networkspeed of the network [1G/10G].
  returned: success
  type: str
  sample: 1G
zone:
  description: Name of zone the physical network is in.
  returned: success
  type: str
  sample: ch-gva-2
domain:
  description: Name of domain the network is in.
  returned: success
  type: str
  sample: domain1
nsps:
  description: list of enabled or disabled Network Service Providers
  type: complex
  returned: on enabling/disabling of Network Service Providers
  contains:
    enabled:
      description: list of Network Service Providers that were enabled
      returned: on Network Service Provider enabling
      type: list
      sample:
       - virtualrouter
    disabled:
      description: list of Network Service Providers that were disabled
      returned: on Network Service Provider disabling
      type: list
      sample:
       - internallbvm

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackPhysicalNetwork(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackPhysicalNetwork, self).__init__(module)
        self.returns = {
            'isolationmethods': 'isolation_method',
            'broadcastdomainrange': 'broadcast_domain_range',
            'networkspeed': 'network_speed',
            'vlan': 'vlan',
            'tags': 'tags',
        }
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

        state = self.module.params.get('state')
        if state in ['enabled', 'disabled']:
            args['state'] = state.capitalize()
        return args

    def get_physical_network(self, key=None):
        physical_network = self.module.params.get('name')
        if self.physical_network:
            return self._get_by_key(key, self.physical_network)

        args = {
            'zoneid': self.get_zone(key='id')
        }
        physical_networks = self.query_api('listPhysicalNetworks', **args)
        if physical_networks:
            for net in physical_networks['physicalnetwork']:
                if physical_network.lower() in [net['name'].lower(), net['id']]:
                    self.physical_network = net
                    self.result['physical_network'] = net['name']
                    break

        return self._get_by_key(key, self.physical_network)

    def get_nsp(self, name=None):
        if not self.nsps:
            args = {
                'physicalnetworkid': self.get_physical_network(key='id')
            }
            res = self.query_api('listNetworkServiceProviders', **args)

            self.nsps = res['networkserviceprovider']

        names = []
        for nsp in self.nsps:
            names.append(nsp['name'])
            if nsp['name'].lower() == name.lower():
                return nsp

        self.module.fail_json(msg="Failed: '{0}' not in network service providers list '[{1}]'".format(name, names))

    def update_nsp(self, name=None, state=None, service_list=None):
        nsp = self.get_nsp(name)
        if not service_list and nsp['state'] == state:
            return nsp

        args = {
            'id': nsp['id'],
            'servicelist': service_list,
            'state': state
        }
        if not self.module.check_mode:
            res = self.query_api('updateNetworkServiceProvider', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                nsp = self.poll_job(res, 'networkserviceprovider')

        self.result['changed'] = True
        return nsp

    def get_vrouter_element(self, nsp_name='virtualrouter'):
        nsp = self.get_nsp(nsp_name)
        nspid = nsp['id']
        if self.vrouters is None:
            self.vrouters = dict()
            res = self.query_api('listVirtualRouterElements', )
            for vrouter in res['virtualrouterelement']:
                self.vrouters[vrouter['nspid']] = vrouter

        if nspid not in self.vrouters:
            self.module.fail_json(msg="Failed: No VirtualRouterElement found for nsp '%s'" % nsp_name)

        return self.vrouters[nspid]

    def get_loadbalancer_element(self, nsp_name='internallbvm'):
        nsp = self.get_nsp(nsp_name)
        nspid = nsp['id']
        if self.loadbalancers is None:
            self.loadbalancers = dict()
            res = self.query_api('listInternalLoadBalancerElements', )
            for loadbalancer in res['internalloadbalancerelement']:
                self.loadbalancers[loadbalancer['nspid']] = loadbalancer

            if nspid not in self.loadbalancers:
                self.module.fail_json(msg="Failed: No Loadbalancer found for nsp '%s'" % nsp_name)

        return self.loadbalancers[nspid]

    def set_vrouter_element_state(self, enabled, nsp_name='virtualrouter'):
        vrouter = self.get_vrouter_element(nsp_name)
        if vrouter['enabled'] == enabled:
            return vrouter

        args = {
            'id': vrouter['id'],
            'enabled': enabled
        }
        if not self.module.check_mode:
            res = self.query_api('configureVirtualRouterElement', **args)
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                vrouter = self.poll_job(res, 'virtualrouterelement')

        self.result['changed'] = True
        return vrouter

    def set_loadbalancer_element_state(self, enabled, nsp_name='internallbvm'):
        loadbalancer = self.get_loadbalancer_element(nsp_name=nsp_name)
        if loadbalancer['enabled'] == enabled:
            return loadbalancer

        args = {
            'id': loadbalancer['id'],
            'enabled': enabled
        }
        if not self.module.check_mode:
            res = self.query_api('configureInternalLoadBalancerElement', **args)
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                loadbalancer = self.poll_job(res, 'internalloadbalancerelement')

        self.result['changed'] = True
        return loadbalancer

    def present_network(self):
        network = self.get_physical_network()
        if network:
            network = self._update_network()
        else:
            network = self._create_network()
        return network

    def _create_network(self):
        self.result['changed'] = True
        args = dict(zoneid=self.get_zone(key='id'))
        args.update(self._get_common_args())
        if self.get_domain(key='id'):
            args['domainid'] = self.get_domain(key='id')

        if not self.module.check_mode:
            resource = self.query_api('createPhysicalNetwork', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                self.network = self.poll_job(resource, 'physicalnetwork')

        return self.network

    def _update_network(self):
        network = self.get_physical_network()

        args = dict(id=network['id'])
        args.update(self._get_common_args())

        if self.has_changed(args, network):
            self.result['changed'] = True

            if not self.module.check_mode:
                resource = self.query_api('updatePhysicalNetwork', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.physical_network = self.poll_job(resource, 'physicalnetwork')
        return self.physical_network

    def absent_network(self):
        physical_network = self.get_physical_network()
        if physical_network:
            self.result['changed'] = True
            args = {
                'id': physical_network['id'],
            }
            if not self.module.check_mode:
                resource = self.query_api('deletePhysicalNetwork', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(resource, 'success')

        return physical_network


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['physical_network']),
        zone=dict(),
        domain=dict(),
        vlan=dict(),
        nsps_disabled=dict(type='list'),
        nsps_enabled=dict(type='list'),
        network_speed=dict(choices=['1G', '10G']),
        broadcast_domain_range=dict(choices=['POD', 'ZONE']),
        isolation_method=dict(choices=['VLAN', 'GRE', 'L3']),
        state=dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
        tags=dict(aliases=['tag']),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_network = AnsibleCloudStackPhysicalNetwork(module)
    state = module.params.get('state')
    nsps_disabled = module.params.get('nsps_disabled', [])
    nsps_enabled = module.params.get('nsps_enabled', [])

    if state in ['absent']:
        network = acs_network.absent_network()
    else:
        network = acs_network.present_network()
    if nsps_disabled is not None:
        for name in nsps_disabled:
            acs_network.update_nsp(name=name, state='Disabled')

    if nsps_enabled is not None:
        for nsp_name in nsps_enabled:
            if nsp_name.lower() in ['virtualrouter', 'vpcvirtualrouter']:
                acs_network.set_vrouter_element_state(enabled=True, nsp_name=nsp_name)
            elif nsp_name.lower() == 'internallbvm':
                acs_network.set_loadbalancer_element_state(enabled=True, nsp_name=nsp_name)

            acs_network.update_nsp(name=nsp_name, state='Enabled')

    result = acs_network.get_result(network)

    if nsps_enabled:
        result['nsps_enabled'] = nsps_enabled
    if nsps_disabled:
        result['nsps_disabled'] = nsps_disabled

    module.exit_json(**result)


if __name__ == '__main__':
    main()
