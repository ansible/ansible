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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_domain
short_description: Manages domains on Apache CloudStack based clouds.
description:
    - Create, update and remove domains.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  path:
    description:
      - Path of the domain.
      - Prefix C(ROOT/) or C(/ROOT/) in path is optional.
    required: true
  network_domain:
    description:
      - Network domain for networks in the domain.
  clean_up:
    description:
      - Clean up all domain resources like child domains and accounts.
      - Considered on C(state=absent).
    default: false
  state:
    description:
      - State of the domain.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a domain
  local_action:
    module: cs_domain
    path: ROOT/customers
    network_domain: customers.example.com

- name: Create another subdomain
  local_action:
    module: cs_domain
    path: ROOT/customers/xy
    network_domain: xy.customers.example.com

- name: Remove a domain
  local_action:
    module: cs_domain
    path: ROOT/customers/xy
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the domain.
  returned: success
  type: string
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
name:
  description: Name of the domain.
  returned: success
  type: string
  sample: customers
path:
  description: Domain path.
  returned: success
  type: string
  sample: /ROOT/customers
parent_domain:
  description: Parent domain of the domain.
  returned: success
  type: string
  sample: ROOT
network_domain:
  description: Network domain of the domain.
  returned: success
  type: string
  sample: example.local
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackDomain(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackDomain, self).__init__(module)
        self.returns = {
            'path': 'path',
            'networkdomain': 'network_domain',
            'parentdomainname': 'parent_domain',
        }
        self.domain = None

    def _get_domain_internal(self, path=None):
        if not path:
            path = self.module.params.get('path')

        if path.endswith('/'):
            self.module.fail_json(msg="Path '%s' must not end with /" % path)

        path = path.lower()

        if path.startswith('/') and not path.startswith('/root/'):
            path = "root" + path
        elif not path.startswith('root/'):
            path = "root/" + path

        args = {
            'listall': True
        }

        domains = self.query_api('listDomains', **args)
        if domains:
            for d in domains['domain']:
                if path == d['path'].lower():
                    return d
        return None

    def get_name(self):
        # last part of the path is the name
        name = self.module.params.get('path').split('/')[-1:]
        return name

    def get_domain(self, key=None):
        if not self.domain:
            self.domain = self._get_domain_internal()
        return self._get_by_key(key, self.domain)

    def get_parent_domain(self, key=None):
        path = self.module.params.get('path')
        # cut off last /*
        path = '/'.join(path.split('/')[:-1])
        if not path:
            return None
        parent_domain = self._get_domain_internal(path=path)
        if not parent_domain:
            self.module.fail_json(msg="Parent domain path %s does not exist" % path)
        return self._get_by_key(key, parent_domain)

    def present_domain(self):
        domain = self.get_domain()
        if not domain:
            domain = self.create_domain(domain)
        else:
            domain = self.update_domain(domain)
        return domain

    def create_domain(self, domain):
        self.result['changed'] = True

        args = {
            'name': self.get_name(),
            'parentdomainid': self.get_parent_domain(key='id'),
            'networkdomain': self.module.params.get('network_domain')
        }
        if not self.module.check_mode:
            res = self.query_api('createDomain', **args)
            domain = res['domain']
        return domain

    def update_domain(self, domain):
        args = {
            'id': domain['id'],
            'networkdomain': self.module.params.get('network_domain')
        }
        if self.has_changed(args, domain):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('updateDomain', **args)
                domain = res['domain']
        return domain

    def absent_domain(self):
        domain = self.get_domain()
        if domain:
            self.result['changed'] = True

            if not self.module.check_mode:
                args = {
                    'id': domain['id'],
                    'cleanup': self.module.params.get('clean_up')
                }
                res = self.query_api('deleteDomain', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    res = self.poll_job(res, 'domain')
        return domain


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        path=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        network_domain=dict(),
        clean_up=dict(type='bool', default=False),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_dom = AnsibleCloudStackDomain(module)

    state = module.params.get('state')
    if state in ['absent']:
        domain = acs_dom.absent_domain()
    else:
        domain = acs_dom.present_domain()

    result = acs_dom.get_result(domain)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
