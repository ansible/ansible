#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it an/or modify
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
# along with Ansible. If not, see <http//www.gnu.or/license/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_vpc
short_description: "Manages VPCs on Apache CloudStack based clouds."
description:
  - "Create, update and delete VPCs."
version_added: "2.3"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - "Name of the VPC."
    required: true
  display_text:
    description:
      - "Display text of the VPC."
      - "If not set, C(name) will be used for creating."
    required: false
    default: null
  cidr:
    description:
      - "CIDR of the VPC, e.g. 10.1.0.0/16"
      - "All VPC guest networks' CIDRs must be within this CIDR."
      - "Required on C(state=present)."
    required: false
    default: null
  network_domain:
    description:
      - "Network domain for the VPC."
      - "All networks inside the VPC will belong to this domain."
    required: false
    default: null
  vpc_offering:
    description:
      - "Name of the VPC offering."
      - "If not set, default VPC offering is used."
    required: false
    default: null
  state:
    description:
      - "State of the VPC."
    required: false
    default: present
    choices:
      - present
      - absent
      - restarted
  domain:
    description:
      - "Domain the VPC is related to."
    required: false
    default: null
  account:
    description:
      - "Account the VPC is related to."
    required: false
    default: null
  project:
    description:
      - "Name of the project the VPC is related to."
    required: false
    default: null
  zone:
    description:
      - "Name of the zone."
      - "If not set, default zone is used."
    required: false
    default: null
  tags:
    description:
      - "List of tags. Tags are a list of dictionaries having keys C(key) and C(value)."
      - "For deleting all tags, set an empty list e.g. C(tags: [])."
    required: false
    default: null
    aliases:
      - tag
  poll_async:
    description:
      - "Poll async jobs until job has finished."
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a VPC is present
- local_action:
    module: cs_vpc
    name: my_vpc
    display_text: My example VPC
    cidr: 10.10.0.0/16

# Ensure a VPC is absent
- local_action:
    module: cs_vpc
    name: my_vpc
    state: absent

# Ensure a VPC is restarted
- local_action:
    module: cs_vpc
    name: my_vpc
    state: restarted
'''

RETURN = '''
---
id:
  description: "UUID of the VPC."
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: "Name of the VPC."
  returned: success
  type: string
  sample: my_vpc
display_text:
  description: "Display text of the VPC."
  returned: success
  type: string
  sample: My example VPC
cidr:
  description: "CIDR of the VPC."
  returned: success
  type: string
  sample: 10.10.0.0/16
network_domain:
  description: "Network domain of the VPC."
  returned: success
  type: string
  sample: example.com
region_level_vpc:
  description: "Whether the VPC is region level or not."
  returned: success
  type: boolean
  sample: true
restart_required:
  description: "Whether the VPC router needs a restart or not."
  returned: success
  type: boolean
  sample: true
distributed_vpc_router:
  description: "Whether the VPC uses distributed router or not."
  returned: success
  type: boolean
  sample: true
redundant_vpc_router:
  description: "Whether the VPC has redundant routers or not."
  returned: success
  type: boolean
  sample: true
domain:
  description: "Domain the VPC is related to."
  returned: success
  type: string
  sample: example domain
account:
  description: "Account the VPC is related to."
  returned: success
  type: string
  sample: example account
project:
  description: "Name of project the VPC is related to."
  returned: success
  type: string
  sample: Production
zone:
  description: "Name of zone the VPC is in."
  returned: success
  type: string
  sample: ch-gva-2
state:
  description: "State of the VPC."
  returned: success
  type: string
  sample: Enabled
