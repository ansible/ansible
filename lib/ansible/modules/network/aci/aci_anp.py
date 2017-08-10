#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_anp
short_description: Manage top level application network profile objects
description:
-  Manage top level application network profile object, i.e. this does
      not manage EPGs.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The tenant used must exist before using this module in your playbook. The M(aci_tenant) module can be used for this.
options:
   tenant:
     description:
     - The name of the tenant.
     required: yes
     aliases: ['tenant_name']
   app_profile:
     description:
     - The name of the application network profile.
     required: yes
     aliases: ['app_profile']
   description:
     description:
     - Description for the ANP.
   state:
     description:
     - present, absent, query
     default: present
     choices: [ absent, present, query ]
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new ANP
  aci_anp:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    description: Production Tenant
    state: present

- name: Remove an ANP
  aci_anp:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    state: absent

- name: Query an ANP
  aci_anp:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    app_profile: default
    state: query

- name: Query all ANPs
  aci_anp:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: query

'''

RETURN = r'''
status:
  description: The status code of the http request
  returned: upon making a successful GET, POST or DELETE request to the Cisco ACI APIC
  type: int
  sample: 200
response:
  description: Response text returned by Cisco ACI APIC
  returned: when a HTTP request has been made to Cisco ACI APIC
  type: string
  sample: '{"totalCount":"0","imdata":[]}'
'''

import json

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        tenant=dict(type='str', aliases=['tenant_name']),
        app_profile=dict(type='str', aliases=['app_profile_name']),
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    tenant = module.params['tenant']
    app_profile = module.params['app_profile']
    description = str(module.params['description'])
    state = module.params['state']

    aci = ACIModule(module)

    if (tenant, app_profile) is not None:
        # Work with specific anp
        path = 'api/mo/uni/tn-%(tenant)s/ap-%(app_profile)s.json' % module.params
    elif state == 'query':
        # Query all anps
        path = 'api/node/class/fvAp.json'
    else:
        module.fail_json(msg="Parameters 'tenant' and 'app_profile' are required for state 'absent' or 'present'")

    if state == 'query':
        aci.request(path)
    else:
        payload = {"fvAp": {"attributes": {"name": app_profile, "descr": description}}}
        aci.request_diff(path, payload=json.dumps(payload))

    module.exit_json(**aci.result)

if __name__ == "__main__":
    main()
