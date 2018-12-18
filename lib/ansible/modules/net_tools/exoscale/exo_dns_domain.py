#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: exo_dns_domain
short_description: Manages domain records on Exoscale DNS API.
description:
    - Create and remove domain records.
version_added: "2.2"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the record.
    required: true
  state:
    description:
      - State of the resource.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
extends_documentation_fragment: exoscale
'''

EXAMPLES = '''
- name: Create a domain
  local_action:
    module: exo_dns_domain
    name: example.com

- name: Remove a domain
  local_action:
    module: exo_dns_domain
    name: example.com
    state: absent
'''

RETURN = '''
---
exo_dns_domain:
    description: API domain results
    returned: success
    type: complex
    contains:
        account_id:
            description: Your account ID
            returned: success
            type: int
            sample: 34569
        auto_renew:
            description: Whether domain is auto renewed or not
            returned: success
            type: bool
            sample: false
        created_at:
            description: When the domain was created
            returned: success
            type: str
            sample: "2016-08-12T15:24:23.989Z"
        expires_on:
            description: When the domain expires
            returned: success
            type: str
            sample: "2016-08-12T15:24:23.989Z"
        id:
            description: ID of the domain
            returned: success
            type: int
            sample: "2016-08-12T15:24:23.989Z"
        lockable:
            description: Whether the domain is lockable or not
            returned: success
            type: bool
            sample: true
        name:
            description: Domain name
            returned: success
            type: str
            sample: example.com
        record_count:
            description: Number of records related to this domain
            returned: success
            type: int
            sample: 5
        registrant_id:
            description: ID of the registrant
            returned: success
            type: int
            sample: null
        service_count:
            description: Number of services
            returned: success
            type: int
            sample: 0
        state:
            description: State of the domain
            returned: success
            type: str
            sample: "hosted"
        token:
            description: Token
            returned: success
            type: str
            sample: "r4NzTRp6opIeFKfaFYvOd6MlhGyD07jl"
        unicode_name:
            description: Domain name as unicode
            returned: success
            type: str
            sample: "example.com"
        updated_at:
            description: When the domain was updated last.
            returned: success
            type: str
            sample: "2016-08-12T15:24:23.989Z"
        user_id:
            description: ID of the user
            returned: success
            type: int
            sample: null
        whois_protected:
            description: Whether the whois is protected or not
            returned: success
            type: bool
            sample: false
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.exoscale import ExoDns, exo_dns_argument_spec, exo_dns_required_together


class ExoDnsDomain(ExoDns):

    def __init__(self, module):
        super(ExoDnsDomain, self).__init__(module)
        self.name = self.module.params.get('name').lower()

    def get_domain(self):
        domains = self.api_query("/domains", "GET")
        for z in domains:
            if z['domain']['name'].lower() == self.name:
                return z
        return None

    def present_domain(self):
        domain = self.get_domain()
        data = {
            'domain': {
                'name': self.name,
            }
        }
        if not domain:
            self.result['diff']['after'] = data['domain']
            self.result['changed'] = True
            if not self.module.check_mode:
                domain = self.api_query("/domains", "POST", data)
        return domain

    def absent_domain(self):
        domain = self.get_domain()
        if domain:
            self.result['diff']['before'] = domain
            self.result['changed'] = True
            if not self.module.check_mode:
                self.api_query("/domains/%s" % domain['domain']['name'], "DELETE")
        return domain

    def get_result(self, resource):
        if resource:
            self.result['exo_dns_domain'] = resource['domain']
        return self.result


def main():
    argument_spec = exo_dns_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=exo_dns_required_together(),
        supports_check_mode=True
    )

    exo_dns_domain = ExoDnsDomain(module)
    if module.params.get('state') == "present":
        resource = exo_dns_domain.present_domain()
    else:
        resource = exo_dns_domain.absent_domain()
    result = exo_dns_domain.get_result(resource)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
