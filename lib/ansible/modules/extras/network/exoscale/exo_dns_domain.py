#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
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
  api_key:
    description:
      - API key of the Exoscale DNS API.
    required: false
    default: null
  api_secret:
    description:
      - Secret key of the Exoscale DNS API.
    required: false
    default: null
  api_timeout:
    description:
      - HTTP timeout to Exoscale DNS API.
    required: false
    default: 10
  api_region:
    description:
      - Name of the ini section in the C(cloustack.ini) file.
    required: false
    default: cloudstack
  validate_certs:
    description:
      - Validate SSL certs of the Exoscale DNS API.
    required: false
    default: true
requirements:
  - "python >= 2.6"
notes:
  - As Exoscale DNS uses the same API key and secret for all services, we reuse the config used for Exscale Compute based on CloudStack.
    The config is read from several locations, in the following order.
    The C(CLOUDSTACK_KEY), C(CLOUDSTACK_SECRET) environment variables.
    A C(CLOUDSTACK_CONFIG) environment variable pointing to an C(.ini) file,
    A C(cloudstack.ini) file in the current working directory.
    A C(.cloudstack.ini) file in the users home directory.
    Optionally multiple credentials and endpoints can be specified using ini sections in C(cloudstack.ini).
    Use the argument C(api_region) to select the section name, default section is C(cloudstack).
  - This module does not support multiple A records and will complain properly if you try.
  - More information Exoscale DNS can be found on https://community.exoscale.ch/documentation/dns/.
  - This module supports check mode and diff.
'''

EXAMPLES = '''
# Create a domain.
- local_action:
    module: exo_dns_domain
    name: example.com

# Remove a domain.
- local_action:
    module: exo_dns_domain
    name: example.com
    state: absent
'''

RETURN = '''
---
exo_dns_domain:
    description: API domain results
    returned: success
    type: dictionary
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
            type: string
            sample: "2016-08-12T15:24:23.989Z"
        expires_on:
            description: When the domain expires
            returned: success
            type: string
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
            type: string
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
            type: string
            sample: "hosted"
        token:
            description: Token
            returned: success
            type: string
            sample: "r4NzTRp6opIeFKfaFYvOd6MlhGyD07jl"
        unicode_name:
            description: Domain name as unicode
            returned: success
            type: string
            sample: "example.com"
        updated_at:
            description: When the domain was updated last.
            returned: success
            type: string
            sample: "2016-08-12T15:24:23.989Z"
        user_id:
            description: ID of the user
            returned: success
            type: int
            sample: null
        whois_protected:
            description: Wheter the whois is protected or not
            returned: success
            type: bool
            sample: false
'''

# import exoscale common
from ansible.module_utils.exoscale import *


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

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
