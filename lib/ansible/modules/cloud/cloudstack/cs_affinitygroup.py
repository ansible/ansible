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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_affinitygroup
short_description: Manages affinity groups on Apache CloudStack based clouds.
description:
    - Create and remove affinity groups.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the affinity group.
    required: true
  affinity_type:
    description:
      - Type of the affinity group. If not specified, first found affinity type is used.
    aliases: [ affinty_type ]
  description:
    description:
      - Description of the affinity group.
  state:
    description:
      - State of the affinity group.
    default: 'present'
    choices: [ 'present', 'absent' ]
  domain:
    description:
      - Domain the affinity group is related to.
  account:
    description:
      - Account the affinity group is related to.
  project:
    description:
      - Name of the project the affinity group is related to.
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: 'yes'
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create a affinity group
- local_action:
    module: cs_affinitygroup
    name: haproxy
    affinity_type: host anti-affinity

# Remove a affinity group
- local_action:
    module: cs_affinitygroup
    name: haproxy
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the affinity group.
  returned: success
  type: string
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
name:
  description: Name of affinity group.
  returned: success
  type: string
  sample: app
description:
  description: Description of affinity group.
  returned: success
  type: string
  sample: application affinity group
affinity_type:
  description: Type of affinity group.
  returned: success
  type: string
  sample: host anti-affinity
project:
  description: Name of project the affinity group is related to.
  returned: success
  type: string
  sample: Production
domain:
  description: Domain the affinity group is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the affinity group is related to.
  returned: success
  type: string
  sample: example account
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackAffinityGroup(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackAffinityGroup, self).__init__(module)
        self.returns = {
            'type': 'affinity_type',
        }
        self.affinity_group = None

    def get_affinity_group(self):
        if not self.affinity_group:

            args = {
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'name': self.module.params.get('name'),
            }
            affinity_groups = self.query_api('listAffinityGroups', **args)
            if affinity_groups:
                self.affinity_group = affinity_groups['affinitygroup'][0]
        return self.affinity_group

    def get_affinity_type(self):
        affinity_type = self.module.params.get('affinity_type') or self.module.params.get('affinty_type')

        affinity_types = self.query_api('listAffinityGroupTypes', )
        if affinity_types:
            if not affinity_type:
                return affinity_types['affinityGroupType'][0]['type']

            for a in affinity_types['affinityGroupType']:
                if a['type'] == affinity_type:
                    return a['type']
        self.module.fail_json(msg="affinity group type not found: %s" % affinity_type)

    def create_affinity_group(self):
        affinity_group = self.get_affinity_group()
        if not affinity_group:
            self.result['changed'] = True

            args = {
                'name': self.module.params.get('name'),
                'type': self.get_affinity_type(),
                'description': self.module.params.get('description'),
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
            }
            if not self.module.check_mode:
                res = self.query_api('createAffinityGroup', **args)

                poll_async = self.module.params.get('poll_async')
                if res and poll_async:
                    affinity_group = self.poll_job(res, 'affinitygroup')
        return affinity_group

    def remove_affinity_group(self):
        affinity_group = self.get_affinity_group()
        if affinity_group:
            self.result['changed'] = True

            args = {
                'name': self.module.params.get('name'),
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
            }
            if not self.module.check_mode:
                res = self.query_api('deleteAffinityGroup', **args)

                poll_async = self.module.params.get('poll_async')
                if res and poll_async:
                    self.poll_job(res, 'affinitygroup')
        return affinity_group


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        affinty_type=dict(removed_in_version='2.9'),
        affinity_type=dict(),
        description=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        domain=dict(),
        account=dict(),
        project=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        mutually_exclusive=(
            ['affinity_type', 'affinty_type'],
        ),
        supports_check_mode=True
    )

    acs_ag = AnsibleCloudStackAffinityGroup(module)

    state = module.params.get('state')
    if state in ['absent']:
        affinity_group = acs_ag.remove_affinity_group()
    else:
        affinity_group = acs_ag.create_affinity_group()

    result = acs_ag.get_result(affinity_group)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
