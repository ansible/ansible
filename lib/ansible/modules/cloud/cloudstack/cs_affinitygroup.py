#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the affinity group.
    type: str
    required: true
  affinity_type:
    description:
      - Type of the affinity group. If not specified, first found affinity type is used.
    type: str
    aliases: [ affinty_type ]
  description:
    description:
      - Description of the affinity group.
    type: str
  state:
    description:
      - State of the affinity group.
    type: str
    choices: [ present, absent ]
    default: present
  domain:
    description:
      - Domain the affinity group is related to.
    type: str
  account:
    description:
      - Account the affinity group is related to.
    type: str
  project:
    description:
      - Name of the project the affinity group is related to.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a affinity group
  cs_affinitygroup:
    name: haproxy
    affinity_type: host anti-affinity
  delegate_to: localhost

- name: Remove a affinity group
  cs_affinitygroup:
    name: haproxy
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the affinity group.
  returned: success
  type: str
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
name:
  description: Name of affinity group.
  returned: success
  type: str
  sample: app
description:
  description: Description of affinity group.
  returned: success
  type: str
  sample: application affinity group
affinity_type:
  description: Type of affinity group.
  returned: success
  type: str
  sample: host anti-affinity
project:
  description: Name of project the affinity group is related to.
  returned: success
  type: str
  sample: Production
domain:
  description: Domain the affinity group is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the affinity group is related to.
  returned: success
  type: str
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
