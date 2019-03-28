#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, David Passante (@dpassante)
# Copyright (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cs_network_offering
short_description: Manages network offerings on Apache CloudStack based clouds.
description:
    - Create, update, enable, disable and remove network offerings.
version_added: '2.5'
author: David Passante (@dpassante)
options:
  state:
    description:
      - State of the network offering.
    type: str
    choices: [ enabled, present, disabled, absent]
    default: present
  display_text:
    description:
      - Display text of the network offerings.
    type: str
  guest_ip_type:
    description:
      - Guest type of the network offering.
    type: str
    choices: [ Shared, Isolated ]
  name:
    description:
      - The name of the network offering.
    type: str
    required: true
  supported_services:
    description:
      - Services supported by the network offering.
      - A list of one or more items from the choice list.
    type: list
    choices: [ Dns, PortForwarding, Dhcp, SourceNat, UserData, Firewall, StaticNat, Vpn, Lb ]
    aliases: [ supported_service ]
  traffic_type:
    description:
      - The traffic type for the network offering.
    type: str
    default: Guest
  availability:
    description:
      - The availability of network offering. Default value is Optional
    type: str
  conserve_mode:
    description:
      - Whether the network offering has IP conserve mode enabled.
    type: bool
  details:
    description:
      - Network offering details in key/value pairs.
      - with service provider as a value
    type: list
  egress_default_policy:
    description:
      - Whether the default egress policy is allow or to deny.
    type: str
    choices: [ allow, deny ]
  persistent:
    description:
      - True if network offering supports persistent networks
      - defaulted to false if not specified
    type: bool
  keepalive_enabled:
    description:
      - If true keepalive will be turned on in the loadbalancer.
      - At the time of writing this has only an effect on haproxy.
      - the mode http and httpclose options are unset in the haproxy conf file.
    type: bool
  max_connections:
    description:
      - Maximum number of concurrent connections supported by the network offering.
    type: int
  network_rate:
    description:
      - Data transfer rate in megabits per second allowed.
    type: int
  service_capabilities:
    description:
      - Desired service capabilities as part of network offering.
    type: list
    aliases: [ service_capability ]
  service_offering:
    description:
      - The service offering name or ID used by virtual router provider.
    type: str
  service_providers:
    description:
      - Provider to service mapping.
      - If not specified, the provider for the service will be mapped to the default provider on the physical network.
    type: list
    aliases: [ service_provider ]
  specify_ip_ranges:
    description:
      - Wheter the network offering supports specifying IP ranges.
      - Defaulted to C(no) by the API if not specified.
    type: bool
  specify_vlan:
    description:
      - Whether the network offering supports vlans or not.
    type: bool
  for_vpc:
    description:
      - Whether the offering is meant to be used for VPC or not.
    type: bool
    version_added: '2.8'
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a network offering and enable it
  cs_network_offering:
    name: my_network_offering
    display_text: network offering description
    state: enabled
    guest_ip_type: Isolated
    supported_services: [ Dns, PortForwarding, Dhcp, SourceNat, UserData, Firewall, StaticNat, Vpn, Lb ]
    service_providers:
      - { service: 'dns', provider: 'virtualrouter' }
      - { service: 'dhcp', provider: 'virtualrouter' }
  delegate_to: localhost


- name: Remove a network offering
  cs_network_offering:
    name: my_network_offering
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the network offering.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: The name of the network offering.
  returned: success
  type: str
  sample: MyCustomNetworkOffering
display_text:
  description: The display text of the network offering.
  returned: success
  type: str
  sample: My network offering
state:
  description: The state of the network offering.
  returned: success
  type: str
  sample: Enabled
guest_ip_type:
  description: Guest type of the network offering.
  returned: success
  type: str
  sample: Isolated
availability:
  description: The availability of network offering.
  returned: success
  type: str
  sample: Optional
service_offering_id:
  description: The service offering ID.
  returned: success
  type: str
  sample: c5f7a5fc-43f8-11e5-a151-feff819cdc9f
max_connections:
  description: The maximum number of concurrents connections to be handled by LB.
  returned: success
  type: int
  sample: 300
network_rate:
  description: The network traffic transfer ate in Mbit/s.
  returned: success
  type: int
  sample: 200
traffic_type:
  description: The traffic type.
  returned: success
  type: str
  sample: Guest
egress_default_policy:
  description: Default egress policy.
  returned: success
  type: str
  sample: allow
is_persistent:
  description: Whether persistent networks are supported or not.
  returned: success
  type: bool
  sample: false
is_default:
  description: Whether network offering is the default offering or not.
  returned: success
  type: bool
  sample: false
