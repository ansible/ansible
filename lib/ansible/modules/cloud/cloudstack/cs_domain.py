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
module: cs_domain
short_description: Manages domains on Apache CloudStack based clouds.
description:
    - Create, update and remove domains.
version_added: '2.0'
author: René Moser (@resmo)
options:
  path:
    description:
      - Path of the domain.
      - Prefix C(ROOT/) or C(/ROOT/) in path is optional.
    type: str
    required: true
  network_domain:
    description:
      - Network domain for networks in the domain.
    type: str
  clean_up:
    description:
      - Clean up all domain resources like child domains and accounts.
      - Considered on I(state=absent).
    type: bool
    default: no
  state:
    description:
      - State of the domain.
    type: str
    choices: [ present, absent ]
    default: present
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a domain
  cs_domain:
    path: ROOT/customers
    network_domain: customers.example.com
  delegate_to: localhost

- name: Create another subdomain
  cs_domain:
    path: ROOT/customers/xy
    network_domain: xy.customers.example.com
  delegate_to: localhost

- name: Remove a domain
  cs_domain:
    path: ROOT/customers/xy
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the domain.
  returned: success
  type: str
  sample: 87b1e0ce-4e01-11e4-bb66-0050569e64b8
name:
  description: Name of the domain.
  returned: success
  type: str
  sample: customers
path:
  description: Domain path.
  returned: success
  type: str
  sample: /ROOT/customers
parent_domain:
  description: Parent domain of the domain.
  returned: success
  type: str
  sample: ROOT
network_domain:
  description: Network domain of the domain.
  returned: success
  type: str
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
            'listall': True,
            'fetch_list': True,
        }

        domains = self.query_api('listDomains', **args)
        if domains:
            for d in domains:
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
