#!/usr/bin/python

# Copyright 2017 Dag Wieers <dag@wieers.com>
# Copyright 2017 Swetha Chunduri (@schunduri)

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_tenant
short_description: Manage tenants on Cisco ACI fabrics
description:
- Manage tenants on a Cisco ACI fabric.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  tenant_name:
    description:
    - The name of the tenant.
    required: yes
  descr:
    description:
    - Description for the AEP.
  state:
    description:
    - present, absent, query
    default: present
    choices: [ absent, present, query ]
extends_documentation_fragment: aci
'''

EXAMPLES = '''
- name: Add a new tenant
  aci_tenant:
    hostname: acme-apic-1
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    descriptions: Name of the production tenant
    state: present

- name: Remove a tenant
  aci_tenant:
    hostname: acme-apic-1
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    state: absent

- name: Query a tenant
  aci_tenant:
    hostname: acme-apic-1
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    state: query

- name: Query all tenants
  aci_tenant:
    hostname: acme-apic-1
    username: admin
    password: SomeSecretPassword
    state: query
'''

RETURN = r'''
status:
  description: The status code of the http request
  returned: upon making a successful GET, POST or DELETE request to the APIC
  type: int
  sample: 200
response:
  description: Response text returned by APIC
  returned: when a HTTP request has been made to APIC
  type: string
  sample: '{"totalCount":"0","imdata":[]}'
'''

import json

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        tenant_name=dict(type='str', aliases=['name']),
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action']),  # Deprecated starting from v2.8
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    tenant_name = module.params['tenant_name']
    description = module.params['description']
    state = module.params['state']

    aci = ACIModule(module)

    if tenant_name is not None:
        # Work with a specific tenant
        path = 'api/mo/uni/tn-%(tenant_name)s.json' % module.params
    elif state == 'query':
        # Query all tenants
        path = 'api/node/class/fvTenant.json'
    else:
        module.fail_json("Parameter 'tenant_name' is required for state 'absent' or 'present'")

    if state == 'query':
        aci.request(path)
    elif module.check_mode:
        # TODO: Implement proper check-mode (presence check)
        aci.result(changed=True, response='OK (Check mode)', status=200)
    else:
        payload = {'fvTenant': {'attributes': {'name': tenant_name, 'descr': description}}}
        aci.request_diff(path, payload=json.dumps(payload))

    module.exit_json(**aci.result)

if __name__ == "__main__":
    main()
