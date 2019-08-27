#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_aep
short_description: Manage attachable Access Entity Profile (AEP) objects (infra:AttEntityP, infra:ProvAcc)
description:
- Connect to external virtual and physical domains by using
  attachable Access Entity Profiles (AEP) on Cisco ACI fabrics.
version_added: '2.4'
options:
  aep:
    description:
    - The name of the Attachable Access Entity Profile.
    type: str
    required: yes
    aliases: [ aep_name, name ]
  description:
    description:
    - Description for the AEP.
    type: str
    aliases: [ descr ]
  infra_vlan:
    description:
    - Enable infrastructure VLAN.
    - The hypervisor functions of the AEP.
    - C(no) will disable the infrastructure vlan if it is enabled.
    type: bool
    aliases: [ infrastructure_vlan ]
    version_added: '2.5'
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    default: present
    choices: [ absent, present, query ]
extends_documentation_fragment: aci
seealso:
- module: aci_aep_to_domain
- name: APIC Management Information Model reference
  description: More information about the internal APIC classes B(infra:AttEntityP) and B(infra:ProvAcc).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Swetha Chunduri (@schunduri)
'''

EXAMPLES = r'''
- name: Add a new AEP
  aci_aep:
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: ACI-AEP
    description: default
    state: present
  delegate_to: localhost

- name: Remove an existing AEP
  aci_aep:
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: ACI-AEP
    state: absent
  delegate_to: localhost

- name: Query all AEPs
  aci_aep:
    host: apic
    username: admin
    password: SomeSecretPassword
    state: query
  delegate_to: localhost
  register: query_result

- name: Query a specific AEP
  aci_aep:
    host: apic
    username: admin
    password: SomeSecretPassword
    aep: ACI-AEP
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
current:
  description: The existing configuration from the APIC after the module has finished
  returned: success
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production environment",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
error:
  description: The error information as returned from the APIC
  returned: failure
  type: dict
  sample:
    {
        "code": "122",
        "text": "unknown managed object class foo"
    }
raw:
  description: The raw output returned by the APIC REST API (xml or json)
  returned: parse error
  type: str
  sample: '<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1"><error code="122" text="unknown managed object class foo"/></imdata>'
sent:
  description: The actual/minimal configuration pushed to the APIC
  returned: info
  type: list
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment"
            }
        }
    }
previous:
  description: The original configuration from the APIC before the module has started
  returned: info
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
proposed:
  description: The assembled configuration from the user-provided parameters
  returned: info
  type: dict
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment",
                "name": "production"
            }
        }
    }
filter_string:
  description: The filter string used for the request
  returned: failure or debug
  type: str
  sample: ?rsp-prop-include=config-only
method:
  description: The HTTP method used for the request to the APIC
  returned: failure or debug
  type: str
  sample: POST
response:
  description: The HTTP response from the APIC
  returned: failure or debug
  type: str
  sample: OK (30 bytes)
status:
  description: The HTTP status from the APIC
  returned: failure or debug
  type: int
  sample: 200
url:
  description: The HTTP url used for the request to the APIC
  returned: failure or debug
  type: str
  sample: https://10.11.12.13/api/mo/uni/tn-production.json
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        aep=dict(type='str', aliases=['name', 'aep_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        infra_vlan=dict(type='bool', aliases=['infrastructure_vlan']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['aep']],
            ['state', 'present', ['aep']],
        ],
    )

    aep = module.params['aep']
    description = module.params['description']
    infra_vlan = module.params['infra_vlan']
    state = module.params['state']

    if infra_vlan:
        child_configs = [dict(infraProvAcc=dict(attributes=dict(name='provacc')))]
    elif infra_vlan is False:
        child_configs = [dict(infraProvAcc=dict(attributes=dict(name='provacc', status='deleted')))]
    else:
        child_configs = []

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='infraAttEntityP',
            aci_rn='infra/attentp-{0}'.format(aep),
            module_object=aep,
            target_filter={'name': aep},
        ),
    )
    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='infraAttEntityP',
            class_config=dict(
                name=aep,
                descr=description,
            ),
            child_configs=child_configs,
        )

        aci.get_diff(aci_class='infraAttEntityP')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
