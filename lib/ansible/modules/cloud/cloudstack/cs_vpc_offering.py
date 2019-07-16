#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, David Passante (@dpassante)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cs_vpc_offering
short_description: Manages vpc offerings on Apache CloudStack based clouds.
description:
    - Create, update, enable, disable and remove CloudStack VPC offerings.
version_added: '2.5'
author: David Passante (@dpassante)
options:
  name:
    description:
      - The name of the vpc offering
    type: str
    required: true
  state:
    description:
      - State of the vpc offering.
    type: str
    choices: [ enabled, present, disabled, absent ]
    default: present
  display_text:
    description:
      - Display text of the vpc offerings
    type: str
  service_capabilities:
    description:
      - Desired service capabilities as part of vpc offering.
    type: list
    aliases: [ service_capability ]
  service_offering:
    description:
      - The name or ID of the service offering for the VPC router appliance.
    type: str
  supported_services:
    description:
      - Services supported by the vpc offering
    type: list
    aliases: [ supported_service ]
  service_providers:
    description:
      - provider to service mapping. If not specified, the provider for the service will be mapped to the default provider on the physical network
    type: list
    aliases: [ service_provider ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a vpc offering and enable it
  cs_vpc_offering:
    name: my_vpc_offering
    display_text: vpc offering description
    state: enabled
    supported_services: [ Dns, Dhcp ]
    service_providers:
      - {service: 'dns', provider: 'VpcVirtualRouter'}
      - {service: 'dhcp', provider: 'VpcVirtualRouter'}
  delegate_to: localhost

- name: Create a vpc offering with redundant router
  cs_vpc_offering:
    name: my_vpc_offering
    display_text: vpc offering description
    supported_services: [ Dns, Dhcp, SourceNat ]
    service_providers:
      - {service: 'dns', provider: 'VpcVirtualRouter'}
      - {service: 'dhcp', provider: 'VpcVirtualRouter'}
      - {service: 'SourceNat', provider: 'VpcVirtualRouter'}
    service_capabilities:
      - {service: 'SourceNat', capabilitytype: 'RedundantRouter', capabilityvalue: true}
  delegate_to: localhost

- name: Create a region level vpc offering with distributed router
  cs_vpc_offering:
    name: my_vpc_offering
    display_text: vpc offering description
    state: present
    supported_services: [ Dns, Dhcp, SourceNat ]
    service_providers:
      - {service: 'dns', provider: 'VpcVirtualRouter'}
      - {service: 'dhcp', provider: 'VpcVirtualRouter'}
      - {service: 'SourceNat', provider: 'VpcVirtualRouter'}
    service_capabilities:
      - {service: 'Connectivity', capabilitytype: 'DistributedRouter', capabilityvalue: true}
      - {service: 'Connectivity', capabilitytype: 'RegionLevelVPC', capabilityvalue: true}
  delegate_to: localhost

- name: Remove a vpc offering
  cs_vpc_offering:
    name: my_vpc_offering
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the vpc offering.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: The name of the vpc offering
  returned: success
  type: str
  sample: MyCustomVPCOffering
display_text:
  description: The display text of the vpc offering
  returned: success
  type: str
  sample: My vpc offering
state:
  description: The state of the vpc offering
  returned: success
  type: str
  sample: Enabled
service_offering_id:
  description: The service offering ID.
  returned: success
  type: str
  sample: c5f7a5fc-43f8-11e5-a151-feff819cdc9f
is_default:
  description: Whether VPC offering is the default offering or not.
  returned: success
  type: bool
  sample: false
region_level:
  description: Indicated if the offering can support region level vpc.
  returned: success
  type: bool
  sample: false
distributed:
  description: Indicates if the vpc offering supports distributed router for one-hop forwarding.
  returned: success
  type: bool
  sample: false
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackVPCOffering(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVPCOffering, self).__init__(module)
        self.returns = {
            'serviceofferingid': 'service_offering_id',
            'isdefault': 'is_default',
            'distributedvpcrouter': 'distributed',
            'supportsregionLevelvpc': 'region_level',
        }
        self.vpc_offering = None

    def get_vpc_offering(self):
        if self.vpc_offering:
            return self.vpc_offering

        args = {
            'name': self.module.params.get('name'),
        }
        vo = self.query_api('listVPCOfferings', **args)

        if vo:
            for vpc_offer in vo['vpcoffering']:
                if args['name'] == vpc_offer['name']:
                    self.vpc_offering = vpc_offer

        return self.vpc_offering

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

    def create_or_update(self):
        vpc_offering = self.get_vpc_offering()

        if not vpc_offering:
            vpc_offering = self.create_vpc_offering()

        return self.update_vpc_offering(vpc_offering)

    def create_vpc_offering(self):
        vpc_offering = None
        self.result['changed'] = True
        args = {
            'name': self.module.params.get('name'),
            'state': self.module.params.get('state'),
            'displaytext': self.module.params.get('display_text'),
            'supportedservices': self.module.params.get('supported_services'),
            'serviceproviderlist': self.module.params.get('service_providers'),
            'serviceofferingid': self.get_service_offering_id(),
            'servicecapabilitylist': self.module.params.get('service_capabilities'),
        }

        required_params = [
            'display_text',
            'supported_services',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        if not self.module.check_mode:
            res = self.query_api('createVPCOffering', **args)
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                vpc_offering = self.poll_job(res, 'vpcoffering')

        return vpc_offering

    def delete_vpc_offering(self):
        vpc_offering = self.get_vpc_offering()

        if vpc_offering:
            self.result['changed'] = True

            args = {
                'id': vpc_offering['id'],
            }

            if not self.module.check_mode:
                res = self.query_api('deleteVPCOffering', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    vpc_offering = self.poll_job(res, 'vpcoffering')

        return vpc_offering

    def update_vpc_offering(self, vpc_offering):
        if not vpc_offering:
            return vpc_offering

        args = {
            'id': vpc_offering['id'],
            'state': self.module.params.get('state'),
            'name': self.module.params.get('name'),
            'displaytext': self.module.params.get('display_text'),
        }

        if args['state'] in ['enabled', 'disabled']:
            args['state'] = args['state'].title()
        else:
            del args['state']

        if self.has_changed(args, vpc_offering):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('updateVPCOffering', **args)
                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    vpc_offering = self.poll_job(res, 'vpcoffering')

        return vpc_offering


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        display_text=dict(),
        state=dict(choices=['enabled', 'present', 'disabled', 'absent'], default='present'),
        service_capabilities=dict(type='list', aliases=['service_capability']),
        service_offering=dict(),
        supported_services=dict(type='list', aliases=['supported_service']),
        service_providers=dict(type='list', aliases=['service_provider']),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_vpc_offering = AnsibleCloudStackVPCOffering(module)

    state = module.params.get('state')
    if state in ['absent']:
        vpc_offering = acs_vpc_offering.delete_vpc_offering()
    else:
        vpc_offering = acs_vpc_offering.create_or_update()

    result = acs_vpc_offering.get_result(vpc_offering)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
