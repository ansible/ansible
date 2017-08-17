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
module: aci_contract
short_description: Manage contract resources on Cisco ACI fabrics (vz:BrCP)
description:
- Manage Contract resources on Cisco ACI fabrics.
- More information from the internal APIC class
  I(vz:BrCP) at U(https://developer.cisco.com/media/mim-ref/MO-vzBrCP.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- This module does not manage Contract Subjects, see M(aci_contract_subject) to do this.
  Contract Subjects can still be removed using this module.
- The C(tenant) used must exist before using this module in your playbook.
  The M(aci_tenant) module can be used for this.
options:
  contract:
    description:
    - The name of the contract.
    required: yes
    aliases: [ contract_name, name ]
  description:
    description:
    - Description for the contract.
    aliases: [ descr ]
  tenant:
    description:
    - The name of the tenant.
    required: yes
    aliases: [ tenant_name ]
  scope:
    description:
    - The scope of a service contract.
    choices: [ application-profile, context, global, tenant ]
    default: 'context'
  priority:
    description:
    - The desired QoS class to be used.
    default: unspecified
    choices: [ level1, level2, level3, unspecified ]
  dscp:
    description:
    - The target Differentiated Service (DSCP) value.
    choices: [ AF11, AF12, AF13, AF21, AF22, AF23, AF31, AF32, AF33, AF41, AF42, AF43, CS0, CS1, CS2, CS3, CS4, CS5, CS6, CS7, EF, VA, unspecified ]
    default: unspecified
    aliases: [ target ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

# FIXME: Add more, better examples
EXAMPLES = r'''
- aci_contract:
    hostname: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    contract: '{{ contract }}'
    description: '{{ descr }}'
    tenant: '{{ tenant }}'
    scope: '{{ scope }}'
    priority: '{{ priority }}'
    target: '{{ target }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        contract=dict(type='str', required=False, aliases=['contract_name', 'name']),  # Not required for querying all objects
        tenant=dict(type='str', required=True, aliases=['tenant_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        scope=dict(type='str', choices=['application-profile', 'context', 'global', 'tenant']),
        priority=dict(type='str', choices=['level1', 'level2', 'level3', 'unspecified']),  # No default provided on purpose
        dscp=dict(type='str',
                  choices=['AF11', 'AF12', 'AF13', 'AF21', 'AF22', 'AF23', 'AF31', 'AF32', 'AF33', 'AF41', 'AF42', 'AF43',
                           'CS0', 'CS1', 'CS2', 'CS3', 'CS4', 'CS5', 'CS6', 'CS7', 'EF', 'VA', 'unspecified'],
                  aliases=['target']),  # No default provided on purpose
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    contract = module.params['contract']
    tenant = module.params['tenant']
    description = module.params['description']
    scope = module.params['scope']
    priority = module.params['priority']
    target = module.params['target']
    state = module.params['state']

    aci = ACIModule(module)

    # TODO: This logic could be cleaner.
    if contract is not None:
        if tenant is not None:
            path = 'api/mo/uni/tn-%(tenant)s/brc-%(contract)s.json' % module.params
        elif state == 'query':
            path = 'api/mo/uni/tn-%(tenant)s.json?rsp-subtree=children&rsp-subtree-class=vzBrCP&rsp-subtree-include=no-scoped' % module.params
        else:
            module.fail_json(msg="Parameters 'tenant' is required for state 'absent' or 'present'")
    elif state == 'query':
        # Query all objects
        path = 'api/node/class/vzBrCP.json'
    else:
        module.fail_json(msg="Parameter 'contract' is required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='vzBrCP', class_config=dict(name=contract, descr=description, scope=scope, prio=priority, targetDscp=target))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='vzBrCP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
