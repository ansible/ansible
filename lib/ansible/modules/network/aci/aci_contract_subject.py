#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_contract_subject
short_description: Manage initial Contract Subjects on Cisco ACI fabrics (vz:Subj)
description:
- Manage initial Contract Subjects on Cisco ACI fabrics.
- More information from the internal APIC class
  I(vz:Subj) at U(https://developer.cisco.com/media/mim-ref/MO-vzSubj.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant) and C(contract) used must exist before using this module in your playbook.
- The M(aci_tenant) and M(aci_contract) modules can be used for this.
options:
  tenant:
    description:
    - The name of the tenant.
    aliases: [ tenant_name ]
  subject:
    description:
    - The contract subject name.
    aliases: [ contract_subject, name, subject_name ]
  contract:
    description:
    - The name of the Contract.
    aliases: [ contract_name ]
  reverse_filter:
    description:
    - Determines if the APIC should reverse the src and dst ports to allow the
      return traffic back, since ACI is stateless filter.
    - The APIC defaults new Contract Subjects to C(yes).
    choices: [ yes, no ]
    default: yes
  priority:
    description:
    - The QoS class.
    - The APIC defaults new Contract Subjects to C(unspecified).
    choices: [ level1, level2, level3, unspecified ]
    default: unspecified
  dscp:
    description:
    - The target DSCP.
    - The APIC defaults new Contract Subjects to C(unspecified).
    choices: [ AF11, AF12, AF13, AF21, AF22, AF23, AF31, AF32, AF33, AF41, AF42, AF43,
               CS0, CS1, CS2, CS3, CS4, CS5, CS6, CS7, EF, VA, unspecified ]
    aliases: [ target ]
    default: unspecified
  description:
    description:
    - Description for the contract subject.
  consumer_match:
    description:
    - The match criteria across consumers.
    - The APIC defaults new Contract Subjects to C(at_least_one).
    choices: [ all, at_least_one, at_most_one, none ]
    default: at_least_one
  provider_match:
    description:
    - The match criteria across providers.
    - The APIC defaults new Contract Subjects to C(at_least_one).
    choices: [ all, at_least_one, at_most_one, none ]
    default: at_least_one
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new contract subject
  aci_contract_subject:
    hostname: apic
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

- name: Remove a contract subject
  aci_contract_subject:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: default
    state: absent

- name: Query a contract subject
  aci_contract_subject:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    contract: web_to_db
    subject: default
    state: query

- name: Query all contract subjects
  aci_contract_subject:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: query
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

MATCH_MAPPING = dict(all='All', at_least_one='AtleastOne', at_most_one='AtmostOne', none='None')


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        contract=dict(type='str', aliases=['contract_name']),
        subject=dict(type='str', aliases=['contract_subject', 'name', 'subject_name']),
        tenant=dict(type='str', aliases=['tenant_name']),
        priority=dict(type='str', choices=['unspecified', 'level1', 'level2', 'level3']),
        reverse_filter=dict(type='str', choices=['yes', 'no']),
        dscp=dict(type='str', aliases=['target']),
        description=dict(type='str', aliases=['descr']),
        consumer_match=dict(type='str', choices=['all', 'at_least_one', 'at_most_one', 'none']),
        provider_match=dict(type='str', choices=['all', 'at_least_one', 'at_most_one', 'none']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
        directive=dict(type='str', removed_in_version='2.4'),  # Deprecated starting from v2.4
        filter=dict(type='str', aliases=['filter_name'], removed_in_version='2.4'),  # Deprecated starting from v2.4
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['contract', 'subject', 'tenant']],
            ['state', 'present', ['contract', 'subject', 'tenant']],
        ],
    )

    subject = module.params['subject']
    priority = module.params['priority']
    reverse_filter = module.params['reverse_filter']
    contract = module.params['contract']
    dscp = module.params['dscp']
    description = module.params['description']
    filter_name = module.params['filter']
    directive = module.params['directive']
    consumer_match = module.params['consumer_match']
    if consumer_match is not None:
        consumer_match = MATCH_MAPPING[consumer_match]
    provider_match = module.params['provider_match']
    if provider_match is not None:
        provider_match = MATCH_MAPPING[provider_match]
    state = module.params['state']
    tenant = module.params['tenant']

    if directive is not None or filter_name is not None:
        module.fail_json(msg='Managing Contract Subjects to Filter bindings has been moved to M(aci_subject_bind_filter)')

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{}'.format(tenant),
            filter_target='eq(fvTenant.name, "{}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='vzBrCP',
            aci_rn='brc-{}'.format(contract),
            filter_target='eq(vzBrCP.name, "{}")'.format(contract),
            module_object=contract,
        ),
        subclass_2=dict(
            aci_class='vzSubj',
            aci_rn='subj-{}'.format(subject),
            filter_target='eq(vzSubj.name, "{}")'.format(subject),
            module_object=subject,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
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

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='vzSubj')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)

if __name__ == "__main__":
    main()
