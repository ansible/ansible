#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cs_network_acl
short_description: Manages network access control lists (ACL) on Apache CloudStack based clouds.
description:
    - Create and remove network ACLs.
version_added: '2.4'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the network ACL.
    type: str
    required: true
  description:
    description:
      - Description of the network ACL.
      - If not set, identical to I(name).
    type: str
  vpc:
    description:
      - VPC the network ACL is related to.
    type: str
    required: true
  state:
    description:
      - State of the network ACL.
    type: str
    default: present
    choices: [ present, absent ]
  domain:
    description:
      - Domain the network ACL rule is related to.
    type: str
  account:
    description:
      - Account the network ACL rule is related to.
    type: str
  project:
    description:
      - Name of the project the network ACL is related to.
    type: str
  zone:
    description:
      - Name of the zone the VPC is related to.
      - If not set, default zone is used.
    type: str
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: create a network ACL
  cs_network_acl:
    name: Webserver ACL
    description: a more detailed description of the ACL
    vpc: customers
  delegate_to: localhost

- name: remove a network ACL
  cs_network_acl:
    name: Webserver ACL
    vpc: customers
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
name:
  description: Name of the network ACL.
  returned: success
  type: str
  sample: customer acl
description:
  description: Description of the network ACL.
  returned: success
  type: str
  sample: Example description of a network ACL
vpc:
  description: VPC of the network ACL.
  returned: success
  type: str
  sample: customer vpc
zone:
  description: Zone the VPC is related to.
  returned: success
  type: str
  sample: ch-gva-2
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackNetworkAcl(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackNetworkAcl, self).__init__(module)

    def get_network_acl(self):
        args = {
            'name': self.module.params.get('name'),
            'vpcid': self.get_vpc(key='id'),
        }
        network_acls = self.query_api('listNetworkACLLists', **args)
        if network_acls:
            return network_acls['networkacllist'][0]
        return None

    def present_network_acl(self):
        network_acl = self.get_network_acl()
        if not network_acl:
            self.result['changed'] = True
            args = {
                'name': self.module.params.get('name'),
                'description': self.get_or_fallback('description', 'name'),
                'vpcid': self.get_vpc(key='id')
            }
            if not self.module.check_mode:
                res = self.query_api('createNetworkACLList', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    network_acl = self.poll_job(res, 'networkacllist')

        return network_acl

    def absent_network_acl(self):
        network_acl = self.get_network_acl()
        if network_acl:
            self.result['changed'] = True
            args = {
                'id': network_acl['id'],
            }
            if not self.module.check_mode:
                res = self.query_api('deleteNetworkACLList', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'networkacllist')

        return network_acl


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        description=dict(),
        vpc=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        zone=dict(),
        domain=dict(),
        account=dict(),
        project=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_network_acl = AnsibleCloudStackNetworkAcl(module)

    state = module.params.get('state')
    if state == 'absent':
        network_acl = acs_network_acl.absent_network_acl()
    else:
        network_acl = acs_network_acl.present_network_acl()

    result = acs_network_acl.get_result(network_acl)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