for_vpc:
  description: Whether the offering is meant to be used for VPC or not.
  returned: success
  type: bool
  sample: false
  version_added: '2.8'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackNetworkOffering(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackNetworkOffering, self).__init__(module)
        self.returns = {
            'guestiptype': 'guest_ip_type',
            'availability': 'availability',
            'serviceofferingid': 'service_offering_id',
            'networkrate': 'network_rate',
            'maxconnections': 'max_connections',
            'traffictype': 'traffic_type',
            'isdefault': 'is_default',
            'ispersistent': 'is_persistent',
            'forvpc': 'for_vpc'
        }
        self.network_offering = None

    def get_service_offering_id(self):
        service_offering = self.module.params.get('service_offering')
        if not service_offering:
            return None

        args = {
            'issystem': True
        }

        service_offerings = self.query_api('listServiceOfferings', **args)
        if service_offerings:
            for s in service_offerings['serviceoffering']:
                if service_offering in [s['name'], s['id']]:
                    return s['id']
        self.fail_json(msg="Service offering '%s' not found" % service_offering)

    def get_network_offering(self):
        if self.network_offering:
            return self.network_offering

        args = {
            'name': self.module.params.get('name'),
            'guestiptype': self.module.params.get('guest_type'),
        }
        no = self.query_api('listNetworkOfferings', **args)
        if no:
            self.network_offering = no['networkoffering'][0]

        return self.network_offering

    def create_or_update(self):
        network_offering = self.get_network_offering()

        if not network_offering:
            network_offering = self.create_network_offering()

        return self.update_network_offering(network_offering=network_offering)

    def create_network_offering(self):
        network_offering = None
        self.result['changed'] = True

        args = {
            'state': self.module.params.get('state'),
            'displaytext': self.module.params.get('display_text'),
            'guestiptype': self.module.params.get('guest_ip_type'),
            'name': self.module.params.get('name'),
            'supportedservices': self.module.params.get('supported_services'),
            'traffictype': self.module.params.get('traffic_type'),
            'availability': self.module.params.get('availability'),
            'conservemode': self.module.params.get('conserve_mode'),
            'details': self.module.params.get('details'),
            'egressdefaultpolicy': self.module.params.get('egress_default_policy') == 'allow',
            'ispersistent': self.module.params.get('persistent'),
            'keepaliveenabled': self.module.params.get('keepalive_enabled'),
            'maxconnections': self.module.params.get('max_connections'),
            'networkrate': self.module.params.get('network_rate'),
            'servicecapabilitylist': self.module.params.get('service_capabilities'),
            'serviceofferingid': self.get_service_offering_id(),
            'serviceproviderlist': self.module.params.get('service_providers'),
            'specifyipranges': self.module.params.get('specify_ip_ranges'),
            'specifyvlan': self.module.params.get('specify_vlan'),
            'forvpc': self.module.params.get('for_vpc'),
        }

        required_params = [
            'display_text',
            'guest_ip_type',
            'supported_services',
            'service_providers',
        ]

        self.module.fail_on_missing_params(required_params=required_params)

        if not self.module.check_mode:
            res = self.query_api('createNetworkOffering', **args)
            network_offering = res['networkoffering']

        return network_offering

    def delete_network_offering(self):
        network_offering = self.get_network_offering()

        if network_offering:
            self.result['changed'] = True
            if not self.module.check_mode:
                self.query_api('deleteNetworkOffering', id=network_offering['id'])

        return network_offering

    def update_network_offering(self, network_offering):
        if not network_offering:
            return network_offering

        args = {
            'id': network_offering['id'],
            'state': self.module.params.get('state'),
            'displaytext': self.module.params.get('display_text'),
            'name': self.module.params.get('name'),
            'availability': self.module.params.get('availability'),
            'maxconnections': self.module.params.get('max_connections'),
        }

        if args['state'] in ['enabled', 'disabled']:
            args['state'] = args['state'].title()
        else:
            del args['state']

        if self.has_changed(args, network_offering):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('updateNetworkOffering', **args)
                network_offering = res['networkoffering']

        return network_offering

    def get_result(self, network_offering):
        super(AnsibleCloudStackNetworkOffering, self).get_result(network_offering)
        if network_offering:
            self.result['egress_default_policy'] = 'allow' if network_offering.get('egressdefaultpolicy') else 'deny'
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        state=dict(choices=['enabled', 'present', 'disabled', 'absent'], default='present'),
        display_text=dict(),
        guest_ip_type=dict(choices=['Shared', 'Isolated']),
        name=dict(required=True),
        supported_services=dict(type='list', aliases=['supported_service'], choices=[
            'Dns',
            'PortForwarding',
            'Dhcp',
            'SourceNat',
            'UserData',
            'Firewall',
            'StaticNat',
            'Vpn',
            'Lb',
        ]),
        traffic_type=dict(default='Guest'),
        availability=dict(),
        conserve_mode=dict(type='bool'),
        details=dict(type='list'),
        egress_default_policy=dict(choices=['allow', 'deny']),
        persistent=dict(type='bool'),
        keepalive_enabled=dict(type='bool'),
        max_connections=dict(type='int'),
        network_rate=dict(type='int'),
        service_capabilities=dict(type='list', aliases=['service_capability']),
        service_offering=dict(),
        service_providers=dict(type='list', aliases=['service_provider']),
        specify_ip_ranges=dict(type='bool'),
        specify_vlan=dict(type='bool'),
        for_vpc=dict(type='bool'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_network_offering = AnsibleCloudStackNetworkOffering(module)

    state = module.params.get('state')
    if state in ['absent']:
        network_offering = acs_network_offering.delete_network_offering()
    else:
        network_offering = acs_network_offering.create_or_update()

    result = acs_network_offering.get_result(network_offering)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
