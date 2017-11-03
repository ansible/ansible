#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_securitygroup
short_description: Manages security groups on Apache CloudStack based clouds.
description:
    - Create and remove security groups.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the security group.
    required: true
  description:
    description:
      - Description of the security group.
  state:
    description:
      - State of the security group.
    default: present
    choices: [ present, absent ]
  domain:
    description:
      - Domain the security group is related to.
  account:
    description:
      - Account the security group is related to.
  project:
    description:
      - Name of the project the security group to be created in.
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: create a security group
  local_action:
    module: cs_securitygroup
    name: default
    description: default security group

- name: remove a security group
  local_action:
    module: cs_securitygroup
    name: default
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the security group.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: Name of security group.
  returned: success
  type: string
  sample: app
description:
  description: Description of security group.
  returned: success
  type: string
  sample: application security group
tags:
  description: List of resource tags associated with the security group.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
project:
  description: Name of project the security group is related to.
  returned: success
  type: string
  sample: Production
domain:
  description: Domain the security group is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the security group is related to.
  returned: success
  type: string
  sample: example account
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import AnsibleCloudStack, cs_argument_spec, cs_required_together


class AnsibleCloudStackSecurityGroup(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackSecurityGroup, self).__init__(module)
        self.security_group = None

    def get_security_group(self):
        if not self.security_group:

            args = {
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'securitygroupname': self.module.params.get('name'),
            }
            sgs = self.query_api('listSecurityGroups', **args)
            if sgs:
                self.security_group = sgs['securitygroup'][0]
        return self.security_group

    def create_security_group(self):
        security_group = self.get_security_group()
        if not security_group:
            self.result['changed'] = True

            args = {
                'name': self.module.params.get('name'),
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'description': self.module.params.get('description'),
            }

            if not self.module.check_mode:
                res = self.query_api('createSecurityGroup', **args)
                security_group = res['securitygroup']

        return security_group

    def remove_security_group(self):
        security_group = self.get_security_group()
        if security_group:
            self.result['changed'] = True

            args = {
                'name': self.module.params.get('name'),
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
            }

            if not self.module.check_mode:
                self.query_api('deleteSecurityGroup', **args)

        return security_group


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        description=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
        project=dict(),
        account=dict(),
        domain=dict(),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_sg = AnsibleCloudStackSecurityGroup(module)

    state = module.params.get('state')
    if state in ['absent']:
        sg = acs_sg.remove_security_group()
    else:
        sg = acs_sg.create_security_group()

    result = acs_sg.get_result(sg)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
