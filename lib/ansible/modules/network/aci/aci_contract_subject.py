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
module: aci_contract_subject
short_description: Manage initial Contract Subjects (vz:Subj)
description:
- Manage initial Contract Subjects on Cisco ACI fabrics.
version_added: '2.4'
options:
  tenant:
    description:
    - The name of the tenant.
    type: str
    aliases: [ tenant_name ]
  subject:
    description:
    - The contract subject name.
    type: str
    aliases: [ contract_subject, name, subject_name ]
  contract:
    description:
    - The name of the Contract.
    type: str
    aliases: [ contract_name ]
  reverse_filter:
    description:
    - Determines if the APIC should reverse the src and dst ports to allow the
      return traffic back, since ACI is stateless filter.
    - The APIC defaults to C(yes) when unset during creation.
    type: bool
  priority:
    description:
    - The QoS class.
    - The APIC defaults to C(unspecified) when unset during creation.
    type: str
    choices: [ level1, level2, level3, unspecified ]
  dscp:
    description:
    - The target DSCP.
    - The APIC defaults to C(unspecified) when unset during creation.
    type: str
    choices: [ AF11, AF12, AF13, AF21, AF22, AF23, AF31, AF32, AF33, AF41, AF42, AF43,
               CS0, CS1, CS2, CS3, CS4, CS5, CS6, CS7, EF, VA, unspecified ]
    aliases: [ target ]
  description:
    description:
    - Description for the contract subject.
    type: str
    aliases: [ descr ]
  consumer_match:
    description:
    - The match criteria across consumers.
    - The APIC defaults to C(at_least_one) when unset during creation.
    type: str
    choices: [ all, at_least_one, at_most_one, none ]
  provider_match:
    description:
    - The match criteria across providers.
    - The APIC defaults to C(at_least_one) when unset during creation.
    type: str
    choices: [ all, at_least_one, at_most_one, none ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
notes:
- The C(tenant) and C(contract) used must exist before using this module in your playbook.
  The M(aci_tenant) and M(aci_contract) modules can be used for this.
seealso:
- module: aci_contract
- module: aci_tenant
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(vz:Subj).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Swetha Chunduri (@schunduri)
'''

EXAMPLES = r'''
- name: Add a new contract subject
  aci_contract_subject:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: default
    description: test
    reverse_filter: yes
    priority: level1
    dscp: unspecified
    state: present
  register: query_result

- name: Remove a contract subject
  aci_contract_subject:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: default
    state: absent
  delegate_to: localhost

- name: Query a contract subject
  aci_contract_subject:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: default
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all contract subjects
  aci_contract_subject:
    host: apic
    username: admin
    password: SomeSecretPassword
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

MATCH_MAPPING = dict(
    all='All',
    at_least_one='AtleastOne',
    at_most_one='AtmostOne',
    none='None',
)


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        contract=dict(type='str', aliases=['contract_name']),  # Not required for querying all objects
        subject=dict(type='str', aliases=['contract_subject', 'name', 'subject_name']),  # Not required for querying all objects
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
        priority=dict(type='str', choices=['unspecified', 'level1', 'level2', 'level3']),
        reverse_filter=dict(type='bool'),
        dscp=dict(type='str', aliases=['target'],
                  choices=['AF11', 'AF12', 'AF13', 'AF21', 'AF22', 'AF23', 'AF31', 'AF32', 'AF33', 'AF41', 'AF42', 'AF43',
                           'CS0', 'CS1', 'CS2', 'CS3', 'CS4', 'CS5', 'CS6', 'CS7', 'EF', 'VA', 'unspecified']),
        description=dict(type='str', aliases=['descr']),
        consumer_match=dict(type='str', choices=['all', 'at_least_one', 'at_most_one', 'none']),
        provider_match=dict(type='str', choices=['all', 'at_least_one', 'at_most_one', 'none']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['contract', 'subject', 'tenant']],
            ['state', 'present', ['contract', 'subject', 'tenant']],
        ],
    )

    aci = ACIModule(module)

    subject = module.params['subject']
    priority = module.params['priority']
    reverse_filter = aci.boolean(module.params['reverse_filter'])
    contract = module.params['contract']
    dscp = module.params['dscp']
    description = module.params['description']
    filter_name = module.params['filter']
    consumer_match = module.params['consumer_match']
    if consumer_match is not None:
        consumer_match = MATCH_MAPPING[consumer_match]
    provider_match = module.params['provider_match']
    if provider_match is not None:
        provider_match = MATCH_MAPPING[provider_match]
    state = module.params['state']
    tenant = module.params['tenant']

    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            module_object=tenant,
            target_filter={'name': tenant},
        ),
        subclass_1=dict(
            aci_class='vzBrCP',
            aci_rn='brc-{0}'.format(contract),
            module_object=contract,
            target_filter={'name': contract},
        ),
        subclass_2=dict(
            aci_class='vzSubj',
            aci_rn='subj-{0}'.format(subject),
            module_object=subject,
            target_filter={'name': subject},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='vzSubj',
            class_config=dict(
                name=subject,
                prio=priority,
                revFltPorts=reverse_filter,
                targetDscp=dscp,
                consMatchT=consumer_match,
                provMatchT=provider_match,
                descr=description,
            ),
        )

        aci.get_diff(aci_class='vzSubj')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
