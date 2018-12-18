#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vultr_dns_domain
short_description: Manages DNS domains on Vultr.
description:
  - Create and remove DNS domains.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - The domain name.
    required: true
    aliases: [ domain ]
  server_ip:
    description:
      - The default server IP.
      - Use M(vultr_dns_record) to change it once the domain is created.
      - Required if C(state=present).
  state:
    description:
      - State of the DNS domain.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Ensure a domain exists
  local_action:
    module: vultr_dns_domain
    name: example.com
    server_ip: 10.10.10.10

- name: Ensure a domain is absent
  local_action:
    module: vultr_dns_domain
    name: example.com
    state: absent
'''

RETURN = r'''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: str
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: str
      sample: "https://api.vultr.com"
vultr_dns_domain:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    name:
      description: Name of the DNS Domain.
      returned: success
      type: str
      sample: example.com
    date_created:
      description: Date the DNS domain was created.
      returned: success
      type: str
      sample: "2017-08-26 12:47:48"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrDnsDomain(Vultr):

    def __init__(self, module):
        super(AnsibleVultrDnsDomain, self).__init__(module, "vultr_dns_domain")

        self.returns = {
            'domain': dict(key='name'),
            'date_created': dict(),
        }

    def get_domain(self):
        domains = self.api_query(path="/v1/dns/list")
        name = self.module.params.get('name').lower()
        if domains:
            for domain in domains:
                if domain.get('domain').lower() == name:
                    return domain
        return {}

    def present_domain(self):
        domain = self.get_domain()
        if not domain:
            domain = self._create_domain(domain)
        return domain

    def _create_domain(self, domain):
        self.result['changed'] = True
        data = {
            'domain': self.module.params.get('name'),
            'serverip': self.module.params.get('server_ip'),
        }
        self.result['diff']['before'] = {}
        self.result['diff']['after'] = data

        if not self.module.check_mode:
            self.api_query(
                path="/v1/dns/create_domain",
                method="POST",
                data=data
            )
            domain = self.get_domain()
        return domain

    def absent_domain(self):
        domain = self.get_domain()
        if domain:
            self.result['changed'] = True

            data = {
                'domain': domain['domain'],
            }

            self.result['diff']['before'] = domain
            self.result['diff']['after'] = {}

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/dns/delete_domain",
                    method="POST",
                    data=data
                )
        return domain


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['domain']),
        server_ip=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['server_ip']),
        ],
        supports_check_mode=True,
    )

    vultr_domain = AnsibleVultrDnsDomain(module)
    if module.params.get('state') == "absent":
        domain = vultr_domain.absent_domain()
    else:
        domain = vultr_domain.present_domain()

    result = vultr_domain.get_result(domain)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
