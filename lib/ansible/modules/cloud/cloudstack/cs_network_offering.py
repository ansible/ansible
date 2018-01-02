#!/usr/bin/python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cs_network_offering

short_description: Manages network offerings on Apache CloudStack based clouds.

description:
    - Create, update, enable, disable and remove network offerings.

version_added: '2.5'

author: "David Passante (@dpassante)"

options:
  state:
    description:
      - State of the network offering.
    required: false
    default: 'present'
    choices: [ 'enabled, 'present', 'disabled', 'absent']
  display_text:
    description:
      - Display text of the network offerings
    required: true
    default: null
  guest_ip_type:
    description:
      - Guest type of the network offering: Shared or Isolated
    choices: ['Shared', 'Isolated']
    required: true
    default: null
  name:
    description:
      - The name of the network offering
    required: true
    default: null
  supported_services:
    description:
      - Services supported by the network offering
    required: true
    default: null
  traffic_type:
    description:
      - The traffic type for the network offering. Supported type in current release is GUEST only
    required: false
    default: GUEST
  availability:
    description:
      - The availability of network offering. Default value is Optional
    required: false
    default: null
  conserve_mode:
    description:
      - true if the network offering is IP conserve mode enabled
    choices: ['true', 'false']
    required: false
    default: true
  details:
    description:
      - Network offering details in key/value pairs.
      - Supported keys are internallbprovider/publiclbprovider with service provider as a value
    choices: ['internallbprovider', 'publiclbprovider']
    required: false
    default: null
  egress_default_policy:
    description:
      - True if guest network default egress policy is allow; false if default egress policy is deny
    choices: ['true', 'false']
    required: false
    default: null
  persistent:
    description:
      - True if network offering supports persistent networks; defaulted to false if not specified
    required: false
    default: false
  keepalive_enabled:
    description:
      - If true keepalive will be turned on in the loadbalancer. 
      - At the time of writing this has only an effect on haproxy; 
      - the mode http and httpclose options are unset in the haproxy conf file.
    choices: ['true', 'false']
    required: false
    default: null
  max_connections:
    description:
      - Maximum number of concurrent connections supported by the network offering
    required: false
    default: true
  network_rate:
    description:
      - Data transfer rate in megabits per second allowed
    required: false
    default: true
  service_capability_list:
    description:
      - Desired service capabilities as part of network offering
    required: false
    default: true
  service_offering_id:
    description:
      - The service offering ID used by virtual router provider
    required: false
    default: null
  service_provider_list:
    description:
      - provider to service mapping. If not specified, the provider for the service will be mapped to the default provider on the physical network
    required: false
    default: null
  specify_ip_ranges:
    description:
      - true if network offering supports specifying ip ranges; defaulted to false if not specified
    choices: ['true', 'false']
    required: false
    default: null
  specify_vlan:
    description:
      - true if network offering supports vlans
    choices: ['true', 'false']
    required: false
    default: false
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create a network offering and enable it
- local_action:
    module: cs_network_offering
    name: "my_network_offering"
    display_text: "network offering description"
    state: enabled
    guest_ip_type: Isolated
    supported_services: Dns,PortForwarding,Dhcp,SourceNat,UserData,Firewall,StaticNat,Vpn,Lb
    service_provider_list:
      - {service: 'dns', provider: 'virtualrouter'}
      - {service: 'dhcp', provider: 'virtualrouter'}


# Remove a network offering
- local_action:
    module: cs_network_offering
    name: "my_network_offering"
    display_text: "network offering description"
    state: absent
    guest_ip_type: Isolated
    supported_services: Dns,PortForwarding,Dhcp,SourceNat,UserData,Firewall,StaticNat,Vpn,Lb
    service_provider_list:
      - {service: 'dns', provider: 'virtualrouter'}
      - {service: 'dhcp', provider: 'virtualrouter'}
'''

RETURN = '''
---
id:
  description: UUID of the network offering.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: The name of the network offering
  returned: success
  type: string
  sample: MyCustomNetworkOffering
display_text:
  description: The display text of the network offering
  returned: success
  type: string
  sample: My network offering
state:
  description: The state of the network offering
  returned: success
  type: string
  sample: Enabled
guestiptype:
  returned: success
  type: string
  sample: Isolated
availability:
  returned: success
  type: string
  sample: Optional
serviceofferingid:
  returned: success
  type: string
  sample: c5f7a5fc-43f8-11e5-a151-feff819cdc9f
'''

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackNetworkOffering(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackNetworkOffering, self).__init__(module)
        self.returns = {
            'guestiptype': 'guest_ip_type',
            'availability': 'availability',
            'serviceofferingid': 'service_offering_id',
        }
        self.network_offering = None

    def get_network_offering(self):
        if self.network_offering:
            return self.network_offering


        args = {
            'name': self.module.params.get('name'),
            'guestiptype': self.module.params.get('guest_type'),
        }
        no = self.cs.listNetworkOfferings(**args)
        if no:
            self.network_offering = no['networkoffering'][0]

        return self.network_offering

    def create_or_update(self):
        network_offering = self.get_network_offering()
        if not network_offering:
          network_offering = self.create_network_offering()

        return self.update_network_offering(network_offering=network_offering)

    def create_network_offering(self): 
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
            'egressdefaultpolicy': self.module.params.get('egress_default_policy'),
            'ispersistent': self.module.params.get('persistent'),
            'keepaliveenabled': self.module.params.get('keepalive_enabled'),
            'maxconnections': self.module.params.get('max_connections'),
            'networkrate': self.module.params.get('network_rate'),
            'servicecapabilitylist': self.module.params.get('service_capability_list'),
            'serviceofferingid': self.module.params.get('service_offering_id'),
            'serviceproviderlist': self.module.params.get('service_provider_list'),
            'specifyipranges': self.module.params.get('specify_ip_ranges'),
            'specifyvlan': self.module.params.get('specify_vlan'),
        }
        if not self.module.check_mode:
            res = self.cs.createNetworkOffering(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            if res:
                network_offering = res['networkoffering']

        return network_offering

    def delete_network_offering(self):
        network_offering = self.get_network_offering()

        if not network_offering:
            return network_offering
        
        self.result['changed'] = True

        if not self.module.check_mode:
            res = self.cs.deleteNetworkOffering(id=network_offering['id'])

        return network_offering

    def update_network_offering(self, network_offering):
        args = {
            'id': network_offering['id'],
            'state': self.module.params.get('state'),
            'displaytext': self.module.params.get('display_text'),
            'name': self.module.params.get('name'),
            'availability': self.module.params.get('availability'),
        }

        if args['state'] == 'enabled' or args['state'] == 'disabled':
            args['state'] = args['state'].title()
        else:
            del args['state']

        for k,v in args.items():
            if network_offering[k] != args[k]:
                self.result['changed'] = True

        if not self.module.check_mode:
            network_offering = self.cs.updateNetworkOffering(**args)

        return network_offering['networkoffering']

def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        state=dict(choices=['enabled', 'present', 'disabled', 'absent'], default='present'),
        display_text=dict(required=True),
        guest_ip_type=dict(required=True, choices=['Shared', 'Isolated']),
        name=dict(required=True),
        supported_services=dict(required=True),
        traffic_type=dict(default='GUEST'),
        availability=dict(default='Optional'),
        conserve_mode=dict(type='bool', default=True),
        details=dict(type='list'),
        egress_default_policy=dict(type='bool'),
        persistent=dict(type='bool', default=False),
        keepalive_enabled=dict(type='bool', default=False),
        max_connections=dict(),
        network_rate=dict(),
        service_capability_list=dict(type='list'),
        service_offering_id=dict(),
        service_provider_list=dict(type='list', required=True),
        specify_ip_ranges=dict(type='bool', default=False),
        specify_vlan=dict(type='bool', default=False),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    try:
        acs_network_offering = AnsibleCloudStackNetworkOffering(module)

        state = module.params.get('state')
        if state in ['absent']:
            network_offering = acs_network_offering.delete_network_offering()
        else:
            network_offering = acs_network_offering.create_or_update()

        result = acs_network_offering.get_result(network_offering)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