tags:
  description: "List of resource tags associated with the VPC."
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackVpc(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVpc, self).__init__(module)
        self.returns = {
            'cidr': 'cidr',
            'networkdomain': 'network_domain',
            'redundantvpcrouter': 'redundant_vpc_router',
            'distributedvpcrouter': 'distributed_vpc_router',
            'regionlevelvpc': 'region_level_vpc',
            'restartrequired': 'restart_required',
        }
        self.vpc = None
        self.vpc_offering = None

    def get_vpc_offering(self, key=None):
        if self.vpc_offering:
            return self._get_by_key(key, self.vpc_offering)

        vpc_offering = self.module.params.get('vpc_offering')
        args = {}
        if vpc_offering:
            args['name'] = vpc_offering
        else:
            args['isdefault'] = True

        vpc_offerings = self.query_api('listVPCOfferings', **args)
        if vpc_offerings:
            self.vpc_offering = vpc_offerings['vpcoffering'][0]
            return self._get_by_key(key, self.vpc_offering)
        self.module.fail_json(msg="VPC offering '%s' not found" % vpc_offering)

    def get_vpc(self):
        if self.vpc:
            return self.vpc
        args = {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'zoneid': self.get_zone(key='id'),
        }
        vpcs = self.query_api('listVPCs', **args)
        if vpcs:
            vpc_name = self.module.params.get('name')
            for v in vpcs['vpc']:
                if vpc_name in [v['name'], v['displaytext'], v['id']]:
                    # Fail if the identifyer matches more than one VPC
                    if self.vpc:
                        self.module.fail_json(msg="More than one VPC found with the provided identifyer '%s'" % vpc_name)
                    else:
                        self.vpc = v
        return self.vpc

    def restart_vpc(self):
        self.result['changed'] = True
        vpc = self.get_vpc()
        if vpc and not self.module.check_mode:
            args = {
                'id': vpc['id'],
            }
            res = self.query_api('restartVPC', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                self.poll_job(res, 'vpc')
        return vpc

    def present_vpc(self):
        vpc = self.get_vpc()
        if not vpc:
            vpc = self._create_vpc(vpc)
        else:
            vpc = self._update_vpc(vpc)

        if vpc:
            vpc = self.ensure_tags(resource=vpc, resource_type='Vpc')
        return vpc

    def _create_vpc(self, vpc):
        self.result['changed'] = True
        args = {
            'name': self.module.params.get('name'),
            'displaytext': self.get_or_fallback('display_text', 'name'),
            'vpcofferingid': self.get_vpc_offering(key='id'),
            'cidr': self.module.params.get('cidr'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'zoneid': self.get_zone(key='id'),
        }
        self.result['diff']['after'] = args
        if not self.module.check_mode:
            res = self.query_api('createVPC', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                vpc = self.poll_job(res, 'vpc')
        return vpc

    def _update_vpc(self, vpc):
        args = {
            'id': vpc['id'],
            'displaytext': self.module.params.get('display_text'),
        }
        if self.has_changed(args, vpc):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('updateVPC', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    vpc = self.poll_job(res, 'vpc')
        return vpc

    def absent_vpc(self):
        vpc = self.get_vpc()
        if vpc:
            self.result['changed'] = True
            self.result['diff']['before'] = vpc
            if not self.module.check_mode:
                res = self.query_api('deleteVPC', id=vpc['id'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'vpc')
        return vpc


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        cidr=dict(default=None),
        display_text=dict(default=None),
        vpc_offering=dict(default=None),
        network_domain=dict(default=None),
        state=dict(choices=['present', 'absent', 'restarted'], default='present'),
        domain=dict(default=None),
        account=dict(default=None),
        project=dict(default=None),
        zone=dict(default=None),
        tags=dict(type='list', aliases=['tag'], default=None),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_if=[
            ('state', 'present', ['cidr']),
        ],
        supports_check_mode=True,
    )

    acs_vpc = AnsibleCloudStackVpc(module)

    state = module.params.get('state')
    if state == 'absent':
        vpc = acs_vpc.absent_vpc()
    elif state == 'restarted':
        vpc = acs_vpc.restart_vpc()
    else:
        vpc = acs_vpc.present_vpc()

    result = acs_vpc.get_result(vpc)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
