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
module: aci_contract_subject_to_filter
short_description: Bind Contract Subjects to Filters (vz:RsSubjFiltAtt)
description:
- Bind Contract Subjects to Filters on Cisco ACI fabrics.
version_added: '2.4'
options:
  contract:
    description:
    - The name of the contract.
    type: str
    aliases: [ contract_name ]
  filter:
    description:
    - The name of the Filter to bind to the Subject.
    type: str
    aliases: [ filter_name ]
  log:
    description:
    - Determines if the binding should be set to log.
    - The APIC defaults to C(none) when unset during creation.
    type: str
    choices: [ log, none ]
    aliases: [ directive ]
  subject:
    description:
    - The name of the Contract Subject.
    type: str
    aliases: [ contract_subject, subject_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
  tenant:
    description:
    - The name of the tenant.
    type: str
    required: yes
    aliases: [ tenant_name ]
extends_documentation_fragment: aci
notes:
- The C(tenant), C(contract), C(subject), and C(filter_name) must exist before using this module in your playbook.
  The M(aci_tenant), M(aci_contract), M(aci_contract_subject), and M(aci_filter) modules can be used for these.
seealso:
- module: aci_contract_subject
- module: aci_filter
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(vz:RsSubjFiltAtt).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Jacob McGill (@jmcgill298)
'''

EXAMPLES = r'''
- name: Add a new contract subject to filer binding
  aci_contract_subject_to_filter:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: test
    filter: '{{ filter }}'
    log: '{{ log }}'
    state: present
  delegate_to: localhost

- name: Remove an existing contract subject to filter binding
  aci_contract_subject_to_filter:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: test
    filter: '{{ filter }}'
    log: '{{ log }}'
    state: present
  delegate_to: localhost

- name: Query a specific contract subject to filter binding
  aci_contract_subject_to_filter:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: test
    filter: '{{ filter }}'
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all contract subject to filter bindings
  aci_contract_subject_to_filter:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: test
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
        contract=dict(type='str', aliases=['contract_name']),  # Not required for querying all objects
        filter=dict(type='str', aliases=['filter_name']),  # Not required for querying all objects
        subject=dict(type='str', aliases=['contract_subject', 'subject_name']),  # Not required for querying all objects
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
        log=dict(type='str', choices=['log', 'none'], aliases=['directive']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['contract', 'filter', 'subject', 'tenant']],
            ['state', 'present', ['contract', 'filter', 'subject', 'tenant']],
        ],
    )

    contract = module.params['contract']
    filter_name = module.params['filter']
    log = module.params['log']
    subject = module.params['subject']
    tenant = module.params['tenant']
    state = module.params['state']

    # Add subject_filter key to modul.params for building the URL
    module.params['subject_filter'] = filter_name

    # Convert log to empty string if none, as that is what API expects. An empty string is not a good option to present the user.
    if log == 'none':
        log = ''

    aci = ACIModule(module)
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
        subclass_3=dict(
            aci_class='vzRsSubjFiltAtt',
            aci_rn='rssubjFiltAtt-{0}'.format(filter_name),
            module_object=filter_name,
            target_filter={'tnVzFilterName': filter_name},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='vzRsSubjFiltAtt',
            class_config=dict(
                tnVzFilterName=filter_name,
                directives=log,
            ),
        )

        aci.get_diff(aci_class='vzRsSubjFiltAtt')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    # Remove subject_filter used to build URL from module.params
    module.params.pop('subject_filter')

    aci.exit_json()


if __name__ == "__main__":
    main()
