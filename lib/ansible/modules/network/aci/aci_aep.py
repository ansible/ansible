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
module: aci_aep
short_description: Direct access to the Cisco ACI APIC API
description:
- Offers direct access to the Cisco ACI APIC API
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
    aep_name:
      description:
      - The name of the Attachable Access Entity Profile.
      required: yes
    description:
      description:
      - Description for the AEP.
    state:
      description:
      - Ensure that the Attachable entity profile  with this C(aep_name) exists or does not exist. 
      - Query for retrieving information of existing managed objects.
      default: present
      choices: [ absent, present, query ]
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new AEP
  aci_aep:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    aep_name: ACI-AEP
    description: default
    state: present

- name: Remove an existing AEP
  aci_aep:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    aep_name: ACI-AEP
    state: absent

- name: Query an AEP
  aci_aep:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    aep_name: ACI-AEP
    state: query

- name: Query all AEPs
  aci_aep:
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
        aep_name=dict(type='str'),
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    aep_name = module.params['aep_name']
    description = str(module.params['description'])
    state = module.params['state']

    aci = ACIModule(module)

    if aep_name is not None:
        # Work with a specific attachable entitiy profile
        path = 'api/mo/uni/infra/attentp-%(aep_name)s.json' % module.params
    elif state == 'query':
        # Query all AEPs
        path = 'api/node/class/infraAttEntityP.json'
    else:
        module.fail_json("Parameter 'tenant_name' is required for state 'absent' or 'present'")

    if state == 'query':
        aci.request(path)
    else:
        payload = {"infraAttEntityP": {"attributes": {"descr": description, "name": aep_name}}}
        aci.request_diff(path, payload=json.dumps(payload))

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
