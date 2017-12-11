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
module: aci_contract_subject_to_filter
short_description: Bind Contract Subjects to Filters on Cisco ACI fabrics (vz:RsSubjFiltAtt)
description:
- Bind Contract Subjects to Filters on Cisco ACI fabrics.
- More information from the internal APIC class
  I(vz:RsSubjFiltAtt) at U(https://developer.cisco.com/media/mim-ref/MO-vzRsSubjFiltAtt.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant), C(contract), C(subject), and C(filter_name) must exist before using this module in your playbook.
- The M(aci_tenant), M(aci_contract), M(aci_contract_subject), and M(aci_filter) modules can be used for these.
options:
  contract:
    description:
    - The name of the contract.
    aliases: [ contract_name ]
  filter:
    description:
    - The name of the Filter to bind to the Subject.
  log:
    description:
    - Determines if the binding should be set to log.
    - The APIC defaults new Subject to Filter bindings to C(none).
    choices: [ log, none ]
    aliases: [ directive ]
    default: none
  subject:
    description:
    - The name of the Contract Subject.
    aliases: [ contract_subject, subject_name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
  tenant:
    description:
    - The name of the tenant.
    required: yes
    aliases: [ tenant_name ]
extends_documentation_fragment: aci
'''

# FIXME: Add more, better examples
EXAMPLES = r'''
- aci_subject_filter_binding:
    hostname: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    tenant: '{{ tenant }}'
    contract: '{{ contract }}'
    subject: '{{ subject }}'
    filter: '{{ filter }}'
    log: '{{ log }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        contract=dict(type='str', aliases=['contract_name']),
        filter=dict(type='str', aliases=['filter_name']),
        log=dict(tyep='str', choices=['log', 'none'], aliases=['directive']),
        subject=dict(type='str', aliases=['contract_subject', 'subject_name']),
        tenant=dict(type='str', aliases=['tenant_name']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
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
        subclass_3=dict(
            aci_class='vzRsSubjFiltAtt',
            aci_rn='rssubjFiltAtt-{}'.format(filter_name),
            filter_target='eq(vzRsSubjFiltAtt.tnVzFilterName, "{}")'.format(filter_name),
            module_object=filter_name,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='vzRsSubjFiltAtt',
            class_config=dict(
                tnVzFilterName=filter_name,
                directives=log,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='vzRsSubjFiltAtt')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    # Remove subject_filter used to build URL from module.params
    module.params.pop('subject_filter')

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
