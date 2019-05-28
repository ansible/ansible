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
module: cs_instancegroup
short_description: Manages instance groups on Apache CloudStack based clouds.
description:
    - Create and remove instance groups.
version_added: '2.0'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the instance group.
    type: str
    required: true
  domain:
    description:
      - Domain the instance group is related to.
    type: str
  account:
    description:
      - Account the instance group is related to.
    type: str
  project:
    description:
      - Project the instance group is related to.
    type: str
  state:
    description:
      - State of the instance group.
    type: str
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create an instance group
  cs_instancegroup:
    name: loadbalancers
  delegate_to: localhost

- name: Remove an instance group
  cs_instancegroup:
    name: loadbalancers
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the instance group.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the instance group.
  returned: success
  type: str
  sample: webservers
created:
  description: Date when the instance group was created.
  returned: success
  type: str
  sample: 2015-05-03T15:05:51+0200
domain:
  description: Domain the instance group is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the instance group is related to.
  returned: success
  type: str
  sample: example account
project:
  description: Project the instance group is related to.
  returned: success
  type: str
  sample: example project
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackInstanceGroup(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackInstanceGroup, self).__init__(module)
        self.instance_group = None

    def get_instance_group(self):
        if self.instance_group:
            return self.instance_group

        name = self.module.params.get('name')

        args = {
            'account': self.get_account('name'),
            'domainid': self.get_domain('id'),
            'projectid': self.get_project('id'),
            'fetch_list': True,
        }
        instance_groups = self.query_api('listInstanceGroups', **args)
        if instance_groups:
            for g in instance_groups:
                if name in [g['name'], g['id']]:
                    self.instance_group = g
                    break
        return self.instance_group

    def present_instance_group(self):
        instance_group = self.get_instance_group()
        if not instance_group:
            self.result['changed'] = True

            args = {
                'name': self.module.params.get('name'),
                'account': self.get_account('name'),
                'domainid': self.get_domain('id'),
                'projectid': self.get_project('id'),
            }
            if not self.module.check_mode:
                res = self.query_api('createInstanceGroup', **args)
                instance_group = res['instancegroup']
        return instance_group

    def absent_instance_group(self):
        instance_group = self.get_instance_group()
        if instance_group:
            self.result['changed'] = True
            if not self.module.check_mode:
                self.query_api('deleteInstanceGroup', id=instance_group['id'])
        return instance_group


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        domain=dict(),
        account=dict(),
        project=dict(),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_ig = AnsibleCloudStackInstanceGroup(module)

    state = module.params.get('state')
    if state in ['absent']:
        instance_group = acs_ig.absent_instance_group()
    else:
        instance_group = acs_ig.present_instance_group()

    result = acs_ig.get_result(instance_group)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
