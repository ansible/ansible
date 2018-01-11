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
module: aci_tenant_action_rule_profile
short_description: Manage action rule profiles on Cisco ACI fabrics (rtctrl:AttrP)
description:
- Manage action rule profiles on Cisco ACI fabrics.
- More information from the internal APIC class
  I(rtctrl:AttrP) at U(https://developer.cisco.com/media/mim-ref/MO-rtctrlAttrP.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant) used must exist before using this module in your playbook.
  The M(aci_tenant) module can be used for this.
options:
  action_rule:
    description:
    - The name of the action rule profile.
    aliases: [ action_rule_name, name ]
  description:
    description:
    - The description for the action rule profile.
    aliases: [ descr ]
  tenant:
    description:
    - The name of the tenant.
    aliases: [ tenant_name ]
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
- aci_tenant_action_rule_profile:
    hostname: '{{ inventory_hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    action_rule: '{{ action_rule }}'
    description: '{{ descr }}'
    tenant: '{{ tenant }}'
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        action_rule=dict(type='str', required=False, aliases=['action_rule_name', 'name']),  # Not required for querying all objects
        tenant=dict(type='str', required=False, aliases=['tenant_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['action_rule', 'tenant']],
            ['state', 'present', ['action_rule', 'tenant']],
        ],
    )

    action_rule = module.params['action_rule']
    description = module.params['description']
    state = module.params['state']
    tenant = module.params['tenant']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{}'.format(tenant),
            filter_target='eq(fvTenant.name, "{}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='rtctrlAttrP',
            aci_rn='attr-{}'.format(action_rule),
            filter_target='eq(rtctrlAttrP.name, "{}")'.format(action_rule),
            module_object=action_rule,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='rtctrlAttrP',
            class_config=dict(
                name=action_rule,
                descr=description,
            ),

        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='rtctrlAttrP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
