#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_action_rule_profile
short_description: Manage action rule profiles on Cisco ACI fabrics
description:
- Manage action rule profiles on Cisco ACI fabrics.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The tenant used must exist before using this module in your playbook. The M(aci_tenant) module can be used for this.
options:
  action_rule:
    description:
    - The name of the action rule profile.
    aliases: [ action_rule_name, name ]
  description:
    description:
    - Description for the action rule profile.
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
- aci_action_rule_profile:
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

from ansible.module_utils.aci import ACIModule, aci_argument_spec
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
    )

    action_rule = module.params['action_rule']
    # tenant = module.params['tenant']
    description = module.params['description']
    state = module.params['state']

    aci = ACIModule(module)

    # TODO: This logic could be cleaner.
    if action_rule is not None:
        path = 'api/mo/uni/tn-%(tenant)s/attr-%(action_rule)s.json' % module.params
    elif state == 'query':
        # Query all objects
        path = 'api/node/class/rtctrlAttrP.json'
    else:
        module.fail_json(msg="Parameter 'action_rule' is required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='rtctrlAttrP', class_config=dict(name=action_rule, descr=description))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='rtctrlAttrP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
