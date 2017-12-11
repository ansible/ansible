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
module: aci_ap
short_description: Manage top level Application Profile (AP) objects on Cisco ACI fabrics (fv:Ap)
description:
- Manage top level Application Profile (AP) objects on Cisco ACI fabrics
- More information from the internal APIC class
  I(fv:Ap) at U(https://developer.cisco.com/media/mim-ref/MO-fvAp.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- This module does not manage EPGs, see M(aci_epg) to do this.
- The C(tenant) used must exist before using this module in your playbook.
  The M(aci_tenant) module can be used for this.
options:
   tenant:
     description:
     - The name of an existing tenant.
     required: yes
     aliases: [ tenant_name ]
   ap:
     description:
     - The name of the application network profile.
     required: yes
     aliases: [ app_profile, app_profile_name, name ]
   descr:
     description:
     - Description for the AP.
   state:
     description:
     - Use C(present) or C(absent) for adding or removing.
     - Use C(query) for listing an object or multiple objects.
     choices: [ absent, present, query ]
     default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Add a new AP
  aci_ap:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: default
    description: default ap
    state: present

- name: Remove an AP
  aci_ap:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: default
    state: absent

- name: Query an AP
  aci_ap:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant: production
    ap: default
    state: query

- name: Query all APs
  aci_ap:
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


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        tenant=dict(type='str', aliases=['tenant_name']),  # tenant not required for querying all APs
        ap=dict(type='str', aliases=['app_profile', 'app_profile_name', 'name']),
        description=dict(type='str', aliases=['descr'], required=False),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['tenant', 'ap']],
            ['state', 'present', ['tenant', 'ap']],
        ],
    )

    # tenant = module.params['tenant']
    ap = module.params['ap']
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
            aci_class='fvAp',
            aci_rn='ap-{}'.format(ap),
            filter_target='eq(fvAp.name, "{}")'.format(ap),
            module_object=ap,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='fvAp',
            class_config=dict(
                name=ap,
                descr=description,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvAp')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
